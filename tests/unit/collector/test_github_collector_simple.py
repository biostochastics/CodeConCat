"""Simple tests for GitHub repository collector functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess

from codeconcat.collector.github_collector import (
    parse_git_url,
    collect_git_repo,
    build_git_clone_url,
)
from codeconcat.base_types import CodeConCatConfig, ParsedFileData


class TestParseGitUrl:
    """Test Git URL parsing functionality."""

    def test_parse_shorthand_owner_repo(self):
        """Test parsing owner/repo shorthand."""
        owner, repo, ref = parse_git_url("octocat/Hello-World")
        assert owner == "octocat"
        assert repo == "Hello-World"
        assert ref is None

    def test_parse_shorthand_with_branch(self):
        """Test parsing owner/repo/branch shorthand."""
        owner, repo, ref = parse_git_url("octocat/Hello-World/main")
        assert owner == "octocat"
        assert repo == "Hello-World"
        assert ref == "main"

    def test_parse_https_url(self):
        """Test parsing HTTPS URL."""
        owner, repo, ref = parse_git_url("https://github.com/octocat/Hello-World.git")
        assert owner == "octocat"
        assert repo == "Hello-World"
        assert ref is None

    def test_parse_ssh_url(self):
        """Test parsing SSH URL."""
        owner, repo, ref = parse_git_url("git@github.com:octocat/Hello-World.git")
        assert owner == "octocat"
        assert repo == "Hello-World"
        assert ref is None

    def test_parse_invalid_url(self):
        """Test parsing invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Git URL"):
            parse_git_url("not-a-valid-url")


class TestBuildGitCloneUrl:
    """Test Git clone URL building."""

    def test_build_https_url(self):
        """Test building HTTPS clone URL."""
        url = build_git_clone_url("octocat/Hello-World", "octocat", "Hello-World")
        assert url == "https://github.com/octocat/Hello-World.git"

    def test_build_url_with_token(self):
        """Test building URL with GitHub token."""
        url = build_git_clone_url("octocat/private-repo", "octocat", "private-repo", "test_token")
        assert url == "https://test_token@github.com/octocat/private-repo.git"


class TestCollectGitRepo:
    """Test Git repository collection."""

    @patch("codeconcat.collector.github_collector.tempfile.TemporaryDirectory")
    @patch("codeconcat.collector.github_collector.subprocess.run")
    @patch("codeconcat.collector.github_collector.collect_local_files")
    def test_collect_success(self, mock_collect_local, mock_run, mock_temp_dir):
        """Test successful repository collection."""
        # Mock temp directory
        mock_temp_context = MagicMock()
        mock_temp_context.__enter__.return_value = "/tmp/test"
        mock_temp_context.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_context

        # Mock successful git operations
        mock_run.return_value = Mock(returncode=0)

        # Mock local file collection
        mock_files = [
            ParsedFileData(
                file_path="/tmp/test/Hello-World/README.md",
                content="# Hello World",
                language="markdown",
            ),
        ]
        mock_collect_local.return_value = mock_files

        config = CodeConCatConfig()
        result, temp_path = collect_git_repo("octocat/Hello-World", config)

        assert len(result) == 1
        # Check that we got the expected file (path is absolute from local collector)
        assert result[0].file_path.endswith("Hello-World/README.md")
        assert temp_path == "/tmp/test"

    @patch("codeconcat.collector.github_collector.tempfile.TemporaryDirectory")
    @patch("codeconcat.collector.github_collector.subprocess.run")
    def test_collect_clone_failure(self, mock_run, mock_temp_dir):
        """Test handling clone failure."""
        # Mock temp directory
        mock_temp_context = MagicMock()
        mock_temp_context.__enter__.return_value = "/tmp/test"
        mock_temp_context.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_context

        # Mock clone failure
        mock_run.side_effect = subprocess.CalledProcessError(1, "git clone")

        config = CodeConCatConfig()
        result, temp_path = collect_git_repo("octocat/Hello-World", config)

        assert result == []
        assert temp_path == ""

    def test_collect_invalid_url(self):
        """Test handling invalid URL."""
        config = CodeConCatConfig()
        result, temp_path = collect_git_repo("not-a-valid-url", config)

        assert result == []
        assert temp_path == ""

    @patch("codeconcat.collector.github_collector.tempfile.TemporaryDirectory")
    @patch("codeconcat.collector.github_collector.subprocess.run")
    @patch("codeconcat.collector.github_collector.collect_local_files")
    def test_collect_with_ref(self, mock_collect_local, mock_run, mock_temp_dir):
        """Test collection with specific ref/branch."""
        # Mock temp directory
        mock_temp_context = MagicMock()
        mock_temp_context.__enter__.return_value = "/tmp/test"
        mock_temp_context.__exit__.return_value = None
        mock_temp_dir.return_value = mock_temp_context

        # Mock successful git operations
        mock_run.return_value = Mock(returncode=0)
        mock_collect_local.return_value = []

        config = CodeConCatConfig()
        result, temp_path = collect_git_repo("octocat/Hello-World/develop", config)

        # Should have cloned and checked out develop branch
        assert any("develop" in str(call) for call in mock_run.call_args_list)


class TestEdgeCases:
    """Test edge cases."""

    def test_parse_url_with_special_chars(self):
        """Test parsing URLs with special characters."""
        owner, repo, ref = parse_git_url("user-name/repo_name")
        assert owner == "user-name"
        assert repo == "repo_name"

    def test_parse_url_removes_git_extension(self):
        """Test that .git extension is removed."""
        owner, repo, ref = parse_git_url("octocat/Hello-World.git")
        assert repo == "Hello-World"  # .git should be removed

    @patch.dict("os.environ", {"GITHUB_TOKEN": ""})
    def test_build_url_no_token(self):
        """Test building URL without token."""
        url = build_git_clone_url("octocat/Hello-World", "octocat", "Hello-World")
        assert url == "https://github.com/octocat/Hello-World.git"
        assert "@" not in url
