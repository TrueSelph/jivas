"""Command group for deploying and interfacing with the Jivas Manager."""

from pathlib import Path
import click
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from uvicorn import run
from jvmanager.group import jvmanager


@jvmanager.command()
@click.option("--port", default=8990, help="Port for the manager to launch on.")
@click.option("--host", default="0.0.0.0", help="Host for the manager to launch on.")
def launch(port: int, host: str) -> None:
    """Launch the Jivas Manager on the specified port."""
    click.echo(f"Launching Jivas Manager on port {port}...")
    app = FastAPI(title="Jivas Studio API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    client_dir = Path(__file__).resolve().parent.parent.joinpath("manager", "client")

    app.mount("/assets", StaticFiles(directory=client_dir / "assets"), name="assets")
    app.mount("/dist", StaticFiles(directory=client_dir / "dist"), name="dist")

    @app.get("/favicon.ico")
    async def favicon():
        return FileResponse(client_dir / "favicon.ico")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA for all routes."""

        requested_file = client_dir / full_path

        if requested_file.exists() and requested_file.is_file():
            return FileResponse(requested_file)

        index_file = client_dir / "index.html"
        return FileResponse(index_file)

    run(app, host=host, port=port)
