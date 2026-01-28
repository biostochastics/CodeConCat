"""
Interactive configuration generator for CodeConCat.

This module provides an interactive command-line interface for creating
and customizing CodeConCat configuration files. It guides users through
the process of setting up a configuration tailored to their project's needs.
"""

import logging
import os
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class InteractiveConfigBuilder:
    """
    Interactive builder for CodeConCat configuration.

    This class provides a command-line interface for creating and customizing
    CodeConCat configuration files, guiding users through the process with
    clear prompts and helpful explanations.
    """

    def __init__(self, target_dir: str = "."):
        """
        Initialize the interactive config builder.

        Args:
            target_dir: The target directory where the config file will be created.
                        Defaults to the current directory.
        """
        self.target_dir = target_dir
        self.config_filename = os.path.join(target_dir, ".codeconcat.yml")
        self.config: dict[str, Any] = {}
        self.template_path = os.path.join(
            os.path.dirname(__file__), "templates", "default_config.template.yml"
        )

    def load_template(self) -> dict[str, Any]:
        """
        Load the default configuration template.

        Returns:
            The default configuration as a dictionary.
        """
        try:
            with open(self.template_path) as f:
                # Parse as yaml but preserve comments for later
                template_data = yaml.safe_load(f)
                return cast(dict[str, Any], template_data) if template_data else {}
        except FileNotFoundError:
            logger.error(f"Default configuration template not found: {self.template_path}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load default configuration template: {e}")
            return {}

    def run_interactive_setup(self) -> bool:
        """
        Run the interactive configuration setup.

        Returns:
            True if the configuration was successfully created, False otherwise.
        """
        if os.path.exists(self.config_filename) and not self._confirm_overwrite():
            print(f"\n🛑 Keeping existing {self.config_filename} file.")
            return False

        # Welcome message
        self._print_welcome()

        # Load the template configuration
        self.config = self.load_template()
        if not self.config:
            print("\n❌ Failed to load default configuration template.")
            return False

        # Interactive setup steps
        self._setup_preset()
        self._setup_project_languages()
        self._setup_exclude_paths()
        self._setup_output_format()
        self._setup_parser_engine()
        self._setup_compression()

        # Write the configuration to file
        return self._write_config()

    def _confirm_overwrite(self) -> bool:
        """
        Confirm with the user if they want to overwrite an existing config file.

        Returns:
            True if the user confirms overwrite, False otherwise.
        """
        answer = input(f"\n⚠️  The file {self.config_filename} already exists. Overwrite? (y/N): ")
        return answer.lower() in ["y", "yes"]

    def _print_welcome(self) -> None:
        """Print a welcome message and introduction."""
        print("\n" + "=" * 80)
        print(f"{'CodeConCat Interactive Configuration Setup':^80}")
        print("=" * 80)
        print("\nWelcome to the CodeConCat interactive configuration setup!")
        print("This tool will help you create a customized configuration for your project.")
        print("You'll be asked a series of questions to tailor the configuration to your needs.")
        print("Press Enter to accept the default values (shown in brackets).\n")
        print("=" * 80 + "\n")

    def _setup_preset(self) -> None:
        """Configure the output preset."""
        print("\n📊 Output Preset Configuration")
        print("-" * 30)
        print("Select an output preset that defines the amount of information included:")
        print("  1. lean   - Minimal output with core code only")
        print("  2. medium - Balanced output with code and important metadata")
        print("  3. full   - Comprehensive output with all available information")

        current_preset = self.config.get("output_preset", "medium")
        preset_map = {"1": "lean", "2": "medium", "3": "full"}
        preset_number = (
            "2" if current_preset == "medium" else "1" if current_preset == "lean" else "3"
        )

        while True:
            choice = (
                input(f"Choose preset [1-3] (default: {preset_number}): ").strip() or preset_number
            )
            if choice in preset_map:
                self.config["output_preset"] = preset_map[choice]
                break
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

    def _setup_project_languages(self) -> None:
        """Configure the included programming languages."""
        print("\n🔍 Language Selection")
        print("-" * 30)
        print("Select the programming languages in your project:")

        languages = [
            ("Python", "**/*.py"),
            ("JavaScript", "**/*.js"),
            ("TypeScript", "**/*.ts"),
            ("Java", "**/*.java"),
            ("Go", "**/*.go"),
            ("Ruby", "**/*.rb"),
            ("PHP", "**/*.php"),
            ("R", "**/*.r"),
            ("Rust", "**/*.rs"),
            ("C++", "**/*.cpp"),
            ("C", "**/*.c"),
            ("C#", "**/*.cs"),
            ("Julia", "**/*.jl"),
        ]

        # Get current include paths
        current_includes = self.config.get("include_paths", [])

        # Build a list of selected languages with checkboxes
        print("\nCurrent selection:")
        for i, (lang, pattern) in enumerate(languages, 1):
            checked = "✓" if pattern in current_includes else " "
            print(f"  {i:2d}. [{checked}] {lang} ({pattern})")

        print("\nEnter language numbers to toggle selection (comma-separated, e.g., '1,3,5')")
        print("Or press Enter to keep current selection")

        choice = input("Toggle languages: ").strip()
        if choice:
            # Parse user selection
            try:
                selected_indices = [int(idx.strip()) - 1 for idx in choice.split(",")]
                for idx in selected_indices:
                    if 0 <= idx < len(languages):
                        lang, pattern = languages[idx]
                        if pattern in current_includes:
                            current_includes.remove(pattern)
                        else:
                            current_includes.append(pattern)
            except ValueError:
                print("❌ Invalid input. Using current selection.")

        # Always include README and LICENSE files
        special_files = ["README*", "LICENSE*"]
        for special in special_files:
            if special not in current_includes:
                current_includes.append(special)

        self.config["include_paths"] = current_includes

    def _setup_exclude_paths(self) -> None:
        """Configure the excluded paths."""
        print("\n🚫 Excluded Paths")
        print("-" * 30)
        print("Configure paths to exclude from processing:")

        default_excludes = [
            "**/tests/**",
            "**/test/**",
            "**/examples/**",
            "**/docs/**",
            "**/build/**",
            "**/dist/**",
        ]

        current_excludes = self.config.get("exclude_paths", default_excludes)

        print("\nCommon excludes:")
        for i, path in enumerate(default_excludes, 1):
            checked = "✓" if path in current_excludes else " "
            print(f"  {i:2d}. [{checked}] {path}")

        print("\nEnter numbers to toggle (comma-separated, e.g., '1,3,5')")
        print("Or press Enter to keep current selection")

        choice = input("Toggle excludes: ").strip()
        if choice:
            try:
                selected_indices = [int(idx.strip()) - 1 for idx in choice.split(",")]
                for idx in selected_indices:
                    if 0 <= idx < len(default_excludes):
                        path = default_excludes[idx]
                        if path in current_excludes:
                            current_excludes.remove(path)
                        else:
                            current_excludes.append(path)
            except ValueError:
                print("❌ Invalid input. Using current selection.")

        # Ask for custom exclude paths
        print("\nAdd custom exclude patterns (comma-separated, leave empty to skip)")
        custom = input("Custom exclude patterns: ").strip()
        if custom:
            custom_patterns = [p.strip() for p in custom.split(",")]
            for pattern in custom_patterns:
                if pattern and pattern not in current_excludes:
                    current_excludes.append(pattern)

        self.config["exclude_paths"] = current_excludes

    def _setup_output_format(self) -> None:
        """Configure the output format."""
        print("\n📄 Output Format")
        print("-" * 30)
        print("Select the output format for the code aggregation:")
        print("  1. markdown - Formatted markdown document (best for readability)")
        print("  2. json     - JSON format (best for further processing)")
        print("  3. xml      - XML format (best for structured data)")
        print("  4. text     - Plain text (minimal formatting)")

        format_map = {"1": "markdown", "2": "json", "3": "xml", "4": "text"}
        current_format = self.config.get("format", "markdown")
        format_number = "1"
        for num, fmt in format_map.items():
            if fmt == current_format:
                format_number = num

        while True:
            choice = (
                input(f"Choose format [1-4] (default: {format_number}): ").strip() or format_number
            )
            if choice in format_map:
                self.config["format"] = format_map[choice]
                break
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

        # Configure clipboard option
        clipboard_choice = input("Copy output to clipboard? (y/N): ").strip().lower()
        self.config["clipboard"] = clipboard_choice in ["y", "yes"]

    def _setup_parser_engine(self) -> None:
        """Configure the parser engine."""
        print("\n🔍 Parser Engine")
        print("-" * 30)
        print("Select the parser engine to use:")
        print("  1. tree_sitter - Advanced parsing with better accuracy (recommended)")
        print("  2. regex       - Fallback parsing with simpler implementation")

        engine_map = {"1": "tree_sitter", "2": "regex"}
        current_engine = self.config.get("parser_engine", "tree_sitter")
        engine_number = "1" if current_engine == "tree_sitter" else "2"

        while True:
            choice = (
                input(f"Choose engine [1-2] (default: {engine_number}): ").strip() or engine_number
            )
            if choice in engine_map:
                self.config["parser_engine"] = engine_map[choice]
                break
            print("❌ Invalid choice. Please enter 1 or 2.")

    def _setup_compression(self) -> None:
        """Configure code compression settings."""
        print("\n🗜️  Code Compression")
        print("-" * 30)
        print(
            "Code compression reduces output size by intelligently omitting less important code segments."
        )

        # Enable compression
        current_enabled = self.config.get("enable_compression", False)
        enabled_default = "Y" if current_enabled else "N"
        compression_choice = (
            input("Enable code compression? (y/N): ").strip().lower() or enabled_default.lower()
        )
        enable_compression = compression_choice in ["y", "yes"]
        self.config["enable_compression"] = enable_compression

        if enable_compression:
            # Compression level
            print("\nSelect compression level:")
            print("  1. low       - Minimal compression, keeps most code")
            print("  2. medium    - Balanced compression level")
            print("  3. high      - Strong compression, keeps important code only")
            print("  4. aggressive - Maximum compression, keeps only critical code")

            level_map = {"1": "low", "2": "medium", "3": "high", "4": "aggressive"}
            current_level = self.config.get("compression_level", "medium")
            level_number = "2"
            for num, level in level_map.items():
                if level == current_level:
                    level_number = num

            while True:
                choice = (
                    input(f"Choose level [1-4] (default: {level_number}): ").strip() or level_number
                )
                if choice in level_map:
                    self.config["compression_level"] = level_map[choice]
                    break
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

    def _write_config(self) -> bool:
        """
        Write the configuration to file.

        Returns:
            True if the configuration was successfully written, False otherwise.
        """
        try:
            # Read the original template file to preserve comments
            with open(self.template_path) as f:
                template_content = f.read()

            # Write the configuration to file
            with open(self.config_filename, "w") as f:
                f.write(template_content)

            print(f"\n✅ Configuration saved to {self.config_filename}")
            print("\nTo use this configuration, run CodeConCat without the --init flag:")
            print("  codeconcat --target-path <your_code_directory>")
            print("\nYou can also override specific settings via command line, for example:")
            print("  codeconcat --format json --output custom_output.json")

            return True
        except Exception as e:
            logger.error(f"Failed to write configuration file: {e}")
            print(f"\n❌ Failed to write configuration file: {e}")
            return False


def run_interactive_setup(target_dir: str = ".") -> bool:
    """
    Run the interactive configuration setup.

    Args:
        target_dir: The target directory where the config file will be created.
                    Defaults to the current directory.

    Returns:
        True if the configuration was successfully created, False otherwise.
    """
    builder = InteractiveConfigBuilder(target_dir)
    return builder.run_interactive_setup()


if __name__ == "__main__":
    # For testing the module directly
    run_interactive_setup()
