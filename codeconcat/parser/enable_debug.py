"""
Enable debug logging for all language parsers.

This module provides a simple way to enable debug logging for all parsers
by importing it at the start of your script.

Usage:
    import codeconcat.parser.enable_debug

    # After this import, all parsers will output debug logs
"""

import logging
import inspect
import importlib
import pkgutil
from pathlib import Path

# Set up the logger
PARSER_DEBUG = logging.getLogger("codeconcat.parser")
PARSER_DEBUG.setLevel(logging.DEBUG)

# Add a console handler if one doesn't exist
if not PARSER_DEBUG.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    PARSER_DEBUG.addHandler(handler)


def enable_debug_for_parsers():
    """Enable debug logging for all parser modules."""
    PARSER_DEBUG.debug("Enabling debug logging for all parsers")

    # Get the path to the language_parsers directory
    try:
        from codeconcat.parser import language_parsers

        parsers_path = Path(language_parsers.__file__).parent

        # Iterate through all modules in the language_parsers package
        for _, name, _ in pkgutil.iter_modules([str(parsers_path)]):
            if "parser" in name.lower():
                try:
                    # Import the module
                    module_name = f"codeconcat.parser.language_parsers.{name}"
                    PARSER_DEBUG.debug(f"Loading parser module: {module_name}")
                    module = importlib.import_module(module_name)

                    # Find all classes that might be parsers
                    for class_name, cls in inspect.getmembers(module, inspect.isclass):
                        if "parser" in class_name.lower():
                            # Set logger for the class if it has one
                            if hasattr(cls, "logger"):
                                cls.logger.setLevel(logging.DEBUG)
                                PARSER_DEBUG.debug(f"Enabled debug logging for {class_name}")
                except Exception as e:
                    PARSER_DEBUG.error(f"Error enabling debug for {name}: {e}")
    except ImportError:
        PARSER_DEBUG.error("Could not locate codeconcat.parser.language_parsers package")


def enable_all_parser_debug_logging():
    """Public API for enabling debug logging for all parsers.

    This is a wrapper around enable_debug_for_parsers that can be imported
    and called from other modules.
    """
    enable_debug_for_parsers()
    return PARSER_DEBUG


# Enable debug logging for all parsers when this module is imported
enable_debug_for_parsers()

# Enable debug logging for base_parser and enhanced_base_parser specifically
try:
    from codeconcat.parser.language_parsers.base_parser import BaseParser

    if hasattr(BaseParser, "logger"):
        BaseParser.logger.setLevel(logging.DEBUG)
        PARSER_DEBUG.debug("Enabled debug logging for BaseParser")
except (ImportError, AttributeError):
    PARSER_DEBUG.debug("Could not enable debug logging for BaseParser")

try:
    from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser

    if hasattr(EnhancedBaseParser, "logger"):
        EnhancedBaseParser.logger.setLevel(logging.DEBUG)
        PARSER_DEBUG.debug("Enabled debug logging for EnhancedBaseParser")
except (ImportError, AttributeError):
    PARSER_DEBUG.debug("Could not enable debug logging for EnhancedBaseParser")
