"""Comprehensive tests for async GitHub collector with 85%+ coverage."""

import asyncio
import shutil
import tempfile
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.collector.async_github_collector import (
    build_git_clone_url,
    collect_git_repo,
    collect_git_repo_async,
    parse_git_url,
    run_git_command,
)


class TestAsyncGitHubCollectorComprehensive:
    """Comprehensive test suite for async GitHub collector with 85%+ coverage."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return CodeConCatConfig(
            include_languages=["python", "javascript"],
            exclude_paths=["test_*", "*.pyc"],
        )

    @pytest.fixture
    def mock_security_validation(self):
        """Mock security path validation to allow temp directories."""
        with patch(
            "codeconcat.collector.async_github_collector.SecurityProcessor.validate_path"
        ) as mock_validate:
            mock_validate.side_effect = lambda _base, path: path  # Return path as-is
            yield mock_validate

    # === URL PARSING TESTS ===

    def test_parse_git_url_github_shorthand(self):
        """Test parsing GitHub shorthand notation."""
        # owner/repo format
        owner, repo, ref = parse_git_url("facebook/react")
        assert owner == "facebook"
        assert repo == "react"
        assert ref is None

        # owner/repo/ref format
        owner, repo, ref = parse_git_url("facebook/react/main")
        assert owner == "facebook"
        assert repo == "react"
        assert ref == "main"

    def test_parse_git_url_with_git_extension_removal(self):
        """Test that .git extension is properly removed."""
        # Shorthand with .git
        owner, repo, ref = parse_git_url("facebook/react.git")
        assert owner == "facebook"
        assert repo == "react"
        assert ref is None

        # Shorthand with .git and ref
        owner, repo, ref = parse_git_url("facebook/react.git/main")
        assert owner == "facebook"
        assert repo == "react"
        assert ref == "main"

    def test_parse_git_url_https_urls(self):
        """Test parsing HTTPS GitHub URLs."""
        # Standard HTTPS URL
        owner, repo, ref = parse_git_url("https://github.com/facebook/react.git")
        assert owner == "facebook"
        assert repo == "react"
        assert ref is None

        # HTTPS with www prefix
        owner, repo, ref = parse_git_url("https://www.github.com/facebook/react.git")
        assert owner == "facebook"
        assert repo == "react"
        assert ref is None

        # HTTPS without .git
        owner, repo, ref = parse_git_url("https://github.com/facebook/react")
        assert owner == "facebook"
        assert repo == "react"
        assert ref is None

    def test_parse_git_url_https_with_tree_branch(self):
        """Test parsing HTTPS URLs with /tree/branch path."""
        owner, repo, ref = parse_git_url("https://github.com/facebook/react/tree/feature-branch")
        assert owner == "facebook"
        assert repo == "react"
        assert ref == "feature-branch"

    def test_parse_git_url_ssh_urls(self):
        """Test parsing SSH GitHub URLs."""
        owner, repo, ref = parse_git_url("git@github.com:facebook/react.git")
        assert owner == "facebook"
        assert repo == "react"
        assert ref is None

    def test_parse_git_url_http_protocol(self):
        """Test parsing HTTP URLs (not HTTPS)."""
        owner, repo, ref = parse_git_url("http://github.com/facebook/react.git")
        assert owner == "facebook"
        assert repo == "react"
        assert ref is None

    def test_parse_git_url_edge_cases(self):
        """Test edge cases in URL parsing."""
        # URL with tree/branch path
        owner, repo, ref = parse_git_url("https://github.com/facebook/react/tree/main")
        assert owner == "facebook"
        assert repo == "react"
        assert ref == "main"

        # Shorthand with multiple slashes (nested ref)
        owner, repo, ref = parse_git_url("facebook/react/feature/new-ui")
        assert owner == "facebook"
        assert repo == "react"
        assert ref == "feature/new-ui"

    def test_parse_git_url_malformed_inputs(self):
        """Test various malformed inputs."""
        with pytest.raises(ValueError):
            parse_git_url("single-word")

        with pytest.raises(ValueError):
            parse_git_url("https://gitlab.com/owner/repo")

        with pytest.raises(ValueError):
            parse_git_url("http://not-github.com/owner/repo")

        with pytest.raises(ValueError):
            parse_git_url("")

        # Test that ftp URLs are parsed as shorthand (current behavior)
        owner, repo, ref = parse_git_url("ftp://github.com/owner/repo")
        assert owner == "ftp:"
        assert repo == ""
        assert ref == "github.com/owner/repo"

    # === BUILD URL TESTS ===

    def test_build_git_clone_url_various_formats(self):
        """Test build_git_clone_url with various input formats."""
        # Standard case
        url = build_git_clone_url("ignored", "owner", "repo", None)
        assert url == "https://github.com/owner/repo.git"

        # With token
        url = build_git_clone_url("ignored", "owner", "repo", "token123")
        assert url == "https://token123@github.com/owner/repo.git"

        # Special characters in owner/repo
        url = build_git_clone_url("ignored", "owner-name", "repo_name", None)
        assert url == "https://github.com/owner-name/repo_name.git"

    def test_build_git_clone_url_empty_token(self):
        """Test build_git_clone_url with empty token."""
        url = build_git_clone_url("ignored", "owner", "repo", "")
        assert url == "https://github.com/owner/repo.git"

    # === ASYNC GIT COMMAND TESTS ===

    @pytest.mark.asyncio
    async def test_run_git_command_success(self):
        """Test successful git command execution."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"output", b""))
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(["git", "status"])

            assert returncode == 0
            assert stdout == "output"
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_run_git_command_failure(self):
        """Test failed git command execution."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"error"))
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(["git", "invalid"])

            assert returncode == 1
            assert stdout == ""
            assert stderr == "error"

    @pytest.mark.asyncio
    async def test_run_git_command_timeout(self):
        """Test git command timeout."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_process.kill = Mock()
            mock_process.wait = AsyncMock()
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(
                ["git", "clone", "large-repo"], timeout=1
            )

            assert returncode == -1
            assert "timed out" in stderr.lower()
            mock_process.kill.assert_called_once()
            mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_git_command_with_cwd(self):
        """Test git command with working directory."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"output", b""))
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(["git", "status"], cwd="/tmp")

            assert returncode == 0
            mock_create.assert_called_once_with(
                "git",
                "status",
                cwd="/tmp",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

    @pytest.mark.asyncio
    async def test_run_git_command_custom_timeout(self):
        """Test git command with custom timeout."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_process.kill = Mock()
            mock_process.wait = AsyncMock()
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(
                ["git", "clone", "large-repo"], timeout=30.0
            )

            assert returncode == -1
            assert "30.0 seconds" in stderr

    @pytest.mark.asyncio
    async def test_run_git_command_unicode_handling(self):
        """Test git command with unicode output."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            unicode_bytes = "déjà vu".encode()
            mock_process.communicate = AsyncMock(return_value=(unicode_bytes, b""))
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(["git", "log"])

            assert returncode == 0
            assert stdout == "déjà vu"

    @pytest.mark.asyncio
    async def test_run_git_command_invalid_unicode_handling(self):
        """Test git command with invalid unicode bytes."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            invalid_bytes = b"\xff\xfe"
            mock_process.communicate = AsyncMock(return_value=(invalid_bytes, b""))
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(["git", "log"])

            assert returncode == 0
            assert len(stdout) > 0  # Should handle invalid bytes gracefully

    @pytest.mark.asyncio
    async def test_run_git_command_none_output(self):
        """Test git command with None stdout/stderr."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(None, None))
            mock_create.return_value = mock_process

            returncode, stdout, stderr = await run_git_command(["git", "status"])

            assert returncode == 0
            assert stdout == ""
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_run_git_command_exception_handling(self):
        """Test git command with general exception."""
        with patch("asyncio.create_subprocess_exec") as mock_create:
            mock_create.side_effect = OSError("Permission denied")

            returncode, stdout, stderr = await run_git_command(["git", "status"])

            assert returncode == -1
            assert stdout == ""
            assert "Permission denied" in stderr

    # === ASYNC REPO COLLECTION TESTS ===

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_success(self, _mock_security_validation, config):
        """Test successful async git repo collection."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.return_value = (0, "Cloning into 'repo'...", "")
            mock_collect.return_value = [
                ParsedFileData(file_path="file1.py", content="print('hello')", language="python"),
                ParsedFileData(
                    file_path="file2.js", content="console.log('world')", language="javascript"
                ),
            ]

            result, repo_path = await collect_git_repo_async(
                source_url_in="https://github.com/test/repo.git",
                config=config,
            )

            assert len(result) == 2
            assert result[0].file_path == "file1.py"
            assert result[1].file_path == "file2.js"
            assert isinstance(repo_path, str)

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_clone_failure(self, config):
        """Test handling of clone failure."""
        with patch("codeconcat.collector.async_github_collector.run_git_command") as mock_run_git:
            mock_run_git.return_value = (128, "", "fatal: repository not found")

            result, repo_path = await collect_git_repo_async(
                source_url_in="https://github.com/nonexistent/repo.git",
                config=config,
            )

            assert result == []
            assert repo_path == ""

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_invalid_url(self, config):
        """Test collection with invalid URL."""
        result, repo_path = await collect_git_repo_async("invalid-url", config)

        assert result == []
        assert repo_path == ""

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_with_ref(self, _mock_security_validation, config):
        """Test collection with specific ref/branch."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.return_value = (0, "Cloning...", "")
            mock_collect.return_value = [
                ParsedFileData(file_path="feature.py", content="# feature", language="python"),
            ]

            config.source_ref = "feature-branch"

            result, repo_path = await collect_git_repo_async(
                source_url_in="https://github.com/test/repo.git",
                config=config,
            )

            assert len(result) == 1
            assert result[0].file_path == "feature.py"

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_private_with_token(
        self, _mock_security_validation, config
    ):
        """Test collection of private repo with authentication token."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.return_value = (0, "Cloning private repo...", "")
            mock_collect.return_value = [
                ParsedFileData(file_path="private.py", content="# private", language="python"),
            ]

            config.github_token = "ghp_secret123"

            result, repo_path = await collect_git_repo_async(
                source_url_in="https://github.com/private/repo.git",
                config=config,
            )

            assert len(result) == 1
            # Check that clone was called with authenticated URL
            clone_call = mock_run_git.call_args_list[0]
            clone_cmd = clone_call[0][0]
            assert "ghp_secret123@github.com" in " ".join(clone_cmd)

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_url_ref_priority(self, _mock_security_validation, config):
        """Test that config.source_ref takes priority over URL ref."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.return_value = (0, "success", "")
            mock_collect.return_value = [
                ParsedFileData(file_path="test.py", content="test", language="python")
            ]

            config.source_ref = "config-branch"

            result, repo_path = await collect_git_repo_async("owner/repo/url-branch", config)

            assert len(result) == 1
            clone_call = mock_run_git.call_args_list[0]
            clone_cmd = " ".join(clone_call[0][0])
            assert "--branch config-branch" in clone_cmd

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_fallback_to_main(self, _mock_security_validation, config):
        """Test fallback to 'main' when no ref specified."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git:
            mock_run_git.return_value = (128, "", "error")

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            clone_call = mock_run_git.call_args_list[0]
            clone_cmd = " ".join(clone_call[0][0])
            assert "--branch main" in clone_cmd

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_clone_then_fetch_success(
        self, _mock_security_validation, config
    ):
        """Test successful clone then fetch sequence."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.side_effect = [
                (128, "", "fatal: Remote branch specific-ref not found"),  # initial clone fails
                (0, "Cloned default", ""),  # clone default succeeds
                (0, "Fetched", ""),  # fetch succeeds
                (0, "Checked out", ""),  # checkout succeeds
            ]

            mock_collect.return_value = [
                ParsedFileData(file_path="test.py", content="test", language="python")
            ]

            config.source_ref = "specific-ref"

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            assert len(result) == 1
            assert mock_run_git.call_count == 4

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_default_clone_fails(
        self, _mock_security_validation, config
    ):
        """Test when both initial and default clone fail."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git:
            mock_run_git.side_effect = [
                (128, "", "fatal: Remote branch not found"),
                (128, "", "fatal: Repository not found"),
            ]

            config.source_ref = "nonexistent-branch"

            result, repo_path = await collect_git_repo_async("owner/nonexistent", config)

            assert result == []
            assert repo_path == ""
            assert mock_run_git.call_count == 2

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_fetch_fails_proceed_default(
        self, _mock_security_validation, config
    ):
        """Test proceeding with default branch when fetch fails."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.side_effect = [
                (128, "", "fatal: Remote branch not found"),
                (0, "Cloned default", ""),
                (128, "", "fatal: Couldn't find remote ref"),
            ]

            mock_collect.return_value = [
                ParsedFileData(file_path="default.py", content="default", language="python")
            ]

            config.source_ref = "nonexistent-ref"

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            assert len(result) == 1
            assert result[0].file_path == "default.py"
            assert mock_run_git.call_count == 3

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_checkout_fails(self, _mock_security_validation, config):
        """Test when checkout fails after successful fetch."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git:
            mock_run_git.side_effect = [
                (128, "", "fatal: Remote branch not found"),
                (0, "Cloned default", ""),
                (0, "Fetched", ""),
                (128, "", "fatal: reference is not a tree"),
            ]

            config.source_ref = "invalid-commit-sha"

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            assert result == []
            assert repo_path == ""
            assert mock_run_git.call_count == 4

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_general_exception(self, config):
        """Test handling of general exceptions during collection."""
        with patch("codeconcat.collector.async_github_collector.run_git_command") as mock_run_git:
            mock_run_git.side_effect = Exception("Unexpected error")

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            assert result == []
            assert repo_path == ""

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_empty_file_collection(
        self, _mock_security_validation, config
    ):
        """Test handling when no files are collected."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.return_value = (0, "success", "")
            mock_collect.return_value = []

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            assert result == []
            assert isinstance(repo_path, str)
            assert len(repo_path) > 0

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_collect_local_files_exception(
        self, _mock_security_validation, config
    ):
        """Test handling when collect_local_files raises exception."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.return_value = (0, "success", "")
            mock_collect.side_effect = Exception("Collection failed")

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            assert result == []
            assert repo_path == ""

    @pytest.mark.asyncio
    async def test_collect_git_repo_wrapper_calls_async(self, config):
        """Test that collect_git_repo properly calls async version."""
        with patch(
            "codeconcat.collector.async_github_collector.collect_git_repo_async"
        ) as mock_async:
            mock_async.return_value = ([], "")

            result, repo_path = await collect_git_repo("owner/repo", config)

            assert result == []
            assert repo_path == ""
            mock_async.assert_called_once_with("owner/repo", config)

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_command_structure(
        self, _mock_security_validation, config
    ):
        """Test the structure of git commands being executed."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git:
            mock_run_git.return_value = (128, "", "error")

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            clone_call = mock_run_git.call_args_list[0]
            clone_cmd = clone_call[0][0]

            expected_elements = [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "main",
                "--no-tags",
                "https://github.com/owner/repo.git",
            ]

            for element in expected_elements:
                assert element in clone_cmd

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_authenticated_url_structure(
        self, _mock_security_validation, config
    ):
        """Test authenticated URL structure with token."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git:
            mock_run_git.return_value = (128, "", "error")
            config.github_token = "ghp_token123"

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            clone_call = mock_run_git.call_args_list[0]
            clone_cmd = " ".join(clone_call[0][0])

            assert "https://ghp_token123@github.com/owner/repo.git" in clone_cmd

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_fetch_command_structure(
        self, _mock_security_validation, config
    ):
        """Test fetch command structure in fallback scenario."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git:
            mock_run_git.side_effect = [
                (128, "", "initial clone failed"),
                (0, "default clone success", ""),
                (0, "fetch success", ""),
            ]

            config.source_ref = "feature-branch"

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            fetch_call = mock_run_git.call_args_list[2]
            fetch_cmd = fetch_call[0][0]

            expected_fetch_elements = [
                "git",
                "-C",
                "fetch",
                "origin",
                "feature-branch",
                "--depth",
                "1",
            ]

            for element in expected_fetch_elements:
                assert element in fetch_cmd

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_checkout_command_structure(
        self, _mock_security_validation, config
    ):
        """Test checkout command structure."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git:
            mock_run_git.side_effect = [
                (128, "", "initial clone failed"),
                (0, "default clone success", ""),
                (0, "fetch success", ""),
                (0, "checkout success", ""),
            ]

            config.source_ref = "feature-branch"

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            checkout_call = mock_run_git.call_args_list[3]
            checkout_cmd = checkout_call[0][0]

            expected_checkout_elements = ["git", "-C", "checkout", "FETCH_HEAD"]

            for element in expected_checkout_elements:
                assert element in checkout_cmd

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_executor_usage(self, _mock_security_validation, config):
        """Test that collect_local_files runs in executor."""
        with patch(
            "codeconcat.collector.async_github_collector.run_git_command"
        ) as mock_run_git, patch(
            "codeconcat.collector.async_github_collector.collect_local_files"
        ) as mock_collect:
            mock_run_git.return_value = (0, "success", "")
            mock_collect.return_value = [
                ParsedFileData(file_path="test.py", content="test", language="python")
            ]

            with patch("asyncio.get_event_loop") as mock_get_loop:
                mock_loop = Mock()
                mock_get_loop.return_value = mock_loop
                mock_loop.run_in_executor = AsyncMock(
                    return_value=[
                        ParsedFileData(file_path="test.py", content="test", language="python")
                    ]
                )

                result, repo_path = await collect_git_repo_async("owner/repo", config)

                assert len(result) == 1
                mock_loop.run_in_executor.assert_called_once_with(
                    None,
                    mock_collect,
                    ANY,
                    config,  # Default executor  # temp_dir path
                )

    # === LOGGING COVERAGE TESTS ===

    def test_parse_git_url_logging_coverage(self):
        """Test that logging statements are executed for coverage."""
        import logging

        with patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "debug"
        ) as mock_log:
            # Test shorthand parsing logs
            parse_git_url("owner/repo")
            mock_log.assert_called()

            # Test HTTPS parsing logs
            parse_git_url("https://github.com/owner/repo.git")
            assert mock_log.call_count >= 2

            # Test SSH parsing logs
            parse_git_url("git@github.com:owner/repo.git")
            assert mock_log.call_count >= 3

    @pytest.mark.asyncio
    async def test_run_git_command_logging_coverage(self):
        """Test logging statements in run_git_command for coverage."""
        import logging

        with patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "debug"
        ) as mock_debug, patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "error"
        ) as _mock_error, patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"output", b""))
            mock_create.return_value = mock_process

            await run_git_command(["git", "status"])

            mock_debug.assert_called_with("Running async git command: git status")

    @pytest.mark.asyncio
    async def test_run_git_command_timeout_logging(self):
        """Test timeout error logging for coverage."""
        import logging

        with patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "error"
        ) as mock_error, patch("asyncio.create_subprocess_exec") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_process.kill = Mock()
            mock_process.wait = AsyncMock()
            mock_create.return_value = mock_process

            await run_git_command(["git", "status"], timeout=1.0)

            mock_error.assert_called_with("Git command timed out after 1.0 seconds")

    @pytest.mark.asyncio
    async def test_run_git_command_general_exception_logging(self):
        """Test general exception logging for coverage."""
        import logging

        with patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "error"
        ) as mock_error, patch("asyncio.create_subprocess_exec") as mock_create:
            mock_create.side_effect = OSError("Test error")

            await run_git_command(["git", "status"])

            mock_error.assert_called_with("Error running git command: Test error")

    @pytest.mark.asyncio
    async def test_collect_git_repo_async_logging_coverage(self, _mock_security_validation, config):
        """Test logging statements in collect_git_repo_async for coverage."""
        import logging

        with patch(
            "codeconcat.collector.async_github_collector.run_git_command", new_callable=AsyncMock
        ) as mock_run_git, patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "info"
        ) as mock_info, patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "warning"
        ) as mock_warning, patch.object(
            logging.getLogger("codeconcat.collector.async_github_collector"), "error"
        ) as _mock_error:
            mock_run_git.return_value = (128, "", "repo not found")

            result, repo_path = await collect_git_repo_async("owner/repo", config)

            # Verify various logging calls were made
            assert mock_info.call_count >= 1
            assert mock_warning.call_count >= 1
