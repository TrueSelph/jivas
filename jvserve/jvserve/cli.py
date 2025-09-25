"""Module for registering CLI plugins for jaseci."""

import asyncio
import json
import logging
import mimetypes
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime
from pickle import load
from typing import AsyncIterator, Optional

import aiohttp
import psutil
import pymongo
import requests
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from jac_cloud.core.context import JaseciContext
from jac_cloud.jaseci.datasources.redis import Redis
from jac_cloud.jaseci.main import FastAPI as JaseciFastAPI  # type: ignore
from jac_cloud.jaseci.utils import logger
from jac_cloud.jaseci.utils.logger import Level
from jac_cloud.plugin.jaseci import NodeAnchor
from jaclang import JacMachine as Jac
from jaclang.cli.cmdreg import cmd_registry
from jaclang.runtimelib.machine import hookimpl
from typing_extensions import Any
from watchfiles import Change, watch

from jvserve.lib.agent_interface import AgentInterface
from jvserve.lib.agent_pulse import AgentPulse
from jvserve.lib.file_interface import (
    DEFAULT_FILES_ROOT,
    FILE_INTERFACE,
    file_interface,
)
from jvserve.lib.jvlogger import JVLogger

redis = Redis().get_rd()

load_dotenv(".env")
# quiet the jac_cloud logger down to errors only
logger.setLevel(Level.ERROR.value)
# Set up logging for JIVAS
JVLogger.setup_logging(level="INFO")
jvlogger = logging.getLogger(__name__)

# Global for MongoDB collection with thread-safe initialization
url_proxy_collection = None
collection_init_lock = asyncio.Lock()

# Global state for watcher control
watcher_enabled = True


# taken from kubernetes HOSTNAME for replicated deployment
SERVER_ID = os.environ.get("HOSTNAME", "unknown_server")


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


async def serve_proxied_file(file_path: str) -> FileResponse | StreamingResponse:
    """Serve a proxied file from a remote or local URL (non-blocking)"""

    if FILE_INTERFACE == "local":
        root_path = os.environ.get("JIVAS_FILES_ROOT_PATH", DEFAULT_FILES_ROOT)
        full_path = os.path.join(root_path, file_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(full_path)

    file_url = file_interface.get_file_url(file_path)
    if file_url and ("localhost" in file_url or "127.0.0.1" in file_url):
        # prevent recursive calls when env vars are not detected
        raise HTTPException(status_code=500, detail="Environment not set up correctly")

    if not file_url:
        raise HTTPException(status_code=404, detail="File not found")

    file_extension = os.path.splitext(file_path)[1].lower()

    # List of extensions to serve directly
    direct_serve_extensions = [
        ".pdf",
        ".html",
        ".txt",
        ".js",
        ".css",
        ".json",
        ".xml",
        ".svg",
        ".csv",
        ".ico",
    ]

    if file_extension in direct_serve_extensions:
        # Run the blocking request in a thread pool
        file_response = await asyncio.to_thread(requests.get, file_url)
        file_response.raise_for_status()  # Raise HTTPError for bad responses (4XX or 5XX)

        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        return StreamingResponse(iter([file_response.content]), media_type=mime_type)

    # For streaming responses, we need to handle it differently
    # Get the response headers first to check if request is valid
    file_response = await asyncio.to_thread(requests.get, file_url, stream=True)
    file_response.raise_for_status()

    # Create an async generator that reads chunks in thread pool
    async def generate_chunks() -> Any:
        try:
            # Read chunks in thread pool to avoid blocking
            for chunk in file_response.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive chunks
                    yield chunk
        finally:
            # Ensure the response is closed
            file_response.close()

    return StreamingResponse(
        generate_chunks(),
        media_type="application/octet-stream",
    )


def start_file_watcher(
    watchdir: str, filename: str, host: str, port: int
) -> threading.Thread:
    """Start the file watcher in a separate thread"""

    def watcher_loop() -> None:
        """File watcher loop that runs in a separate thread"""
        global watcher_enabled

        jvlogger.info(f"Starting file watcher for directory: {watchdir}")

        try:
            for changes in watch(watchdir):
                if watcher_enabled:
                    log_reload(changes)
                    # Kill the current server process and restart
                    reload_jivas()
                else:
                    time.sleep(1)  # Prevent busy loop when disabled
        except KeyboardInterrupt:
            jvlogger.info("File watcher stopped")
        except Exception as e:
            jvlogger.error(f"File watcher error: {e}")

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
                            jvlogger.info("Server is ready, initializing agents...")
                            await agent_interface.init_agents()
                            return
            except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                jvlogger.warning(
                    f"Server not ready yet (attempt {attempt + 1} / {max_retries}): {e}"
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff

        jvlogger.error(
            "Server did not become ready in time. Agent initialization skipped."
        )

    # set up lifespan events
    async def on_startup() -> None:
        jvlogger.info("JIVAS is starting up...")
        # Start initialization in background without blocking
        asyncio.create_task(post_startup())

    async def on_shutdown() -> None:
        jvlogger.info("JIVAS is shutting down...")
        AgentPulse.stop()

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

    @app.get("/action/webhook/{namespace}/{action}/{walker}/{agent_id}/{key}")
    async def webhook_exec_get(
        namespace: str,
        action: str,
        walker: str,
        agent_id: str,
        key: str,
        request: Request,
    ) -> JSONResponse:
        return await agent_interface.webhook_exec(
            namespace=namespace,
            action=action,
            walker=walker,
            agent_id=agent_id,
            key=key,
            request=request,
        )

    @app.post("/action/webhook/{namespace}/{action}/{walker}/{agent_id}/{key}")
    async def webhook_exec_post(
        namespace: str,
        action: str,
        walker: str,
        agent_id: str,
        key: str,
        request: Request,
    ) -> JSONResponse:
        return await agent_interface.webhook_exec(
            namespace=namespace,
            action=action,
            walker=walker,
            agent_id=agent_id,
            key=key,
            request=request,
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
            jvlogger.error(f"Proxy error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    ctx.close()

    # Start file watcher BEFORE starting the server (in development mode)
    is_development = os.environ.get("JIVAS_ENVIRONMENT") == "development"
    if is_development:
        watchdir = os.path.join(
            os.path.abspath(os.path.dirname(filename)), "actions", ""
        )
        jvlogger.info("Development mode: Starting file watcher")
        start_file_watcher(watchdir, filename, host, port)

    threading.Thread(target=redis_listener, daemon=True).start()

    # Run the app
    JaseciFastAPI.start(host=host, port=port)


def log_reload(changes: set[tuple[Change, str]]) -> None:
    """Log changes and check watcher state."""
    global watcher_enabled

    jvlogger.warning(f"Watcher is: {watcher_enabled}")

    # Check if watcher is disabled
    if not watcher_enabled:
        return

    num_of_changes = len(changes)
    jvlogger.warning(
        f'Detected {num_of_changes} change{"s" if num_of_changes > 1 else ""}'
    )
    for change in changes:
        jvlogger.warning(f"{change[1]} ({change[0].name})")
    jvlogger.warning("Reloading ...")


def disable_watcher() -> dict:
    """Disable the watcher from auto-reloading"""
    if os.environ.get("JIVAS_ENVIRONMENT") == "development":
        global watcher_enabled
        watcher_enabled = False
        return {"message": "Watcher disabled"}
    else:
        return {"message": "Watcher already disabled"}


def enable_watcher() -> dict:
    """Enable the watcher for auto-reloading"""
    if os.environ.get("JIVAS_ENVIRONMENT") == "development":
        global watcher_enabled
        watcher_enabled = True
        return {"message": "Watcher enabled"}
    else:
        return {"message": "Watcher already enabled"}


def reload_jivas() -> None:
    """Reload the server, handling virtual environments robustly."""
    try:
        # Use sys.executable to ensure correct Python interpreter (handles venv)
        current_process = psutil.Process(os.getpid())
        cmdline = current_process.cmdline()
        if cmdline:
            # Replace executable with sys.executable if different (for venv safety)
            exec_path = sys.executable
            if os.path.exists(exec_path):
                cmdline[0] = exec_path
                jvlogger.info(f"Restarting with command: {' '.join(cmdline)}")
                os.execvp(exec_path, cmdline)
            else:
                raise RuntimeError("sys.executable does not exist")
        else:
            raise RuntimeError("Invalid cmdline from psutil")
    except Exception as e:
        jvlogger.error(f"Failed to reload using psutil cmdline: {e}")
        # Fallback to sys.argv if psutil fails or cmdline is not usable
        reload_jivas_from_argv()


def reload_jivas_from_argv() -> None:
    """Reload using sys.argv (the original command line arguments)."""
    jvlogger.info("Reloading server using sys.argv...")
    jvlogger.info(f"Original command: {' '.join(sys.argv)}")

    # sys.argv[0] is the script name, rest are arguments
    os.execvp(sys.executable, [sys.executable] + sys.argv)


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


def handle_message(msg: str) -> None:
    """
    Handles incoming messages from the Redis channel 'jivas_actions'.
    Expects the message to be a JSON string with 'action' and 'initiator' fields.
    Only acts on 'reload_jivas' messages not sent by this pod.
    """
    try:
        data = json.loads(msg)
    except json.JSONDecodeError:
        print(f"Received invalid message: {msg}")
        return

    action = data.get("action")
    initiator = data.get("initiator")

    # Ignore messages sent by this pod
    if initiator == SERVER_ID:
        jvlogger.info("Skipping message from self")
        return

    if action == "reload_jivas":
        print(f"Received reload_jivas action from {initiator}, executing reload.")
        reload_jivas()
    else:
        print(f"Ignored action: {action} from {initiator}")


def redis_listener() -> None:
    """Listens to the Redis channel 'walker_install_action' and handles incoming messages."""
    pubsub = redis.pubsub()
    pubsub.subscribe("jivas_actions")
    jvlogger.info("Subscribed to channel: jivas_actions")

    for message in pubsub.listen():
        if message["type"] == "message":
            handle_message(message["data"])


def send_action_notification(action: str, extra_data: dict | None = None) -> None:
    """
    Sends a message to the Redis channel 'jivas_actions'.

    Args:
        action (str): the action name, e.g., 'reload_jivas'
        extra_data (dict): optional additional data to include in the message
    """
    payload = {
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
        "initiator": SERVER_ID,
    }

    if extra_data:
        payload.update(extra_data)

    # Publish the message
    redis.publish("jivas_actions", json.dumps(payload))
    jvlogger.info(f"Sent message: {payload}")
