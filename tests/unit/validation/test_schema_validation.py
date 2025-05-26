"""Unit tests for the schema validation module."""

import json
import os
import pytest
import tempfile

from codeconcat.validation.schema_validation import (
    validate_against_schema,
    load_schema_from_file,
    register_schema,
    generate_schema_from_example,
    SCHEMAS,
)
from codeconcat.errors import ValidationError


class TestSchemaValidation:
    """Test suite for schema validation."""

    def test_validate_against_schema_valid(self):
        """Test validating valid data against a schema."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 0}},
        }

        data = {"name": "Test User", "age": 30}

        # Should not raise an exception
        assert validate_against_schema(data, schema) is True

    def test_validate_against_schema_invalid(self):
        """Test validating invalid data against a schema."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 0}},
        }

        # Missing required field 'age'
        data = {"name": "Test User"}

        with pytest.raises(ValidationError) as excinfo:
            validate_against_schema(data, schema)

        assert "required property" in str(excinfo.value).lower()

    def test_validate_against_schema_by_name(self):
        """Test validating against a predefined schema by name."""
        data = {
            "source": "https://github.com/user/repo",
            "format": "markdown",
            "options": {"include_paths": ["src/**/*.py"]},
        }

        # Should not raise an exception
        assert validate_against_schema(data, "api_request") is True

    def test_validate_against_unknown_schema(self):
        """Test validating against an unknown schema name."""
        data = {"key": "value"}

        with pytest.raises(ValidationError) as excinfo:
            validate_against_schema(data, "unknown_schema")

        assert "unknown schema" in str(excinfo.value).lower()

    def test_load_schema_from_file(self):
        """Test loading a schema from a file."""
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp:
            json.dump(schema, temp)
            temp_path = temp.name

        try:
            loaded_schema = load_schema_from_file(temp_path)
            assert loaded_schema == schema
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    def test_load_schema_from_invalid_file(self):
        """Test loading a schema from an invalid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp:
            temp.write("This is not valid JSON")
            temp_path = temp.name

        try:
            with pytest.raises(ValidationError) as excinfo:
                load_schema_from_file(temp_path)

            assert "failed to load schema" in str(excinfo.value).lower()
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    def test_register_schema(self):
        """Test registering a new schema."""
        schema_name = "test_schema"
        schema = {"type": "object", "properties": {"test": {"type": "string"}}}

        # Register the schema
        register_schema(schema_name, schema)

        # Check that it was registered
        assert schema_name in SCHEMAS
        assert SCHEMAS[schema_name] == schema

    def test_generate_schema_from_example(self):
        """Test generating a schema from an example object."""
        example = {
            "name": "User",
            "age": 30,
            "is_active": True,
            "address": {"street": "123 Main St", "city": "Anytown"},
            "tags": ["user", "active"],
            "settings": None,
        }

        schema = generate_schema_from_example(example, required_fields=["name", "age"])

        # Check schema structure
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert schema["required"] == ["name", "age"]

        # Check property types
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["age"]["type"] == "integer"
        assert schema["properties"]["is_active"]["type"] == "boolean"
        assert schema["properties"]["address"]["type"] == "object"
        assert "properties" in schema["properties"]["address"]
        assert schema["properties"]["tags"]["type"] == "array"
        assert schema["properties"]["settings"]["type"] == "null"

    def test_generate_schema_from_non_dict(self):
        """Test generating a schema from a non-dictionary."""
        with pytest.raises(ValidationError) as excinfo:
            generate_schema_from_example("not a dict")

        assert "must be a dictionary" in str(excinfo.value).lower()
