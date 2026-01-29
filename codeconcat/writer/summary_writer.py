"""File persistence for AI-generated summaries."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base_types import CodeConCatConfig, ParsedFileData

logger = logging.getLogger(__name__)


class SummaryWriter:
    """Handles saving AI summaries and meta-overviews to disk."""

    def __init__(self, config: CodeConCatConfig):
        """Initialize the summary writer.

        Args:
            config: Global configuration object
        """
        self.config = config

        # Resolve summaries directory path
        summaries_path = Path(config.ai_summaries_dir)
        if not summaries_path.is_absolute():
            # Make it relative to output file's directory
            if config.output:
                output_dir = Path(config.output).parent
                self.summaries_dir = output_dir / summaries_path
            else:
                # Fall back to current directory
                self.summaries_dir = Path.cwd() / summaries_path
        else:
            self.summaries_dir = summaries_path

        logger.info(f"Summary writer initialized with directory: {self.summaries_dir}")

    def ensure_summary_dirs(self):
        """Create the summary directories if they don't exist."""
        try:
            # Create main summaries directory
            self.summaries_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            individual_dir = self.summaries_dir / "individual"
            individual_dir.mkdir(exist_ok=True)

            logger.debug(f"Summary directories ensured at {self.summaries_dir}")
        except Exception as e:
            logger.error(f"Failed to create summary directories: {e}")
            raise

    def _hash_file_path(self, file_path: str) -> str:
        """Generate a consistent hash for a file path.

        Args:
            file_path: The file path to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]

    def save_individual_summary(
        self,
        file_data: ParsedFileData,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> Path | None:
        """Save an individual file summary to disk.

        Args:
            file_data: The parsed file data
            summary: The AI-generated summary
            metadata: Optional metadata (tokens, cost, model, etc.)

        Returns:
            Path to the saved summary file, or None if save failed
        """
        if not summary:
            logger.debug(f"Skipping save for {file_data.file_path}: no summary")
            return None

        try:
            self.ensure_summary_dirs()

            # Generate filename from file path hash
            file_hash = self._hash_file_path(file_data.file_path)
            summary_path = self.summaries_dir / "individual" / f"{file_hash}.json"

            # Prepare summary data
            summary_data = {
                "file_path": file_data.file_path,
                "language": file_data.language,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            # Add optional token stats if available
            if hasattr(file_data, "token_stats") and file_data.token_stats:
                summary_data["file_stats"] = {
                    "gpt4_tokens": file_data.token_stats.gpt4_tokens,
                    "claude_tokens": file_data.token_stats.claude_tokens,
                }

            # Write to file
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2)

            logger.info(f"Saved summary for {file_data.file_path} to {summary_path}")
            return summary_path

        except Exception as e:
            logger.error(f"Failed to save summary for {file_data.file_path}: {e}")
            return None

    def save_meta_overview(
        self,
        meta_overview: str,
        files_summarized: int,
        metadata: dict[str, Any] | None = None,
        tree_structure: str | None = None,
    ) -> Path | None:
        """Save the meta-overview to disk.

        Args:
            meta_overview: The meta-overview text
            files_summarized: Number of files included in the overview
            metadata: Optional metadata (tokens, cost, model, etc.)
            tree_structure: Optional tree structure visualization

        Returns:
            Path to the saved meta-overview file, or None if save failed
        """
        if not meta_overview:
            logger.debug("Skipping meta-overview save: no content")
            return None

        try:
            self.ensure_summary_dirs()

            meta_path = self.summaries_dir / "meta_overview.json"

            # Prepare meta-overview data
            meta_data = {
                "meta_overview": meta_overview,
                "files_summarized": files_summarized,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            # Add tree structure if provided
            if tree_structure:
                meta_data["tree_structure"] = tree_structure

            # Write to file
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, indent=2)

            logger.info(f"Saved meta-overview to {meta_path}")
            return meta_path

        except Exception as e:
            logger.error(f"Failed to save meta-overview: {e}")
            return None

    def load_individual_summary(self, file_path: str) -> dict[str, Any] | None:
        """Load a previously saved individual summary.

        Args:
            file_path: The file path to load summary for

        Returns:
            Dictionary with summary data, or None if not found
        """
        try:
            file_hash = self._hash_file_path(file_path)
            summary_path = self.summaries_dir / "individual" / f"{file_hash}.json"

            if not summary_path.exists():
                return None

            with open(summary_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data

        except Exception as e:
            logger.warning(f"Failed to load summary for {file_path}: {e}")
            return None

    def load_meta_overview(self) -> dict[str, Any] | None:
        """Load a previously saved meta-overview.

        Returns:
            Dictionary with meta-overview data, or None if not found
        """
        try:
            meta_path = self.summaries_dir / "meta_overview.json"

            if not meta_path.exists():
                return None

            with open(meta_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data

        except Exception as e:
            logger.warning(f"Failed to load meta-overview: {e}")
            return None
