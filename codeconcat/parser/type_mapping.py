"""
Standardized type mapping for all parsers in the CodeConCat project.

This module provides consistent type names and mappings across all parser
implementations to ensure uniform output format and prevent confusion
for consumers of parser output.
"""

from enum import Enum
from typing import Dict, List, Optional, Set


class DeclarationType(Enum):
    """Standardized declaration types across all languages."""

    # Core types
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"

    # Language-specific types
    MODULE = "module"
    PACKAGE = "package"
    NAMESPACE = "namespace"
    TRAIT = "trait"
    PROTOCOL = "protocol"
    IMPLEMENTATION = "implementation"
    IMPL_BLOCK = "impl_block"

    # Variables and properties
    VARIABLE = "variable"
    CONSTANT = "constant"
    PROPERTY = "property"
    FIELD = "field"

    # Special types
    MACRO = "macro"
    TYPE_ALIAS = "type_alias"
    IMPORT = "import"
    EXPORT = "export"

    # Generic/unknown
    UNKNOWN = "unknown"


class TypeMapper:
    """
    Provides standardized type mapping across all parsers.

    This class ensures that different parsers use consistent type names
    for similar constructs, making the output uniform and predictable.
    """

    # Language-specific type mappings to standardized types
    LANGUAGE_TYPE_MAPPINGS: Dict[str, Dict[str, DeclarationType]] = {
        "python": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "module": DeclarationType.MODULE,
            "import": DeclarationType.IMPORT,
        },
        "javascript": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "import": DeclarationType.IMPORT,
            "export": DeclarationType.EXPORT,
        },
        "typescript": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "interface": DeclarationType.INTERFACE,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "import": DeclarationType.IMPORT,
            "export": DeclarationType.EXPORT,
            "type_alias": DeclarationType.TYPE_ALIAS,
        },
        "java": {
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "interface": DeclarationType.INTERFACE,
            "enum": DeclarationType.ENUM,
            "package": DeclarationType.PACKAGE,
            "import": DeclarationType.IMPORT,
            "field": DeclarationType.FIELD,
        },
        "c": {
            "function": DeclarationType.FUNCTION,
            "struct": DeclarationType.STRUCT,
            "enum": DeclarationType.ENUM,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "macro": DeclarationType.MACRO,
            "typedef": DeclarationType.TYPE_ALIAS,
        },
        "cpp": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "struct": DeclarationType.STRUCT,
            "enum": DeclarationType.ENUM,
            "namespace": DeclarationType.NAMESPACE,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "macro": DeclarationType.MACRO,
            "typedef": DeclarationType.TYPE_ALIAS,
        },
        "csharp": {
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "interface": DeclarationType.INTERFACE,
            "struct": DeclarationType.STRUCT,
            "enum": DeclarationType.ENUM,
            "namespace": DeclarationType.NAMESPACE,
            "property": DeclarationType.PROPERTY,
            "field": DeclarationType.FIELD,
            "import": DeclarationType.IMPORT,
        },
        "rust": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "struct": DeclarationType.STRUCT,
            "enum": DeclarationType.ENUM,
            "trait": DeclarationType.TRAIT,
            "impl": DeclarationType.IMPL_BLOCK,
            "module": DeclarationType.MODULE,
            "use": DeclarationType.IMPORT,
            "macro": DeclarationType.MACRO,
            "constant": DeclarationType.CONSTANT,
            "variable": DeclarationType.VARIABLE,
        },
        "go": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "struct": DeclarationType.STRUCT,
            "interface": DeclarationType.INTERFACE,
            "package": DeclarationType.PACKAGE,
            "import": DeclarationType.IMPORT,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
        },
        "php": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "interface": DeclarationType.INTERFACE,
            "trait": DeclarationType.TRAIT,
            "namespace": DeclarationType.NAMESPACE,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "import": DeclarationType.IMPORT,
        },
        "ruby": {
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "module": DeclarationType.MODULE,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "require": DeclarationType.IMPORT,
        },
        "julia": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "struct": DeclarationType.STRUCT,
            "module": DeclarationType.MODULE,
            "import": DeclarationType.IMPORT,
            "using": DeclarationType.IMPORT,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "macro": DeclarationType.MACRO,
        },
        "r": {
            "function": DeclarationType.FUNCTION,
            "class": DeclarationType.CLASS,
            "s3_class": DeclarationType.CLASS,
            "s4_class": DeclarationType.CLASS,
            "package": DeclarationType.PACKAGE,
            "library": DeclarationType.IMPORT,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
        },
        "kotlin": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "interface": DeclarationType.INTERFACE,
            "object": DeclarationType.CLASS,  # Kotlin object declarations
            "enum": DeclarationType.ENUM,
            "package": DeclarationType.PACKAGE,
            "import": DeclarationType.IMPORT,
            "property": DeclarationType.PROPERTY,
            "field": DeclarationType.FIELD,
        },
        "swift": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "struct": DeclarationType.STRUCT,
            "enum": DeclarationType.ENUM,
            "protocol": DeclarationType.PROTOCOL,
            "extension": DeclarationType.IMPLEMENTATION,
            "import": DeclarationType.IMPORT,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "property": DeclarationType.PROPERTY,
        },
        "dart": {
            "function": DeclarationType.FUNCTION,
            "method": DeclarationType.METHOD,
            "class": DeclarationType.CLASS,
            "interface": DeclarationType.INTERFACE,
            "enum": DeclarationType.ENUM,
            "mixin": DeclarationType.TRAIT,
            "library": DeclarationType.MODULE,
            "import": DeclarationType.IMPORT,
            "variable": DeclarationType.VARIABLE,
            "constant": DeclarationType.CONSTANT,
            "property": DeclarationType.PROPERTY,
        },
    }

    # Reverse mapping for lookup
    _reverse_mappings: Optional[Dict[str, Dict[DeclarationType, Set[str]]]] = None

    @classmethod
    def get_standard_type(cls, language: str, raw_type: str) -> DeclarationType:
        """
        Get the standardized type for a language-specific type.

        Args:
            language: The programming language (e.g., 'python', 'javascript')
            raw_type: The raw type string from the parser

        Returns:
            Standardized DeclarationType
        """
        language = language.lower()
        raw_type = raw_type.lower()

        # Get the mapping for this language
        lang_mapping = cls.LANGUAGE_TYPE_MAPPINGS.get(language, {})

        # Return the mapped type or UNKNOWN
        return lang_mapping.get(raw_type, DeclarationType.UNKNOWN)

    @classmethod
    def get_all_types_for_language(cls, language: str) -> Set[DeclarationType]:
        """
        Get all standardized types available for a language.

        Args:
            language: The programming language

        Returns:
            Set of DeclarationType values for the language
        """
        language = language.lower()
        lang_mapping = cls.LANGUAGE_TYPE_MAPPINGS.get(language, {})
        return set(lang_mapping.values())

    @classmethod
    def get_raw_types_for_standard_type(
        cls, language: str, standard_type: DeclarationType
    ) -> Set[str]:
        """
        Get all raw type strings that map to a standard type in a language.

        Args:
            language: The programming language
            standard_type: The standardized DeclarationType

        Returns:
            Set of raw type strings that map to the standard type
        """
        # Build reverse mappings if not already done
        if cls._reverse_mappings is None:
            cls._build_reverse_mappings()

        language = language.lower()
        if cls._reverse_mappings is None:
            return set()
        lang_reverse_mapping = cls._reverse_mappings.get(language, {})
        return lang_reverse_mapping.get(standard_type, set())

    @classmethod
    def _build_reverse_mappings(cls) -> None:
        """Build reverse mappings for efficient lookup."""
        cls._reverse_mappings = {}

        for language, type_mapping in cls.LANGUAGE_TYPE_MAPPINGS.items():
            reverse_mapping: Dict[DeclarationType, Set[str]] = {}

            for raw_type, standard_type in type_mapping.items():
                if standard_type not in reverse_mapping:
                    reverse_mapping[standard_type] = set()
                reverse_mapping[standard_type].add(raw_type)

            cls._reverse_mappings[language] = reverse_mapping

    @classmethod
    def is_function_like(cls, declaration_type: DeclarationType) -> bool:
        """
        Check if a declaration type is function-like (contains executable code).

        Args:
            declaration_type: The DeclarationType to check

        Returns:
            True if the type is function-like
        """
        return declaration_type in {
            DeclarationType.FUNCTION,
            DeclarationType.METHOD,
            DeclarationType.MACRO,
        }

    @classmethod
    def is_type_like(cls, declaration_type: DeclarationType) -> bool:
        """
        Check if a declaration type defines a type or structure.

        Args:
            declaration_type: The DeclarationType to check

        Returns:
            True if the type defines a type or structure
        """
        return declaration_type in {
            DeclarationType.CLASS,
            DeclarationType.INTERFACE,
            DeclarationType.STRUCT,
            DeclarationType.ENUM,
            DeclarationType.TRAIT,
            DeclarationType.PROTOCOL,
            DeclarationType.TYPE_ALIAS,
        }

    @classmethod
    def is_container_like(cls, declaration_type: DeclarationType) -> bool:
        """
        Check if a declaration type can contain other declarations.

        Args:
            declaration_type: The DeclarationType to check

        Returns:
            True if the type can contain other declarations
        """
        return declaration_type in {
            DeclarationType.CLASS,
            DeclarationType.INTERFACE,
            DeclarationType.STRUCT,
            DeclarationType.TRAIT,
            DeclarationType.PROTOCOL,
            DeclarationType.MODULE,
            DeclarationType.PACKAGE,
            DeclarationType.NAMESPACE,
            DeclarationType.IMPL_BLOCK,
            DeclarationType.IMPLEMENTATION,
        }

    @classmethod
    def get_type_hierarchy(cls) -> Dict[DeclarationType, List[DeclarationType]]:
        """
        Get a hierarchy of types for organizing declarations.

        Returns:
            Dictionary mapping parent types to child types
        """
        return {
            DeclarationType.FUNCTION: [
                DeclarationType.METHOD,
                DeclarationType.MACRO,
            ],
            DeclarationType.CLASS: [
                DeclarationType.INTERFACE,
                DeclarationType.STRUCT,
                DeclarationType.TRAIT,
                DeclarationType.PROTOCOL,
                DeclarationType.IMPLEMENTATION,
            ],
            DeclarationType.MODULE: [
                DeclarationType.PACKAGE,
                DeclarationType.NAMESPACE,
            ],
            DeclarationType.VARIABLE: [
                DeclarationType.CONSTANT,
                DeclarationType.PROPERTY,
                DeclarationType.FIELD,
            ],
        }


def get_standard_type(language: str, raw_type: str) -> DeclarationType:
    """
    Convenience function to get standardized type.

    Args:
        language: The programming language
        raw_type: The raw type string from the parser

    Returns:
        Standardized DeclarationType
    """
    return TypeMapper.get_standard_type(language, raw_type)


def standardize_declaration_kind(language: str, raw_kind: str) -> str:
    """
    Standardize a declaration kind string.

    Args:
        language: The programming language
        raw_kind: The raw kind string from the parser

    Returns:
        Standardized kind string
    """
    return get_standard_type(language, raw_kind).value
