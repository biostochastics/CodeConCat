"""Tests for GitHub collector functionality."""

import logging
import os
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.collector.github_collector import (
    build_clone_url,
    collect_github_files,
    parse_github_url,
)

logger = logging.getLogger(__name__)


class TestGitHubCollector(TestCase):
    def setUp(self):
        self.config = CodeConCatConfig(
            target_path=".",
            github_url="test/repo",
            github_token="test_token",
            github_ref="main",
            include_languages=[
                "python"
            ],  # Add this to ensure Python files are included
            include_paths=["*.py"],  # Add this to ensure .py files are included
        )

    def test_parse_github_url(self):
        # Test shorthand notation
        owner, repo, ref = parse_github_url("owner/repo")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertIsNone(ref)

        # Test shorthand with branch
        owner, repo, ref = parse_github_url("owner/repo/branch")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(ref, "branch")

        # Test full URL
        owner, repo, ref = parse_github_url("https://github.com/owner/repo")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertIsNone(ref)

        # Test full URL with branch
        owner, repo, ref = parse_github_url("https://github.com/owner/repo/tree/branch")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(ref, "branch")

        # Test invalid URL
        with self.assertRaises(ValueError):
            parse_github_url("invalid_url")

    def test_build_clone_url(self):
        # Test URL without token
        url = build_clone_url("https://github.com/owner/repo")
        self.assertEqual(url, "https://github.com/owner/repo")

        # Test URL with token
        url = build_clone_url("https://github.com/owner/repo", "test_token")
        self.assertEqual(url, "https://test_token@github.com/owner/repo")

        # Test shorthand without token
        url = build_clone_url("owner/repo")
        self.assertEqual(url, "https://github.com/owner/repo")

        # Test shorthand with token
        url = build_clone_url("owner/repo", "test_token")
        self.assertEqual(url, "https://test_token@github.com/owner/repo")

    @mock.patch("subprocess.run")
    @mock.patch("codeconcat.collector.github_collector.collect_local_files")
    def test_collect_github_files(self, mock_collect_local, mock_run):
        # Create a temporary test file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, "w") as f:
                f.write("print('test')")

            # Create a test non-Python file that should be excluded
            other_file = os.path.join(temp_dir, "test.txt")
            with open(other_file, "w") as f:
                f.write("test")

            # Mock successful clone
            mock_run.return_value.returncode = 0

            # Mock local collector to return our test file
            mock_collect_local.return_value = [
                ParsedFileData(
                    file_path=test_file,
                    language="python",
                    content="print('test')",
                    declarations=[],
                )
            ]

            # Test successful collection
            files = collect_github_files("owner/repo", self.config)
            self.assertEqual(len(files), 1)
            self.assertEqual(Path(files[0].file_path).name, "test.py")
            self.assertEqual(files[0].language, "python")
            self.assertEqual(files[0].content, "print('test')")

            # Verify clone command
            mock_run.assert_called_once()
            clone_args = mock_run.call_args[0][0]
            self.assertEqual(clone_args[0:3], ["git", "clone", "--depth"])

            # Test failed clone
            mock_run.side_effect = Exception("Clone failed")
            files = collect_github_files("owner/repo", self.config)
            self.assertEqual(files, [])
