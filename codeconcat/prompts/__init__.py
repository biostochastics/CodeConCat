"""
Prompt management for CodeConCat codebase analysis.

This module provides functionality for loading, templating, and managing
prompts used for LLM-based codebase analysis.
"""

import os
import re
from pathlib import Path


class PromptManager:
    """Manages prompts for codebase analysis."""

    DEFAULT_PROMPT_FILE = "codebase_review_default.md"
    MAX_PROMPT_SIZE = 50000  # 50KB max to prevent huge prompts

    def __init__(self):
        """Initialize the prompt manager."""
        self.prompts_dir = Path(__file__).parent
        self.default_prompt_path = self.prompts_dir / self.DEFAULT_PROMPT_FILE

    def load_prompt(self, prompt_file: str | None = None) -> str:
        """
        Load a prompt from file.

        Args:
            prompt_file: Path to custom prompt file. Must be provided.

        Returns:
            The loaded prompt text.

        Raises:
            FileNotFoundError: If prompt file doesn't exist.
            ValueError: If prompt file is too large or invalid.
        """
        if not prompt_file:
            raise ValueError("Prompt file must be specified")

        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            # Check if it's a special keyword for the default prompt
            if prompt_file == "default":
                prompt_path = self.default_prompt_path
                if not prompt_path.exists():
                    raise FileNotFoundError(f"Default prompt not found: {self.default_prompt_path}")
            else:
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        # Check file size
        file_size = prompt_path.stat().st_size
        if file_size > self.MAX_PROMPT_SIZE:
            raise ValueError(
                f"Prompt file too large ({file_size} bytes). "
                f"Maximum size is {self.MAX_PROMPT_SIZE} bytes."
            )

        # Load prompt content
        try:
            with open(prompt_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read prompt file: {e}") from e

        # Validate it's not empty
        if not content.strip():
            raise ValueError("Prompt file is empty")

        return content

    def substitute_variables(self, prompt: str, variables: dict[str, str]) -> str:
        """
        Substitute variables in the prompt.

        Variables in the prompt should be in the format {VARIABLE_NAME}.
        Also supports environment variable expansion with ${ENV_VAR}.

        Args:
            prompt: The prompt text with placeholders.
            variables: Dictionary of variable names to values.

        Returns:
            The prompt with variables substituted.

        Raises:
            ValueError: If required variables are missing.
        """

        # First, expand environment variables (${VAR} format)
        def expand_env(match):
            var_name = match.group(1)
            value = os.environ.get(var_name)
            if value is None:
                # Keep original if env var not found
                return match.group(0)
            return value

        prompt = re.sub(r"\$\{([A-Z_][A-Z0-9_]*)\}", expand_env, prompt)

        # Then substitute provided variables ({VAR} format)
        pattern = re.compile(r"\{([A-Z_][A-Z0-9_]*)\}")

        # Find all variables in the prompt
        required_vars = set(pattern.findall(prompt))

        # Check for missing required variables
        provided_vars = set(variables.keys())
        missing_vars = required_vars - provided_vars

        # Some variables are optional (context variables)
        optional_vars = {
            "PROJECT_GOALS",
            "TECH_CONSTRAINTS",
            "TEAM_SIZE",
            "TIMELINE",
            "FOCUS_AREAS",
            "REPO_NAME",
            "REPO_SUMMARY",
            "PATHS_INCLUDED",
            "PATHS_EXCLUDED",
            "OUTPUT_FORMAT",
            "TIME_BUDGET",
            "CONSTRAINTS",
        }

        truly_missing = missing_vars - optional_vars
        if truly_missing:
            raise ValueError(f"Required variables missing: {', '.join(sorted(truly_missing))}")

        # Perform substitution
        def replace_var(match):
            """Replace variable placeholders within a matched pattern with their corresponding values.
            Parameters:
                - match (re.Match): The match object representing a variable placeholder.
            Returns:
                - str: The value associated with the variable if present, or the original match if the variable is neither found in `variables` nor `optional_vars`.
            """
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            elif var_name in optional_vars:
                # Remove optional variables if not provided
                return ""
            return match.group(0)

        return pattern.sub(replace_var, prompt)

    def get_default_prompt(self) -> str:
        """Get the default codebase review prompt."""
        return self.load_prompt()

    def prepare_prompt(
        self, prompt_file: str | None = None, variables: dict[str, str] | None = None
    ) -> str:
        """
        Load and prepare a prompt with variable substitution.

        Args:
            prompt_file: Optional custom prompt file.
            variables: Optional variables to substitute.

        Returns:
            The prepared prompt text.
        """
        prompt = self.load_prompt(prompt_file)

        if variables:
            prompt = self.substitute_variables(prompt, variables)

        return prompt


# Convenience function
def get_review_prompt(custom_file: str | None = None, **kwargs) -> str:
    """
    Get a codebase review prompt.

    Args:
        custom_file: Optional path to custom prompt file.
        **kwargs: Variables to substitute in the prompt.

    Returns:
        The prepared prompt text.
    """
    manager = PromptManager()
    return manager.prepare_prompt(custom_file, kwargs if kwargs else None)
