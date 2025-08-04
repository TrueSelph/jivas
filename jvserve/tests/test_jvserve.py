"""Test case for the Jac CLI commands."""

import os
import signal
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
        self.kill_process_on_port(8000)

        # Create a temporary .jac file for testing
        with open(filename, "w") as f:
            f.write("with entry {print('Test Execution');}")

        # Launch `jvserve`
        self.server_process = subprocess.Popen(
            ["jac", "jvserve", filename, "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), "fixtures"),
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
            self.kill_process_on_port(8000)

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

    def tearDown(self) -> None:
        """Cleanup after each test."""
        self.stop_server()
        with suppress(FileNotFoundError):
            os.remove("test.jac")

    def kill_process_on_port(self, port: int = 8000) -> bool:
        """Kill any process running on the specified port."""
        try:
            # Find the PID of the process using the port
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"], capture_output=True, text=True
            )
            pids = result.stdout.strip().split("\n")

            if not pids or pids[0] == "":
                print(f"No process found running on port {port}.")
                return False

            # Kill each process found
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGKILL)  # Force kill
                        print(
                            f"Successfully killed process {pid} running on port {port}."
                        )
                    except ProcessLookupError:
                        print(f"Process {pid} not found (may have already exited).")
                    except PermissionError:
                        print(
                            f"Permission denied: Cannot kill process {pid}. Try running with sudo."
                        )
            return True
        except Exception as e:
            print(f"Error killing process on port {port}: {e}")
            return False


if __name__ == "__main__":
    unittest.main()
