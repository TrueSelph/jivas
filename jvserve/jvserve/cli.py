"""Module for registering CLI plugins for jaseci."""

import asyncio
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pickle import load
from typing import AsyncIterator, Optional

import aiohttp
import psutil
import pymongo
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from jac_cloud.core.context import JaseciContext
from jac_cloud.jaseci.main import FastAPI as JaseciFastAPI  # type: ignore
from jac_cloud.plugin.jaseci import NodeAnchor
from jaclang import JacMachine as Jac
from jaclang.cli.cmdreg import cmd_registry
from jaclang.runtimelib.machine import hookimpl
from watchfiles import Change, watch

from jvserve.lib.agent_interface import AgentInterface
from jvserve.lib.file_interface import (
    DEFAULT_FILES_ROOT,
    FILE_INTERFACE,
    file_interface,
)
from jvserve.lib.jvlogger import JVLogger

# quiet the jac_cloud logger down to errors only
# jac cloud dumps payload details to console which makes it hard to debug in JIVAS
os.environ["LOGGER_LEVEL"] = "ERROR"
load_dotenv(".env")
# Set up logging
JVLogger.setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# Global for MongoDB collection with thread-safe initialization
url_proxy_collection = None
collection_init_lock = asyncio.Lock()

# Global state for watcher control
WATCHER_STATE_FILE = ".jvserve_watcher_state"
watcher_enabled = True


async def get_url_proxy_collection() -> pymongo.collection.Collection:
    """Thread-safe initialization of MongoDB collection"""
    global url_proxy_collection
    if url_proxy_collection is None:
        async with collection_init_lock:
            if url_proxy_collection is None:  # Double-check locking
                loop = asyncio.get_running_loop()
                with ThreadPoolExecutor() as pool:
                    url_proxy_collection = await loop.run_in_executor(
                        pool,
                        lambda: NodeAnchor.Collection.get_collection("url_proxies"),
                    )
    return url_proxy_collection


async def serve_proxied_file(
    file_path: str,
) -> FileResponse | StreamingResponse | Response:
    """Serve a proxied file from a remote or local URL (async version)"""
    if FILE_INTERFACE == "local":
        root_path = os.environ.get("JIVAS_FILES_ROOT_PATH", DEFAULT_FILES_ROOT)
        full_path = os.path.join(root_path, file_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(full_path)

    file_url = file_interface.get_file_url(file_path)

    # Security check to prevent recursive calls
    if file_url and ("localhost" in file_url or "127.0.0.1" in file_url):
        raise HTTPException(
            status_code=500, detail="Environment misconfiguration detected"
        )

    if not file_url:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                response.raise_for_status()

                return StreamingResponse(
                    response.content.iter_chunked(8192),
                    media_type=response.headers.get(
                        "Content-Type", "application/octet-stream"
                    ),
                )
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=502, detail=f"File fetch error: {str(e)}")


def start_file_watcher(
    watchdir: str, filename: str, host: str, port: int
) -> threading.Thread:
    """Start the file watcher in a separate thread"""

    def watcher_loop() -> None:
        """File watcher loop that runs in a separate thread"""
        global watcher_enabled

        logger.info(f"Starting file watcher for directory: {watchdir}")

        try:
            for changes in watch(watchdir):
                if watcher_enabled:
                    log_reload(changes)
                    # Kill the current server process and restart
                    reload_server()
                else:
                    logger.info("Watcher disabled, ignoring changes")
                    time.sleep(1)  # Prevent busy loop when disabled
        except KeyboardInterrupt:
            logger.info("File watcher stopped")
        except Exception as e:
            logger.error(f"File watcher error: {e}")

    # Start watcher in daemon thread so it doesn't prevent program exit
    watcher_thread = threading.Thread(target=watcher_loop, daemon=True)
    watcher_thread.start()
    return watcher_thread


def run_jivas(filename: str, host: str = "localhost", port: int = 8000) -> None:
    """Starts JIVAS server with integrated file services"""

    # Create agent interface instance with configuration
    agent_interface = AgentInterface.get_instance(host=host, port=port)

    base, mod = os.path.split(filename)
    base = base if base else "./"
    mod = mod[:-4]

    JaseciFastAPI.enable()

    ctx = JaseciContext.create(None)
    if filename.endswith(".jac"):
        Jac.jac_import(target=mod, base_path=base, override_name="__main__")
    elif filename.endswith(".jir"):
        with open(filename, "rb") as f:
            Jac.attach_program(load(f))
            Jac.jac_import(target=mod, base_path=base, override_name="__main__")
    else:
        raise ValueError("Not a valid file!\nOnly supports `.jac` and `.jir`")

    # Define post-startup function to run AFTER server is ready
    async def post_startup() -> None:
        """Wait for server to be ready before initializing agents"""
        health_url = f"http://{host}:{port}/healthz"
        max_retries = 10
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(health_url, timeout=1) as response:
                        if response.status == 200:
                            logger.info("Server is ready, initializing agents...")
                            await agent_interface.init_agents()
                            return
            except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                logger.warning(
                    f"Server not ready yet (attempt {attempt + 1} / {max_retries}): {e}"
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff

        logger.error(
            "Server did not become ready in time. Agent initialization skipped."
        )

    # set up lifespan events
    async def on_startup() -> None:
        logger.info("JIVAS is starting up...")
        # Start initialization in background without blocking
        asyncio.create_task(post_startup())

    async def on_shutdown() -> None:
        logger.info("JIVAS is shutting down...")

    app = JaseciFastAPI.get()
    app_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan_wrapper(app: FastAPI) -> AsyncIterator[Optional[str]]:
        await on_startup()
        async with app_lifespan(app) as maybe_state:
            yield maybe_state
        await on_shutdown()

    app.router.lifespan_context = lifespan_wrapper

    # Add CORS middleware to main app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure the local file directory exists if that's the interface
    if FILE_INTERFACE == "local":
        directory = os.environ.get("JIVAS_FILES_ROOT_PATH", DEFAULT_FILES_ROOT)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    # Setup file serving endpoint for both local and S3
    @app.get("/files/{file_path:path}", response_model=None)
    async def serve_file(
        file_path: str,
    ) -> FileResponse | StreamingResponse | Response:
        # The serve_proxied_file function already handles both local and S3 cases
        return await serve_proxied_file(file_path)

    # Setup URL proxy endpoint
    @app.get("/f/{file_id:path}", response_model=None)
    async def get_proxied_file(
        file_id: str,
    ) -> FileResponse | StreamingResponse | Response:
        params = file_id.split("/")
        object_id = params[0]

        try:
            # Get MongoDB collection (thread-safe initialization)
            collection = await get_url_proxy_collection()

            # Run blocking MongoDB operation in thread pool
            loop = asyncio.get_running_loop()
            file_details = await loop.run_in_executor(
                None, lambda: collection.find_one({"_id": ObjectId(object_id)})
            )

            descriptor_path = os.environ.get("JIVAS_DESCRIPTOR_ROOT_PATH")

            if file_details:
                if descriptor_path and descriptor_path in file_details["path"]:
                    return Response(status_code=403)
                return await serve_proxied_file(file_details["path"])

            raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            logger.error(f"Proxy error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    ctx.close()

    # Start file watcher BEFORE starting the server (in development mode)
    is_development = os.environ.get("JIVAS_ENVIRONMENT") == "development"
    if is_development:
        watchdir = os.path.join(
            os.path.abspath(os.path.dirname(filename)), "actions", ""
        )
        logger.info("Development mode: Starting file watcher")
        enable_watcher()
        start_file_watcher(watchdir, filename, host, port)

    # Run the app
    JaseciFastAPI.start(host=host, port=port)


def log_reload(changes: set[tuple[Change, str]]) -> None:
    """Log changes and check watcher state."""
    global watcher_enabled

    logger.warning(f"Watcher is: {watcher_enabled}")

    # Check if watcher is disabled
    if not watcher_enabled:
        logger.warning("Watcher is disabled. Ignoring changes.")
        return

    num_of_changes = len(changes)
    logger.warning(
        f'Detected {num_of_changes} change{"s" if num_of_changes > 1 else ""}'
    )
    for change in changes:
        logger.warning(f"{change[1]} ({change[0].name})")
    logger.warning("Reloading ...")


class JacCmd:
    """Jac CLI."""

    @staticmethod
    @hookimpl
    def create_cmd() -> None:
        """Create Jac CLI cmds."""

        @cmd_registry.register
        def jvserve(filename: str, host: str = "localhost", port: int = 8000) -> None:
            """Launch unified JIVAS server with file services"""
            run_jivas(filename, host, port)


def disable_watcher() -> dict:
    """Disable the watcher from auto-reloading"""
    if os.environ.get("JIVAS_ENVIRONMENT") == "development":
        global watcher_enabled
        watcher_enabled = False
        with open(WATCHER_STATE_FILE, "w") as f:
            f.write("disabled")
        return {"message": "Watcher disabled"}
    else:
        return {"message": "Watcher already disabled"}


def enable_watcher() -> dict:
    """Enable the watcher for auto-reloading"""
    if os.environ.get("JIVAS_ENVIRONMENT") == "development":
        global watcher_enabled
        watcher_enabled = True
        with open(WATCHER_STATE_FILE, "w") as f:
            f.write("enabled")
        return {"message": "Watcher enabled"}
    else:
        return {"message": "Watcher already enabled"}


def reload_server() -> None:
    """Reload the server using the exact command that started it."""
    try:
        # Get the command used to start the sever
        current_process = psutil.Process(os.getpid())
        cmdline = current_process.cmdline()

        logger.info(f"Restarting with command: {' '.join(cmdline)}")

        # Replace current process with the same command
        os.execvp(cmdline[0], cmdline)

    except Exception as e:
        logger.error(f"Failed to get process command line: {e}")
        # Fallback to sys.argv
        reload_server_from_argv()
    finally:
        is_development = os.environ.get("JIVAS_ENVIRONMENT") == "development"

        if is_development:
            enable_watcher()


def reload_server_from_argv() -> None:
    """Reload using sys.argv (the original command line arguments)."""
    logger.info("Reloading server using sys.argv...")
    logger.info(f"Original command: {' '.join(sys.argv)}")

    # sys.argv[0] is the script name, rest are arguments
    os.execvp(sys.executable, [sys.executable] + sys.argv)
