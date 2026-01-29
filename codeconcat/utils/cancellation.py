"""Cancellation support for graceful Ctrl+C handling.

Provides a CancellationToken that can be checked by long-running operations
to enable cooperative cancellation, plus signal handler setup for CLI usage.
"""

import contextlib
import signal
import sys
import threading
import time
from collections.abc import Callable
from typing import Literal, cast


class CancellationToken:
    """Thread-safe cancellation token for cooperative task cancellation.

    Usage:
        token = CancellationToken()

        # In worker code:
        for item in items:
            if token.is_cancelled():
                break
            process(item)

        # Or raise an exception:
        token.raise_if_cancelled()
    """

    def __init__(self) -> None:
        self._event = threading.Event()
        self._cancel_time: float | None = None
        self._lock = threading.Lock()

    def cancel(self) -> None:
        """Signal cancellation. Thread-safe and signal-safe."""
        # Set time before event to avoid race in time_since_cancel()
        # This is safe even without lock since _cancel_time is write-once
        if not self._event.is_set():
            self._cancel_time = time.monotonic()
            self._event.set()

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested. Thread-safe."""
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        """Raise CancelledException if cancellation was requested."""
        if self.is_cancelled():
            raise CancelledException("Operation cancelled by user")

    def reset(self) -> None:
        """Reset the token for reuse. Thread-safe."""
        with self._lock:
            self._event.clear()
            self._cancel_time = None

    def time_since_cancel(self) -> float | None:
        """Return seconds since cancel() was called, or None if not cancelled.

        Note: Lock-free for signal handler safety. Uses Event check first
        to ensure _cancel_time is set before reading it.
        """
        if not self._event.is_set():
            return None
        ct = self._cancel_time
        return None if ct is None else (time.monotonic() - ct)

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for cancellation. Returns True if cancelled, False if timeout."""
        return self._event.wait(timeout=timeout)


class CancelledException(Exception):
    """Raised when an operation is cancelled via CancellationToken."""

    pass


# Global singleton for CLI usage
_global_token: CancellationToken | None = None
_token_lock = threading.Lock()


def get_cancellation_token() -> CancellationToken:
    """Get or create the global cancellation token."""
    global _global_token
    with _token_lock:
        if _global_token is None:
            _global_token = CancellationToken()
        return _global_token


def reset_cancellation_token() -> None:
    """Reset the global cancellation token (useful for testing)."""
    global _global_token
    with _token_lock:
        if _global_token is not None:
            _global_token.reset()


class SignalHandler:
    """SIGINT handler with double-press force quit support.

    First Ctrl+C: Sets cancellation token, prints message
    Second Ctrl+C within timeout: Force exits immediately
    """

    FORCE_QUIT_TIMEOUT = 2.0  # seconds

    def __init__(
        self,
        token: CancellationToken | None = None,
        on_cancel: Callable[[], None] | None = None,
        on_force_quit: Callable[[], None] | None = None,
        quiet: bool = False,
    ) -> None:
        """Initialize signal handler.

        Args:
            token: CancellationToken to set on Ctrl+C (uses global if None)
            on_cancel: Optional callback on first Ctrl+C
            on_force_quit: Optional callback on force quit (before exit)
            quiet: If True, suppress cancellation messages
        """
        self.token = token or get_cancellation_token()
        self.on_cancel = on_cancel
        self.on_force_quit = on_force_quit
        self.quiet = quiet
        self._original_handler: signal.Handlers | int | None = None
        self._installed = False

    def _handler(self, _signum: int, _frame) -> None:  # noqa: ARG002
        """Handle SIGINT signal."""
        time_since = self.token.time_since_cancel()

        if time_since is not None and time_since < self.FORCE_QUIT_TIMEOUT:
            # Second Ctrl+C within timeout - force quit
            if not self.quiet:
                print("\nForce quitting...", file=sys.stderr, flush=True)
            if self.on_force_quit:
                with contextlib.suppress(Exception):
                    self.on_force_quit()
            sys.exit(130)
        else:
            # First Ctrl+C - graceful cancellation
            self.token.cancel()
            if not self.quiet:
                print(
                    "\nCancelling gracefully... (press Ctrl+C again to force quit)",
                    file=sys.stderr,
                    flush=True,
                )
            if self.on_cancel:
                with contextlib.suppress(Exception):
                    self.on_cancel()

    def install(self) -> "SignalHandler":
        """Install the signal handler. Returns self for chaining.

        Note: signal.signal() can only be called from the main thread.
        Silently skips installation if called from a non-main thread.
        """
        if not self._installed:
            if threading.current_thread() is not threading.main_thread():
                return self
            self._original_handler = cast(
                signal.Handlers | int | None, signal.signal(signal.SIGINT, self._handler)
            )
            self._installed = True
        return self

    def uninstall(self) -> None:
        """Restore the original signal handler."""
        if self._installed and self._original_handler is not None:
            signal.signal(signal.SIGINT, self._original_handler)
            self._installed = False
            self._original_handler = None

    def __enter__(self) -> "SignalHandler":
        """Context manager entry - installs handler."""
        return self.install()

    def __exit__(self, exc_type, exc_val, exc_tb) -> Literal[False]:
        """Context manager exit - restores original handler."""
        self.uninstall()
        return False  # Don't suppress exceptions


def setup_signal_handler(
    token: CancellationToken | None = None,
    on_cancel: Callable[[], None] | None = None,
    on_force_quit: Callable[[], None] | None = None,
    quiet: bool = False,
) -> SignalHandler:
    """Convenience function to create and install a signal handler.

    Args:
        token: CancellationToken to set on Ctrl+C (uses global if None)
        on_cancel: Optional callback on first Ctrl+C
        on_force_quit: Optional callback on force quit (before exit)
        quiet: If True, suppress cancellation messages

    Returns:
        Installed SignalHandler instance

    Example:
        handler = setup_signal_handler()
        try:
            # Long-running operation
            token = get_cancellation_token()
            while not token.is_cancelled():
                do_work()
        finally:
            handler.uninstall()
    """
    return SignalHandler(
        token=token,
        on_cancel=on_cancel,
        on_force_quit=on_force_quit,
        quiet=quiet,
    ).install()
