"""
System utilities for Codetective - handle system information and tool availability.
"""

import subprocess
import sys
from typing import Optional, Tuple

import requests

from codetective import __version__
from codetective.models.schemas import SystemInfo


class RequiredTools:
    OLLAMA = "ollama"
    SEMGREP = "semgrep"
    TRIVY = "trivy"


class SystemUtils:
    """Utility class for system-related operations."""

    @staticmethod
    def check_tool_availability(tool_name: str) -> Tuple[bool, Optional[str]]:
        """Check if a tool is available in PATH and get its version."""
        if tool_name == RequiredTools.OLLAMA:
            return SystemUtils._check_ollama_availability()
        else:
            return SystemUtils._check_standard_tool_availability(tool_name)

    @staticmethod
    def _check_ollama_availability() -> Tuple[bool, Optional[str]]:
        """Check Ollama availability using multiple methods."""
        # Method 1: Try HTTP API
        api_result = SystemUtils._check_ollama_api()
        if api_result[0]:
            return api_result

        # Method 2: Try command line version
        cli_result = SystemUtils._check_ollama_cli_version()
        if cli_result[0]:
            return cli_result

        # Method 3: Check if ollama process is running
        process_result = SystemUtils._check_ollama_process()
        if process_result[0]:
            return process_result

        return False, None

    @staticmethod
    def _check_ollama_api(ollama_base_url: str = "http://localhost:11434") -> Tuple[bool, Optional[str]]:
        """Check Ollama via HTTP API."""
        try:
            response = requests.get(f"{ollama_base_url}/api/version", timeout=3)
            if response.status_code == 200:
                version_info = response.json()
                return True, version_info.get("version", "running")
        except requests.RequestException:
            pass
        return False, None

    @staticmethod
    def _check_ollama_cli_version() -> Tuple[bool, Optional[str]]:
        """Check Ollama via command line version."""
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_line = result.stdout.strip().split("\n")[0]
                return True, version_line
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        return False, None

    @staticmethod
    def _check_ollama_process() -> Tuple[bool, Optional[str]]:
        """Check if Ollama process is running."""
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True, "available"
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        return False, None

    @staticmethod
    def _check_standard_tool_availability(tool_name: str) -> Tuple[bool, Optional[str]]:
        """Check standard tool availability via subprocess."""
        try:
            result = subprocess.run([tool_name, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract version from output (first line usually contains version)
                version_line = result.stdout.strip().split("\n")[0]
                return True, version_line
            return False, None
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False, None

    @staticmethod
    def get_system_info() -> SystemInfo:
        """Get comprehensive system information."""
        semgrep_available, semgrep_version = SystemUtils.check_tool_availability(RequiredTools.SEMGREP)
        trivy_available, trivy_version = SystemUtils.check_tool_availability(RequiredTools.TRIVY)
        ollama_available, ollama_version = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)

        return SystemInfo(
            semgrep_available=semgrep_available,
            trivy_available=trivy_available,
            ollama_available=ollama_available,
            semgrep_version=semgrep_version,
            trivy_version=trivy_version,
            ollama_version=ollama_version,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            codetective_version=__version__,
        )
