"""JacInterface: A connection and context state provider for Jac Runtime."""

import asyncio
import logging
import os
import threading
import time
import traceback
from typing import Optional, Tuple

import requests
from fastapi import Request
from jac_cloud.core.archetype import (  # type: ignore
    NodeAnchor,
    WalkerArchetype,
)
from jac_cloud.core.context import (
    JASECI_CONTEXT,
    JaseciContext,
)
from jac_cloud.plugin.jaseci import JacPlugin
from jaclang.runtimelib.machine import JacMachine


class JacInterface:
    """Thread-safe connection and context state provider for Jac Runtime with auto-authentication."""

    def __init__(self, host: str = "localhost", port: int = 8000) -> None:
        """Initialize JacInterface with host and port."""
        self.host = host
        self.port = port
        self.root_id = ""
        self.token = ""
        self.expiration = 0.0
        self._lock = threading.RLock()  # Thread-safe lock
        self.logger = logging.getLogger(__name__)

    def update(self, root_id: str, token: str, expiration: float) -> None:
        """Thread-safe state update"""
        with self._lock:
            self.root_id = root_id
            self.token = token
            self.expiration = expiration

    def reset(self) -> None:
        """Thread-safe state reset"""
        with self._lock:
            self.root_id = ""
            self.token = ""
            self.expiration = 0.0

    def is_valid(self) -> bool:
        """Thread-safe validity check"""
        with self._lock:
            return bool(
                self.token and self.expiration and self.expiration > time.time()
            )

    def get_state(self) -> Tuple[str, str, Optional[float]]:
        """Get current state with auto-authentication"""
        if not self.is_valid():
            self._authenticate()
        with self._lock:
            return (self.root_id, self.token, self.expiration)

    def get_context(self, request: Request | None = None) -> Optional[JaseciContext]:
        """Get Jaseci context with proper thread safety."""

        state = self.get_state()
        if not state or not self.is_valid():
            self.logger.error("Failed to get valid state for Jaseci context")
            return None

        try:
            root_id = state[0]
            entry_node = NodeAnchor.ref(f"n:root:{root_id}")  # type: ignore
            if not entry_node:
                self.logger.error("Failed to resolve entry node from root_id")
                return None

            ctx = JaseciContext.create(request, entry_node)
            if not ctx:
                self.logger.error("Failed to create JaseciContext with entry node")
                return None

            ctx.system_root = entry_node
            ctx.root_state = entry_node

            # Clean up any existing context before setting new one
            existing_ctx = JASECI_CONTEXT.get(None)
            if existing_ctx:
                try:
                    existing_ctx.close()
                except Exception as e:
                    self.logger.warning(f"Error while closing existing context: {e}")

            JASECI_CONTEXT.set(ctx)
            return ctx

        except Exception as e:
            self.logger.error(
                f"Failed to create JaseciContext: {e}\n{traceback.format_exc()}"
            )
            return None

    def spawn_walker(
        self,
        walker_name: str | None,
        module_name: str,
        attributes: dict = {},  # noqa: B006
        request: Request | None = None,  # noqa: B006
    ) -> Optional[WalkerArchetype]:
        """Spawn walker with proper context handling and thread safety"""

        if not all([walker_name, module_name]):
            self.logger.error("Missing required parameters for spawning walker")
            return None

        ctx = self.get_context(request)
        if not ctx:
            return None

        try:
            if module_name not in JacMachine.list_modules():
                self.logger.error(f"Module {module_name} not loaded")
                return None

            entry_node = ctx.entry_node.archetype

            return JacPlugin.spawn(
                JacMachine.spawn_walker(walker_name, attributes, module_name),
                entry_node,
            )
        except Exception as e:
            self.logger.error(f"Error spawning walker: {e}\n{traceback.format_exc()}")
            return None
        finally:
            if ctx:
                ctx.close()
                if JASECI_CONTEXT.get(None) == ctx:
                    JASECI_CONTEXT.set(None)

    def _authenticate(self) -> None:
        """Thread-safe authentication with retry logic and improved error handling"""
        user = os.environ.get("JIVAS_USER")
        password = os.environ.get("JIVAS_PASSWORD")
        if not user or not password:
            self.logger.error("Missing JIVAS_USER or JIVAS_PASSWORD")
            return

        login_url = f"http://{self.host}:{self.port}/user/login"
        register_url = f"http://{self.host}:{self.port}/user/register"

        with self._lock:
            try:
                # Try login first
                response = requests.post(
                    login_url, json={"email": user, "password": password}, timeout=15
                )
                self.logger.info(f"Login response status: {response.status_code}")
                if response.status_code == 200:
                    self._process_auth_response(response.json())
                    return

                # Register if login fails
                reg_response = requests.post(
                    register_url, json={"email": user, "password": password}, timeout=15
                )
                self.logger.info(
                    f"Register response status: {reg_response.status_code}"
                )
                if reg_response.status_code == 201:
                    # Retry login after registration
                    login_response = requests.post(
                        login_url,
                        json={"email": user, "password": password},
                        timeout=15,
                    )
                    self.logger.info(
                        f"Retry login response status: {login_response.status_code}"
                    )
                    if login_response.status_code == 200:
                        self._process_auth_response(login_response.json())
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error during authentication: {e}")
            except Exception as e:
                self.logger.error(
                    f"Authentication failed: {e}\n{traceback.format_exc()}"
                )
                self.reset()

    def _process_auth_response(self, response_data: dict) -> None:
        """Process authentication response and update state"""
        user_data = response_data.get("user", {})
        root_id = user_data.get("root_id", "")
        token = response_data.get("token", "")
        expiration = user_data.get("expiration")

        if not all([root_id, token, expiration]):
            self.logger.error("Invalid authentication response")
            return

        self.update(root_id, token, expiration)

    # Async versions of methods
    async def _authenticate_async(self) -> None:
        """Asynchronous wrapper for authentication"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._authenticate)

    async def spawn_walker_async(
        self,
        walker_name: str,
        module_name: str,
        attributes: dict,
        request: Request | None = None,
    ) -> Optional[WalkerArchetype]:
        """Asynchronous wrapper for walker spawning"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.spawn_walker, walker_name, module_name, attributes, request
        )
