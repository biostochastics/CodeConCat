"""Integration tests for differential outputs functionality."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from git import Repo

from codeconcat.base_types import DiffMetadata
from codeconcat.cli.commands.run import run_command
from codeconcat.collector.diff_collector import DiffCollector
from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.main import run_codeconcat
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.text_writer import write_text
from codeconcat.writer.xml_writer import write_xml


@pytest.fixture
def test_repo(tmp_path):
    """Create a test Git repository with multiple commits."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize repository
    repo = Repo.init(repo_path)

    # Configure git user for commits
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial commit on main branch
    file1 = repo_path / "file1.py"
    file1.write_text("def hello():\n    return 'Hello'\n")
    repo.index.add(["file1.py"])
    repo.index.commit("Initial commit")

    # Ensure the branch is named "main" (git default may be "master" on some systems)
    if repo.active_branch.name != "main":
        repo.active_branch.rename("main")

    # Create feature branch
    feature_branch = repo.create_head("feature-branch")
    feature_branch.checkout()

    # Modify file1 and add file2 on feature branch
    file1.write_text(
        "def hello():\n    return 'Hello World'\n\ndef goodbye():\n    return 'Goodbye'\n"
    )
    file2 = repo_path / "file2.py"
    file2.write_text("class TestClass:\n    pass\n")
    repo.index.add(["file1.py", "file2.py"])
    repo.index.commit("Feature changes")

    # Go back to main
    repo.heads.main.checkout()

    return repo_path


@pytest.fixture
def config():
    """Create a test configuration."""
    builder = ConfigBuilder()
    builder.with_defaults()
    config = builder.build()
    return config


class TestDiffCollector:
    """Test the DiffCollector class."""

    def test_collect_diffs_basic(self, test_repo, config):
        """Test basic diff collection between branches."""
        collector = DiffCollector(str(test_repo), "main", "feature-branch", config)

        diffs = collector.collect_diffs()

        # Should have changes for file1.py and file2.py
        assert len(diffs) == 2

        # Check file paths - extract just the basename for comparison
        file_paths = [os.path.basename(d.file_path) for d in diffs]
        assert "file1.py" in file_paths
        assert "file2.py" in file_paths

        # Check change types
        for diff in diffs:
            basename = os.path.basename(diff.file_path)
            if basename == "file1.py":
                assert diff.diff_metadata.change_type == "modified"
                assert diff.diff_metadata.additions > 0
                assert diff.diff_metadata.deletions > 0
            elif basename == "file2.py":
                assert diff.diff_metadata.change_type == "added"
                assert diff.diff_metadata.additions > 0
                assert diff.diff_metadata.deletions == 0

    def test_diff_metadata(self, test_repo, config):
        """Test that diff metadata is properly populated."""
        collector = DiffCollector(str(test_repo), "main", "feature-branch", config)

        diffs = collector.collect_diffs()

        for diff in diffs:
            # Check metadata exists
            assert diff.diff_metadata is not None
            assert isinstance(diff.diff_metadata, DiffMetadata)

            # Check required fields
            assert diff.diff_metadata.from_ref
            assert diff.diff_metadata.to_ref
            assert diff.diff_metadata.change_type in ["added", "modified", "deleted", "renamed"]
            assert isinstance(diff.diff_metadata.additions, int)
            assert isinstance(diff.diff_metadata.deletions, int)
            assert isinstance(diff.diff_metadata.binary, bool)

            # Check diff content
            assert diff.diff_content is not None
            if diff.diff_metadata.change_type != "deleted":
                assert "@@" in diff.diff_content  # Should have diff markers

    def test_invalid_refs(self, test_repo, config):
        """Test handling of invalid Git refs."""
        with pytest.raises(ValueError, match="Invalid from_ref"):
            DiffCollector(str(test_repo), "nonexistent-branch", "main", config)

        with pytest.raises(ValueError, match="Invalid to_ref"):
            DiffCollector(str(test_repo), "main", "nonexistent-branch", config)

    def test_get_changed_files(self, test_repo, config):
        """Test getting list of changed files."""
        collector = DiffCollector(str(test_repo), "main", "feature-branch", config)

        changed_files = collector.get_changed_files()

        assert len(changed_files) == 2
        assert "file1.py" in changed_files
        assert "file2.py" in changed_files


class TestWriterDiffSupport:
    """Test that all writers properly handle diff output."""

    @pytest.fixture
    def diff_data(self):
        """Create sample diff data."""
        from codeconcat.base_types import AnnotatedFileData

        diff_meta = DiffMetadata(
            from_ref="main",
            to_ref="feature",
            change_type="modified",
            additions=5,
            deletions=2,
            binary=False,
        )

        return [
            AnnotatedFileData(
                file_path="test.py",
                language="python",
                content="def test():\n    pass",
                annotated_content="def test():\n    pass",
                summary="Modified test file",
                declarations=[],
                imports=[],
                diff_content="@@ -1,2 +1,5 @@\n def test():\n-    pass\n+    return True",
                diff_metadata=diff_meta,
            )
        ]

    def test_markdown_writer_diff(self, diff_data, config, tmp_path):
        """Test MarkdownWriter handles diff data."""
        output_file = tmp_path / "test.md"

        # Use write_markdown function directly
        markdown_content = write_markdown(diff_data, config, "")
        output_file.write_text(markdown_content)

        content = output_file.read_text()

        # Check for diff-specific content
        assert "Differential Analysis" in content
        assert "MODIFIED" in content or "modified" in content.lower()
        assert "+5 / -2" in content or "+5" in content
        assert "```diff" in content
        assert "@@ -1,2 +1,5 @@" in content

    def test_json_writer_diff(self, diff_data, config, tmp_path):
        """Test JSONWriter includes diff metadata."""
        output_file = tmp_path / "test.json"

        # Use write_json function directly
        json_content = write_json(diff_data, config, "")
        output_file.write_text(json_content)

        with open(output_file) as f:
            data = json.load(f)

        # Check for diff metadata in JSON
        file_data = data["files"][0]
        assert "diff" in file_data
        assert file_data["diff"]["change_type"] == "modified"
        assert file_data["diff"]["additions"] == 5
        assert file_data["diff"]["deletions"] == 2
        assert "content" in file_data["diff"]

    def test_xml_writer_diff(self, diff_data, config, tmp_path):
        """Test XMLWriter includes diff information."""
        output_file = tmp_path / "test.xml"

        # Use write_xml function directly
        xml_content = write_xml(diff_data, config, "")
        output_file.write_text(xml_content)

        content = output_file.read_text()

        # Check for diff elements in XML
        assert "<diff_info>" in content
        assert '<diff change_type="modified"' in content
        assert 'additions="5"' in content
        assert 'deletions="2"' in content
        assert "<diff" in content

    def test_text_writer_diff(self, diff_data, config, tmp_path):
        """Test TextWriter handles diff output."""
        output_file = tmp_path / "test.txt"

        # Use write_text function directly
        text_content = write_text(diff_data, config, "")
        output_file.write_text(text_content)

        content = output_file.read_text()

        # Check for diff indicators
        assert "[MODIFIED]" in content or "MODIFIED" in content
        assert "+" in content  # additions
        assert "-" in content  # deletions


class TestCLIIntegration:
    """Test CLI integration of diff functionality."""

    def test_cli_diff_options(self, test_repo, tmp_path):
        """Test that CLI accepts diff options."""
        output_file = tmp_path / "diff_output.md"

        with patch("codeconcat.cli.commands.run.Path.cwd", return_value=test_repo):
            # Test with CLI arguments
            from codeconcat.cli.commands.run import OutputFormat

            run_command(
                target=str(test_repo),
                diff_from="main",
                diff_to="feature-branch",
                output=output_file,
                format=OutputFormat.MARKDOWN,
                disable_progress=True,
            )

        # Check output was created
        assert output_file.exists()
        content = output_file.read_text()

        # Verify diff content
        assert "file1.py" in content
        assert "file2.py" in content

    def test_main_diff_mode_detection(self, test_repo, config):
        """Test that main.py properly detects diff mode."""
        # Add diff options to config
        config.diff_from = "main"
        config.diff_to = "feature-branch"
        config.target_path = str(test_repo)
        config.output = "test_diff.md"
        config.format = "markdown"

        with patch("codeconcat.main.Path.cwd", return_value=Path(test_repo)):
            result = run_codeconcat(config)

        # Should succeed
        assert result is not None

        # Check output file was created
        output_path = Path(test_repo) / "test_diff.md"
        if output_path.exists():
            content = output_path.read_text()
            assert "Differential Analysis" in content or "diff" in content.lower()


class TestAIDiffSummarization:
    """Test AI summarization for diffs."""

    @pytest.fixture
    def ai_config(self, config):
        """Create config with AI enabled."""
        config.enable_ai_summary = True
        config.ai_provider = "openai"
        config.ai_api_key = "test-key"
        config.ai_model = "gpt-3.5-turbo"
        config.ai_min_file_lines = 0  # Allow AI summarization for all files
        return config

    def test_diff_summary_prompt_creation(self):
        """Test that diff-specific prompts are created."""
        from codeconcat.base_types import ParsedFileData
        from codeconcat.processor.summarization_processor import SummarizationProcessor

        # Create mock config
        config = MagicMock()
        config.enable_ai_summary = True

        processor = SummarizationProcessor(config)

        # Create diff data
        parsed_file = ParsedFileData(
            file_path="test.py",
            language="python",
            content="def test(): pass",
            declarations=[],
            imports=[],
        )

        # Add diff metadata
        parsed_file.diff_metadata = DiffMetadata(
            from_ref="main",
            to_ref="feature",
            change_type="modified",
            additions=10,
            deletions=5,
            binary=False,
        )
        parsed_file.diff_content = "@@ -1,5 +1,10 @@\n+new code\n-old code"

        # Create prompt
        prompt = processor._create_diff_summary_prompt(parsed_file, parsed_file.diff_content)

        # Verify prompt contains diff-specific information
        assert "main" in prompt
        assert "feature" in prompt
        assert "modified" in prompt.lower()
        assert "+10 / -5" in prompt or "10" in prompt
        assert "purpose and impact" in prompt.lower()

    @patch("codeconcat.ai.get_ai_provider")
    async def test_ai_diff_summarization(self, mock_get_provider, ai_config):
        """Test that AI summarization works with diffs."""
        from codeconcat.ai import SummarizationResult
        from codeconcat.base_types import ParsedFileData
        from codeconcat.processor.summarization_processor import SummarizationProcessor

        # Mock AI provider
        mock_provider = MagicMock()

        # Create async mock that returns the result
        async def async_summarize(*args, **kwargs):  # noqa: ARG001
            return SummarizationResult(
                summary="This change refactors the authentication logic for better security.",
                tokens_used=100,
                cost_estimate=0.01,
                model_used="gpt-3.5-turbo",
                cached=False,
                error=None,
            )

        mock_provider.summarize_code = AsyncMock(side_effect=async_summarize)
        mock_get_provider.return_value = mock_provider

        processor = SummarizationProcessor(ai_config)
        processor.ai_provider = mock_provider

        # Create diff data
        parsed_file = ParsedFileData(
            file_path="auth.py",
            language="python",
            content="def authenticate(): pass",
            declarations=[],
            imports=[],
        )

        parsed_file.diff_metadata = DiffMetadata(
            from_ref="main",
            to_ref="security-fix",
            change_type="modified",
            additions=20,
            deletions=10,
            binary=False,
        )
        parsed_file.diff_content = "@@ -1,10 +1,20 @@\n+secure code\n-insecure code"

        # Process file
        result = await processor.process_file(parsed_file)

        # Verify AI was called with diff context
        mock_provider.summarize_code.assert_called_once()
        call_args = mock_provider.summarize_code.call_args

        # Check that diff information was passed
        content_arg = call_args[0][0]
        assert "main" in content_arg
        assert "security-fix" in content_arg

        # Check result
        assert (
            result.ai_summary
            == "This change refactors the authentication logic for better security."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
