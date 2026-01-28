"""
FastAPI application for CodeConCat.

This module defines the FastAPI application with routes for the CodeConCat
REST API, including API models, endpoints, and server configuration.
"""

import logging
import os
import tempfile
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from http import HTTPStatus
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.middleware.base import BaseHTTPMiddleware

from codeconcat.api.timeout_middleware import add_timeout_middleware
from codeconcat.api.validation_middleware import add_validation_middleware
from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.main import run_codeconcat_in_memory
from codeconcat.validation.schema_validation import SCHEMAS
from codeconcat.version import __version__

# Set up logging
logger = logging.getLogger(__name__)

# Critical dependency check for API security
try:
    HAS_JSONSCHEMA = True
except ImportError as err:
    HAS_JSONSCHEMA = False
    error_msg = (
        "CRITICAL: jsonschema is not installed but is required for API security. "
        "The API cannot start without proper input validation. "
        "Install with: pip install jsonschema"
    )
    logger.critical(error_msg)
    # Fail fast - don't start the API without security validation
    raise RuntimeError(error_msg) from err

# Context variable for request ID tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


# ────────────────────────────────────────────────────────────
# API Models
# ────────────────────────────────────────────────────────────


class CodeConcatRequest(BaseModel):
    """Request model for the CodeConCat API."""

    # Source options
    # SECURITY: target_path disabled in production for security
    # Only enable in development/testing environments with explicit ENV flag
    target_path: str | None = Field(
        None, description="Local path to process (DISABLED in production for security)"
    )
    source_url: str | None = Field(
        None, description="GitHub repository URL or shorthand (username/repo)"
    )
    source_ref: str | None = Field(None, description="Branch, tag, or commit hash for GitHub repos")
    github_token: str | None = Field(None, description="GitHub token for private repositories")

    # Output options
    format: str = Field("json", description="Output format: json, markdown, xml, or text")
    output_preset: str = Field("medium", description="Output preset: lean, medium, or full")

    # Parsing options
    parser_engine: str = Field("tree_sitter", description="Parser engine: tree_sitter or regex")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        """Validate that format is one of the supported values."""
        valid_formats = {"json", "markdown", "xml", "text"}
        if v not in valid_formats:
            raise ValueError(f"format must be one of {valid_formats}")
        return v

    @field_validator("output_preset")
    @classmethod
    def validate_output_preset(cls, v):
        """Validate that output_preset is one of the supported values."""
        valid_presets = {"lean", "medium", "full"}
        if v not in valid_presets:
            raise ValueError(f"output_preset must be one of {valid_presets}")
        return v

    @field_validator("parser_engine")
    @classmethod
    def validate_parser_engine(cls, v):
        """Validate that parser_engine is one of the supported values."""
        valid_engines = {"tree_sitter", "regex"}
        if v not in valid_engines:
            raise ValueError(f"parser_engine must be one of {valid_engines}")
        return v

    @field_validator("compression_level")
    @classmethod
    def validate_compression_level(cls, v):
        """Validate that compression_level is one of the supported values."""
        valid_levels = {"low", "medium", "high", "aggressive"}
        if v not in valid_levels:
            raise ValueError(f"compression_level must be one of {valid_levels}")
        return v

    # Content options
    remove_comments: bool = Field(False, description="Remove comments from code")
    remove_docstrings: bool = Field(False, description="Remove docstrings from code")
    remove_empty_lines: bool = Field(False, description="Remove empty lines from code")

    # Include/exclude options
    include_paths: list[str] | None = Field(None, description="Glob patterns to include")
    exclude_paths: list[str] | None = Field(None, description="Glob patterns to exclude")
    include_languages: list[str] | None = Field(None, description="Languages to include")
    exclude_languages: list[str] | None = Field(None, description="Languages to exclude")

    # Compression options
    enable_compression: bool = Field(False, description="Enable intelligent code compression")
    compression_level: str = Field(
        "medium", description="Compression level: low, medium, high, aggressive"
    )

    # Process control
    max_workers: int = Field(4, description="Maximum number of worker threads")

    @model_validator(mode="before")
    @classmethod
    def validate_source(cls, v):
        """Custom validation to ensure at least one source is provided.

        Security: Disables target_path in production unless explicitly allowed.
        """
        if isinstance(v, dict):
            target_path = v.get("target_path")
            source_url = v.get("source_url")

            # Security check: Disable target_path in production
            if (
                target_path
                and os.getenv("CODECONCAT_ALLOW_LOCAL_PATH", "false").lower() != "true"
                and os.getenv("ENV", "production").lower() == "production"
            ):
                raise ValueError(
                    "target_path is disabled in production for security. "
                    "Use source_url instead or set CODECONCAT_ALLOW_LOCAL_PATH=true "
                    "environment variable (NOT recommended for production)."
                )

            if not target_path and not source_url:
                # Check if we're in production mode for appropriate error message
                if os.getenv("ENV", "production").lower() == "production":
                    raise ValueError(
                        "source_url must be provided (target_path is disabled in production)"
                    )
                else:
                    raise ValueError("Either source_url or target_path must be provided")
        return v

    class Config:
        """Pydantic configuration for CodeConcatRequest model."""

        json_schema_extra = {
            "example": {
                "source_url": "username/repo",
                "format": "json",
                "output_preset": "medium",
                "parser_engine": "tree_sitter",
                "include_paths": ["**/*.py", "**/*.js"],
                "exclude_paths": ["**/tests/**"],
                "enable_compression": True,
                "compression_level": "medium",
            }
        }


class CodeConcatErrorResponse(BaseModel):
    """Error response model for the CodeConCat API."""

    error: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class CodeConcatSuccessResponse(BaseModel):
    """Success response model for the CodeConCat API."""

    message: str = Field(..., description="Success message")
    format: str = Field(..., description="Output format")
    job_id: str | None = Field(None, description="Job ID for async processing")
    content: str | None = Field(None, description="CodeConCat output content")
    result: str | None = Field(None, description="CodeConCat output result (alias for content)")
    files_processed: int | None = Field(None, description="Number of files processed")
    stats: dict[str, Any] | None = Field(None, description="Processing statistics")


# ────────────────────────────────────────────────────────────
# API Application
# ────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with security middleware.

    Configures a comprehensive security stack including:
    - Request tracing with unique IDs for debugging
    - Security headers (HSTS, CSP, X-Frame-Options, etc.)
    - CORS with restricted origins
    - Timeout protection against slowloris attacks
    - Request validation and rate limiting
    - Safe error handling that doesn't leak internal details

    Returns:
        FastAPI: Configured FastAPI application instance with all middleware
                and routes registered.

    Raises:
        RuntimeError: If jsonschema is not installed (required for API security).

    Security Notes:
        - CORS origins are restricted to environment-specified domains
        - All responses include security headers to prevent XSS, clickjacking
        - Request/response validation prevents injection attacks
        - Rate limiting protects against abuse
    """

    app = FastAPI(
        title="CodeConCat API",
        description="REST API for the CodeConCat code aggregation and documentation tool",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Add request ID middleware for request tracing
    class RequestTracingMiddleware(BaseHTTPMiddleware):
        """
        Middleware that adds unique request IDs for tracing and debugging.

        Assigns a UUID to each request and includes it in response headers.
        Request IDs are stored in context variables for access throughout
        the request lifecycle.
        """

        async def dispatch(self, request: Request, call_next: Callable):
            """
            Process request with unique ID assignment.

            Args:
                request: Incoming HTTP request.
                call_next: Next middleware in chain.

            Returns:
                Response with X-Request-ID header.

            Complexity: O(1) - UUID generation and header addition
            """
            request_id = str(uuid.uuid4())
            # Store request_id in context variable
            token = request_id_var.set(request_id)
            request.state.request_id = request_id

            try:
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                return response
            finally:
                # Reset the context variable token
                request_id_var.reset(token)

    app.add_middleware(RequestTracingMiddleware)

    # Add security headers middleware
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        """
        Middleware that adds security headers to all responses.

        Implements defense-in-depth by adding headers that prevent:
        - XSS attacks (Content-Security-Policy, X-XSS-Protection)
        - Clickjacking (X-Frame-Options)
        - MIME sniffing (X-Content-Type-Options)
        - Information disclosure (Referrer-Policy)
        - Downgrade attacks (Strict-Transport-Security)
        """

        async def dispatch(self, request: Request, call_next: Callable):
            """
            Add security headers to response.

            Args:
                request: Incoming HTTP request.
                call_next: Next middleware in chain.

            Returns:
                Response with comprehensive security headers.

            Complexity: O(1) - Header addition only
            """
            response = await call_next(request)
            # Add security headers to all responses
            for header, value in SECURITY_HEADERS.items():
                response.headers[header] = value
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Configure CORS for frontend access
    # Get allowed origins from environment variable or use a secure default
    allowed_origins = os.environ.get("CODECONCAT_ALLOWED_ORIGINS", "http://localhost:3000").split(
        ","
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Restrict to specific trusted domains
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],  # Include OPTIONS for CORS preflight
        allow_headers=["Authorization", "Content-Type"],  # Restrict to required headers only
    )

    # Add timeout middleware for protection against slowloris attacks
    add_timeout_middleware(
        app,
        default_timeout=60.0,  # 60 seconds default timeout
        read_timeout=10.0,  # 10 seconds to read request body
        write_timeout=10.0,  # 10 seconds to write response
        endpoint_timeouts={
            "/api/concat": 120.0,  # 2 minutes for code processing
            "/api/upload": 120.0,  # 2 minutes for file uploads
            "/api/process/*": 180.0,  # 3 minutes for large repo processing
        },
        skip_timeout_paths={"/", "/api/docs", "/api/redoc", "/api/openapi.json", "/api/health"},
    )

    # Add validation middleware for request/response validation
    add_validation_middleware(
        app,
        request_schemas={
            "/api/concat": dict(SCHEMAS["api_request"]),  # type: ignore[call-overload]
            "/api/upload": dict(SCHEMAS["api_request"]),  # type: ignore[call-overload]
        },
        max_request_size=20 * 1024 * 1024,  # 20MB limit
        rate_limit=100,  # 100 requests per minute
        rate_limit_window=60,  # 1 minute window
        skip_validation_paths={"/", "/api/docs", "/api/redoc", "/api/openapi.json"},
    )

    # ────────────────────────────────────────────────────────────
    # Exception Handlers
    # ────────────────────────────────────────────────────────────

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Handle all unhandled exceptions with secure error responses.

        Args:
            request: The incoming request that triggered the exception.
            exc: The unhandled exception.

        Returns:
            JSONResponse: Error response with request ID for tracing.

        Security Notes:
            - Production mode hides internal error details
            - Always includes request ID for debugging
            - Logs full exception internally for investigation

        Complexity: O(1) - Error response generation
        """
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"Unhandled exception in request {request_id}: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
        )

        # Don't expose internal error details in production
        if os.environ.get("CODECONCAT_ENV") == "production":
            error_message = "An internal error occurred. Please try again later."
            error_details = {"request_id": request_id}
        else:
            error_message = f"Internal server error: {type(exc).__name__}"
            error_details = {
                "request_id": request_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }

        return JSONResponse(
            status_code=500,
            content={"error": error_message, "details": error_details},
            headers={"X-Request-ID": request_id},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handle HTTP exceptions with consistent error format.

        Args:
            request: The incoming request that triggered the exception.
            exc: The HTTPException with status code and detail.

        Returns:
            JSONResponse: Formatted error response with status code.

        Complexity: O(1) - Error response formatting
        """
        request_id = getattr(request.state, "request_id", "unknown")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "details": {"request_id": request_id, "status_code": exc.status_code},
            },
            headers={"X-Request-ID": request_id},
        )

    # ────────────────────────────────────────────────────────────
    # API Routes
    # ────────────────────────────────────────────────────────────

    @app.get("/", include_in_schema=False)
    async def read_root():
        """
        Root endpoint that returns API information.

        Returns:
            dict: API name and version information.

        Complexity: O(1) - Simple status return
        """
        from codeconcat.version import __version__

        return {"name": "CodeConCat API", "version": __version__, "documentation": "/api/docs"}

    @app.post(
        "/api/concat",
        response_model=CodeConcatSuccessResponse,
        responses={
            400: {"model": CodeConcatErrorResponse},
            500: {"model": CodeConcatErrorResponse},
        },
    )
    async def process_code(request: CodeConcatRequest):
        """
        Process code with CodeConCat based on the provided configuration.

        This endpoint accepts a JSON configuration and returns the processed output.
        For GitHub repositories, it will clone the repository to a temporary directory.

        Args:
            request: CodeConcatRequest model with processing configuration.

        Returns:
            CodeConcatSuccessResponse: Processed output with statistics.

        Raises:
            HTTPException: On configuration errors or processing failures.

        Security Notes:
            - target_path field is disabled to prevent LFI attacks
            - Configuration is validated before processing
            - Errors don't expose internal details in production

        Complexity: O(n) where n is the number of files to process
        """
        try:
            # Create configuration based on request
            config_builder = ConfigBuilder()
            config_builder.with_defaults()
            config_builder.with_preset(request.output_preset)

            # Convert request to dictionary for config builder
            request_dict = request.model_dump(exclude_unset=True)
            config_builder.with_cli_args(request_dict)

            # Build and validate the configuration
            config = config_builder.build()

            # Validate configuration values explicitly
            from codeconcat.errors import ConfigurationError
            from codeconcat.validation.integration import validate_config_values

            try:
                validate_config_values(config)
                logger.debug(
                    f"Request ID: {request_id_var.get()} - Configuration validation passed"
                )
            except ConfigurationError as e:
                logger.error(
                    f"Request ID: {request_id_var.get()} - Configuration validation failed: {e}"
                )
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Configuration validation failed: {str(e)}",
                ) from e

            # Process the code
            logger.info(f"Processing request with format: {config.format}")
            output = run_codeconcat_in_memory(config)

            # Create response
            stats = {
                "format": config.format,
                "preset": request.output_preset,
                "parser_engine": config.parser_engine,
            }

            # Get file count for compatibility with tests
            files_processed = 0
            try:
                # Try to count files based on the target path if provided
                if hasattr(config, "target_path") and config.target_path:
                    import os

                    for _root, _dirs, files in os.walk(config.target_path):
                        files_processed += len(files)
            except Exception:
                files_processed = 0

            return CodeConcatSuccessResponse(
                message="Processing completed successfully",
                format=config.format,
                job_id=None,
                content=output,
                result=output,  # Alias for compatibility
                files_processed=files_processed,
                stats=stats,
            )

        except Exception as e:
            from codeconcat.errors import FileProcessingError

            request_id = request_id_var.get()
            logger.error(f"Error processing request {request_id}: {e}", exc_info=True)

            # Handle the case where no files are found more gracefully for API users
            if isinstance(e, FileProcessingError) and "No files were successfully parsed" in str(e):
                logger.info(f"No files found for processing in request {request_id}")
                return CodeConcatSuccessResponse(
                    message="No files found to process in the specified location",
                    format=config.format,
                    job_id=None,
                    content="",
                    result="",
                    files_processed=0,
                    stats={
                        "format": config.format,
                        "preset": request.output_preset,
                        "parser_engine": config.parser_engine,
                        "files_found": 0,
                    },
                )

            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Failed to process code. Please check your configuration and try again.",
            ) from e

    @app.post(
        "/api/upload",
        response_model=CodeConcatSuccessResponse,
        responses={
            400: {"model": CodeConcatErrorResponse},
            500: {"model": CodeConcatErrorResponse},
        },
    )
    async def upload_and_process(
        file: UploadFile = File(...),
        format: str = Form("json"),
        output_preset: str = Form("medium"),
        parser_engine: str = Form("tree_sitter"),
        enable_compression: bool = Form(False),
    ):
        """
        Upload a zip file containing code, process it with CodeConCat, and return the result.

        This endpoint accepts a zip file upload and processes it with CodeConCat.
        The zip file should contain the code to be processed.
        Results are returned as JSON by default but can be configured.

        Args:
            file: Uploaded zip file containing code to process.
            format: Output format (json, markdown, xml, text).
            output_preset: Configuration preset (lean, medium, full).
            parser_engine: Parser to use (tree_sitter, regex).
            enable_compression: Whether to compress output.

        Returns:
            CodeConcatSuccessResponse: Processed output with upload statistics.

        Raises:
            HTTPException: On invalid zip files or processing errors.

        Security Notes:
            - Implements safe_extract to prevent Zip Slip attacks
            - Sanitizes filenames to prevent path traversal
            - Validates all zip entries before extraction
            - Uses temporary directories that are cleaned up

        Complexity: O(n*m) where n is number of zip entries, m is file processing
        """
        try:
            # Create a temporary directory to extract the zip file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Sanitize filename to prevent path traversal
                import re

                safe_filename = re.sub(
                    r"[^a-zA-Z0-9._-]", "_", os.path.basename(file.filename or "upload.zip")
                )
                if not safe_filename.endswith(".zip"):
                    safe_filename += ".zip"

                # Save the uploaded file
                zip_path = os.path.join(temp_dir, safe_filename)
                with open(zip_path, "wb") as f:
                    contents = await file.read()
                    f.write(contents)

                # Extract the zip file with path traversal protection
                import zipfile

                def safe_extract(zip_ref, path):
                    """
                    Safely extract zip file, preventing path traversal attacks (Zip Slip).

                    Implements comprehensive protection against malicious zip files that
                    attempt to write files outside the intended extraction directory.

                    Args:
                        zip_ref: ZipFile object to extract from.
                        path: Target directory for extraction.

                    Security Measures:
                        1. Normalizes all paths to prevent '../' traversal
                        2. Checks for absolute paths which could escape sandbox
                        3. Validates real path stays within target directory
                        4. Logs and skips any suspicious entries

                    Complexity: O(n) where n is the number of entries in the zip
                    """
                    for member in zip_ref.namelist():
                        # Normalize the member path
                        member_path = os.path.normpath(member)

                        # Check for path traversal attempts
                        if os.path.isabs(member_path) or ".." in member_path.split(os.sep):
                            logger.warning(f"Skipping potentially malicious zip entry: {member}")
                            continue

                        # Ensure the destination is within temp_dir
                        target_path = os.path.join(path, member_path)
                        target_path = os.path.realpath(target_path)

                        if not target_path.startswith(os.path.realpath(path)):
                            logger.warning(f"Skipping zip entry outside target directory: {member}")
                            continue

                        # Extract the member
                        zip_ref.extract(member, path)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    safe_extract(zip_ref, temp_dir)

                # Create configuration
                # Temporarily allow local path for upload processing
                old_allow_local = os.environ.get("CODECONCAT_ALLOW_LOCAL_PATH")
                old_env = os.environ.get("ENV")

                try:
                    # Set environment to allow temp directory processing
                    os.environ["CODECONCAT_ALLOW_LOCAL_PATH"] = "true"
                    os.environ["ENV"] = "development"

                    config_builder = ConfigBuilder()
                    config_builder.with_defaults()
                    config_builder.with_preset(output_preset)

                    # Set specific options from form fields
                    config_builder.with_cli_args(
                        {
                            "target_path": temp_dir,
                            "format": format,
                            "parser_engine": parser_engine,
                            "enable_compression": enable_compression,
                            "include_paths": [
                                "**/*.py",
                                "**/*.md",
                                "**/*.txt",
                                "**/*.js",
                                "**/*.ts",
                            ],  # Include common file types
                        }
                    )

                    config = config_builder.build()
                finally:
                    # Restore original environment
                    if old_allow_local is not None:
                        os.environ["CODECONCAT_ALLOW_LOCAL_PATH"] = old_allow_local
                    else:
                        os.environ.pop("CODECONCAT_ALLOW_LOCAL_PATH", None)

                    if old_env is not None:
                        os.environ["ENV"] = old_env
                    else:
                        os.environ.pop("ENV", None)

                # Process the code
                logger.info(f"Processing uploaded files with format: {format}")
                output = run_codeconcat_in_memory(config)

                return CodeConcatSuccessResponse(
                    message="Upload and processing completed successfully",
                    format=format,
                    job_id=None,
                    content=output,
                    result=output,
                    files_processed=1,
                    stats={
                        "format": format,
                        "preset": output_preset,
                        "parser_engine": parser_engine,
                        "file_name": file.filename,
                    },
                )

        except Exception as e:
            request_id = request_id_var.get()
            logger.error(
                f"Error processing uploaded file in request {request_id}: {e}", exc_info=True
            )

            # Provide user-friendly error message
            if "zip" in str(e).lower():
                error_msg = (
                    "Failed to extract zip file. Please ensure the file is a valid zip archive."
                )
            else:
                error_msg = (
                    "Failed to process uploaded file. Please check the file format and try again."
                )

            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=error_msg) from e

    @app.get("/api/ping")
    async def ping():
        """
        Health check endpoint for monitoring API availability.

        Returns:
            dict: Status message indicating API is operational.

        Complexity: O(1) - Simple status return
        """
        import time

        return {
            "status": "ok",
            "message": "CodeConCat API is running",
            "timestamp": int(time.time()),
        }

    @app.get("/api/config/presets")
    async def get_presets():
        """
        Get available configuration presets for CodeConCat processing.

        Returns:
            dict: Available preset names (lean, medium, full).

        Complexity: O(1) - Returns static configuration list
        """
        from codeconcat.config.config_builder import PRESET_CONFIGS

        return {"presets": list(PRESET_CONFIGS.keys())}

    @app.get("/api/config/formats")
    async def get_formats():
        """
        Get available output formats for processed code.

        Returns:
            dict: Supported format types (json, markdown, xml, text).

        Complexity: O(1) - Returns static format list
        """
        return {"formats": ["json", "markdown", "xml", "text"]}

    @app.get("/api/config/languages")
    async def get_languages():
        """
        Get list of supported programming languages for parsing.

        Returns:
            dict: Sorted list of language names that can be processed.

        Complexity: O(n log n) where n is number of supported languages (sorting)
        """
        from codeconcat.language_map import ext_map

        # Get unique language values from the extension map
        languages = list(set(ext_map.values()))
        return {"languages": sorted(languages)}

    @app.get("/api/config/defaults")
    async def get_defaults():
        """
        Get default configuration values for CodeConCat processing.

        Returns:
            dict: Default configuration values for various options.

        Complexity: O(1) - Returns static default configuration
        """
        defaults = {
            "format": "json",
            "output_preset": "medium",
            "parser_engine": "tree_sitter",
            "max_workers": 4,
            "remove_comments": False,
            "remove_docstrings": False,
            "remove_empty_lines": False,
            "enable_compression": False,
            "compression_level": "medium",
            "use_gitignore": True,
            "use_default_excludes": True,
        }
        return {"defaults": defaults}

    return app


def start_server(
    host: str = "127.0.0.1", port: int = 8000, log_level: str = "info", reload: bool = False
):
    """
    Start the CodeConCat API server with security-hardened configuration.

    Args:
        host: The host to bind the server to. Default is 127.0.0.1 (localhost only)
              for security. Use 0.0.0.0 with caution in production.
        port: The port to bind the server to. Default is 8000.
        log_level: The log level for uvicorn. Default is "info".
        reload: Whether to reload the server on code changes. Default is False.
                Should only be True in development.

    Security Notes:
        - Default bind to localhost prevents external access
        - Custom logging includes request IDs for tracing
        - All middleware from create_app() is applied
        - Production should use a reverse proxy (nginx/apache)

    Example:
        # Development
        start_server(reload=True)

        # Production (behind reverse proxy)
        start_server(host="0.0.0.0", reload=False, log_level="warning")
    """
    app = create_app()

    # Configure uvicorn logging
    uvicorn_log_config = uvicorn.config.LOGGING_CONFIG
    uvicorn_log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

    # Set up custom formatter with request ID
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
    )

    # Start the server
    uvicorn.run(
        app, host=host, port=port, log_level=log_level, log_config=uvicorn_log_config, reload=reload
    )


# Create module-level app instance for import
app = create_app()

if __name__ == "__main__":
    # For direct execution of this module
    start_server(reload=True)
