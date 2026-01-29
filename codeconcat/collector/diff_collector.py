"""Git diff collector for differential outputs between Git refs."""

import contextlib
import logging
import os
from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from gitdb.exc import BadName

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    DiffMetadata,
    ParsedFileData,
)
from codeconcat.language_map import ext_map, get_language_guesslang
from codeconcat.parser.unified_pipeline import parse_code_files

logger = logging.getLogger(__name__)


class DiffCollector:
    """Collects differential file changes between two Git refs.

    This collector uses GitPython to analyze changes between two Git references
    (branches, tags, or commit SHAs) and generates AnnotatedFileData with diff
    content and metadata.
    """

    def __init__(
        self,
        repo_path: str,
        from_ref: str,
        to_ref: str,
        config: CodeConCatConfig,
    ):
        """Initialize the diff collector.

        Args:
            repo_path: Path to the Git repository
            from_ref: Starting Git ref (branch, tag, or commit SHA)
            to_ref: Ending Git ref (branch, tag, or commit SHA)
            config: CodeConCat configuration

        Raises:
            ValueError: If the path is not a valid Git repository
        """
        self.repo_path = Path(repo_path).resolve()
        self.from_ref = from_ref
        self.to_ref = to_ref
        self.config = config

        try:
            self.repo = Repo(self.repo_path)
            if self.repo.bare:
                raise ValueError(f"Cannot use bare repository at {self.repo_path}")
        except InvalidGitRepositoryError as e:
            raise ValueError(f"Path {self.repo_path} is not a valid Git repository") from e

        # Validate refs
        is_valid, error_msg = self.validate_refs()
        if not is_valid:
            raise ValueError(error_msg)

    def validate_refs(self) -> tuple[bool, str]:
        """Validate that both Git refs exist and are accessible.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.repo.commit(self.from_ref)
        except (GitCommandError, ValueError, BadName):
            return False, f"Invalid from_ref: {self.from_ref}"

        try:
            self.repo.commit(self.to_ref)
        except (GitCommandError, ValueError, BadName):
            return False, f"Invalid to_ref: {self.to_ref}"

        return True, ""

    def collect_diffs(self) -> list[AnnotatedFileData]:
        """Collect all diffs between the two refs.

        Returns:
            List of AnnotatedFileData objects with diff content
        """
        logger.info(f"Collecting diffs between {self.from_ref} and {self.to_ref}")

        from_commit = self.repo.commit(self.from_ref)
        to_commit = self.repo.commit(self.to_ref)

        # Get the diff between commits
        diff_index = from_commit.diff(to_commit, create_patch=True)

        annotated_files = []
        for diff_item in diff_index:
            # Skip binary files if configured
            if diff_item.b_blob and diff_item.b_blob.binsha:
                try:
                    # Check if file is binary
                    diff_item.b_blob.data_stream.read(1)
                    is_binary = False
                except UnicodeDecodeError:
                    is_binary = True
                finally:
                    # Reset stream
                    if hasattr(diff_item.b_blob.data_stream, "seek"):
                        diff_item.b_blob.data_stream.seek(0)

                if is_binary:
                    logger.debug(f"Skipping binary file: {diff_item.b_path}")
                    if self.config.get("include_binary_files", False):
                        # Include binary file metadata without content
                        annotated_file = self._create_binary_file_entry(
                            diff_item, from_commit, to_commit
                        )
                        if annotated_file:
                            annotated_files.append(annotated_file)
                    continue

            # Process text file diff
            annotated_file = self._process_diff_item(diff_item, from_commit, to_commit)
            if annotated_file:
                annotated_files.append(annotated_file)

        logger.info(f"Collected {len(annotated_files)} file diffs")
        return annotated_files

    def _process_diff_item(self, diff_item, from_commit, to_commit) -> AnnotatedFileData | None:
        """Process a single diff item into AnnotatedFileData.

        Args:
            diff_item: GitPython diff item
            from_commit: Starting commit
            to_commit: Ending commit

        Returns:
            AnnotatedFileData with diff content, or None if skipped
        """
        # Determine file path and change type
        if diff_item.new_file:
            file_path = diff_item.b_path
            change_type = "added"
            content = (
                diff_item.b_blob.data_stream.read().decode("utf-8", errors="replace")
                if diff_item.b_blob
                else ""
            )
        elif diff_item.deleted_file:
            file_path = diff_item.a_path
            change_type = "deleted"
            content = (
                diff_item.a_blob.data_stream.read().decode("utf-8", errors="replace")
                if diff_item.a_blob
                else ""
            )
        elif diff_item.renamed_file:
            file_path = diff_item.b_path
            change_type = "renamed"
            content = (
                diff_item.b_blob.data_stream.read().decode("utf-8", errors="replace")
                if diff_item.b_blob
                else ""
            )
        else:
            file_path = diff_item.b_path or diff_item.a_path
            change_type = "modified"
            content = (
                diff_item.b_blob.data_stream.read().decode("utf-8", errors="replace")
                if diff_item.b_blob
                else ""
            )

        # Apply path filters
        if not self._should_include_file(file_path):
            logger.debug(f"Skipping filtered file: {file_path}")
            return None

        # Determine language
        language = self._get_language(file_path)

        # Get diff content
        diff_content = diff_item.diff.decode("utf-8", errors="replace") if diff_item.diff else ""

        # Calculate diff statistics
        additions = 0
        deletions = 0
        for line in diff_content.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        # Create diff metadata
        diff_metadata = DiffMetadata(
            from_ref=str(from_commit),
            to_ref=str(to_commit),
            change_type=change_type,
            additions=additions,
            deletions=deletions,
            binary=False,
            old_path=diff_item.a_path if diff_item.renamed_file else None,
            similarity=diff_item.score if diff_item.renamed_file else None,
        )

        # For diff processing, we need to handle files that may not exist on disk
        # (e.g., new files only in feature branch). We'll use a temp file approach
        # for security scanning but keep the absolute path for display
        absolute_path = str((self.repo_path / file_path).resolve())

        # Parse file content if not deleted
        if change_type != "deleted" and content:
            # Create a temporary file for parsing/scanning if needed
            import tempfile

            temp_file = None
            temp_file_path = absolute_path

            # If file doesn't exist on disk (e.g., new file in diff), create temp file
            if not Path(absolute_path).exists() and content:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=Path(file_path).suffix, delete=False
                ) as tf:
                    tf.write(content)
                    temp_file = tf.name
                    temp_file_path = tf.name

            # Create ParsedFileData for parsing with temp path for scanning
            temp_parsed = ParsedFileData(
                file_path=temp_file_path,
                content=content,
                language=language,
                declarations=[],
                imports=[],
            )

            # Parse the file to extract declarations
            parsed_files, _ = parse_code_files([temp_parsed], self.config)
            if parsed_files:
                parsed_data = parsed_files[0]
                # Restore the original path for display
                parsed_data.file_path = absolute_path
            else:
                parsed_data = temp_parsed
                parsed_data.file_path = absolute_path

            # Clean up temp file if created
            if temp_file:
                with contextlib.suppress(BaseException):
                    Path(temp_file).unlink()
        else:
            parsed_data = ParsedFileData(
                file_path=absolute_path,
                language=language,
                content=content,
                declarations=[],
                imports=[],
            )

        # Create annotated file data
        annotated_file = AnnotatedFileData(
            file_path=absolute_path,
            language=language,
            content=content,
            annotated_content=content,
            summary=f"Diff: {change_type} file with {additions} additions and {deletions} deletions",
            declarations=parsed_data.declarations,
            imports=parsed_data.imports,
            diff_content=diff_content,
            diff_metadata=diff_metadata,
        )

        return annotated_file

    def _create_binary_file_entry(
        self, diff_item, from_commit, to_commit
    ) -> AnnotatedFileData | None:
        """Create an entry for a binary file with metadata only.

        Args:
            diff_item: GitPython diff item
            from_commit: Starting commit
            to_commit: Ending commit

        Returns:
            AnnotatedFileData for binary file, or None if skipped
        """
        # Determine file path and change type
        if diff_item.new_file:
            file_path = diff_item.b_path
            change_type = "added"
        elif diff_item.deleted_file:
            file_path = diff_item.a_path
            change_type = "deleted"
        elif diff_item.renamed_file:
            file_path = diff_item.b_path
            change_type = "renamed"
        else:
            file_path = diff_item.b_path or diff_item.a_path
            change_type = "modified"

        # Apply path filters
        if not self._should_include_file(file_path):
            return None

        # Create diff metadata for binary file
        diff_metadata = DiffMetadata(
            from_ref=str(from_commit),
            to_ref=str(to_commit),
            change_type=change_type,
            additions=0,
            deletions=0,
            binary=True,
            old_path=diff_item.a_path if diff_item.renamed_file else None,
            similarity=diff_item.score if diff_item.renamed_file else None,
        )

        # Create annotated file data for binary file with absolute path
        absolute_path = str((self.repo_path / file_path).resolve())
        annotated_file = AnnotatedFileData(
            file_path=absolute_path,
            language="binary",
            content="[Binary file]",
            annotated_content="[Binary file]",
            summary=f"Binary file {change_type}",
            declarations=[],
            imports=[],
            diff_content=f"Binary file {change_type}",
            diff_metadata=diff_metadata,
        )

        return annotated_file

    def _should_include_file(self, file_path: str) -> bool:
        """Check if a file should be included based on config filters.

        For diff mode, we're more permissive with filters since we want to show
        all changes between refs, not just code files.

        Args:
            file_path: Path to the file

        Returns:
            True if file should be included
        """
        # Skip certain system files even in diff mode
        system_excludes = [
            ".git/",
            ".gitmodules",
            ".gitattributes",
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
        ]
        for pattern in system_excludes:
            if self._match_pattern(file_path, pattern):
                return False

        # In diff mode, be more permissive - only exclude truly unwanted files
        # Don't apply include_paths filter for diffs - show all changed files

        # Still apply some exclude patterns but be selective
        if self.config.exclude_paths:
            # Only exclude true system/build artifacts, not config files
            critical_excludes = [
                "__pycache__/",
                "*.pyc",
                "*.pyo",
                "node_modules/",
                "venv/",
                ".venv/",
                "build/",
                "dist/",
                "*.egg-info/",
                ".pytest_cache/",
                "htmlcov/",
                "coverage/",
                "*.exe",
                "*.dll",
                "*.so",
                "*.dylib",
                "*.bin",
                "*.jar",
                "*.war",
                "*.zip",
                "*.tar.gz",
                "*.rar",
            ]
            for pattern in critical_excludes:
                if self._match_pattern(file_path, pattern):
                    logger.debug(f"Excluding {file_path} - matches critical pattern {pattern}")
                    return False

        # Apply language filters if specified
        if self.config.include_languages:
            language = self._get_language(file_path)
            if language not in self.config.include_languages:
                return False

        if self.config.exclude_languages:
            language = self._get_language(file_path)
            if language in self.config.exclude_languages:
                return False

        return True

    def _match_pattern(self, file_path: str, pattern: str) -> bool:
        """Match a file path against a glob pattern.

        Args:
            file_path: Path to match
            pattern: Glob pattern

        Returns:
            True if path matches pattern
        """
        from fnmatch import fnmatch

        return fnmatch(file_path, pattern) or fnmatch(os.path.basename(file_path), pattern)

    def _get_language(self, file_path: str) -> str:
        """Determine the language of a file.

        Args:
            file_path: Path to the file

        Returns:
            Language identifier string
        """
        ext = os.path.splitext(file_path)[1].lower()

        # Check custom extension map first
        if ext in self.config.custom_extension_map:
            return self.config.custom_extension_map[ext]

        # Check standard extension map
        if ext in ext_map:
            return ext_map[ext]

        # Try to guess language if available
        try:
            if callable(get_language_guesslang):
                with open(os.path.join(self.repo_path, file_path)) as f:
                    content = f.read()
                    lang = get_language_guesslang(content)
                    return lang if lang else "unknown"
        except Exception:
            pass

        return "unknown"

    def get_changed_files(self) -> list[str]:
        """Get a list of all changed file paths between refs.

        Returns:
            List of file paths that changed
        """
        from_commit = self.repo.commit(self.from_ref)
        to_commit = self.repo.commit(self.to_ref)
        diff_index = from_commit.diff(to_commit)

        changed_files = []
        for diff_item in diff_index:
            if diff_item.b_path:
                changed_files.append(diff_item.b_path)
            elif diff_item.a_path:
                changed_files.append(diff_item.a_path)

        return changed_files
