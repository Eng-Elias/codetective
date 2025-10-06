"""
Unit tests for SystemUtils.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
import requests

from codetective.utils.system_utils import SystemUtils, RequiredTools
from codetective.models.schemas import SystemInfo


class TestRequiredTools:
    """Test cases for RequiredTools constants."""

    @pytest.mark.unit
    def test_required_tools_constants(self):
        """Test that required tool constants are defined."""
        assert RequiredTools.OLLAMA == "ollama"
        assert RequiredTools.SEMGREP == "semgrep"
        assert RequiredTools.TRIVY == "trivy"


class TestSystemUtils:
    """Test cases for SystemUtils."""

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils._check_standard_tool_availability')
    def test_check_tool_availability_standard_tool(self, mock_check):
        """Test checking standard tool availability."""
        mock_check.return_value = (True, "1.0.0")
        
        available, version = SystemUtils.check_tool_availability("semgrep")
        
        assert available is True
        assert version == "1.0.0"
        mock_check.assert_called_once_with("semgrep")

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_availability')
    def test_check_tool_availability_ollama(self, mock_check_ollama):
        """Test checking Ollama availability."""
        mock_check_ollama.return_value = (True, "0.1.0")
        
        available, version = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)
        
        assert available is True
        assert version == "0.1.0"
        mock_check_ollama.assert_called_once()

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_standard_tool_availability_success(self, mock_run):
        """Test successful standard tool check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="semgrep 1.0.0\nMore info",
            stderr=""
        )
        
        available, version = SystemUtils._check_standard_tool_availability("semgrep")
        
        assert available is True
        assert "1.0.0" in version
        mock_run.assert_called_once()

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_standard_tool_availability_not_found(self, mock_run):
        """Test standard tool not found."""
        mock_run.side_effect = FileNotFoundError()
        
        available, version = SystemUtils._check_standard_tool_availability("nonexistent")
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_standard_tool_availability_timeout(self, mock_run):
        """Test standard tool check timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["tool"], timeout=10)
        
        available, version = SystemUtils._check_standard_tool_availability("slow-tool")
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_standard_tool_availability_error(self, mock_run):
        """Test standard tool check with error return code."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error")
        
        available, version = SystemUtils._check_standard_tool_availability("error-tool")
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_api')
    def test_check_ollama_availability_via_api(self, mock_api):
        """Test Ollama availability via API."""
        mock_api.return_value = (True, "0.1.0")
        
        available, version = SystemUtils._check_ollama_availability()
        
        assert available is True
        assert version == "0.1.0"

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_process')
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_cli_version')
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_api')
    def test_check_ollama_availability_fallback_to_cli(
        self,
        mock_api,
        mock_cli,
        mock_process
    ):
        """Test Ollama availability falls back to CLI check."""
        mock_api.return_value = (False, None)
        mock_cli.return_value = (True, "ollama 0.1.0")
        
        available, version = SystemUtils._check_ollama_availability()
        
        assert available is True
        assert "0.1.0" in version
        mock_api.assert_called_once()
        mock_cli.assert_called_once()

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_process')
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_cli_version')
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_api')
    def test_check_ollama_availability_fallback_to_process(
        self,
        mock_api,
        mock_cli,
        mock_process
    ):
        """Test Ollama availability falls back to process check."""
        mock_api.return_value = (False, None)
        mock_cli.return_value = (False, None)
        mock_process.return_value = (True, "available")
        
        available, version = SystemUtils._check_ollama_availability()
        
        assert available is True
        assert version == "available"
        mock_process.assert_called_once()

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_process')
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_cli_version')
    @patch('codetective.utils.system_utils.SystemUtils._check_ollama_api')
    def test_check_ollama_availability_all_fail(
        self,
        mock_api,
        mock_cli,
        mock_process
    ):
        """Test Ollama availability when all checks fail."""
        mock_api.return_value = (False, None)
        mock_cli.return_value = (False, None)
        mock_process.return_value = (False, None)
        
        available, version = SystemUtils._check_ollama_availability()
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('requests.get')
    def test_check_ollama_api_success(self, mock_get):
        """Test successful Ollama API check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.1.5"}
        mock_get.return_value = mock_response
        
        available, version = SystemUtils._check_ollama_api()
        
        assert available is True
        assert version == "0.1.5"

    @pytest.mark.unit
    @patch('requests.get')
    def test_check_ollama_api_no_version(self, mock_get):
        """Test Ollama API check without version in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        available, version = SystemUtils._check_ollama_api()
        
        assert available is True
        assert version == "running"  # Default value

    @pytest.mark.unit
    @patch('requests.get')
    def test_check_ollama_api_connection_error(self, mock_get):
        """Test Ollama API check with connection error."""
        mock_get.side_effect = requests.ConnectionError()
        
        available, version = SystemUtils._check_ollama_api()
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('requests.get')
    def test_check_ollama_api_timeout(self, mock_get):
        """Test Ollama API check with timeout."""
        mock_get.side_effect = requests.Timeout()
        
        available, version = SystemUtils._check_ollama_api()
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('requests.get')
    def test_check_ollama_api_custom_url(self, mock_get):
        """Test Ollama API check with custom URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.1.0"}
        mock_get.return_value = mock_response
        
        available, version = SystemUtils._check_ollama_api("http://custom:8080")
        
        assert available is True
        mock_get.assert_called_once_with("http://custom:8080/api/version", timeout=3)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_ollama_cli_version_success(self, mock_run):
        """Test successful Ollama CLI version check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="ollama version 0.1.0\nMore info",
            stderr=""
        )
        
        available, version = SystemUtils._check_ollama_cli_version()
        
        assert available is True
        assert "0.1.0" in version

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_ollama_cli_version_not_found(self, mock_run):
        """Test Ollama CLI not found."""
        mock_run.side_effect = FileNotFoundError()
        
        available, version = SystemUtils._check_ollama_cli_version()
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_ollama_cli_version_timeout(self, mock_run):
        """Test Ollama CLI version check timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ollama"], timeout=5)
        
        available, version = SystemUtils._check_ollama_cli_version()
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_ollama_process_running(self, mock_run):
        """Test Ollama process check when running."""
        mock_run.return_value = Mock(returncode=0, stdout="models list", stderr="")
        
        available, version = SystemUtils._check_ollama_process()
        
        assert available is True
        assert version == "available"

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_ollama_process_not_running(self, mock_run):
        """Test Ollama process check when not running."""
        mock_run.side_effect = FileNotFoundError()
        
        available, version = SystemUtils._check_ollama_process()
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_check_ollama_process_error(self, mock_run):
        """Test Ollama process check with error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["ollama", "list"])
        
        available, version = SystemUtils._check_ollama_process()
        
        assert available is False
        assert version is None

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils.check_tool_availability')
    def test_get_system_info_all_available(self, mock_check):
        """Test getting system info when all tools are available."""
        # Mock all tools as available
        def mock_availability(tool):
            return (True, f"{tool} 1.0.0")
        
        mock_check.side_effect = mock_availability
        
        system_info = SystemUtils.get_system_info()
        
        assert isinstance(system_info, SystemInfo)
        assert system_info.semgrep_available is True
        assert system_info.trivy_available is True
        assert system_info.ollama_available is True
        assert "1.0.0" in system_info.semgrep_version
        assert system_info.python_version is not None
        assert system_info.codetective_version is not None

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils.check_tool_availability')
    def test_get_system_info_tools_unavailable(self, mock_check):
        """Test getting system info when tools are unavailable."""
        # Mock all tools as unavailable
        mock_check.return_value = (False, None)
        
        system_info = SystemUtils.get_system_info()
        
        assert isinstance(system_info, SystemInfo)
        assert system_info.semgrep_available is False
        assert system_info.trivy_available is False
        assert system_info.ollama_available is False
        assert system_info.semgrep_version is None
        assert system_info.trivy_version is None
        assert system_info.ollama_version is None

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils.check_tool_availability')
    def test_get_system_info_partial_availability(self, mock_check):
        """Test getting system info with partial tool availability."""
        def mock_availability(tool):
            if tool == RequiredTools.SEMGREP:
                return (True, "semgrep 1.0.0")
            return (False, None)
        
        mock_check.side_effect = mock_availability
        
        system_info = SystemUtils.get_system_info()
        
        assert system_info.semgrep_available is True
        assert system_info.trivy_available is False
        assert system_info.ollama_available is False

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils.check_tool_availability')
    def test_get_system_info_python_version(self, mock_check):
        """Test that system info includes Python version."""
        mock_check.return_value = (False, None)
        
        system_info = SystemUtils.get_system_info()
        
        # Python version should be in format "3.X.X"
        assert system_info.python_version is not None
        assert "." in system_info.python_version

    @pytest.mark.unit
    @patch('codetective.utils.system_utils.SystemUtils.check_tool_availability')
    def test_get_system_info_codetective_version(self, mock_check):
        """Test that system info includes Codetective version."""
        mock_check.return_value = (False, None)
        
        system_info = SystemUtils.get_system_info()
        
        assert system_info.codetective_version is not None
        assert isinstance(system_info.codetective_version, str)
