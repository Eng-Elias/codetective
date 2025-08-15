"""
System utilities for Codetective - handle system information and tool availability.
"""

import sys
import subprocess
from typing import Tuple, Optional
import requests
from codetective.models.schemas import SystemInfo
from codetective import __version__


class SystemUtils:
    """Utility class for system-related operations."""
    
    @staticmethod
    def check_tool_availability(tool_name: str) -> Tuple[bool, Optional[str]]:
        """Check if a tool is available in PATH and get its version."""
        try:
            if tool_name == "ollama":
                # Check Ollama via multiple methods
                # Method 1: Try HTTP API
                try:
                    response = requests.get("http://localhost:11434/api/version", timeout=3)
                    if response.status_code == 200:
                        version_info = response.json()
                        return True, version_info.get("version", "running")
                except requests.RequestException:
                    pass
                
                # Method 2: Try command line
                try:
                    result = subprocess.run(["ollama", "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version_line = result.stdout.strip().split('\n')[0]
                        return True, version_line
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    pass
                
                # Method 3: Check if ollama process is running
                try:
                    result = subprocess.run(["ollama", "list"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return True, "available"
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    pass
                
                return False, None
            else:
                # Check other tools via subprocess
                result = subprocess.run([tool_name, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Extract version from output (first line usually contains version)
                    version_line = result.stdout.strip().split('\n')[0]
                    return True, version_line
                return False, None
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, 
                requests.RequestException, FileNotFoundError):
            return False, None

    @staticmethod
    def get_system_info() -> SystemInfo:
        """Get comprehensive system information."""
        semgrep_available, semgrep_version = SystemUtils.check_tool_availability("semgrep")
        trivy_available, trivy_version = SystemUtils.check_tool_availability("trivy")
        ollama_available, ollama_version = SystemUtils.check_tool_availability("ollama")
        
        return SystemInfo(
            semgrep_available=semgrep_available,
            trivy_available=trivy_available,
            ollama_available=ollama_available,
            semgrep_version=semgrep_version,
            trivy_version=trivy_version,
            ollama_version=ollama_version,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            codetective_version=__version__
        )
