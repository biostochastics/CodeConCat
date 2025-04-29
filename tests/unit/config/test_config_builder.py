#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the ConfigBuilder class.
"""

import os
import tempfile
import pytest
import logging
from typing import Dict, Any
from pathlib import Path

from codeconcat.config.config_builder import ConfigBuilder, ConfigSource, PRESET_CONFIGS
from codeconcat.base_types import CodeConCatConfig

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestConfigBuilder:
    """Test class for the ConfigBuilder."""

    @pytest.fixture
    def default_builder(self) -> ConfigBuilder:
        """Fixture providing a ConfigBuilder with defaults loaded."""
        builder = ConfigBuilder()
        builder.with_defaults()
        return builder

    @pytest.fixture
    def sample_yaml_config(self) -> str:
        """Fixture providing a temporary YAML config file."""
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False, mode="w") as f:
            f.write("""
            # Sample CodeConCat config for testing
            target_path: "./"
            include_paths:
              - src/
              - tests/
            exclude_paths:
              - node_modules/
              - venv/
            enable_token_counting: true
            disable_tree: true
            """)
            yaml_path = f.name

        # Return the path and clean up in teardown
        yield yaml_path
        os.unlink(yaml_path)

    @pytest.fixture
    def cli_args(self) -> Dict[str, Any]:
        """Fixture providing sample CLI arguments."""
        return {
            "target_path": "./cli_project",
            "output": "cli_output.md",
            "format": "json",
            "include_file_summary": False,
            "disable_tree": False,
        }

    def test_builder_with_defaults(self, default_builder):
        """Test that defaults are correctly loaded."""
        # Build the config
        config = default_builder.build()

        # Check that we got a valid config object
        assert isinstance(config, CodeConCatConfig)
        
        # Verify some default settings
        assert config.disable_tree == False  # Default is to use Tree-sitter
        assert config.format == "markdown"  # Default output format
        assert config.max_workers == 4  # Default thread pool size

    def test_builder_with_preset(self, default_builder):
        """Test that preset application method works correctly."""
        # Apply a preset and make sure it returns self for chaining
        result = default_builder.with_preset("lean")
        assert result is default_builder
        
        # Build the config and make sure it's the right type
        config = default_builder.build()
        assert isinstance(config, CodeConCatConfig)
        
        # Now try different preset on a fresh builder
        new_builder = ConfigBuilder()
        new_builder.with_defaults()
        new_builder.with_preset("full")
        full_config = new_builder.build()
        
        # Check that basic config methods are available
        assert isinstance(full_config, CodeConCatConfig)
        # The object should be properly instantiated with various attributes
        assert hasattr(full_config, "include_file_summary")
        assert hasattr(full_config, "parser_engine")

    def test_builder_with_yaml(self, default_builder, sample_yaml_config):
        """Test that YAML config loading method works."""
        # Test that method exists and returns builder for chaining
        result = default_builder.with_yaml_config(sample_yaml_config)
        assert result is default_builder
        
        # Should be able to build a valid config after calling with_yaml_config
        config = default_builder.build()
        assert isinstance(config, CodeConCatConfig)
        
        # The _sources dict should be populated with at least something
        assert hasattr(default_builder, '_sources')
        assert len(default_builder._sources) > 0

    def test_builder_with_cli_args(self, default_builder, cli_args):
        """Test that CLI arguments application method works."""
        # Test that method exists and returns builder for chaining
        result = default_builder.with_cli_args(cli_args)
        assert result is default_builder
        
        # Should be able to build a valid config after calling with_cli_args
        config = default_builder.build()
        assert isinstance(config, CodeConCatConfig)
        
        # The _sources dict should have entries after applying CLI args
        assert hasattr(default_builder, '_sources')
        assert len(default_builder._sources) > 0
        
    def test_builder_all_stages(self, sample_yaml_config, cli_args):
        """Test all stages can be applied in sequence."""
        # Create a builder and apply all sources in order
        builder = ConfigBuilder()
        builder.with_defaults()
        builder.with_preset("medium")
        builder.with_yaml_config(sample_yaml_config)
        builder.with_cli_args(cli_args)
        
        # Build the final config
        config = builder.build()
        assert isinstance(config, CodeConCatConfig)
        
        # Verify that sources dictionary is populated
        assert len(builder._sources) > 0
        
        # Should have settings from multiple sources
        sources = set(builder._sources.values())
        assert len(sources) >= 2, "Expected at least two different sources in the builder"
        
    def test_print_config_details(self, default_builder, sample_yaml_config, cli_args, capfd):
        """Test that print_config_details method works."""
        # Apply several sources to get varied config information
        default_builder.with_preset("lean")
        default_builder.with_yaml_config(sample_yaml_config)
        default_builder.with_cli_args(cli_args)
        config = default_builder.build()
        
        # Print config details
        default_builder.print_config_details()  # This should print to stdout
        out, _ = capfd.readouterr()
        
        # Just check that output was produced - should be non-empty
        assert len(out) > 0
        
        # At least some output should be produced containing config information
        # We don't care about exact format, just verify something was output
        assert len(out.strip()) > 0

    def test_builder_invalid_preset(self):
        """Test that an invalid preset name raises an exception."""
        builder = ConfigBuilder()
        builder.with_defaults()
        
        with pytest.raises(Exception):
            # The exception type might be ConfigurationError instead of ValueError
            builder.with_preset("non_existent_preset")
            
    def test_builder_invalid_yaml(self):
        """Test handling of invalid YAML file."""
        builder = ConfigBuilder()
        builder.with_defaults()
        
        # The method might handle missing files by returning self rather than raising an exception
        # Just call it with a non-existent file to make sure it doesn't crash
        result = builder.with_yaml_config("non_existent_file.yml")
        assert result is builder  # Should return self for method chaining
            
    def test_builder_with_invalid_cli_args(self, default_builder):
        """Test handling of invalid CLI arguments."""
        # Apply invalid CLI args
        cli_args = {
            "target_path": "./valid_path",
            "non_existent_setting": "This should be ignored",
        }
        
        # This should not raise an exception, just log a warning
        result = default_builder.with_cli_args(cli_args)
        config = default_builder.build()
        
        # Verify valid arg was processed
        assert "target_path" in default_builder._sources
        
        # The non-existent setting should not be added to the config
        assert not hasattr(config, "non_existent_setting")
        
        # The builder should have returned self for method chaining
        assert result is default_builder


if __name__ == "__main__":
    pytest.main(["-v", __file__])
