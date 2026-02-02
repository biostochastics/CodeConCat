"""
API command - Start the CodeConCat API server.
"""

import asyncio
from typing import Annotated

import typer
import uvicorn
from rich.panel import Panel

from ..utils import console, print_error, print_info

app = typer.Typer()


@app.command(name="start")
def start_server(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Host to bind the server to",
            envvar="CODECONCAT_HOST",
            rich_help_panel="Server Options",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="Port to bind the server to",
            envvar="CODECONCAT_PORT",
            min=1,
            max=65535,
            rich_help_panel="Server Options",
        ),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option(
            "--reload/--no-reload",
            "-r/-R",
            help="Enable auto-reload on code changes (development mode)",
            rich_help_panel="Development Options",
        ),
    ] = False,
    workers: Annotated[
        int,
        typer.Option(
            "--workers",
            "-w",
            help="Number of worker processes",
            min=1,
            max=16,
            rich_help_panel="Performance Options",
        ),
    ] = 1,
    log_level: Annotated[
        str,
        typer.Option(
            "--log-level",
            "-l",
            help="Logging level",
            rich_help_panel="Logging Options",
        ),
    ] = "info",
):
    """
    Start the CodeConCat API server.

    The API server provides a RESTful interface for processing code
    programmatically. It includes endpoints for processing files,
    managing configurations, and more.

    \b
    Examples:
      codeconcat api start                      # Start on localhost:8000
      codeconcat api start --host 0.0.0.0       # Listen on all interfaces
      codeconcat api start --reload              # Development mode with auto-reload
      codeconcat api start --workers 4          # Production with 4 workers
    """
    try:
        # Show startup message
        console.print(
            Panel(
                f"[bold cyan]Starting CodeConCat API Server[/bold cyan]\n\n"
                f"Host: [green]{host}[/green]\n"
                f"Port: [green]{port}[/green]\n"
                f"Workers: [green]{workers}[/green]\n"
                f"Reload: [green]{'Enabled' if reload else 'Disabled'}[/green]\n"
                f"Log Level: [green]{log_level}[/green]\n\n"
                f"[dim]API Documentation will be available at:[/dim]\n"
                f"  [cyan]http://{host}:{port}/docs[/cyan]",
                title="🚀 API Server",
                border_style="cyan",
            )
        )

        # Import the FastAPI app
        from codeconcat.api.app import app as fastapi_app

        # Configure uvicorn
        config = uvicorn.Config(
            app=fastapi_app,
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,  # Reload mode doesn't support multiple workers
            log_level=log_level.lower(),
            access_log=True,
        )

        # Create and run server
        server = uvicorn.Server(config)

        print_info(f"Server starting at http://{host}:{port}")
        print_info("Press CTRL+C to stop")

        # Run the server
        asyncio.run(server.serve())

    except KeyboardInterrupt:
        print_info("Server shutdown requested")
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        raise typer.Exit(1) from e


@app.command(name="info")
def server_info():
    """
    Display API server information and available endpoints.
    """
    console.print(
        Panel(
            "[bold cyan]CodeConCat API Server Information[/bold cyan]\n\n"
            "[yellow]Available Endpoints:[/yellow]\n"
            "  • POST /api/concat - Process code and generate output\n"
            "  • POST /api/upload - Upload and process archive (zip/tar)\n"
            "  • GET /api/ping - Health check endpoint\n"
            "  • GET /api/config/presets - Available presets\n"
            "  • GET /api/config/formats - Supported formats\n"
            "  • GET /api/config/languages - Supported languages\n"
            "  • GET /api/config/defaults - Default configuration\n"
            "  • GET /docs - Interactive API documentation (Swagger UI)\n"
            "  • GET /redoc - Alternative API documentation (ReDoc)\n\n"
            "[yellow]Environment Variables:[/yellow]\n"
            "  • CODECONCAT_HOST - Server host (default: 127.0.0.1)\n"
            "  • CODECONCAT_PORT - Server port (default: 8000)\n"
            "  • CODECONCAT_ALLOW_LOCAL_PATH - Enable local paths in API (dev only)\n\n"
            "[yellow]Example Usage:[/yellow]\n"
            "  curl -X POST http://localhost:8000/api/concat \\\n"
            "    -H 'Content-Type: application/json' \\\n"
            '    -d \'{"source_url": "owner/repo", "format": "json"}\'',
            title="📡 API Information",
            border_style="cyan",
        )
    )
