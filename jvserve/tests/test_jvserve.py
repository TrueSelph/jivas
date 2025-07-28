"""Test case for the Jac CLI commands."""

import os
import subprocess
import unittest
from contextlib import suppress
from time import sleep, time
from typing import Optional

import httpx


class JVServeCliTest(unittest.TestCase):
    """Test the Jac CLI commands."""

    def setUp(self) -> None:
        """Setup the test environment."""
        self.host = "http://127.0.0.1:8000"
        self.server_process: Optional[subprocess.Popen] = None

    def run_jvserve(self, filename: str, max_wait: int = 90) -> None:
        """Run jvserve in a subprocess and wait until it's available."""
        # Ensure any process running on port 8000 is terminated
        subprocess.run(["fuser", "-k", "8000/tcp"], capture_output=True, text=True)

        # Create a temporary .jac file for testing
        with open(filename, "w") as f:
            f.write("with entry {print('Test Execution');}")

        # Launch `jvserve`
        self.server_process = subprocess.Popen(
            ["jac", "jvserve", filename, "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait until the server is ready (max 90s)
        try:
            url = f"{self.host}/docs"
            self.wait_for_server(url, max_wait)
        except TimeoutError:
            self.log_server_output()
            raise  # Re-raise the timeout error

    def stop_server(self) -> None:
        """Stop the running server."""
        if self.server_process:
            self.server_process.kill()

    def wait_for_server(self, url: str, max_wait: int = 90) -> None:
        """Wait for the server to be available, checking every second."""
        start_time = time()
        while time() - start_time < max_wait:
            with suppress(Exception):
                res = httpx.get(url, timeout=2)
                if res.status_code == 200:
                    return  # Server is ready
            sleep(1)
        raise TimeoutError(f"Server at {url} did not start within {max_wait} seconds.")

    def log_server_output(self) -> None:
        """Log the server's output to help debug failures."""
        if self.server_process:
            stdout, stderr = self.server_process.communicate(timeout=5)
            print("\n==== SERVER STDOUT ====\n", stdout)
            print("\n==== SERVER STDERR ====\n", stderr)

    def test_jvserve_runs(self) -> None:
        """Ensure `jac jvserve` runs successfully."""
        try:
            self.run_jvserve("test.jac")
            # Check if server started successfully
            res = httpx.get(f"{self.host}/docs")
            self.assertEqual(res.status_code, 200)
        finally:
            self.stop_server()

    def test_action_walker_requires_auth(self) -> None:
        """Ensure /action/walker requires authentication."""
        try:
            self.run_jvserve("test.jac")
            res = httpx.post(f"{self.host}/action/walker", json={})
            self.assertEqual(
                res.status_code, 403
            )  # Should be Not Authenticated / Forbidden
        finally:
            self.stop_server()

    def test_jvfileserve_runs(self) -> None:
        """Ensure `jac jvfileserve` runs successfully."""
        directory = "test_files"
        os.makedirs(directory, exist_ok=True)

        # Add file to the directory
        with open(f"{directory}/test.txt", "w") as f:
            f.write("Hello, World!")

        try:
            server_process = subprocess.Popen(
                ["jac", "jvfileserve", directory, "--port", "9000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for the file server to be ready
            self.wait_for_server("http://127.0.0.1:9000/files/test.txt")

            res = httpx.get("http://127.0.0.1:9000/files/test.txt")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.text, "Hello, World!")

        finally:
            server_process.kill()

            # Clean up the directory
            os.remove(f"{directory}/test.txt")
            os.rmdir(directory)

    def test_jvproxyserve_runs(self) -> None:
        """Ensure `jac jvproxyserve` runs successfully."""
        try:
            directory = "test_files"
            server_process = subprocess.Popen(
                ["jac", "jvproxyserve", directory, "--port", "9100"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for the proxy server to be ready
            self.wait_for_server("http://127.0.0.1:9100/docs")

            res = httpx.get("http://127.0.0.1:9100/docs")
            self.assertEqual(res.status_code, 200)

        finally:
            server_process.kill()

    def tearDown(self) -> None:
        """Cleanup after each test."""
        self.stop_server()
        with suppress(FileNotFoundError):
            os.remove("test.jac")


if __name__ == "__main__":
    unittest.main()
