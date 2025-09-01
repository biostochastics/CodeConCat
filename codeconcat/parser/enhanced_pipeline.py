#!/usr/bin/env python3

"""
Enhanced parsing pipeline for CodeConcat.

This module provides a unified parsing pipeline that attempts to use Tree-sitter first,
then falls back to enhanced regex parsers, and finally standard regex parsers.
It supports progressive enhancement and proper error handling.
"""

import logging
import traceback
from typing import Any, List, Tuple

from rich.progress import track

from ..base_types import CodeConCatConfig, EnhancedParserInterface, ParsedFileData
from ..errors import FileProcessingError, LanguageParserError, ParserError, UnsupportedLanguageError
from ..validation.unsupported_reporter import get_reporter as get_unsupported_reporter
from .file_parser import get_language_parser

logger = logging.getLogger(__name__)


def enhanced_parse_pipeline(
    files_to_parse: List[ParsedFileData], config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], List[ParserError]]:
    """
    Enhanced parsing pipeline with progressive fallbacks.

    This pipeline attempts parsing in the following order:
    1. Tree-sitter (if enabled)
    2. Enhanced regex parsers
    3. Standard regex parsers (slated for deprecation)

    It accumulates partial results and provides detailed error information.

    Args:
        files_to_parse: List of ParsedFileData objects to process
        config: Configuration object controlling parser behavior

    Returns:
        Tuple of (parsed_files, errors) where:
        - parsed_files is a list of ParsedFileData with parsing results
        - errors is a list of ParserError objects for failed files
    """
    logger.info(f"Starting enhanced parsing pipeline for {len(files_to_parse)} files")

    parsed_files_output: List[ParsedFileData] = []
    errors: List[ParserError] = []

    # Use process_with_progress wrapper for better UX
    progress_iterator = process_with_progress(
        files_to_parse, "Parsing files", config.disable_progress_bar
    )

    for file_data in progress_iterator:
        file_path = file_data.file_path
        content = file_data.content
        language = file_data.language

        logger.debug(f"Processing file: {file_path} (Language: {language})")

        try:
            # Skip files with missing data
            if not file_path or content is None:
                errors.append(
                    ParserError(
                        "Missing file path or content in input data",
                        file_path=file_path,
                    )
                )
                continue

            # Skip unsupported languages
            if not language or language == "unknown":
                logger.debug(f"Skipping file with unknown language: {file_path}")
                reporter = get_unsupported_reporter()
                reporter.add_skipped_file(
                    file_path,
                    "Unknown or unsupported language",
                    "unknown_language" if language == "unknown" else "unsupported_language",
                )
                continue

            # Skip excluded languages
            if config.include_languages and language not in config.include_languages:
                logger.debug(f"Skipping {file_path} - language '{language}' not in include list")
                reporter = get_unsupported_reporter()
                reporter.add_skipped_file(
                    file_path, f"Language '{language}' not in include list", "excluded_pattern"
                )
                continue

            if language in config.exclude_languages:
                logger.debug(f"Skipping {file_path} - language '{language}' in exclude list")
                reporter = get_unsupported_reporter()
                reporter.add_skipped_file(
                    file_path, f"Language '{language}' in exclude list", "excluded_pattern"
                )
                continue

            # Try parsing with progressive fallbacks
            parse_result = None
            parser_type_used = None
            parse_error = None

            # First try Tree-sitter if enabled
            if not config.disable_tree:
                logger.debug(f"Attempting Tree-sitter parser for {file_path}")
                try:
                    tree_sitter_parser = get_language_parser(
                        language, config, parser_type="tree_sitter"
                    )
                    if tree_sitter_parser:
                        # Check if parser implements the enhanced interface
                        if isinstance(tree_sitter_parser, EnhancedParserInterface):
                            # Validate the parser is ready to use
                            if not tree_sitter_parser.validate():
                                logger.warning(
                                    f"Tree-sitter parser for {language} failed validation"
                                )
                                raise ValueError(
                                    f"Tree-sitter parser for {language} failed validation"
                                )

                            # Get capabilities for logging
                            capabilities = tree_sitter_parser.get_capabilities()
                            logger.debug(f"Tree-sitter parser capabilities: {capabilities}")

                        # Parse the file
                        parse_result = tree_sitter_parser.parse(content, file_path)
                        if parse_result and not parse_result.error:
                            logger.debug(f"Tree-sitter parsing successful for {file_path}")
                            parser_type_used = "tree_sitter"
                except Exception as e:
                    parse_error = str(e)
                    logger.warning(
                        f"Tree-sitter parsing failed for {file_path}: {parse_error}", exc_info=True
                    )
                    # Continue to fallback parsers

            # Then try enhanced regex parser
            if not parse_result or parse_result.error:
                logger.debug(f"Attempting enhanced regex parser for {file_path}")
                try:
                    enhanced_parser = get_language_parser(language, config, parser_type="enhanced")
                    if enhanced_parser:
                        # Check if parser implements the enhanced interface
                        if isinstance(enhanced_parser, EnhancedParserInterface):
                            # Validate the parser is ready to use
                            if not enhanced_parser.validate():
                                logger.warning(f"Enhanced parser for {language} failed validation")
                                raise ValueError(
                                    f"Enhanced parser for {language} failed validation"
                                )

                            # Get capabilities for logging
                            capabilities = enhanced_parser.get_capabilities()
                            logger.debug(f"Enhanced parser capabilities: {capabilities}")

                        # Parse the file
                        parse_result = enhanced_parser.parse(content, file_path)
                        if parse_result and not parse_result.error:
                            logger.debug(f"Enhanced regex parsing successful for {file_path}")
                            parser_type_used = "enhanced_regex"
                except Exception as e:
                    parse_error = str(e)
                    logger.warning(
                        f"Enhanced regex parsing failed for {file_path}: {parse_error}",
                        exc_info=True,
                    )
                    # Continue to fallback parser

            # Finally try standard regex parser as last resort
            if not parse_result or parse_result.error:
                logger.debug(f"Attempting standard regex parser for {file_path}")
                try:
                    standard_parser = get_language_parser(language, config, parser_type="standard")
                    if standard_parser:
                        # Parse the file
                        parse_result = standard_parser.parse(content, file_path)
                        if parse_result and not parse_result.error:
                            logger.debug(f"Standard regex parsing successful for {file_path}")
                            parser_type_used = "standard_regex"
                except Exception as e:
                    parse_error = str(e)
                    logger.warning(
                        f"Standard regex parsing failed for {file_path}: {parse_error}",
                        exc_info=True,
                    )

            # Handle the final result
            if parse_result:
                file_data.parse_result = parse_result

                # Transfer declarations and imports from parse_result to file_data
                file_data.declarations = parse_result.declarations
                file_data.imports = parse_result.imports

                # If there was a parser error, add it to errors but keep partial results
                if parse_result.error:
                    errors.append(
                        LanguageParserError(
                            f"Parser encountered an error: {parse_result.error}",
                            file_path=file_path,
                        )
                    )
                    logger.warning(f"Partial parsing results for {file_path}: {parse_result.error}")
                else:
                    logger.info(f"Successfully parsed {file_path} using {parser_type_used} parser")

                # Add the file to the output list even with partial results
                parsed_files_output.append(file_data)
            else:
                # No parser was able to handle this file
                error_msg = f"No parser available or all parsers failed for {file_path} (language: {language})"
                if parse_error:
                    error_msg += f": {parse_error}"

                errors.append(UnsupportedLanguageError(error_msg, file_path=file_path))
                logger.warning(f"All parsers failed for {file_path}")

                # Track as unsupported file
                reporter = get_unsupported_reporter()
                reporter.add_skipped_file(
                    file_path,
                    f"No parser available for language '{language}'",
                    "unsupported_language",
                    details=parse_error,
                )

        except Exception as e:
            # Catch-all for any unexpected errors
            logger.error(f"Unexpected error processing {file_path}: {str(e)}", exc_info=True)
            errors.append(
                FileProcessingError(  # type: ignore[arg-type]
                    f"Unexpected error: {str(e)}\n{traceback.format_exc()}", file_path=file_path
                )
            )

    logger.info(
        f"Enhanced parsing pipeline completed: {len(parsed_files_output)} succeeded, {len(errors)} failed"
    )

    return parsed_files_output, errors


def process_with_progress(
    items: List[Any],
    description: str = "Processing",
    disable_progress: bool = False,
) -> Any:
    """
    Wrap a list with Rich progress reporting.

    Args:
        items: The list of items to process
        description: Description for the progress bar
        disable_progress: Whether to disable the progress bar

    Returns:
        A Rich track iterator for the input items
    """
    return track(items, description=description, disable=disable_progress, total=len(items))
