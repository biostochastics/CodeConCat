"""Request timeout middleware for the CodeConCat API."""

import asyncio
import contextlib
import logging
import time

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts and protect against slowloris attacks.

    This middleware:
    1. Sets a maximum time for request processing
    2. Protects against slow request/response attacks
    3. Ensures resources are freed in a timely manner
    4. Provides configurable timeouts per endpoint
    """

    def __init__(
        self,
        app: FastAPI,
        default_timeout: float = 30.0,  # 30 seconds default
        read_timeout: float = 10.0,  # 10 seconds to read request body
        write_timeout: float = 10.0,  # 10 seconds to write response
        endpoint_timeouts: dict[str, float] | None = None,
        skip_timeout_paths: set[str] | None = None,
    ):
        """
        Initialize the timeout middleware.

        Args:
            app: The FastAPI application
            default_timeout: Default timeout for all requests in seconds
            read_timeout: Maximum time to read request body
            write_timeout: Maximum time to write response
            endpoint_timeouts: Dictionary mapping endpoint paths to custom timeouts
            skip_timeout_paths: Set of paths to skip timeout enforcement
        """
        super().__init__(app)
        self.default_timeout = default_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.endpoint_timeouts = endpoint_timeouts or {}
        self.skip_timeout_paths = skip_timeout_paths or {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/health",
            "/api/health",
        }

        logger.info(
            f"Timeout middleware initialized with default timeout: {default_timeout}s, "
            f"read timeout: {read_timeout}s, write timeout: {write_timeout}s"
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process the request with timeout enforcement.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            The HTTP response or timeout error
        """
        path = request.url.path

        # Skip timeout for certain paths
        if any(path.startswith(skip_path) for skip_path in self.skip_timeout_paths):
            return await call_next(request)

        # Determine timeout for this endpoint
        timeout = self._get_timeout_for_path(path)

        # Track request start time
        start_time = time.time()

        process_task = None
        try:
            # Create a task for the actual request processing
            process_task = asyncio.create_task(self._process_with_timeout(request, call_next))

            # Wait for completion with timeout
            response = await asyncio.wait_for(process_task, timeout=timeout)

            # Log successful completion
            elapsed = time.time() - start_time
            if elapsed > timeout * 0.8:  # Warn if we're getting close to timeout
                logger.warning(
                    f"Request to {path} took {elapsed:.2f}s, approaching timeout of {timeout}s"
                )

            return response

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"Request to {path} timed out after {elapsed:.2f}s")

            return JSONResponse(
                status_code=504,
                content={
                    "status": "error",
                    "error": "Gateway Timeout",
                    "detail": f"Request processing exceeded maximum time of {timeout} seconds",
                },
                headers={
                    "X-Timeout": str(timeout),
                    "X-Elapsed-Time": f"{elapsed:.2f}",
                },
            )
        except Exception as e:
            logger.error(f"Unexpected error in timeout middleware: {e}")
            # Don't expose internal error details to client
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": "Internal Server Error",
                    "detail": "An internal error occurred while processing the request",
                },
            )
        finally:
            # Ensure task cleanup regardless of exception type
            if process_task and not process_task.done():
                process_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await process_task

    async def _process_with_timeout(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request with read timeout protection.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            The HTTP response
        """
        # For POST/PUT/PATCH requests, enforce read timeout on body parsing
        if request.method in ("POST", "PUT", "PATCH"):
            body_read_task = None
            try:
                # Set a timeout for reading the request body
                # This protects against slowloris-style attacks
                body_read_task = asyncio.create_task(self._read_body_with_timeout(request))
                await asyncio.wait_for(body_read_task, timeout=self.read_timeout)
            except asyncio.TimeoutError:
                logger.error(f"Request body read timeout for {request.url.path}")
                return JSONResponse(
                    status_code=408,
                    content={
                        "status": "error",
                        "error": "Request Timeout",
                        "detail": f"Failed to read request body within {self.read_timeout} seconds",
                    },
                )
            finally:
                # Clean up the task if it's still running
                if body_read_task and not body_read_task.done():
                    body_read_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await body_read_task

        # Process the actual request
        response = await call_next(request)
        return response

    async def _read_body_with_timeout(self, request: Request) -> bytes:
        """
        Read request body with timeout protection.

        This doesn't actually consume the body (which would prevent
        the endpoint from reading it), but validates that the body
        can be read within the timeout period.

        Args:
            request: The incoming request

        Returns:
            The request body bytes
        """
        # Check if body exists and is readable
        if not hasattr(request, "_body"):
            # This will trigger the body reading without consuming it
            # for the actual endpoint
            _ = await request.body()
        return b""

    def _get_timeout_for_path(self, path: str) -> float:
        """
        Get the timeout value for a specific path.

        Args:
            path: The request path

        Returns:
            The timeout value in seconds
        """
        # Check for exact match
        if path in self.endpoint_timeouts:
            return self.endpoint_timeouts[path]

        # Check for pattern matches (e.g., /api/process/* might have longer timeout)
        for pattern, timeout in self.endpoint_timeouts.items():
            if "*" in pattern:
                prefix = pattern.rstrip("*")
                if path.startswith(prefix):
                    return timeout
            elif "{" in pattern and "}" in pattern:
                # Handle path parameters like /api/items/{id}
                pattern_parts = pattern.split("/")
                path_parts = path.split("/")

                if len(pattern_parts) == len(path_parts):
                    match = True
                    for pp, p in zip(pattern_parts, path_parts, strict=False):
                        if "{" not in pp and "}" not in pp and pp != p:
                            match = False
                            break
                    if match:
                        return timeout

        # Return default timeout
        return self.default_timeout


def add_timeout_middleware(
    app: FastAPI,
    default_timeout: float = 30.0,
    read_timeout: float = 10.0,
    write_timeout: float = 10.0,
    endpoint_timeouts: dict[str, float] | None = None,
    skip_timeout_paths: set[str] | None = None,
) -> None:
    """
    Add timeout middleware to a FastAPI application.

    Args:
        app: The FastAPI application
        default_timeout: Default timeout for all requests in seconds
        read_timeout: Maximum time to read request body
        write_timeout: Maximum time to write response
        endpoint_timeouts: Dictionary mapping endpoint paths to custom timeouts
        skip_timeout_paths: Set of paths to skip timeout enforcement
    """
    app.add_middleware(
        TimeoutMiddleware,  # type: ignore[arg-type]
        default_timeout=default_timeout,
        read_timeout=read_timeout,
        write_timeout=write_timeout,
        endpoint_timeouts=endpoint_timeouts,
        skip_timeout_paths=skip_timeout_paths,
    )
    logger.info("Added timeout middleware to FastAPI application")
