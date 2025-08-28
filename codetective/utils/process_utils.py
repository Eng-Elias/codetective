"""
Process utilities for Codetective - handle command execution and process management.
"""

import os
import signal
import subprocess
from typing import List, Tuple


class ProcessUtils:
    """Utility class for process-related operations."""

    @staticmethod
    def run_command(command: List[str], cwd: str = None, timeout: int = 900) -> Tuple[bool, str, str]:
        """Run a command and return success status, stdout, and stderr."""
        process = None
        try:
            # Start the process
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",  # Replace invalid characters instead of failing
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )

            # Wait for completion with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode == 0, stdout, stderr

        except subprocess.TimeoutExpired:
            # Force terminate the process on timeout
            if process:
                try:
                    if os.name == "nt":  # Windows
                        process.terminate()
                    else:  # Unix/Linux
                        process.send_signal(signal.SIGTERM)
                    process.wait(timeout=5)  # Give it 5 seconds to terminate gracefully
                except:
                    if os.name == "nt":
                        process.kill()
                    else:
                        process.send_signal(signal.SIGKILL)
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            if process:
                try:
                    process.terminate()
                except:
                    pass
            return False, "", str(e)
