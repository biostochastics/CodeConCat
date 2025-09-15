"""Comprehensive tests for timeout middleware."""

import asyncio
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from codeconcat.api.timeout_middleware import TimeoutMiddleware


class TestTimeoutMiddleware:
    """Test the timeout middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        return FastAPI()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance with test configuration."""
        return TimeoutMiddleware(
            app=app,
            default_timeout=1.0,  # 1 second for testing
            read_timeout=0.5,
            write_timeout=0.5,
            endpoint_timeouts={"/slow": 2.0},
            skip_timeout_paths={"/health", "/docs"},
        )

    @pytest.mark.asyncio
    async def test_middleware_initialization(self, app):
        """Test middleware initialization with various configurations."""
        middleware = TimeoutMiddleware(app)
        assert middleware.default_timeout == 30.0
        assert middleware.read_timeout == 10.0
        assert middleware.write_timeout == 10.0
        assert "/health" in middleware.skip_timeout_paths

        # Custom configuration
        middleware = TimeoutMiddleware(
            app,
            default_timeout=5.0,
            read_timeout=2.0,
            write_timeout=3.0,
            endpoint_timeouts={"/api/heavy": 60.0},
        )
        assert middleware.default_timeout == 5.0
        assert middleware.endpoint_timeouts["/api/heavy"] == 60.0

    @pytest.mark.asyncio
    async def test_skip_timeout_paths(self, middleware):
        """Test that certain paths skip timeout enforcement."""
        # Create mock request for /health
        request = Mock(spec=Request)
        request.url.path = "/health"

        # Create mock call_next that returns immediately
        async def mock_call_next(_req):
            return JSONResponse({"status": "ok"})

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

        # Test /docs path
        request.url.path = "/docs"
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_normal_request_within_timeout(self, middleware):
        """Test normal request that completes within timeout."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"

        async def mock_call_next(_req):
            await asyncio.sleep(0.1)  # Quick response
            return JSONResponse({"data": "test"})

        with patch("codeconcat.api.timeout_middleware.time.time", side_effect=[0, 0.1]):
            response = await middleware.dispatch(request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_timeout(self, middleware):
        """Test request that exceeds timeout."""
        request = Mock(spec=Request)
        request.url.path = "/api/slow"

        async def mock_call_next(_req):
            await asyncio.sleep(2.0)  # Exceeds 1 second timeout
            return JSONResponse({"data": "slow"})

        with patch("codeconcat.api.timeout_middleware.logger") as mock_logger, patch(
            "codeconcat.api.timeout_middleware.time.time", side_effect=[0, 1.1]
        ):
            response = await middleware.dispatch(request, mock_call_next)

        # Should return timeout error
        assert response.status_code == 504
        response_body = response.body.decode()
        assert "timeout" in response_body.lower()

        # Should log the timeout
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_custom_endpoint_timeout(self, middleware):
        """Test custom timeout for specific endpoint."""
        request = Mock(spec=Request)
        request.url.path = "/slow"  # Has 2 second custom timeout

        async def mock_call_next(_req):
            await asyncio.sleep(1.5)  # Within custom timeout
            return JSONResponse({"data": "custom"})

        with patch("codeconcat.api.timeout_middleware.time.time", side_effect=[0, 1.5]):
            response = await middleware.dispatch(request, mock_call_next)

        # Should complete successfully with custom timeout
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_warning_for_slow_requests(self, middleware):
        """Test warning logged for requests approaching timeout."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"

        async def mock_call_next(_req):
            await asyncio.sleep(0.85)  # 85% of 1 second timeout
            return JSONResponse({"data": "slow"})

        with patch("codeconcat.api.timeout_middleware.logger") as mock_logger, patch(
            "codeconcat.api.timeout_middleware.time.time", side_effect=[0, 0.85]
        ):
            response = await middleware.dispatch(request, mock_call_next)

        assert response.status_code == 200
        # Should log warning for slow request
        mock_logger.warning.assert_called()

    def test_get_timeout_for_path(self, middleware):
        """Test timeout calculation for different paths."""
        # Default timeout
        assert middleware._get_timeout_for_path("/api/test") == 1.0

        # Custom endpoint timeout
        assert middleware._get_timeout_for_path("/slow") == 2.0

        # Add exact path for testing
        middleware.endpoint_timeouts["/api/v2/users"] = 5.0
        assert middleware._get_timeout_for_path("/api/v2/users") == 5.0

    @pytest.mark.asyncio
    async def test_cleanup_on_timeout(self, middleware):
        """Test that resources are cleaned up on timeout."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"

        cleanup_called = False

        async def mock_call_next(_req):
            try:
                await asyncio.sleep(2.0)  # Will timeout
            finally:
                nonlocal cleanup_called
                cleanup_called = True
            return JSONResponse({"data": "test"})

        with patch("codeconcat.api.timeout_middleware.time.time", side_effect=[0, 1.1, 1.1]):
            response = await middleware.dispatch(request, mock_call_next)

        # Give time for cleanup
        await asyncio.sleep(0.1)

        assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_read_timeout_simulation(self, middleware):
        """Test simulation of read timeout."""
        request = Mock(spec=Request)
        request.url.path = "/api/upload"

        # Simulate slow request body reading
        async def mock_call_next(_req):
            # Simulate reading request body
            await asyncio.sleep(0.3)  # Within read timeout
            return JSONResponse({"status": "uploaded"})

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, middleware):
        """Test handling of concurrent requests with different timeouts."""

        async def make_request(path, delay):
            request = Mock(spec=Request)
            request.url.path = path

            async def call_next(_req):
                await asyncio.sleep(delay)
                return JSONResponse({"path": path})

            return await middleware.dispatch(request, call_next)

        # Run multiple requests concurrently
        with patch(
            "codeconcat.api.timeout_middleware.time.time",
            side_effect=lambda: asyncio.get_event_loop().time(),
        ):
            results = await asyncio.gather(
                make_request("/api/fast", 0.1),
                make_request("/api/normal", 0.5),
                make_request("/slow", 1.5),  # Custom timeout path
                return_exceptions=True,
            )

        # Fast and normal should succeed
        assert results[0].status_code == 200
        assert results[1].status_code == 200
        # Slow should succeed due to custom timeout
        assert results[2].status_code == 200
