"""Agent Interface class and methods for interaction with Jivas."""

import json
import logging
import os
import string
import traceback
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

import requests
from fastapi import File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from jvserve.lib.jac_interface import JacInterface


class AgentInterface:
    """Agent Interface for Jivas with proper concurrency handling."""

    _instance = None
    logger = logging.getLogger(__name__)

    def __init__(self, host: str = "localhost", port: int = 8000) -> None:
        """Initialize the AgentInterface with JacInterface."""
        self._jac = JacInterface(host, port)
        self._cipher_alphabet = self._generate_cipher_alphabet()

    @classmethod
    def get_instance(
        cls, host: str = "localhost", port: int = 8000
    ) -> "AgentInterface":
        """Get a singleton instance of AgentInterface."""
        if cls._instance is None:
            env_host = os.environ.get("JIVAS_HOST", "localhost")
            env_port = int(os.environ.get("JIVAS_PORT", "8000"))
            host = host or env_host
            port = port or env_port
            cls._instance = cls(host, port)
        return cls._instance

    @property
    def cipher_alphabet(self) -> Tuple[str, str]:
        """Get the cipher alphabet for webhook key encryption."""
        if not hasattr(self, "_cipher_alphabet"):
            self._cipher_alphabet = self._generate_cipher_alphabet()
        return self._cipher_alphabet

    async def action_webhook_exec(self, key: str, request: Request) -> Response:
        """Webhook execution optimized for concurrency"""
        if not key:
            return JSONResponse(status_code=400, content="Missing webhook key")

        # Get parameters
        params = dict(request.query_params) if request.query_params else {}

        # Process body based on content type
        if request.method == "POST":
            try:
                content_type = request.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    params = await request.json()
                elif "application/x-www-form-urlencoded" in content_type:
                    form_data = await request.form()
                    params = dict(form_data)
            except Exception as e:
                self.logger.warning(f"Parameter processing warning: {e}")

        # Decode key
        args = self.decrypt_webhook_key(key)
        if not args:
            return JSONResponse(status_code=400, content="Malformed webhook key")

        # Validate required parameters
        required_keys = ("agent_id", "module_root", "walker")
        if not all(k in args for k in required_keys):
            return JSONResponse(status_code=400, content="Invalid webhook parameters")

        agent_id = args["agent_id"]
        module_root = args["module_root"]
        walker = args["walker"]

        try:
            # Execute walker
            walker_obj = await self._jac.spawn_walker_async(
                walker_name=walker,
                module_name=f"{module_root}.{walker}",
                attributes={
                    "headers": dict(request.headers),
                    "agent_id": agent_id,
                    "params": params,
                    "reporting": False,
                },
            )

            if not walker_obj or not walker_obj.response:
                return Response(status_code=204)

            content = walker_obj.response
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    content = {"response": content}

            # Ensure proper Content-Length
            body = json.dumps(content).encode("utf-8")
            return Response(
                content=body,
                status_code=200,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
        except Exception as e:
            if "401" in str(e) or "authentication" in str(e).lower():
                self._jac.reset()
            self.logger.error(f"Webhook error: {e}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "details": str(e)},
            )

    def action_walker_exec(
        self,
        agent_id: Optional[str] = Form(None),  # noqa: B008
        module_root: Optional[str] = Form(None),  # noqa: B008
        walker: Optional[str] = Form(None),  # noqa: B008
        args: Optional[str] = Form(None),  # noqa: B008
        attachments: List[UploadFile] = File(default_factory=list),  # noqa: B008
    ) -> JSONResponse:
        """Synchronous walker execution"""
        if not all([agent_id, module_root, walker]):
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required parameters"},
            )

        try:
            attributes: Dict[str, Any] = {"agent_id": agent_id}

            # Parse additional arguments
            if args:
                try:
                    attributes.update(json.loads(args))
                except json.JSONDecodeError as e:
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"Invalid JSON in arguments: {e}"},
                    )

            # Process files
            if attachments:
                attributes["files"] = []
                for file in attachments:
                    try:
                        attributes["files"].append(
                            {
                                "name": file.filename,
                                "type": file.content_type,
                                "content": file.file.read(),
                            }
                        )
                    except Exception as e:
                        self.logger.error(f"File error: {file.filename}: {e}")

            # Execute walker
            walker_obj = self._jac.spawn_walker(
                walker_name=walker,
                module_name=f"{module_root}.{walker}",
                attributes=attributes,
            )

            if walker_obj and walker_obj.response:
                return walker_obj.response

            return JSONResponse(status_code=204, content=None)
        except Exception as e:
            self.logger.error(f"Action error: {e}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "details": str(e)},
            )

    async def init_agents(self) -> None:
        """Initialize agents - async compatible"""
        try:
            if not await self._jac.spawn_walker_async(
                walker_name="init_agents",
                module_name="jivas.agent.core.init_agents",
                attributes={"reporting": False},
            ):
                self.logger.error("Agent initialization failed")
        except Exception as e:
            self._jac.reset()
            self.logger.error(f"Init error: {e}\n{traceback.format_exc()}")

    def api_pulse(self, action_label: str, agent_id: str) -> dict:
        """Synchronous pulse API call"""
        if not self._jac.is_valid():
            self.logger.warning("Invalid API state for pulse")
            return {}

        # Clean parameters
        action_label = action_label.replace("action_label=", "")
        agent_id = agent_id.replace("agent_id=", "")

        endpoint = f"http://{self._jac.host}:{self._jac.port}/walker/pulse"
        headers = {"Authorization": f"Bearer {self._jac.token}"}
        payload = {"action_label": action_label, "agent_id": agent_id}

        try:
            response = requests.post(
                endpoint, json=payload, headers=headers, timeout=10
            )
            if response.status_code == 200:
                return response.json().get("reports", {})
            if response.status_code == 401:
                self._jac.reset()
        except Exception as e:
            self._jac.reset()
            self.logger.error(f"Pulse error: {e}\n{traceback.format_exc()}")

        return {}

    @staticmethod
    def _generate_cipher_alphabet() -> Tuple[str, str]:
        """Generate cipher alphabet"""
        secret_key = os.environ.get("JIVAS_WEBHOOK_SECRET_KEY", "ABCDEFGHIJK")
        secret_key = secret_key.lower() + secret_key.upper()
        seen = set()
        key_unique_list = []
        for c in secret_key:
            if c.isalpha() and c not in seen:
                seen.add(c)
                key_unique_list.append(c)
        key_unique = "".join(key_unique_list)
        remaining = "".join(
            c
            for c in string.ascii_lowercase + string.ascii_uppercase
            if c not in seen and c.isalpha()
        )
        return key_unique, remaining

    async def _finalize_interaction(
        self, interaction_node: Any, full_text: str, total_tokens: int
    ) -> None:
        """Finalize interaction in background"""
        try:
            interaction_node.set_text_message(message=full_text)
            interaction_node.add_tokens(total_tokens)

            await self._jac.spawn_walker_async(
                walker_name="update_interaction",
                module_name="jivas.agent.memory.update_interaction",
                attributes={"interaction_data": interaction_node.export()},
            )
        except Exception as e:
            self.logger.error(f"Finalize error: {e}")

    def encrypt_webhook_key(self, agent_id: str, module_root: str, walker: str) -> str:
        """Encrypt webhook key"""
        key_text = json.dumps(
            {"agent_id": agent_id, "module_root": module_root, "walker": walker},
            separators=(",", ":"),
        )
        table = str.maketrans(
            string.ascii_lowercase + string.ascii_uppercase,
            self.cipher_alphabet[0] + self.cipher_alphabet[1],
        )
        return quote(key_text.translate(table))

    def decrypt_webhook_key(self, key: str) -> Optional[dict]:
        """Decrypt webhook key"""
        table = str.maketrans(
            self.cipher_alphabet[0] + self.cipher_alphabet[1],
            string.ascii_lowercase + string.ascii_uppercase,
        )
        try:
            decoded = unquote(key).translate(table)
            return json.loads(decoded)
        except Exception as e:
            self.logger.error(f"Key error: {e}\n{traceback.format_exc()}")
            return None


# Module-level functions
def pulse_exec(action_label: str, agent_id: str) -> dict:
    """Execute pulse action synchronously"""
    return AgentInterface.get_instance().api_pulse(action_label, agent_id)


def encrypt_webhook_key_exec(agent_id: str, module_root: str, walker: str) -> str:
    """Encrypt webhook key synchronously"""
    return AgentInterface.get_instance().encrypt_webhook_key(
        agent_id, module_root, walker
    )
