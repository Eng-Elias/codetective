"""
Unit tests for Config and configuration management.
"""

import pytest
from pydantic import ValidationError

from codetective.core.config import Config, get_config
from codetective.models.schemas import AgentType, FixConfig, ScanConfig


class TestConfig:
    """Test cases for Config class."""

    def test_config_default_values(self):
        """Test Config with default values."""
        config = Config()
        
        assert config.agent_timeout == 900
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.ollama_model == "qwen3:4b"
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.backup_files is True
        assert config.keep_backup is False
        assert config.gui_host == "localhost"
        assert config.gui_port == 7891

    def test_config_custom_values(self):
        """Test Config with custom values."""
        config = Config(
            agent_timeout=600,
            ollama_base_url="http://custom:11434",
            ollama_model="custom-model",
            max_file_size=5 * 1024 * 1024,
            backup_files=False,
            keep_backup=True,
            gui_host="0.0.0.0",
            gui_port=8080
        )
        
        assert config.agent_timeout == 600
        assert config.ollama_base_url == "http://custom:11434"
        assert config.ollama_model == "custom-model"
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.backup_files is False
        assert config.keep_backup is True
        assert config.gui_host == "0.0.0.0"
        assert config.gui_port == 8080

    def test_config_scan_config_default(self):
        """Test default ScanConfig in Config."""
        config = Config()
        
        assert isinstance(config.scan_config, ScanConfig)
        assert AgentType.SEMGREP in config.scan_config.agents
        assert AgentType.TRIVY in config.scan_config.agents
        assert config.scan_config.parallel_execution is False
        assert config.scan_config.paths == ["."]

    def test_config_fix_config_default(self):
        """Test default FixConfig in Config."""
        config = Config()
        
        assert isinstance(config.fix_config, FixConfig)
        assert AgentType.EDIT in config.fix_config.agents

    def test_config_with_custom_scan_config(self):
        """Test Config with custom ScanConfig."""
        scan_config = ScanConfig(
            agents=[AgentType.SEMGREP, AgentType.AI_REVIEW],
            parallel_execution=True,
            paths=["/custom/path"],
            max_files=100
        )
        
        config = Config(scan_config=scan_config)
        
        assert config.scan_config.parallel_execution is True
        assert config.scan_config.paths == ["/custom/path"]
        assert config.scan_config.max_files == 100
        assert AgentType.AI_REVIEW in config.scan_config.agents

    def test_config_with_custom_fix_config(self):
        """Test Config with custom FixConfig."""
        fix_config = FixConfig(agents=[AgentType.COMMENT])
        
        config = Config(fix_config=fix_config)
        
        assert AgentType.COMMENT in config.fix_config.agents
        assert AgentType.EDIT not in config.fix_config.agents

    def test_get_config_no_args(self):
        """Test get_config helper with no arguments."""
        config = get_config()
        
        assert isinstance(config, Config)
        assert config.ollama_base_url == "http://localhost:11434"

    def test_get_config_with_kwargs(self):
        """Test get_config helper with keyword arguments."""
        config = get_config(
            agent_timeout=300,
            ollama_model="test-model"
        )
        
        assert isinstance(config, Config)
        assert config.agent_timeout == 300
        assert config.ollama_model == "test-model"

    def test_config_pydantic_validation(self):
        """Test that Config uses Pydantic validation."""
        # Valid config should work
        config = Config(agent_timeout=100)
        assert config.agent_timeout == 100
        
        # Invalid type should raise validation error
        with pytest.raises(ValidationError):
            Config(agent_timeout="invalid")

    def test_config_model_dump(self):
        """Test serializing Config to dict."""
        config = Config(
            agent_timeout=600,
            ollama_model="test-model"
        )
        
        data = config.model_dump()
        
        assert isinstance(data, dict)
        assert data["agent_timeout"] == 600
        assert data["ollama_model"] == "test-model"
        assert "scan_config" in data
        assert "fix_config" in data

    def test_config_immutable_after_creation(self):
        """Test that Config fields can be modified (Pydantic models are mutable by default)."""
        config = Config()
        
        # Pydantic BaseModel allows field assignment
        original_timeout = config.agent_timeout
        config.agent_timeout = 1000
        
        assert config.agent_timeout == 1000
        assert config.agent_timeout != original_timeout


class TestScanConfig:
    """Test cases for ScanConfig class."""

    def test_scan_config_defaults(self):
        """Test ScanConfig default values."""
        config = ScanConfig()
        
        assert AgentType.SEMGREP in config.agents
        assert AgentType.TRIVY in config.agents
        assert config.parallel_execution is False
        assert config.paths == ["."]
        assert config.max_files is None
        assert config.output_file == "codetective_scan_results.json"

    def test_scan_config_custom_agents(self):
        """Test ScanConfig with custom agents."""
        config = ScanConfig(agents=[AgentType.AI_REVIEW])
        
        assert config.agents == [AgentType.AI_REVIEW]
        assert AgentType.SEMGREP not in config.agents

    def test_scan_config_parallel_execution(self):
        """Test ScanConfig with parallel execution."""
        config = ScanConfig(parallel_execution=True)
        
        assert config.parallel_execution is True

    def test_scan_config_custom_paths(self):
        """Test ScanConfig with custom paths."""
        config = ScanConfig(paths=["/path1", "/path2"])
        
        assert config.paths == ["/path1", "/path2"]

    def test_scan_config_max_files(self):
        """Test ScanConfig with max_files limit."""
        config = ScanConfig(max_files=50)
        
        assert config.max_files == 50

    def test_scan_config_output_file(self):
        """Test ScanConfig with custom output file."""
        config = ScanConfig(output_file="custom_results.json")
        
        assert config.output_file == "custom_results.json"

    def test_scan_config_include_exclude_patterns(self):
        """Test ScanConfig with include/exclude patterns."""
        config = ScanConfig(
            include_patterns=["*.py", "*.js"],
            exclude_patterns=["*test*", "*.min.js"]
        )
        
        assert "*.py" in config.include_patterns
        assert "*.js" in config.include_patterns
        assert "*test*" in config.exclude_patterns


class TestFixConfig:
    """Test cases for FixConfig class."""

    def test_fix_config_defaults(self):
        """Test FixConfig default values."""
        config = FixConfig()
        
        assert AgentType.EDIT in config.agents
        assert len(config.agents) == 1

    def test_fix_config_custom_agents(self):
        """Test FixConfig with custom agents."""
        config = FixConfig(agents=[AgentType.COMMENT])
        
        assert config.agents == [AgentType.COMMENT]
        assert AgentType.EDIT not in config.agents

    def test_fix_config_multiple_agents(self):
        """Test FixConfig with multiple agents."""
        config = FixConfig(agents=[AgentType.COMMENT, AgentType.EDIT])
        
        assert len(config.agents) == 2
        assert AgentType.COMMENT in config.agents
        assert AgentType.EDIT in config.agents
