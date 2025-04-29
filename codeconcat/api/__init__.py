"""
REST API module for CodeConCat.

This module provides a FastAPI-based REST API for CodeConCat,
allowing remote access to code aggregation and analysis functionality.
"""

from codeconcat.api.app import create_app, start_server

__all__ = ["create_app", "start_server"]
