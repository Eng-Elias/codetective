"""
Basic tests for Codetective functionality.
"""

import pytest
from pathlib import Path
import tempfile
import os

from codetective.core.config import Config
from codetective.core.utils import get_system_info, validate_paths
from codetective.models.schemas import ScanConfig, AgentType, Issue, SeverityLevel


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = Config()
        assert config.default_timeout == 300
        assert config.semgrep_enabled is True
        assert config.trivy_enabled is True
        assert config.ai_review_enabled is True
    
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        # Set environment variables
        os.environ["CODETECTIVE_DEFAULT_TIMEOUT"] = "600"
        os.environ["CODETECTIVE_SEMGREP_ENABLED"] = "false"
        
        config = Config.from_env()
        assert config.default_timeout == 600
        assert config.semgrep_enabled is False
        
        # Clean up
        del os.environ["CODETECTIVE_DEFAULT_TIMEOUT"]
        del os.environ["CODETECTIVE_SEMGREP_ENABLED"]


class TestUtils:
    """Test utility functions."""
    
    def test_get_system_info(self):
        """Test system information retrieval."""
        system_info = get_system_info()
        assert system_info.python_version is not None
        assert system_info.codetective_version == "0.1.0"
    
    def test_validate_paths_valid(self):
        """Test path validation with valid paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")
            
            validated = validate_paths([str(test_file), temp_dir])
            assert len(validated) == 2
            assert str(test_file.resolve()) in validated
            assert str(Path(temp_dir).resolve()) in validated
    
    def test_validate_paths_invalid(self):
        """Test path validation with invalid paths."""
        with pytest.raises(FileNotFoundError):
            validate_paths(["/nonexistent/path"])


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_issue_creation(self):
        """Test Issue model creation."""
        issue = Issue(
            id="test-issue-1",
            title="Test Issue",
            description="This is a test issue",
            severity=SeverityLevel.HIGH,
            file_path="/path/to/file.py",
            line_number=42
        )
        
        assert issue.id == "test-issue-1"
        assert issue.severity == SeverityLevel.HIGH
        assert issue.line_number == 42
    
    def test_scan_config_creation(self):
        """Test ScanConfig model creation."""
        config = ScanConfig(
            agents=[AgentType.SEMGREP, AgentType.TRIVY],
            timeout=600,
            paths=["/path/to/project"]
        )
        
        assert len(config.agents) == 2
        assert AgentType.SEMGREP in config.agents
        assert config.timeout == 600
        assert config.paths == ["/path/to/project"]
    
    def test_scan_config_defaults(self):
        """Test ScanConfig default values."""
        config = ScanConfig()
        
        assert len(config.agents) == 3  # All agents by default
        assert config.timeout == 300
        assert config.paths == ["."]
        assert config.output_file == "codetective_scan_results.json"


class TestAgentBase:
    """Test base agent functionality."""
    
    def test_agent_initialization(self):
        """Test agent base class initialization."""
        from codetective.agents.base import BaseAgent
        
        config = Config()
        
        # Create a mock agent for testing
        class MockAgent(BaseAgent):
            def __init__(self, config):
                super().__init__(config)
                self.agent_type = AgentType.SEMGREP
            
            def execute(self, paths, **kwargs):
                return self._create_result(success=True)
            
            def is_available(self):
                return True
        
        agent = MockAgent(config)
        assert agent.config == config
        assert agent.agent_type == AgentType.SEMGREP
        assert agent.is_available() is True
    
    def test_agent_execution_timing(self):
        """Test agent execution timing."""
        from codetective.agents.base import BaseAgent
        import time
        
        config = Config()
        
        class MockAgent(BaseAgent):
            def __init__(self, config):
                super().__init__(config)
                self.agent_type = AgentType.SEMGREP
            
            def execute(self, paths, **kwargs):
                self._start_execution()
                time.sleep(0.1)  # Simulate work
                return self._create_result(success=True)
            
            def is_available(self):
                return True
        
        agent = MockAgent(config)
        result = agent.execute([])
        
        assert result.success is True
        assert result.execution_time >= 0.1
        assert result.agent_type == AgentType.SEMGREP


if __name__ == "__main__":
    pytest.main([__file__])
