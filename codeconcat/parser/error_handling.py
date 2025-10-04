"""
Standardized error handling for all parsers in the CodeConCat project.

This module provides consistent error handling utilities that can be used
across all parser implementations to ensure uniform error reporting,
recovery mechanisms, and debugging information.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from codeconcat.base_types import Declaration, ParseResult

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Base exception for parser-related errors."""

    def __init__(
        self,
        message: str,
        parser_name: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.parser_name = parser_name
        self.file_path = file_path
        self.line_number = line_number
        self.details = details or {}


class ParserInitializationError(ParserError):
    """Raised when parser initialization fails."""

    pass


class ParseFailureError(ParserError):
    """Raised when parsing fails completely."""

    pass


class PartialParseError(ParserError):
    """Raised when parsing succeeds but with errors or partial results."""

    pass


class SecurityValidationError(ParserError):
    """Raised when a security validation fails."""

    pass


class ErrorHandler:
    """
    Standardized error handler for all parsers.

    Provides consistent error reporting, logging, and recovery mechanisms
    across all parser implementations.
    """

    def __init__(self, parser_name: str):
        """
        Initialize the error handler.

        Args:
            parser_name: Name of the parser using this handler
        """
        self.parser_name = parser_name
        self.errors: List[ParserError] = []
        self.warnings: List[str] = []

    def handle_error(
        self,
        error: Union[Exception, str],
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        _recover: bool = False,
    ) -> ParseResult:
        """
        Handle an error that occurred during parsing.

        Args:
            error: The exception or error message that occurred
            file_path: Path to the file being parsed
            line_number: Line number where the error occurred
            context: Additional context information
            recover: Whether to attempt error recovery

        Returns:
            ParseResult with appropriate error information
        """
        # Convert string errors to exceptions
        if isinstance(error, str):
            error_msg = error
            parser_error: ParserError = ParseFailureError(
                error_msg,
                parser_name=self.parser_name,
                file_path=file_path,
                line_number=line_number,
                details=context,
            )
            missed_features = ["parsing"]
            parser_quality = "failed"
        elif isinstance(error, ParserInitializationError):
            error_msg = str(error)
            parser_error = ParserInitializationError(
                error_msg,
                parser_name=self.parser_name,
                file_path=file_path,
                line_number=line_number,
                details=context,
            )
            missed_features = ["parser_initialization"]
            parser_quality = "failed"
        elif isinstance(error, SecurityValidationError):
            error_msg = str(error)
            parser_error = SecurityValidationError(
                error_msg,
                parser_name=self.parser_name,
                file_path=file_path,
                line_number=line_number,
                details=context,
            )
            missed_features = ["security_validation"]
            parser_quality = "failed"
        else:
            error_msg = str(error)
            parser_error = ParseFailureError(
                error_msg,
                parser_name=self.parser_name,
                file_path=file_path,
                line_number=line_number,
                details=context,
            )
            missed_features = ["parsing_failure"]
            parser_quality = "failed"

        # Log the error
        logger.error(
            f"Parser error in {self.parser_name} for {file_path}: {error_msg}",
            exc_info=isinstance(error, Exception),
            extra={"context": context},
        )

        # Store the error
        self.errors.append(parser_error)

        # Return appropriate result
        return ParseResult(
            declarations=[],
            imports=[],
            error=error_msg,
            engine_used=self.parser_name,
            parser_quality=parser_quality,
            missed_features=missed_features,
        )

    def handle_partial_parse(
        self,
        declarations: List[Declaration],
        imports: List[str],
        error_message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        missed_features: Optional[List[str]] = None,
    ) -> ParseResult:
        """
        Handle a partial parse result (some data extracted but with errors).

        Args:
            declarations: Declarations that were successfully extracted
            imports: Imports that were successfully extracted
            error_message: Description of the error that occurred
            file_path: Path to the file being parsed
            line_number: Line number where the error occurred
            context: Additional context information
            missed_features: List of features that couldn't be extracted

        Returns:
            ParseResult with partial results and error information
        """
        # Create partial parse error
        parser_error = PartialParseError(
            error_message,
            parser_name=self.parser_name,
            file_path=file_path,
            line_number=line_number,
            details=context,
        )

        # Log the warning
        logger.warning(
            f"Partial parse in {self.parser_name} for {file_path}: {error_message}",
            extra={"context": context},
        )

        # Store the error
        self.errors.append(parser_error)

        # Return partial result
        return ParseResult(
            declarations=declarations,
            imports=imports,
            error=error_message,
            engine_used=self.parser_name,
            parser_quality="partial",
            missed_features=missed_features or ["error_recovery"],
        )

    def handle_warning(
        self,
        warning_message: str,
        file_path: Optional[str] = None,
        _line_number: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle a non-critical warning during parsing.

        Args:
            warning_message: The warning message
            file_path: Path to the file being parsed
            line_number: Line number where the warning occurred
            context: Additional context information
        """
        # Log the warning
        logger.warning(
            f"Parser warning in {self.parser_name} for {file_path}: {warning_message}",
            extra={"context": context},
        )

        # Store the warning
        self.warnings.append(warning_message)

    def create_success_result(
        self,
        declarations: List[Declaration],
        imports: List[str],
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ParseResult:
        """
        Create a successful parse result.

        Args:
            declarations: Declarations that were extracted
            imports: Imports that were extracted
            file_path: Path to the file being parsed
            context: Additional context information

        Returns:
            ParseResult with successful parsing information
        """
        # Log success
        logger.debug(
            f"Successful parse in {self.parser_name} for {file_path}: "
            f"{len(declarations)} declarations, {len(imports)} imports",
            extra={"context": context},
        )

        # Return successful result
        return ParseResult(
            declarations=declarations,
            imports=imports,
            error=None,
            engine_used=self.parser_name,
            parser_quality="full",
            missed_features=[],
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors and warnings.

        Returns:
            Dictionary containing error and warning summaries
        """
        return {
            "parser_name": self.parser_name,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                {
                    "message": str(error),
                    "file_path": error.file_path,
                    "line_number": error.line_number,
                    "details": error.details,
                }
                for error in self.errors
            ],
            "warnings": self.warnings,
        }

    def reset(self) -> None:
        """Reset all stored errors and warnings."""
        self.errors.clear()
        self.warnings.clear()


def create_standard_error_handler(parser_name: str) -> ErrorHandler:
    """
    Create a standardized error handler for a parser.

    Args:
        parser_name: Name of the parser

    Returns:
        Configured ErrorHandler instance
    """
    return ErrorHandler(parser_name)


def handle_security_error(
    error_message: str,
    parser_name: str,
    file_path: Optional[str] = None,
    _context: Optional[Dict[str, Any]] = None,
) -> ParseResult:
    """
    Handle a security validation error.

    Args:
        error_message: Description of the security error
        parser_name: Name of the parser
        file_path: Path to the file being parsed
        context: Additional context information

    Returns:
        ParseResult indicating security failure
    """
    logger.error(f"Security validation failed in {parser_name} for {file_path}: {error_message}")

    return ParseResult(
        declarations=[],
        imports=[],
        error=error_message,
        engine_used=parser_name,
        parser_quality="failed",
        missed_features=["security_validation"],
    )
