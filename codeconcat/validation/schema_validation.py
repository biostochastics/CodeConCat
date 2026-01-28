"""Schema validation for configuration and data files.

This module provides JSON schema validation capabilities for CodeConCat configurations,
API requests/responses, and arbitrary data structures. It includes predefined schemas
for common use cases and utilities for schema management and generation.

Features:
- Predefined schemas for configurations, API requests, and API responses
- Schema loading from files
- Dynamic schema generation from examples
- Schema registration for custom validation needs
- Graceful fallback when jsonschema is not installed (CLI mode only)

Note:
    The jsonschema library is required for API mode (security critical) but optional
    for CLI mode (backward compatibility).
"""

import json
import logging
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema.exceptions import ValidationError as JsonSchemaError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    # Log critical error for production environments
    import sys

    if "codeconcat.api" in sys.modules:
        # We're in API mode, this is critical
        import logging

        logging.getLogger(__name__).critical(
            "jsonschema is not installed but is required for API security. "
            "Install with: pip install jsonschema"
        )

from ..errors import ValidationError

logger = logging.getLogger(__name__)

# Predefined schemas for common configurations
SCHEMAS = {
    "config": {
        "type": "object",
        "required": ["format", "output"],
        "properties": {
            "format": {"type": "string", "enum": ["markdown", "json", "xml", "text"]},
            "output": {"type": "string"},
            "include_paths": {"type": "array", "items": {"type": "string"}},
            "exclude_paths": {"type": "array", "items": {"type": "string"}},
            "include_languages": {"type": "array", "items": {"type": "string"}},
            "max_workers": {"type": "integer", "minimum": 1},
            "disable_ai_context": {"type": "boolean"},
            "remove_comments": {"type": "boolean"},
            "remove_docstrings": {"type": "boolean"},
            "remove_empty_lines": {"type": "boolean"},
            "include_repo_overview": {"type": "boolean"},
            "disable_tree": {"type": "boolean"},
            "github": {"type": ["string", "null"]},
            "cross_link_symbols": {"type": "boolean"},
            "enable_compression": {"type": "boolean"},
            "compression_level": {
                "type": "string",
                "enum": ["low", "medium", "high", "aggressive"],
            },
        },
        "additionalProperties": True,
    },
    "api_request": {
        "type": "object",
        "required": ["source", "format"],
        "properties": {
            "source": {"type": "string"},
            "format": {"type": "string", "enum": ["markdown", "json", "xml", "text"]},
            "options": {
                "type": "object",
                "properties": {
                    "include_paths": {"type": "array", "items": {"type": "string"}},
                    "exclude_paths": {"type": "array", "items": {"type": "string"}},
                    "include_languages": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
    "api_response": {
        "type": "object",
        "required": ["status", "data"],
        "properties": {
            "status": {"type": "string", "enum": ["success", "error"]},
            "data": {"type": "object"},
            "error": {"type": "string"},
            "metadata": {"type": "object"},
        },
        "additionalProperties": False,
        "allOf": [
            {"if": {"properties": {"status": {"const": "error"}}}, "then": {"required": ["error"]}}
        ],
    },
}


def validate_against_schema(
    data: dict[str, Any], schema: dict[str, Any] | str, context: str | None = None
) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: The data to validate
        schema: Either a schema dictionary or a key in the SCHEMAS dictionary
            Supported keys: "config", "api_request", "api_response"
        context: Optional context information for error messages (e.g., "API request")

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails or jsonschema is not installed in API mode

    Complexity:
        O(n) where n is the size of the data structure being validated

    Note:
        In API mode, jsonschema is required for security. In CLI mode, validation
        is skipped if jsonschema is not installed (backward compatibility).

    Example:
        >>> validate_against_schema({"format": "json", "output": "out.json"}, "config")
        True
    """
    if not HAS_JSONSCHEMA:
        # Check if we're in API mode - if so, this is a critical security issue
        import sys

        if "codeconcat.api" in sys.modules or "fastapi" in sys.modules:
            # In API mode, fail closed for security - we cannot proceed without validation
            raise ValidationError(
                "Schema validation is required for API security but jsonschema is not installed. "
                "Install with: pip install jsonschema"
            )
        else:
            # In CLI mode, warn but continue (backward compatibility for existing users)
            logger.warning("jsonschema package not installed. Schema validation is disabled.")
            logger.info("Install with: pip install jsonschema")
            return True

    # If schema is a string, look it up in the predefined schemas
    if isinstance(schema, str):
        if schema not in SCHEMAS:
            raise ValidationError(f"Unknown schema: {schema}")
        schema_dict = SCHEMAS[schema]
    else:
        schema_dict = schema

    try:
        jsonschema.validate(instance=data, schema=schema_dict)
        logger.debug(f"Schema validation passed for {context or 'data'}")
        return True
    except JsonSchemaError as e:
        error_path = "/".join(str(p) for p in e.path)
        context_str = f" in {context}" if context else ""
        message = f"Schema validation failed{context_str}: {e.message}"
        if error_path:
            message += f" (path: {error_path})"

        logger.error(message)
        raise ValidationError(
            message, field=error_path or None, value=e.instance, original_exception=e
        ) from e


def load_schema_from_file(schema_path: str | Path) -> dict[str, Any]:
    """
    Load a JSON schema from a file.

    Args:
        schema_path: Path to the schema file (must be valid JSON)

    Returns:
        The loaded schema as a dictionary

    Raises:
        ValidationError: If the schema file cannot be loaded, is invalid JSON,
            or is not a JSON object

    Complexity:
        O(n) where n is the size of the schema file

    Example:
        >>> schema = load_schema_from_file("path/to/schema.json")
        >>> validate_against_schema(data, schema)
    """
    try:
        with open(schema_path) as f:
            schema = json.load(f)

        # Basic validation that it's actually a schema
        if not isinstance(schema, dict):
            raise ValidationError(f"Schema must be a JSON object: {schema_path}")

        return schema
    except (OSError, json.JSONDecodeError) as e:
        raise ValidationError(
            f"Failed to load schema from {schema_path}", original_exception=e
        ) from e


def register_schema(name: str, schema: dict[str, Any]) -> None:
    """
    Register a new schema or update an existing one.

    This allows dynamic extension of the validation system with custom schemas
    that can be referenced by name in validate_against_schema().

    Args:
        name: The name to register the schema under (will overwrite if exists)
        schema: The schema dictionary conforming to JSON Schema specification

    Note:
        Registered schemas persist for the lifetime of the process

    Example:
        >>> custom_schema = {"type": "object", "required": ["id"]}
        >>> register_schema("my_schema", custom_schema)
        >>> validate_against_schema({"id": 123}, "my_schema")
    """
    SCHEMAS[name] = schema
    logger.debug(f"Registered schema: {name}")


def generate_schema_from_example(
    example: dict[str, Any], required_fields: list | None = None
) -> dict[str, Any]:
    """
    Generate a JSON schema from an example object.

    This is useful for quickly creating a validation schema based on a known-good example.
    The generated schema will match the structure and types of the example.

    Args:
        example: An example object to generate a schema from
        required_fields: List of field names that should be marked as required

    Returns:
        A JSON schema that would validate the example and similar objects

    Raises:
        ValidationError: If example is not a dictionary

    Complexity:
        O(n) where n is the total number of fields in the nested structure

    Note:
        - Recursively handles nested dictionaries and lists
        - Infers types from Python types (str->string, int->integer, etc.)
        - Empty lists result in untyped array schemas
        - None values result in "null" type

    Example:
        >>> example = {"name": "John", "age": 30, "active": True}
        >>> schema = generate_schema_from_example(example, required_fields=["name"])
        >>> # Results in schema requiring "name" field with appropriate types
    """
    if not isinstance(example, dict):
        raise ValidationError("Example must be a dictionary")

    schema: dict[str, Any] = {"type": "object", "properties": {}}

    if required_fields:
        schema["required"] = required_fields

    for key, value in example.items():
        if isinstance(value, dict):
            # Recursively generate schema for nested objects
            properties = schema.setdefault("properties", {})
            properties[key] = generate_schema_from_example(value)
        elif isinstance(value, list):
            if value and all(isinstance(item, dict) for item in value):
                # List of objects - use first item as template for all items
                item_schema = generate_schema_from_example(value[0])
                properties = schema.setdefault("properties", {})
                properties[key] = {"type": "array", "items": item_schema}
            elif value:
                # List of primitives - infer type from first element
                item_type = type(value[0]).__name__
                # Map Python type names to JSON Schema types
                type_mapping = {
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean",
                }
                properties = schema.setdefault("properties", {})
                properties[key] = {
                    "type": "array",
                    "items": {"type": type_mapping.get(item_type, item_type)},
                }
            else:
                # Empty list - can't infer item type
                properties = schema.setdefault("properties", {})
                properties[key] = {"type": "array"}
        elif isinstance(value, str):
            properties = schema.setdefault("properties", {})
            properties[key] = {"type": "string"}
        elif isinstance(value, bool):
            # Check bool before int since bool is a subclass of int in Python
            properties = schema.setdefault("properties", {})
            properties[key] = {"type": "boolean"}
        elif isinstance(value, int):
            properties = schema.setdefault("properties", {})
            properties[key] = {"type": "integer"}
        elif isinstance(value, float):
            properties = schema.setdefault("properties", {})
            properties[key] = {"type": "number"}
        elif value is None:
            properties = schema.setdefault("properties", {})
            properties[key] = {"type": "null"}

    return schema
