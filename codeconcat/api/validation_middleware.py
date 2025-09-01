"""Validation middleware for the CodeConCat API."""

import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, cast

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ..errors import ValidationError
from ..validation.schema_validation import validate_against_schema

logger = logging.getLogger(__name__)

# Constants for memory management
MAX_REQUEST_TRACKING = 10000  # Maximum number of IPs to track
REQUEST_CLEANUP_INTERVAL = 300  # Cleanup every 5 minutes


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API requests and responses against schemas.

    This middleware can:
    1. Validate request bodies against schemas based on endpoint
    2. Validate response bodies against schemas
    3. Log validation errors
    4. Implement rate limiting and request size validation
    """

    def __init__(
        self,
        app: FastAPI,
        request_schemas: Dict[str, Dict[str, Any]] | None = None,
        response_schemas: Dict[str, Dict[str, Any]] | None = None,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        rate_limit: int = 100,  # requests per minute
        rate_limit_window: int = 60,  # seconds
        skip_validation_paths: set | None = None,
    ):
        """
        Initialize the validation middleware.

        Args:
            app: The FastAPI application
            request_schemas: Dictionary mapping endpoint paths to request schemas
            response_schemas: Dictionary mapping endpoint paths to response schemas
            max_request_size: Maximum allowed request size in bytes
            rate_limit: Maximum requests per rate_limit_window
            rate_limit_window: Time window for rate limiting in seconds
            skip_validation_paths: Set of paths to skip validation for (e.g., '/docs', '/redoc')
        """
        super().__init__(app)
        self.request_schemas = request_schemas or {}
        self.response_schemas = response_schemas or {}
        self.max_request_size = max_request_size
        self.rate_limit = rate_limit
        self.rate_limit_window = rate_limit_window
        self.skip_validation_paths = skip_validation_paths or {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        }

        # Rate limiting state with bounded size using OrderedDict for LRU behavior
        self.request_counts: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        # Use RLock for recursive locking support and better thread safety
        self._cleanup_lock = threading.RLock()
        self._last_cleanup = time.time()
        self.max_tracked_clients = MAX_REQUEST_TRACKING
        self.cleanup_interval = REQUEST_CLEANUP_INTERVAL

        logger.info(
            f"Validation middleware initialized with {len(self.request_schemas)} "
            f"request schemas and {len(self.response_schemas)} response schemas. "
            f"Max tracked clients: {self.max_tracked_clients}"
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process the request and apply validation.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            The HTTP response
        """
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Skip validation for certain paths
        if any(path.startswith(skip_path) for skip_path in self.skip_validation_paths):
            return await call_next(request)

        # Perform periodic cleanup of old entries
        self._periodic_cleanup()

        # 1. Check rate limits
        if not self._check_rate_limit(client_ip, path, request.method):
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": "Too many requests",
                    "detail": "Rate limit exceeded",
                },
            )

        # 2. Check request size
        content_length = request.headers.get("content-length", "0")
        if content_length.isdigit() and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content={
                    "status": "error",
                    "error": "Request entity too large",
                    "detail": f"Request size exceeds maximum of {self.max_request_size} bytes",
                },
            )

        # 3. Validate request body against schema if one exists for this path
        schema = self._get_schema_for_path(path, self.request_schemas)

        if schema and request.method in ("POST", "PUT", "PATCH"):
            try:
                # Try to parse JSON body
                body = await request.json()
                logger.debug(f"Validating request body against schema for {path}")
                validate_against_schema(body, schema, context=f"request to {path}")
            except ValidationError as e:
                logger.warning(f"Validation error for {path}: {e}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "error": "Validation error",
                        "detail": str(e),
                        "field": e.field if hasattr(e, "field") else None,
                    },
                )
            except Exception as e:
                logger.error(f"Error parsing request body: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "error": "Invalid request body", "detail": str(e)},
                )

        # 4. Process the request
        try:
            response = await call_next(request)
            return response
        except ValidationError as e:
            logger.error(f"Validation error during request processing: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error": "Validation error",
                    "detail": str(e),
                    "field": e.field if hasattr(e, "field") else None,
                },
            )
        except Exception as e:
            logger.error(f"Unhandled exception in request processing: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "error": "Internal server error",
                    "detail": str(e) if str(e) else "An unexpected error occurred",
                },
            )

    def _check_rate_limit(self, client_ip: str, path: str, method: str) -> bool:
        """
        Check if a client has exceeded the rate limit.

        Args:
            client_ip: The client's IP address
            path: The request path
            method: The HTTP method

        Returns:
            True if the client is within the rate limit, False otherwise
        """
        now = time.time()

        # Create a composite key for more granular rate limiting
        rate_limit_key = f"{client_ip}:{method}:{path}"

        with self._cleanup_lock:
            # Check if we're at capacity and need to evict oldest entries
            if (
                len(self.request_counts) >= self.max_tracked_clients
                and rate_limit_key not in self.request_counts
            ):
                # Remove oldest entry (FIFO) - safe because we're in a lock
                try:
                    oldest_key = next(iter(self.request_counts))
                    del self.request_counts[oldest_key]
                    logger.debug(f"Evicted oldest rate limit entry: {oldest_key}")
                except StopIteration:
                    # Handle edge case where dictionary becomes empty between checks
                    pass

            # Initialize or clean up the client's request history
            if rate_limit_key not in self.request_counts:
                self.request_counts[rate_limit_key] = {"count": 0, "window_start": now}
            elif now - self.request_counts[rate_limit_key]["window_start"] > self.rate_limit_window:
                # Reset the window if it has expired
                self.request_counts[rate_limit_key] = {"count": 0, "window_start": now}

            # Move to end for LRU behavior
            self.request_counts.move_to_end(rate_limit_key)

            # Increment the request count
            self.request_counts[rate_limit_key]["count"] += 1

            # Check if the rate limit is exceeded
            if self.request_counts[rate_limit_key]["count"] > self.rate_limit:
                logger.warning(f"Rate limit exceeded for {rate_limit_key}")
                return False

        return True

    def _periodic_cleanup(self) -> None:
        """
        Periodically clean up expired rate limit entries to prevent memory growth.
        """
        now = time.time()

        # Only cleanup if enough time has passed since last cleanup
        if now - self._last_cleanup < self.cleanup_interval:
            return

        with self._cleanup_lock:
            # Check again inside lock to prevent duplicate cleanup
            if now - self._last_cleanup < self.cleanup_interval:
                return

            # Create a snapshot of keys to avoid dictionary modification during iteration
            # This prevents RuntimeError: dictionary changed size during iteration
            expired_keys = []
            # Use list() to create a snapshot of items for safe iteration
            for key, data in list(self.request_counts.items()):
                # Remove entries that are expired (2x the window for safety)
                if now - data["window_start"] > self.rate_limit_window * 2:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.request_counts[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired rate limit entries")

            self._last_cleanup = now

    def _get_schema_for_path(
        self, path: str, schema_dict: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the schema for a given path, considering path parameters.

        Args:
            path: The request path
            schema_dict: Dictionary mapping paths to schemas

        Returns:
            The schema if found, None otherwise
        """
        # Direct match
        if path in schema_dict:
            schema = schema_dict[path]
            if isinstance(schema, dict):
                return cast(Dict[str, Any], schema)
            # If not a dict, return None as we can't handle other types
            return None

        # Try to match patterns with path parameters
        for pattern, schema in schema_dict.items():
            # Handle path parameter patterns like "/api/items/{id}"
            if "{" in pattern and "}" in pattern:
                pattern_parts = pattern.split("/")
                path_parts = path.split("/")

                if len(pattern_parts) != len(path_parts):
                    continue

                match = True
                for _i, (pattern_part, path_part) in enumerate(zip(pattern_parts, path_parts)):
                    if "{" in pattern_part and "}" in pattern_part:
                        # This is a path parameter, so it matches any value
                        continue
                    elif pattern_part != path_part:
                        match = False
                        break

                if match:
                    if isinstance(schema, dict):
                        return cast(Dict[str, Any], schema)
                    # If not a dict, return None as we can't handle other types
                    return None

        return None


# Add helper function to register with FastAPI app
def add_validation_middleware(
    app: FastAPI,
    request_schemas: Dict[str, Dict[str, Any]] | None = None,
    response_schemas: Dict[str, Dict[str, Any]] | None = None,
    max_request_size: int = 10 * 1024 * 1024,
    rate_limit: int = 100,
    rate_limit_window: int = 60,
    skip_validation_paths: set | None = None,
) -> None:
    """
    Add validation middleware to a FastAPI application.

    Args:
        app: The FastAPI application
        request_schemas: Dictionary mapping endpoint paths to request schemas
        response_schemas: Dictionary mapping endpoint paths to response schemas
        max_request_size: Maximum allowed request size in bytes
        rate_limit: Maximum requests per rate_limit_window
        rate_limit_window: Time window for rate limiting in seconds
        skip_validation_paths: Set of paths to skip validation for
    """
    app.add_middleware(
        ValidationMiddleware,  # type: ignore[arg-type]
        request_schemas=request_schemas,
        response_schemas=response_schemas,
        max_request_size=max_request_size,
        rate_limit=rate_limit,
        rate_limit_window=rate_limit_window,
        skip_validation_paths=skip_validation_paths,
    )
    logger.info("Added validation middleware to FastAPI application")
