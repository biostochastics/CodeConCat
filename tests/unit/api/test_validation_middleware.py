"""Unit tests for the API validation middleware."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from codeconcat.api.validation_middleware import ValidationMiddleware, add_validation_middleware
from codeconcat.errors import ValidationError


# Test fixtures
@pytest.fixture
def app():
    """Create a test FastAPI application."""
    app = FastAPI()

    @app.post("/api/test")
    async def test_endpoint(request: Request):
        body = await request.json()
        return {"status": "success", "data": body}

    @app.get("/api/no-validation")
    async def no_validation():
        return {"status": "success", "data": "No validation needed"}

    @app.post("/api/error")
    async def error_endpoint(request: Request):
        raise ValidationError("Test validation error", field="test_field")

    @app.post("/api/exception")
    async def exception_endpoint(request: Request):
        raise Exception("Test exception")

    return app


@pytest.fixture
def client(app):
    """Create a test client for the application."""
    # Add validation middleware with test schemas
    add_validation_middleware(
        app,
        request_schemas={
            "/api/test": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0},
                },
            }
        },
        max_request_size=1000,  # Small size for testing
        rate_limit=5,  # Low limit for testing
        rate_limit_window=60,
    )

    return TestClient(app)


class TestValidationMiddleware:
    """Test suite for the ValidationMiddleware class."""

    def test_valid_request(self, client):
        """Test a valid request that passes validation."""
        response = client.post("/api/test", json={"name": "Test User", "age": 30})

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_invalid_request(self, client):
        """Test an invalid request that fails validation."""
        response = client.post("/api/test", json={"age": 30})  # Missing required 'name' field

        assert response.status_code == 400
        assert response.json()["status"] == "error"
        assert "validation error" in response.json()["error"].lower()

    def test_no_validation_endpoint(self, client):
        """Test an endpoint with no validation schema."""
        response = client.get("/api/no-validation")

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_validation_error_in_endpoint(self, client):
        """Test an endpoint that raises a ValidationError."""
        response = client.post("/api/error", json={"test": "data"})

        assert response.status_code == 400
        assert response.json()["status"] == "error"
        assert response.json()["field"] == "test_field"

    def test_exception_in_endpoint(self, client):
        """Test an endpoint that raises an unhandled Exception."""
        response = client.post("/api/exception", json={"test": "data"})

        assert response.status_code == 500
        assert response.json()["status"] == "error"
        assert "test exception" in response.json()["detail"].lower()

    def test_request_size_limit(self, client):
        """Test the request size limit."""
        # Create a large payload that exceeds the 1000-byte limit
        large_data = {"name": "Test", "data": "X" * 1000}

        response = client.post("/api/test", json=large_data, headers={"Content-Length": "1100"})

        assert response.status_code == 413
        assert response.json()["status"] == "error"
        assert "request size exceeds" in response.json()["detail"].lower()

    def test_rate_limit(self, client):
        """Test the rate limiting functionality."""
        # Make requests up to the limit
        for _ in range(5):
            client.post("/api/test", json={"name": "Test"})

        # The next request should be rate limited
        response = client.post("/api/test", json={"name": "Test"})

        assert response.status_code == 429
        assert response.json()["status"] == "error"
        assert "rate limit" in response.json()["detail"].lower()

    def test_skip_validation_path(self):
        """Test skipping validation for certain paths."""
        app = FastAPI()
        middleware = ValidationMiddleware(
            app,
            request_schemas={"/api/test": {}},
            skip_validation_paths={"/api/docs", "/skip-this"},
        )

        # Create a mock request for a path that should skip validation
        mock_request = MagicMock()
        mock_request.url.path = "/skip-this"
        mock_request.client.host = "127.0.0.1"

        # Create a mock call_next function
        mock_call_next = AsyncMock()
        mock_response = MagicMock()
        mock_call_next.return_value = mock_response

        # Call the dispatch method
        import asyncio

        response = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

        # Verify that validation was skipped
        assert response == mock_response
        mock_call_next.assert_called_once_with(mock_request)

    def test_schema_path_matching(self):
        """Test matching a schema to a path with parameters."""
        app = FastAPI()
        middleware = ValidationMiddleware(
            app,
            request_schemas={
                "/api/items/{id}": {"type": "object"},
                "/api/users/{id}/posts": {"type": "object"},
            },
        )

        # Test exact match
        schema1 = middleware._get_schema_for_path("/api/items/{id}", middleware.request_schemas)
        assert schema1 == {"type": "object"}

        # Test parameter match
        schema2 = middleware._get_schema_for_path(
            "/api/users/123/posts", middleware.request_schemas
        )
        assert schema2 == {"type": "object"}
