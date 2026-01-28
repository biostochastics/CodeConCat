"""Parser for TOML configuration files."""

import tomli

from codeconcat.base_types import Declaration, ParseResult

from .base_parser import BaseParser


class TomlParser(BaseParser):
    """Parser for TOML configuration files."""

    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Return the list of languages this parser supports."""
        return ["config", "toml"]

    def parse(self, content: str, file_path: str) -> ParseResult:  # noqa: ARG002
        """Parse a TOML file and extract structure."""
        try:
            # Parse the TOML content
            toml_dict = tomli.loads(content)

            # Create declarations for top-level sections
            declarations = []
            for section_name, section_value in toml_dict.items():
                # Create a declaration for each top-level section
                section_decl = Declaration(
                    kind="section",
                    name=section_name,
                    start_line=self._find_section_line(content, section_name),
                    end_line=self._find_section_end_line(content, section_name),
                    docstring="",
                )

                # If section has subsections, add them as children
                if isinstance(section_value, dict):
                    for key, value in section_value.items():
                        child_decl = Declaration(
                            kind="property",
                            name=key,
                            start_line=self._find_property_line(content, key),
                            end_line=self._find_property_line(content, key),
                            docstring=str(value)[:50] + ("..." if len(str(value)) > 50 else ""),
                        )
                        section_decl.children.append(child_decl)

                declarations.append(section_decl)

            return ParseResult(
                declarations=declarations,
                imports=[],  # TOML doesn't have imports
                engine_used="tomli",
            )

        except Exception as e:
            # Return ParseResult with error message
            return ParseResult(
                declarations=[],
                imports=[],
                error=f"Error parsing TOML: {str(e)}",
                engine_used="tomli",
            )

    def _find_section_line(self, content: str, section_name: str) -> int:
        """Find the line number where a section appears in the TOML content."""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == f"[{section_name}]":
                return i + 1  # 1-based line numbers
        return 1  # Default to first line if not found

    def _find_section_end_line(self, content: str, section_name: str) -> int:
        """Find the end line number for a section in the TOML content."""
        lines = content.split("\n")
        start_line = self._find_section_line(content, section_name) - 1  # Convert back to 0-based

        # Look for the next section or end of file
        for i in range(start_line + 1, len(lines)):
            if lines[i].strip().startswith("["):
                return i  # End line is the line before the next section

        return len(lines)  # End of file if no next section

    def _find_property_line(self, content: str, property_name: str) -> int:
        """Find the line number where a property appears in the TOML content."""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith(f"{property_name} =") or stripped_line.startswith(
                f"{property_name}="
            ):
                return i + 1  # 1-based line numbers
        return 1  # Default to first line if not found
