"""
FastAPI application for CodeConCat.

This module defines the FastAPI application with routes for the CodeConCat
REST API, including API models, endpoints, and server configuration.
"""

import os
import logging
import tempfile
import uvicorn
import uuid
from contextvars import ContextVar
from http import HTTPStatus
from typing import Dict, List, Optional, Any, Callable

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from codeconcat.main import run_codeconcat_in_memory
from codeconcat.config.config_builder import ConfigBuilder

# Set up logging
logger = logging.getLogger(__name__)

# Context variable for request ID tracking
request_id_var = ContextVar("request_id", default=None)


# ────────────────────────────────────────────────────────────
# API Models
# ────────────────────────────────────────────────────────────


class CodeConcatRequest(BaseModel):
    """Request model for the CodeConCat API."""

    # Source options
    target_path: Optional[str] = Field(None, description="Local path to process (server-side path)")
    source_url: Optional[str] = Field(
        None, description="GitHub repository URL or shorthand (username/repo)"
    )
    source_ref: Optional[str] = Field(
        None, description="Branch, tag, or commit hash for GitHub repos"
    )
    github_token: Optional[str] = Field(None, description="GitHub token for private repositories")

    # Output options
    format: str = Field("json", description="Output format: json, markdown, xml, or text")
    output_preset: str = Field("medium", description="Output preset: lean, medium, or full")

    # Parsing options
    parser_engine: str = Field("tree_sitter", description="Parser engine: tree_sitter or regex")

    # Content options
    remove_comments: bool = Field(False, description="Remove comments from code")
    remove_docstrings: bool = Field(False, description="Remove docstrings from code")
    remove_empty_lines: bool = Field(False, description="Remove empty lines from code")

    # Include/exclude options
    include_paths: Optional[List[str]] = Field(None, description="Glob patterns to include")
    exclude_paths: Optional[List[str]] = Field(None, description="Glob patterns to exclude")
    include_languages: Optional[List[str]] = Field(None, description="Languages to include")
    exclude_languages: Optional[List[str]] = Field(None, description="Languages to exclude")

    # Compression options
    enable_compression: bool = Field(False, description="Enable intelligent code compression")
    compression_level: str = Field(
        "medium", description="Compression level: low, medium, high, aggressive"
    )

    # Process control
    max_workers: int = Field(4, description="Maximum number of worker threads")

    class Config:
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
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class CodeConcatSuccessResponse(BaseModel):
    """Success response model for the CodeConCat API."""

    message: str = Field(..., description="Success message")
    format: str = Field(..., description="Output format")
    job_id: Optional[str] = Field(None, description="Job ID for async processing")
    content: Optional[str] = Field(None, description="CodeConCat output content")
    stats: Optional[Dict[str, Any]] = Field(None, description="Processing statistics")


# ────────────────────────────────────────────────────────────
# API Application
# ────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="CodeConCat API",
        description="REST API for the CodeConCat code aggregation and documentation tool",
        version="0.7.0",  # Should match the package version
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Add request ID middleware for request tracing
    class RequestTracingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next: Callable):
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

    # Configure CORS for frontend access
    # Get allowed origins from environment variable or use a secure default
    allowed_origins = os.environ.get("CODECONCAT_ALLOWED_ORIGINS", "http://localhost:3000").split(
        ","
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Restrict to specific trusted domains
        allow_credentials=True,
        allow_methods=["GET", "POST"],  # Restrict to required methods only
        allow_headers=["Authorization", "Content-Type"],  # Restrict to required headers only
    )

    # ────────────────────────────────────────────────────────────
    # API Routes
    # ────────────────────────────────────────────────────────────

    from fastapi.responses import RedirectResponse

    @app.get("/", include_in_schema=False)
    async def read_root():
        """Redirect to API documentation."""
        return RedirectResponse(url="/api/docs")

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
        For local paths, it will process the files on the server.
        """
        try:
            # Create configuration based on request
            config_builder = ConfigBuilder()
            config_builder.with_defaults()
            config_builder.with_preset(request.output_preset)

            # Convert request to dictionary for config builder
            request_dict = request.dict(exclude_unset=True)
            config_builder.with_cli_args(request_dict)

            # Build and validate the configuration
            config = config_builder.build()

            # Process the code
            logger.info(f"Processing request with format: {config.format}")
            output = run_codeconcat_in_memory(config)

            # Create response
            stats = {
                "format": config.format,
                "preset": request.output_preset,
                "parser_engine": config.parser_engine,
            }

            return CodeConcatSuccessResponse(
                message="Processing completed successfully",
                format=config.format,
                content=output,
                stats=stats,
            )

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to process code", "details": str(e)},
            )

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
        """
        try:
            # Create a temporary directory to extract the zip file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save the uploaded file
                zip_path = os.path.join(temp_dir, file.filename)
                with open(zip_path, "wb") as f:
                    contents = await file.read()
                    f.write(contents)

                # Extract the zip file
                import zipfile

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Create configuration
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
                    }
                )

                config = config_builder.build()

                # Process the code
                logger.info(f"Processing uploaded files with format: {format}")
                output = run_codeconcat_in_memory(config)

                return CodeConcatSuccessResponse(
                    message="Upload and processing completed successfully",
                    format=format,
                    content=output,
                    stats={
                        "format": format,
                        "preset": output_preset,
                        "parser_engine": parser_engine,
                        "file_name": file.filename,
                    },
                )

        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail={"error": "Failed to extract or process zip file", "details": str(e)},
            )

    @app.get("/api/ping")
    async def ping():
        """Check if the API is running."""
        return {"status": "ok", "message": "CodeConCat API is running"}

    @app.get("/api/config/presets")
    async def get_presets():
        """Get available configuration presets."""
        from codeconcat.config.config_builder import PRESET_CONFIGS

        return {"presets": list(PRESET_CONFIGS.keys())}

    @app.get("/api/config/formats")
    async def get_formats():
        """Get available output formats."""
        return {"formats": ["json", "markdown", "xml", "text"]}

    @app.get("/api/config/languages")
    async def get_languages():
        """Get supported programming languages."""
        from codeconcat.language_map import SUPPORTED_LANGUAGES

        return {"languages": list(SUPPORTED_LANGUAGES.keys())}

    return app


def start_server(
    host: str = "127.0.0.1", port: int = 8000, log_level: str = "info", reload: bool = False
):
    """
    Start the CodeConCat API server.

    Args:
        host: The host to bind the server to. Default is 127.0.0.1 (localhost only).
        port: The port to bind the server to. Default is 8000.
        log_level: The log level for uvicorn. Default is "info".
        reload: Whether to reload the server on code changes. Default is False.
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


if __name__ == "__main__":
    # For direct execution of this module
    start_server(reload=True)
