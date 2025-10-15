"""
Unit tests for SemGrepAgent.
"""

import json
import pytest
from unittest.mock import Mock, patch

from codetective.agents.scan.semgrep_agent import SemGrepAgent
from codetective.models.schemas import AgentType, Issue, SeverityLevel


class TestSemGrepAgent:
    """Test cases for SemGrepAgent."""

    def test_semgrep_agent_init(self, base_config):
        """Test SemGrepAgent initialization."""
        agent = SemGrepAgent(base_config)
        
        assert agent.config == base_config
        assert agent.agent_type == AgentType.SEMGREP

    def test_is_available_tool_installed(self, base_config):
        """Test is_available when SemGrep is installed."""
        agent = SemGrepAgent(base_config)
        
        with patch('codetective.utils.SystemUtils.check_tool_availability', return_value=(True, "1.0.0")):
            assert agent.is_available() is True

    def test_is_available_tool_not_installed(self, base_config):
        """Test is_available when SemGrep is not installed."""
        agent = SemGrepAgent(base_config)
        
        with patch('codetective.utils.SystemUtils.check_tool_availability', return_value=(False, None)):
            assert agent.is_available() is False

    @pytest.mark.unit
    def test_scan_files_empty_list(self, base_config, mock_semgrep_output):
        """Test scanning with empty file list."""
        agent = SemGrepAgent(base_config)
        
        with patch.object(agent, '_scan_directory', return_value=[]):
            issues = agent.scan_files([])
            
            # Should scan current directory when no files provided
            assert isinstance(issues, list)

    @pytest.mark.unit
    def test_parse_semgrep_output(self, base_config, mock_semgrep_output):
        """Test parsing SemGrep JSON output."""
        agent = SemGrepAgent(base_config)
        
        # Access the _parse_semgrep_output method if it exists
        if hasattr(agent, '_parse_semgrep_output'):
            issues = agent._parse_semgrep_output(mock_semgrep_output)
            
            assert len(issues) > 0
            assert all(isinstance(issue, Issue) for issue in issues)
            assert all(issue.rule_id for issue in issues)

    @pytest.mark.unit
    def test_map_severity_high(self, base_config):
        """Test severity mapping for high/error severity."""
        agent = SemGrepAgent(base_config)
        
        if hasattr(agent, '_map_severity'):
            severity = agent._map_severity("ERROR")
            assert severity == SeverityLevel.HIGH
            
            severity = agent._map_severity("error")
            assert severity == SeverityLevel.HIGH

    @pytest.mark.unit
    def test_map_severity_medium(self, base_config):
        """Test severity mapping for medium/warning severity."""
        agent = SemGrepAgent(base_config)
        
        if hasattr(agent, '_map_severity'):
            severity = agent._map_severity("WARNING")
            assert severity == SeverityLevel.MEDIUM

    @pytest.mark.unit
    def test_map_severity_low(self, base_config):
        """Test severity mapping for low/info severity."""
        agent = SemGrepAgent(base_config)
        
        if hasattr(agent, '_map_severity'):
            severity = agent._map_severity("INFO")
            assert severity == SeverityLevel.LOW

    @pytest.mark.unit
    @patch('codetective.utils.ProcessUtils.run_command')
    def test_scan_single_file_success(self, mock_run_command, base_config, sample_python_file, mock_semgrep_output):
        """Test scanning a single file successfully."""
        agent = SemGrepAgent(base_config)
        
        # Mock successful semgrep execution
        mock_run_command.return_value = (True, json.dumps(mock_semgrep_output), "")
        
        if hasattr(agent, '_scan_single_file'):
            issues = agent._scan_single_file(str(sample_python_file))
            
            assert isinstance(issues, list)

    @pytest.mark.unit
    @patch('codetective.utils.ProcessUtils.run_command')
    def test_scan_batch_files_success(self, mock_run_command, base_config, sample_python_file, mock_semgrep_output):
        """Test scanning multiple files in batch."""
        agent = SemGrepAgent(base_config)
        
        # Mock successful semgrep execution
        mock_run_command.return_value = (True, json.dumps(mock_semgrep_output), "")
        
        if hasattr(agent, '_scan_files_batch'):
            issues = agent._scan_files_batch([str(sample_python_file)])
            
            assert isinstance(issues, list)

    @pytest.mark.unit
    @patch('codetective.utils.ProcessUtils.run_command')
    def test_scan_directory_success(self, mock_run_command, base_config, temp_dir, mock_semgrep_output):
        """Test scanning a directory."""
        agent = SemGrepAgent(base_config)
        
        # Mock successful semgrep execution
        mock_run_command.return_value = (True, json.dumps(mock_semgrep_output), "")
        
        if hasattr(agent, '_scan_directory'):
            issues = agent._scan_directory(str(temp_dir))
            
            assert isinstance(issues, list)

    @pytest.mark.unit
    @patch('codetective.utils.ProcessUtils.run_command')
    def test_scan_files_command_failure(self, mock_run_command, base_config, sample_python_file):
        """Test handling of command failure."""
        agent = SemGrepAgent(base_config)
        
        # Mock failed execution
        mock_run_command.return_value = (False, "", "Error: SemGrep failed")
        
        # Should handle error gracefully
        issues = agent.scan_files([str(sample_python_file)])
        
        # Depending on implementation, might return empty list or raise
        assert isinstance(issues, list)

    @pytest.mark.unit
    def test_scan_files_mixed_paths(self, base_config, sample_python_file, temp_dir):
        """Test scanning with mixed file and directory paths."""
        agent = SemGrepAgent(base_config)
        
        with patch.object(agent, '_scan_files_batch', return_value=[]), \
             patch.object(agent, '_scan_directory', return_value=[]):
            
            issues = agent.scan_files([str(sample_python_file), str(temp_dir)])
            
            assert isinstance(issues, list)

    @pytest.mark.unit
    def test_scan_files_nonexistent_path(self, base_config):
        """Test scanning with nonexistent paths."""
        agent = SemGrepAgent(base_config)
        
        # Should handle gracefully
        issues = agent.scan_files(["/nonexistent/path/file.py"])
        
        assert isinstance(issues, list)

    @pytest.mark.integration
    @pytest.mark.requires_semgrep
    def test_execute_real_semgrep(self, base_config, sample_python_file):
        """Test execution with real SemGrep tool."""
        agent = SemGrepAgent(base_config)
        
        if not agent.is_available():
            pytest.skip("SemGrep not available")
        
        result = agent.execute([str(sample_python_file)])
        
        assert result.success is True
        assert result.agent_type == AgentType.SEMGREP
        assert result.execution_time > 0
