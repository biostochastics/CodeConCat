"""
Command-line interface for the CodeConCat API server.

This module provides a command-line entry point for starting the
CodeConCat API server with configurable options.
"""

import argparse
import logging
from codeconcat.api.app import start_server
from codeconcat import version

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the API server CLI."""
    parser = argparse.ArgumentParser(description="Start the CodeConCat API server")

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Logging level (default: info)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit",
    )

    return parser


def cli_entry_point() -> int:
    """
    Command-line entry point for the API server.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = build_parser()
    args = parser.parse_args()

    # Show version and exit if requested
    if args.version:
        try:
            version_str = version.__version__
        except AttributeError as e:
            version_str = "unknown"
            logger.debug(f"Could not retrieve version: {e}. Using default value.")
        print(f"CodeConCat API v{version_str}")
        return 0

    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        try:
            version_str = version.__version__
        except AttributeError as e:
            version_str = "unknown"
            logger.debug(f"Could not retrieve version: {e}. Using default value.")
        logger.info(f"Starting CodeConCat API server v{version_str}")
        logger.info(f"Binding to {args.host}:{args.port}")

        # Start the server
        start_server(host=args.host, port=args.port, log_level=args.log_level, reload=args.reload)
        return 0
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        return 1


if __name__ == "__main__":
    cli_entry_point()
