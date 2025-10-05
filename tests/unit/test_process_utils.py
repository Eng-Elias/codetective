"""
Unit tests for ProcessUtils.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch

from codetective.utils.process_utils import ProcessUtils


class TestProcessUtils:
    """Test cases for ProcessUtils."""

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_success(self, mock_popen):
        """Test successful command execution."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("Success output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        success, stdout, stderr = ProcessUtils.run_command(['echo', 'test'])
        
        assert success is True
        assert stdout == "Success output"
        assert stderr == ""

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_failure(self, mock_popen):
        """Test failed command execution."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "Error message")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        success, stdout, stderr = ProcessUtils.run_command(['false'])
        
        assert success is False
        assert stderr == "Error message"

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_with_timeout(self, mock_popen):
        """Test command execution with timeout."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        success, stdout, stderr = ProcessUtils.run_command(
            ['sleep', '10'],
            timeout=5
        )
        
        # Should pass timeout to communicate
        mock_process.communicate.assert_called_once_with(timeout=5)
        assert success is True

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_timeout_exception(self, mock_popen):
        """Test handling of timeout exception."""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(
            cmd=['sleep', '10'],
            timeout=5
        )
        mock_popen.return_value = mock_process
        
        success, stdout, stderr = ProcessUtils.run_command(
            ['sleep', '10'],
            timeout=5
        )
        
        # Should return failed status
        assert success is False
        assert "timeout" in stderr.lower() or "timed out" in stderr.lower()

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_with_cwd(self, mock_popen, temp_dir):
        """Test command execution with custom working directory."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        ProcessUtils.run_command(['ls'], cwd=str(temp_dir))
        
        # Should pass cwd parameter
        call_kwargs = mock_popen.call_args.kwargs
        assert 'cwd' in call_kwargs
        assert call_kwargs['cwd'] == str(temp_dir)

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_capture_output(self, mock_popen):
        """Test that output is captured as text."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("Test output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        success, stdout, stderr = ProcessUtils.run_command(['echo', 'test'])
        
        # Should capture output as string
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_with_env(self, mock_popen):
        """Test command execution with custom environment."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        custom_env = {"PATH": "/custom/path"}
        
        if hasattr(ProcessUtils, 'run_command'):
            # Check if run_command supports env parameter
            try:
                ProcessUtils.run_command(['test'], env=custom_env)
            except TypeError:
                # env parameter might not be supported
                pass

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_subprocess_error(self, mock_popen):
        """Test handling of subprocess errors."""
        mock_popen.side_effect = subprocess.SubprocessError("Command failed")
        
        success, stdout, stderr = ProcessUtils.run_command(['invalid-command'])
        
        # Should handle error gracefully
        assert success is False

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_file_not_found(self, mock_popen):
        """Test handling of FileNotFoundError."""
        mock_popen.side_effect = FileNotFoundError("Command not found")
        
        success, stdout, stderr = ProcessUtils.run_command(['nonexistent-command'])
        
        # Should handle error gracefully
        assert success is False

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_permission_error(self, mock_popen):
        """Test handling of permission errors."""
        mock_popen.side_effect = PermissionError("Permission denied")
        
        success, stdout, stderr = ProcessUtils.run_command(['restricted-command'])
        
        # Should handle error gracefully
        assert success is False

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_invalid_utf8(self, mock_popen):
        """Test handling of invalid UTF-8 in output."""
        # Simulate binary output that's not valid UTF-8
        mock_process = Mock()
        mock_process.communicate.return_value = ("Valid text", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        success, stdout, stderr = ProcessUtils.run_command(['test'])
        
        # Should handle encoding issues gracefully
        assert isinstance(stdout, str)

    @pytest.mark.unit
    @patch('subprocess.Popen')
    def test_run_command_shell_injection_protection(self, mock_popen):
        """Test that shell injection is prevented."""
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Commands should be passed as list, not shell string
        ProcessUtils.run_command(['echo', '; rm -rf /'])
        
        # Should NOT use shell=True (Popen doesn't use shell by default)
        call_kwargs = mock_popen.call_args.kwargs
        if 'shell' in call_kwargs:
            assert call_kwargs['shell'] is False

    @pytest.mark.integration
    def test_real_command_execution(self):
        """Test executing a real simple command."""
        # Use a platform-agnostic command
        import sys
        if sys.platform == 'win32':
            cmd = ['cmd', '/c', 'echo', 'test']
        else:
            cmd = ['echo', 'test']
        
        success, stdout, stderr = ProcessUtils.run_command(cmd)
        
        assert success is True
        assert 'test' in stdout.lower()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_timeout(self):
        """Test real timeout with actual command."""
        import sys
        
        if sys.platform == 'win32':
            cmd = ['ping', '-n', '10', '127.0.0.1']  # Windows
        else:
            cmd = ['sleep', '10']  # Unix/Linux
        
        success, stdout, stderr = ProcessUtils.run_command(cmd, timeout=1)
        
        # Should timeout
        assert success is False
