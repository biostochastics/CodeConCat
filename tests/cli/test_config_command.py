from typer.testing import CliRunner

from codeconcat.cli import app


def test_config_command_help_lists_local_llm():
    runner = CliRunner()
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "local-llm" in result.stdout


def test_config_local_llm_help():
    runner = CliRunner()
    result = runner.invoke(app, ["config", "local-llm", "--help"])
    assert result.exit_code == 0
    assert "codeconcat config local-llm" in result.stdout.lower()
    assert "options" in result.stdout.lower()
