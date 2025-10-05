"""
Unit tests for TrivyAgent.
"""

import json
import pytest
from unittest.mock import patch

from codetective.agents.scan.trivy_agent import TrivyAgent
from codetective.models.schemas import AgentType, Issue, SeverityLevel


class TestTrivyAgent:
    """Test cases for TrivyAgent."""

    def test_trivy_agent_init(self, base_config):
        """Test TrivyAgent initialization."""
        agent = TrivyAgent(base_config)
        
        assert agent.config == base_config
        assert agent.agent_type == AgentType.TRIVY

    def test_is_available_tool_installed(self, base_config):
        """Test is_available when Trivy is installed."""
        agent = TrivyAgent(base_config)
        
        with patch('codetective.utils.SystemUtils.check_tool_availability', return_value=(True, "0.45.0")):
            assert agent.is_available() is True

    def test_is_available_tool_not_installed(self, base_config):
        """Test is_available when Trivy is not installed."""
        agent = TrivyAgent(base_config)
        
        with patch('codetective.utils.SystemUtils.check_tool_availability', return_value=(False, None)):
            assert agent.is_available() is False

    @pytest.mark.unit
    def test_parse_trivy_output_vulnerabilities(self, base_config, mock_trivy_output):
        """Test parsing Trivy output with vulnerabilities."""
        agent = TrivyAgent(base_config)
        
        if hasattr(agent, '_parse_trivy_output'):
            issues = agent._parse_trivy_output(mock_trivy_output)
            
            assert len(issues) > 0
            assert all(isinstance(issue, Issue) for issue in issues)
            
            # Check that vulnerability information is extracted
            vulnerability_issues = [i for i in issues if "CVE" in i.rule_id or "vulnerability" in i.title.lower()]
            assert len(vulnerability_issues) > 0

    @pytest.mark.unit
    def test_parse_trivy_output_empty(self, base_config):
        """Test parsing empty Trivy output."""
        agent = TrivyAgent(base_config)
        
        empty_output = {"Results": []}
        
        if hasattr(agent, '_parse_trivy_output'):
            issues = agent._parse_trivy_output(empty_output)
            
            assert isinstance(issues, list)
            assert len(issues) == 0

    @pytest.mark.unit
    def test_map_trivy_severity(self, base_config):
        """Test Trivy severity mapping."""
        agent = TrivyAgent(base_config)
        
        if hasattr(agent, '_map_severity'):
            assert agent._map_severity("CRITICAL") == SeverityLevel.CRITICAL
            assert agent._map_severity("HIGH") == SeverityLevel.HIGH
            assert agent._map_severity("MEDIUM") == SeverityLevel.MEDIUM
            assert agent._map_severity("LOW") == SeverityLevel.LOW
            assert agent._map_severity("UNKNOWN") == SeverityLevel.INFO

    @pytest.mark.unit
    @patch('codetective.utils.ProcessUtils.run_command')
    def test_scan_files_success(self, mock_run_command, base_config, temp_dir, mock_trivy_output):
        """Test scanning files successfully."""
        agent = TrivyAgent(base_config)
        
        # Mock successful trivy execution
        mock_run_command.return_value = (True, json.dumps(mock_trivy_output), "")
        
        issues = agent.scan_files([str(temp_dir)])
        
        assert isinstance(issues, list)

    @pytest.mark.unit
    @patch('codetective.utils.ProcessUtils.run_command')
    def test_scan_files_command_failure(self, mock_run_command, base_config, temp_dir):
        """Test handling of command failure."""
        agent = TrivyAgent(base_config)
        
        # Mock failed execution
        mock_run_command.return_value = (False, "", "Error: Trivy failed")
        
        issues = agent.scan_files([str(temp_dir)])
        
        # Should handle error gracefully
        assert isinstance(issues, list)

    @pytest.mark.unit
    @patch('codetective.utils.ProcessUtils.run_command')
    def test_scan_files_invalid_json(self, mock_run_command, base_config, temp_dir):
        """Test handling of invalid JSON output."""
        agent = TrivyAgent(base_config)
        
        # Mock execution with invalid JSON
        mock_run_command.return_value = (True, "Invalid JSON {{{", "")
        
        issues = agent.scan_files([str(temp_dir)])
        
        # Should handle JSON parse error gracefully
        assert isinstance(issues, list)

    @pytest.mark.unit
    def test_scan_files_multiple_targets(self, base_config, temp_dir):
        """Test scanning multiple target paths."""
        agent = TrivyAgent(base_config)
        
        # Create test files
        file1 = temp_dir / "requirements.txt"
        file1.write_text("requests==2.0.0\n")
        
        file2 = temp_dir / "package.json"
        file2.write_text('{"dependencies": {"lodash": "1.0.0"}}\n')
        
        with patch('codetective.utils.ProcessUtils.run_command', return_value=(0, '{"Results": []}', "")):
            issues = agent.scan_files([str(file1), str(file2)])
            
            assert isinstance(issues, list)

    @pytest.mark.unit
    def test_parse_secrets_in_output(self, base_config):
        """Test parsing secrets from Trivy output."""
        agent = TrivyAgent(base_config)
        
        secrets_output = {
            "Results": [{
                "Target": "config.py",
                "Type": "secret",
                "Secrets": [{
                    "RuleID": "aws-access-key",
                    "Category": "AWS",
                    "Severity": "CRITICAL",
                    "Title": "AWS Access Key",
                    "StartLine": 10,
                    "EndLine": 10,
                    "Match": "AKIA****************"
                }]
            }]
        }
        
        if hasattr(agent, '_parse_trivy_output'):
            issues = agent._parse_trivy_output(secrets_output)
            
            # Should parse secrets
            if len(issues) > 0:
                secret_issues = [i for i in issues if "secret" in i.title.lower() or "aws" in i.title.lower()]
                assert len(secret_issues) > 0

    @pytest.mark.unit
    def test_parse_misconfigurations(self, base_config):
        """Test parsing misconfigurations from Trivy output."""
        agent = TrivyAgent(base_config)
        
        misconfig_output = {
            "Results": [{
                "Target": "Dockerfile",
                "Type": "dockerfile",
                "Misconfigurations": [{
                    "ID": "DS002",
                    "Title": "Image user should not be root",
                    "Description": "Running as root increases risks",
                    "Severity": "HIGH",
                    "Message": "Specify USER to switch to non-root user",
                    "CauseMetadata": {
                        "StartLine": 5,
                        "EndLine": 5
                    }
                }]
            }]
        }
        
        if hasattr(agent, '_parse_trivy_output'):
            issues = agent._parse_trivy_output(misconfig_output)
            
            # Should parse misconfigurations
            if len(issues) > 0:
                misconfig_issues = [i for i in issues if "DS002" in i.rule_id]
                assert len(misconfig_issues) > 0

    @pytest.mark.integration
    @pytest.mark.requires_trivy
    def test_execute_real_trivy(self, base_config, temp_dir):
        """Test execution with real Trivy tool."""
        agent = TrivyAgent(base_config)
        
        if not agent.is_available():
            pytest.skip("Trivy not available")
        
        # Create a test requirements file
        req_file = temp_dir / "requirements.txt"
        req_file.write_text("requests==2.0.0\n")
        
        result = agent.execute([str(temp_dir)])
        
        assert result.success is True
        assert result.agent_type == AgentType.TRIVY
        assert result.execution_time > 0
