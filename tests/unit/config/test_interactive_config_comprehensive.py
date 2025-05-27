"""Comprehensive tests for interactive config to improve code coverage."""

from unittest.mock import patch, MagicMock
from pathlib import Path
from codeconcat.config.interactive_config import InteractiveConfig


class TestInteractiveConfigComprehensive:
    """Comprehensive test suite for InteractiveConfig."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interactive = InteractiveConfig()

    @patch("builtins.input")
    def test_get_user_input_with_default(self, mock_input):
        """Test getting user input with default value."""
        mock_input.return_value = ""
        result = self.interactive.get_user_input("Enter value", "default")
        assert result == "default"

        mock_input.return_value = "custom"
        result = self.interactive.get_user_input("Enter value", "default")
        assert result == "custom"

    @patch("builtins.input")
    def test_get_user_input_required(self, mock_input):
        """Test getting required user input."""
        mock_input.side_effect = ["", "", "value"]
        result = self.interactive.get_user_input("Enter value", required=True)
        assert result == "value"
        assert mock_input.call_count == 3

    @patch("builtins.input")
    def test_get_user_input_strip_whitespace(self, mock_input):
        """Test input stripping whitespace."""
        mock_input.return_value = "  value  "
        result = self.interactive.get_user_input("Enter value")
        assert result == "value"

    @patch("builtins.input")
    def test_confirm_with_user_yes(self, mock_input):
        """Test user confirmation with yes responses."""
        for yes_response in ["y", "Y", "yes", "YES", "Yes"]:
            mock_input.return_value = yes_response
            result = self.interactive.confirm_with_user("Confirm?")
            assert result is True

    @patch("builtins.input")
    def test_confirm_with_user_no(self, mock_input):
        """Test user confirmation with no responses."""
        for no_response in ["n", "N", "no", "NO", "No", "x", ""]:
            mock_input.return_value = no_response
            result = self.interactive.confirm_with_user("Confirm?")
            assert result is False

    @patch("builtins.input")
    def test_select_from_list(self, mock_input):
        """Test selecting from a list of options."""
        options = ["option1", "option2", "option3"]

        # Test valid selection
        mock_input.return_value = "2"
        result = self.interactive.select_from_list("Choose:", options)
        assert result == "option2"

        # Test invalid then valid selection
        mock_input.side_effect = ["0", "4", "abc", "1"]
        result = self.interactive.select_from_list("Choose:", options)
        assert result == "option1"
        assert mock_input.call_count == 4

    @patch("builtins.input")
    def test_select_from_list_empty_for_none(self, mock_input):
        """Test selecting none from list with allow_none."""
        options = ["option1", "option2"]
        mock_input.return_value = ""
        result = self.interactive.select_from_list("Choose:", options, allow_none=True)
        assert result is None

    @patch("builtins.input")
    def test_get_multiple_inputs(self, mock_input):
        """Test getting multiple inputs from user."""
        mock_input.side_effect = ["item1", "item2", "item3", ""]
        result = self.interactive.get_multiple_inputs("Enter items")
        assert result == ["item1", "item2", "item3"]

    @patch("builtins.input")
    def test_get_multiple_inputs_empty(self, mock_input):
        """Test getting multiple inputs with immediate empty."""
        mock_input.return_value = ""
        result = self.interactive.get_multiple_inputs("Enter items")
        assert result == []

    @patch("builtins.input")
    def test_get_path_input_existing_file(self, mock_input):
        """Test getting path input for existing file."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                mock_input.return_value = "/path/to/file.txt"
                result = self.interactive.get_path_input(
                    "Enter file path", must_exist=True, path_type="file"
                )
                assert result == Path("/path/to/file.txt")

    @patch("builtins.input")
    def test_get_path_input_existing_directory(self, mock_input):
        """Test getting path input for existing directory."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=True):
                mock_input.return_value = "/path/to/dir"
                result = self.interactive.get_path_input(
                    "Enter dir path", must_exist=True, path_type="directory"
                )
                assert result == Path("/path/to/dir")

    @patch("builtins.input")
    def test_get_path_input_expanduser(self, mock_input):
        """Test path input with tilde expansion."""
        with patch("pathlib.Path.expanduser") as mock_expanduser:
            with patch("pathlib.Path.exists", return_value=True):
                mock_expanduser.return_value = Path("/home/user/file.txt")
                mock_input.return_value = "~/file.txt"
                result = self.interactive.get_path_input("Enter path")
                assert result == Path("~/file.txt")

    @patch("builtins.input")
    def test_get_path_input_invalid_then_valid(self, mock_input):
        """Test path input with invalid then valid input."""

        def exists_side_effect(self):
            return self == Path("/valid/path")

        with patch.object(Path, "exists", exists_side_effect):
            mock_input.side_effect = ["/invalid/path", "/valid/path"]
            result = self.interactive.get_path_input("Enter path", must_exist=True)
            assert result == Path("/valid/path")

    @patch("builtins.input")
    def test_get_path_input_empty_default(self, mock_input):
        """Test path input with empty input and default."""
        mock_input.return_value = ""
        result = self.interactive.get_path_input("Enter path", default="/default/path")
        assert result == Path("/default/path")

    @patch("codeconcat.config.interactive_config.InteractiveConfig.print_welcome")
    @patch("codeconcat.config.interactive_config.InteractiveConfig.configure_basic")
    @patch("codeconcat.config.interactive_config.InteractiveConfig.configure_paths")
    @patch("codeconcat.config.interactive_config.InteractiveConfig.configure_output")
    @patch("codeconcat.config.interactive_config.InteractiveConfig.configure_exclusions")
    @patch("codeconcat.config.interactive_config.InteractiveConfig.configure_features")
    @patch("codeconcat.config.interactive_config.InteractiveConfig.review_and_save")
    def test_run_full_flow(
        self,
        mock_review,
        mock_features,
        mock_exclusions,
        mock_output,
        mock_paths,
        mock_basic,
        mock_welcome,
    ):
        """Test running the full interactive configuration flow."""
        mock_config = MagicMock()
        result = self.interactive.run(mock_config)

        assert result == mock_config
        mock_welcome.assert_called_once()
        mock_basic.assert_called_once_with(mock_config)
        mock_paths.assert_called_once_with(mock_config)
        mock_output.assert_called_once_with(mock_config)
        mock_exclusions.assert_called_once_with(mock_config)
        mock_features.assert_called_once_with(mock_config)
        mock_review.assert_called_once_with(mock_config)

    def test_print_welcome(self, capsys):
        """Test welcome message printing."""
        self.interactive.print_welcome()
        captured = capsys.readouterr()
        assert "Welcome to CodeConcat Interactive Configuration" in captured.out
        assert "=" * 50 in captured.out

    @patch("builtins.input")
    def test_configure_basic(self, mock_input):
        """Test basic configuration."""
        mock_config = MagicMock()
        mock_input.side_effect = ["My Project", "config_name"]

        self.interactive.configure_basic(mock_config)

        mock_config.set_field.assert_any_call("project_name", "My Project")
        mock_config.set_field.assert_any_call("config_name", "config_name")

    @patch("builtins.input")
    def test_configure_paths_local(self, mock_input):
        """Test configuring paths for local source."""
        mock_config = MagicMock()
        mock_input.side_effect = ["1", "/path/to/project"]

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_dir", return_value=True):
                self.interactive.configure_paths(mock_config)

        mock_config.set_field.assert_any_call("source", "local")
        mock_config.set_field.assert_any_call("path", "/path/to/project")

    @patch("builtins.input")
    def test_configure_paths_github(self, mock_input):
        """Test configuring paths for GitHub source."""
        mock_config = MagicMock()
        mock_input.side_effect = ["2", "owner/repo", "main", ""]

        self.interactive.configure_paths(mock_config)

        mock_config.set_field.assert_any_call("source", "github")
        mock_config.set_field.assert_any_call("github_repo", "owner/repo")
        mock_config.set_field.assert_any_call("branch", "main")

    @patch("builtins.input")
    def test_configure_output(self, mock_input):
        """Test configuring output settings."""
        mock_config = MagicMock()
        mock_input.side_effect = ["output.md", "2", "n"]

        self.interactive.configure_output(mock_config)

        mock_config.set_field.assert_any_call("output", "output.md")
        mock_config.set_field.assert_any_call("format", "text")
        mock_config.set_field.assert_any_call("compress", False)

    @patch("builtins.input")
    def test_configure_exclusions_with_items(self, mock_input):
        """Test configuring exclusions with items."""
        mock_config = MagicMock()
        mock_config.exclude = []
        mock_config.gitignore = True

        mock_input.side_effect = ["y", "*.log", "*.tmp", "", "y", "*.py", ""]

        self.interactive.configure_exclusions(mock_config)

        # Check that exclude patterns were added
        calls = [call for call in mock_config.set_field.call_args_list if call[0][0] == "exclude"]
        assert len(calls) == 1
        assert calls[0][0][1] == ["*.log", "*.tmp"]

    @patch("builtins.input")
    def test_configure_exclusions_skip(self, mock_input):
        """Test skipping exclusion configuration."""
        mock_config = MagicMock()
        mock_config.exclude = []
        mock_config.gitignore = True

        mock_input.side_effect = ["n", "n"]

        self.interactive.configure_exclusions(mock_config)

        # Should not modify exclude list
        exclude_calls = [
            call for call in mock_config.set_field.call_args_list if call[0][0] == "exclude"
        ]
        assert len(exclude_calls) == 0

    @patch("builtins.input")
    def test_configure_features(self, mock_input):
        """Test configuring features."""
        mock_config = MagicMock()
        mock_input.side_effect = [
            "y",  # line numbers
            "n",  # tree
            "y",  # include empty
            "n",  # verbose
        ]

        self.interactive.configure_features(mock_config)

        mock_config.set_field.assert_any_call("line_numbers", True)
        mock_config.set_field.assert_any_call("tree", False)
        mock_config.set_field.assert_any_call("include_empty", True)
        mock_config.set_field.assert_any_call("verbose", False)

    @patch("builtins.input")
    def test_review_and_save_save_yaml(self, mock_input):
        """Test reviewing and saving configuration as YAML."""
        mock_config = MagicMock()
        mock_config.to_dict.return_value = {"key": "value"}
        mock_input.side_effect = ["y", "config.yml"]

        with patch("builtins.open", create=True) as mock_open:
            with patch("yaml.dump") as mock_yaml_dump:
                self.interactive.review_and_save(mock_config)

        mock_yaml_dump.assert_called_once()
        mock_open.assert_called_once_with("config.yml", "w")

    @patch("builtins.input")
    def test_review_and_save_no_save(self, mock_input):
        """Test reviewing without saving configuration."""
        mock_config = MagicMock()
        mock_config.to_dict.return_value = {"key": "value"}
        mock_input.return_value = "n"

        with patch("builtins.open", create=True) as mock_open:
            self.interactive.review_and_save(mock_config)

        mock_open.assert_not_called()

    def test_print_section_header(self, capsys):
        """Test printing section headers."""
        self.interactive.print_section_header("Test Section")
        captured = capsys.readouterr()
        assert "Test Section" in captured.out
        assert "-" * 30 in captured.out

    @patch("builtins.input")
    def test_get_integer_input(self, mock_input):
        """Test getting integer input."""
        # Test valid integer
        mock_input.return_value = "42"
        result = self.interactive.get_integer_input("Enter number")
        assert result == 42

        # Test invalid then valid
        mock_input.side_effect = ["abc", "-5", "10"]
        result = self.interactive.get_integer_input("Enter number", min_value=0)
        assert result == 10

        # Test with max value
        mock_input.side_effect = ["100", "5"]
        result = self.interactive.get_integer_input("Enter number", max_value=10)
        assert result == 5

    @patch("builtins.input")
    def test_configure_paths_url(self, mock_input):
        """Test configuring paths for URL source."""
        mock_config = MagicMock()
        mock_input.side_effect = ["3", "https://example.com/file.zip"]

        self.interactive.configure_paths(mock_config)

        mock_config.set_field.assert_any_call("source", "url")
        mock_config.set_field.assert_any_call("url", "https://example.com/file.zip")

    @patch("builtins.input")
    def test_configure_output_all_formats(self, mock_input):
        """Test configuring output with all format options."""
        mock_config = MagicMock()

        # Test markdown format
        mock_input.side_effect = ["output.md", "1", "n"]
        self.interactive.configure_output(mock_config)
        mock_config.set_field.assert_any_call("format", "markdown")

        # Test text format
        mock_config.reset_mock()
        mock_input.side_effect = ["output.txt", "2", "n"]
        self.interactive.configure_output(mock_config)
        mock_config.set_field.assert_any_call("format", "text")

        # Test JSON format
        mock_config.reset_mock()
        mock_input.side_effect = ["output.json", "3", "n"]
        self.interactive.configure_output(mock_config)
        mock_config.set_field.assert_any_call("format", "json")

        # Test XML format
        mock_config.reset_mock()
        mock_input.side_effect = ["output.xml", "4", "n"]
        self.interactive.configure_output(mock_config)
        mock_config.set_field.assert_any_call("format", "xml")

    @patch("builtins.input")
    def test_error_handling_in_yaml_save(self, mock_input):
        """Test error handling when saving YAML fails."""
        mock_config = MagicMock()
        mock_config.to_dict.return_value = {"key": "value"}
        mock_input.side_effect = ["y", "config.yml"]

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with patch("builtins.print") as mock_print:
                self.interactive.review_and_save(mock_config)

                # Check that error message was printed
                error_calls = [call for call in mock_print.call_args_list if "Error" in str(call)]
                assert len(error_calls) > 0
