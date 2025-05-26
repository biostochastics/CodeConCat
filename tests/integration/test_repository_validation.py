"""Integration tests for CodeConCat using real repositories."""

import pytest
import subprocess
import logging
from unittest.mock import patch

import traceback
from codeconcat.base_types import CodeConCatConfig
from codeconcat.main import run_codeconcat
from codeconcat.errors import ValidationError, ConfigurationError


# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Test repositories - a mix of clean and potentially problematic repos
TEST_REPOSITORIES = [
    # Clean repositories
    {
        "name": "flask-microblog",
        "url": "https://github.com/miguelgrinberg/microblog",
        "ref": "master",
        "description": "Flask tutorial project, clean code",
        "expected_findings": 0,
        "languages": ["python", "html", "javascript"],
        "files": ["app/__init__.py", "app/models.py"],
    },
    {
        "name": "django-oscar",
        "url": "https://github.com/django-oscar/django-oscar",
        "ref": "master",
        "description": "Django e-commerce framework",
        "expected_findings": 0,
        "languages": ["python", "html", "javascript", "css"],
        "files": ["src/oscar/apps/checkout/views.py"],
    },
    # Repositories with potential security issues (for semgrep testing)
    {
        "name": "dvna",
        "url": "https://github.com/appsecco/dvna",
        "ref": "master",
        "description": "Damn Vulnerable NodeJS Application - intentionally vulnerable",
        "expected_findings": 5,  # At least this many issues should be found
        "languages": ["javascript", "html"],
        "files": ["core/appHandler.js"],
    },
    {
        "name": "juice-shop",
        "url": "https://github.com/juice-shop/juice-shop",
        "ref": "master",
        "description": "OWASP Juice Shop - intentionally vulnerable",
        "expected_findings": 3,  # At least this many issues should be found
        "languages": ["typescript", "javascript", "html"],
        "files": ["routes/login.ts", "routes/verify.ts"],
    },
]


@pytest.mark.skip(
    reason="Repository tests are time-consuming and network-dependent. Security features are already well-tested in unit tests."
)
class TestRepositoryValidation:
    """Integration tests with real repositories."""

    @pytest.fixture(scope="module", autouse=True)
    def enable_debug_logging(self):
        """Enable debug logging for all tests in this module."""
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.DEBUG)
        yield
        logging.getLogger().setLevel(original_level)

    @pytest.mark.parametrize("repo", TEST_REPOSITORIES, ids=[r["name"] for r in TEST_REPOSITORIES])
    def test_repository_basic_validation(self, repo, tmp_path):
        """Test basic validation on real repositories."""
        # The GITHUB_TOKEN check has been removed to test cloning public repositories without a token.
        # Clone repo to temporary directory
        repo_dir = tmp_path / repo["name"]
        repo_dir.mkdir()

        # Use git clone instead of codeconcat.collector to ensure we have the full repo
        try:
            logger.info(f"Cloning repository {repo['url']} to {repo_dir}")
            subprocess.run(
                ["git", "clone", repo["url"], str(repo_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Verify the repo was cloned successfully
            assert (repo_dir / ".git").exists(), f"Failed to clone repository {repo['name']}"
            logger.info(f"Successfully cloned repository {repo['name']}")

            # Run CodeConCat with basic validation
            config = CodeConCatConfig(
                target_path=str(repo_dir),
                format="markdown",
                output=str(tmp_path / f"{repo['name']}_output.md"),
                enable_security_scanning=True,
                strict_security=False,
                verbose=True,
                parser_engine="tree_sitter",
            )

            try:
                logger.info(f"Running CodeConCat on repository {repo['name']}")
                output = run_codeconcat(config)
                logger.info(f"CodeConCat completed successfully for {repo['name']}")

                # Check that output was generated
                assert output, "No output was generated"
                # Output is returned as string, no need to check file creation
                assert len(output) > 100, "Output seems too short"
            except Exception as e:
                if repo["name"] == "flask-microblog":
                    debug_log_path = tmp_path / "debug_flask_microblog.log"
                    with open(debug_log_path, "w") as f:
                        f.write(f"Exception Type: {type(e).__name__}\n")
                        f.write(f"Exception Message: {str(e)}\n")
                        f.write("Traceback:\n")
                        traceback.print_exc(file=f)
                    logger.error(
                        f"Detailed traceback for flask-microblog written to {debug_log_path}"
                    )
                    print(f"--- START content of {debug_log_path} ---")
                    with open(debug_log_path, "r") as f_read:
                        print(f_read.read())
                    print(f"--- END content of {debug_log_path} ---")
                logger.error(
                    f"Error running CodeConCat on {repo['name']}: {e}"
                )  # General error log for all repos
                raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository {repo['name']}: {e.stderr}")
            pytest.skip(f"Failed to clone repository {repo['name']}")

    @pytest.mark.parametrize("repo", TEST_REPOSITORIES, ids=[r["name"] for r in TEST_REPOSITORIES])
    def test_repository_semgrep_validation(self, repo, tmp_path):
        """Test Semgrep validation on real repositories."""
        # Skip test if semgrep is not available and can't be installed
        with patch(
            "codeconcat.validation.semgrep_validator.semgrep_validator.is_available",
            return_value=False,
        ):
            with patch("codeconcat.validation.setup_semgrep.install_semgrep", return_value=False):
                try:
                    import semgrep  # noqa: F401
                except ImportError:
                    pytest.skip("Semgrep is not available and cannot be installed")

        # Clone repo to temporary directory
        repo_dir = tmp_path / f"{repo['name']}_semgrep"
        repo_dir.mkdir()

        # Use git clone to get the repo
        try:
            logger.info(f"Cloning repository {repo['url']} to {repo_dir}")
            subprocess.run(
                ["git", "clone", repo["url"], str(repo_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Verify the repo was cloned successfully
            assert (repo_dir / ".git").exists(), f"Failed to clone repository {repo['name']}"
            logger.info(f"Successfully cloned repository {repo['name']}")

            # Create mock findings for testing without actual semgrep
            mock_findings = []
            if repo["expected_findings"] > 0:
                # In a real test, this would be replaced with actual semgrep findings
                for i in range(repo["expected_findings"]):
                    mock_findings.append(
                        {
                            "type": "semgrep",
                            "rule_id": f"test-rule-{i}",
                            "message": f"Test finding {i}",
                            "severity": "WARNING",
                            "line": i + 1,
                            "column": 1,
                            "snippet": "test code snippet",
                        }
                    )

            # Run with semgrep validation
            with patch(
                "codeconcat.validation.semgrep_validator.SemgrepValidator.scan_file",
                return_value=mock_findings,
            ):
                with patch(
                    "codeconcat.validation.semgrep_validator.semgrep_validator.is_available",
                    return_value=True,
                ):
                    config = CodeConCatConfig(
                        target_path=str(repo_dir),
                        format="json",  # Use JSON to easily parse the output for findings
                        output=str(tmp_path / f"{repo['name']}_semgrep_output.json"),
                        enable_security_scanning=True,
                        enable_semgrep=True,
                        strict_security=False,
                        verbose=True,
                    )

                    try:
                        logger.info(f"Running CodeConCat with Semgrep on {repo['name']}")
                        output = run_codeconcat(config)
                        logger.info(f"CodeConCat with Semgrep completed for {repo['name']}")

                        # Check output
                        assert output, "No output was generated"
                        # No need to check file existence since run_codeconcat returns string

                        # In a real test, we would check for actual findings in the output
                        if repo["expected_findings"] > 0:
                            assert (
                                "WARNING" in output or "security" in output.lower()
                            ), f"Expected security findings in {repo['name']} output"

                    except Exception as e:
                        logger.error(
                            f"Error running CodeConCat with Semgrep on {repo['name']}: {e}"
                        )
                        raise

        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository {repo['name']}: {e.stderr}")
            pytest.skip(f"Failed to clone repository {repo['name']}")

    @pytest.mark.parametrize("repo", TEST_REPOSITORIES, ids=[r["name"] for r in TEST_REPOSITORIES])
    def test_repository_strict_security(self, repo, tmp_path):
        """Test strict security mode on real repositories."""
        # Clone repo to temporary directory
        repo_dir = tmp_path / f"{repo['name']}_strict"
        repo_dir.mkdir()

        # Use git clone to get the repo
        try:
            logger.info(f"Cloning repository {repo['url']} to {repo_dir}")
            subprocess.run(
                ["git", "clone", repo["url"], str(repo_dir)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Verify the repo was cloned successfully
            assert (repo_dir / ".git").exists(), f"Failed to clone repository {repo['name']}"
            logger.info(f"Successfully cloned repository {repo['name']}")

            # Create a configuration with strict security
            config = CodeConCatConfig(
                target_path=str(repo_dir),
                format="markdown",
                output=str(tmp_path / f"{repo['name']}_strict_output.md"),
                enable_security_scanning=True,
                strict_security=True,
                verbose=True,
            )

            try:
                logger.info(f"Running CodeConCat with strict security on {repo['name']}")

                # Repositories with expected security issues should fail in strict mode
                if repo["expected_findings"] > 0:
                    with pytest.raises((ValidationError, ConfigurationError)) as excinfo:
                        run_codeconcat(config)
                    logger.info(
                        f"CodeConCat correctly failed in strict mode for {repo['name']}: {excinfo.value}"
                    )
                    assert (
                        "suspicious content" in str(excinfo.value).lower()
                        or "security" in str(excinfo.value).lower()
                    )
                else:
                    # Clean repositories should pass even in strict mode
                    output = run_codeconcat(config)
                    logger.info(
                        f"CodeConCat completed in strict mode for clean repo {repo['name']}"
                    )
                    assert output, "No output was generated"
                    # No need to check file existence since run_codeconcat returns string

            except Exception as e:
                if repo["expected_findings"] > 0:
                    # Expected to fail for repositories with security issues
                    logger.info(f"Expected failure for {repo['name']} in strict mode: {e}")
                else:
                    # Unexpected failure for clean repositories
                    logger.error(f"Unexpected error for {repo['name']} in strict mode: {e}")
                    raise

        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository {repo['name']}: {e.stderr}")
            pytest.skip(f"Failed to clone repository {repo['name']}")
