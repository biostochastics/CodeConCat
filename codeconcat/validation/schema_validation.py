"""Schema validation for configuration and data files."""

import json
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path

try:
    import jsonschema
    from jsonschema.exceptions import ValidationError as JsonSchemaError

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

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
    data: Dict[str, Any], schema: Union[Dict[str, Any], str], context: Optional[str] = None
) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: The data to validate
        schema: Either a schema dictionary or a key in the SCHEMAS dictionary
        context: Optional context information for error messages

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails or jsonschema is not installed
    """
    if not HAS_JSONSCHEMA:
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
        )


def load_schema_from_file(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON schema from a file.

    Args:
        schema_path: Path to the schema file

    Returns:
        The loaded schema as a dictionary

    Raises:
        ValidationError: If the schema file cannot be loaded or is invalid
    """
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Basic validation that it's actually a schema
        if not isinstance(schema, dict):
            raise ValidationError(f"Schema must be a JSON object: {schema_path}")

        return schema
    except (IOError, json.JSONDecodeError) as e:
        raise ValidationError(f"Failed to load schema from {schema_path}", original_exception=e)


def register_schema(name: str, schema: Dict[str, Any]) -> None:
    """
    Register a new schema or update an existing one.

    Args:
        name: The name to register the schema under
        schema: The schema dictionary
    """
    SCHEMAS[name] = schema
    logger.debug(f"Registered schema: {name}")


def generate_schema_from_example(
    example: Dict[str, Any], required_fields: Optional[list] = None
) -> Dict[str, Any]:
    """
    Generate a JSON schema from an example object.

    This is useful for quickly creating a validation schema based on a known-good example.
    The generated schema will match the structure and types of the example.

    Args:
        example: An example object to generate a schema from
        required_fields: List of field names that should be required

    Returns:
        A JSON schema that would validate the example
    """
    if not isinstance(example, dict):
        raise ValidationError("Example must be a dictionary")

    schema = {"type": "object", "properties": {}}

    if required_fields:
        schema["required"] = required_fields

    for key, value in example.items():
        if isinstance(value, dict):
            schema["properties"][key] = generate_schema_from_example(value)
        elif isinstance(value, list):
            if value and all(isinstance(item, dict) for item in value):
                # List of objects
                item_schema = generate_schema_from_example(value[0])
                schema["properties"][key] = {"type": "array", "items": item_schema}
            elif value:
                # List of primitives
                item_type = type(value[0]).__name__
                type_mapping = {
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean",
                }
                schema["properties"][key] = {
                    "type": "array",
                    "items": {"type": type_mapping.get(item_type, item_type)},
                }
            else:
                # Empty list
                schema["properties"][key] = {"type": "array"}
        elif isinstance(value, str):
            schema["properties"][key] = {"type": "string"}
        elif isinstance(value, bool):
            # Check bool before int since bool is a subclass of int
            schema["properties"][key] = {"type": "boolean"}
        elif isinstance(value, int):
            schema["properties"][key] = {"type": "integer"}
        elif isinstance(value, float):
            schema["properties"][key] = {"type": "number"}
        elif value is None:
            schema["properties"][key] = {"type": "null"}

    return schema
