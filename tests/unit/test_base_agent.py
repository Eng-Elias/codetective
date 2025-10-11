"""
Unit tests for BaseAgent, ScanAgent, and OutputAgent classes.
"""

import pytest
from unittest.mock import Mock, patch

from codetective.agents.base import BaseAgent, OutputAgent, ScanAgent
from codetective.core.config import Config
from codetective.models.schemas import AgentResult, AgentType, Issue, IssueStatus, SeverityLevel


class TestBaseAgent:
    """Test cases for BaseAgent abstract class."""

    def test_base_agent_init(self, base_config):
        """Test BaseAgent initialization."""
        # Create concrete implementation for testing
        class ConcreteAgent(BaseAgent):
            def execute(self, paths, **kwargs):
                pass
            
            def is_available(self):
                return True
        
        agent = ConcreteAgent(base_config)
        
        assert agent.config == base_config
        assert agent.agent_type == AgentType.UNKOWN
        assert agent._execution_start_time is None

    def test_create_result_success(self, base_config, sample_issues):
        """Test creating successful AgentResult."""
        class ConcreteAgent(BaseAgent):
            def execute(self, paths, **kwargs):
                pass
            
            def is_available(self):
                return True
        
        agent = ConcreteAgent(base_config)
        agent.agent_type = AgentType.SEMGREP
        agent._start_execution()
        
        result = agent._create_result(
            success=True,
            issues=sample_issues,
            metadata={"files": 5}
        )
        
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.agent_type == AgentType.SEMGREP
        assert len(result.issues) == len(sample_issues)
        assert result.execution_time >= 0
        assert result.metadata["files"] == 5
        assert result.error_message is None

    def test_create_result_failure(self, base_config):
        """Test creating failed AgentResult."""
        class ConcreteAgent(BaseAgent):
            def execute(self, paths, **kwargs):
                pass
            
            def is_available(self):
                return True
        
        agent = ConcreteAgent(base_config)
        agent.agent_type = AgentType.TRIVY
        agent._start_execution()
        
        result = agent._create_result(
            success=False,
            error_message="Tool not found"
        )
        
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert result.agent_type == AgentType.TRIVY
        assert len(result.issues) == 0
        assert result.error_message == "Tool not found"

    def test_get_supported_files_single_file(self, base_config, sample_python_file):
        """Test getting supported files from a single file path."""
        class ConcreteAgent(BaseAgent):
            def execute(self, paths, **kwargs):
                pass
            
            def is_available(self):
                return True
        
        agent = ConcreteAgent(base_config)
        paths = [str(sample_python_file)]
        
        supported_files = agent._get_supported_files(paths)
        
        assert len(supported_files) == 1
        assert str(sample_python_file) in supported_files

    def test_get_supported_files_directory(self, base_config, temp_dir):
        """Test getting supported files from directory."""
        # Create test files
        (temp_dir / "file1.py").write_text("print('test')")
        (temp_dir / "file2.py").write_text("print('test')")
        (temp_dir / "file3.js").write_text("console.log('test');")
        
        class ConcreteAgent(BaseAgent):
            def execute(self, paths, **kwargs):
                pass
            
            def is_available(self):
                return True
        
        agent = ConcreteAgent(base_config)
        paths = [str(temp_dir)]
        
        supported_files = agent._get_supported_files(paths)
        
        assert len(supported_files) >= 3

    def test_get_supported_files_with_extension_filter(self, base_config, temp_dir):
        """Test filtering files by extension."""
        (temp_dir / "file1.py").write_text("print('test')")
        (temp_dir / "file2.py").write_text("print('test')")
        (temp_dir / "file3.js").write_text("console.log('test');")
        
        class ConcreteAgent(BaseAgent):
            def execute(self, paths, **kwargs):
                pass
            
            def is_available(self):
                return True
        
        agent = ConcreteAgent(base_config)
        paths = [str(temp_dir)]
        
        supported_files = agent._get_supported_files(paths, extensions=[".py"])
        
        assert len(supported_files) == 2
        assert all(f.endswith(".py") for f in supported_files)


class TestScanAgent:
    """Test cases for ScanAgent base class."""

    def test_scan_agent_execute_unavailable_tool(self, base_config):
        """Test ScanAgent when tool is unavailable."""
        class TestScanAgent(ScanAgent):
            def scan_files(self, files, **kwargs):
                return []
            
            def is_available(self):
                return False
        
        agent = TestScanAgent(base_config)
        agent.agent_type = AgentType.SEMGREP
        
        result = agent.execute(["."])
        
        assert result.success is False
        assert "not available" in result.error_message.lower()

    def test_scan_agent_execute_no_valid_paths(self, base_config):
        """Test ScanAgent with no valid paths."""
        class TestScanAgent(ScanAgent):
            def scan_files(self, files, **kwargs):
                return []
            
            def is_available(self):
                return True
        
        agent = TestScanAgent(base_config)
        
        with patch('codetective.utils.file_utils.FileUtils.validate_paths', return_value=[]):
            result = agent.execute(["/nonexistent/path"])
        
        assert result.success is False
        assert "no valid paths" in result.error_message.lower()

    def test_scan_agent_execute_success(self, base_config, sample_python_file, sample_issues):
        """Test successful ScanAgent execution."""
        print(sample_python_file)
        class TestScanAgent(ScanAgent):
            def scan_files(self, files, **kwargs):
                return sample_issues
            
            def is_available(self):
                return True
        
        agent = TestScanAgent(base_config)
        result = agent.execute([str(sample_python_file)])
        
        assert result.success is True
        assert len(result.issues) == len(sample_issues)
        assert result.execution_time >= 0
        assert result.metadata["scanned_paths"]

    def test_scan_agent_execute_exception_handling(self, base_config):
        """Test ScanAgent exception handling."""
        class TestScanAgent(ScanAgent):
            def scan_files(self, files, **kwargs):
                raise ValueError("Test error")
            
            def is_available(self):
                return True
        
        agent = TestScanAgent(base_config)
        result = agent.execute(["."])
        
        assert result.success is False
        assert "Test error" in result.error_message


class TestOutputAgent:
    """Test cases for OutputAgent base class."""

    def test_output_agent_execute_unavailable(self, base_config, sample_issues):
        """Test OutputAgent when unavailable."""
        class TestOutputAgent(OutputAgent):
            def process_issues(self, issues, **kwargs):
                return issues
            
            def is_available(self):
                return False
        
        agent = TestOutputAgent(base_config)
        agent.agent_type = AgentType.EDIT
        
        result = agent.execute([], issues=sample_issues)
        
        assert result.success is False
        assert "not available" in result.error_message.lower()

    def test_output_agent_execute_no_issues(self, base_config):
        """Test OutputAgent with no issues to process."""
        class TestOutputAgent(OutputAgent):
            def process_issues(self, issues, **kwargs):
                return issues
            
            def is_available(self):
                return True
        
        agent = TestOutputAgent(base_config)
        result = agent.execute([])
        
        assert result.success is True
        assert len(result.issues) == 0
        assert "no issues" in result.metadata["message"].lower()

    def test_output_agent_execute_success(self, base_config, sample_issues):
        """Test successful OutputAgent execution."""
        class TestOutputAgent(OutputAgent):
            def process_issues(self, issues, **kwargs):
                # Mark all as fixed
                for issue in issues:
                    issue.status = IssueStatus.FIXED
                return issues
            
            def is_available(self):
                return True
        
        agent = TestOutputAgent(base_config)
        result = agent.execute([], issues=sample_issues)
        
        assert result.success is True
        assert len(result.issues) == len(sample_issues)
        assert all(issue.status == IssueStatus.FIXED for issue in result.issues)
        assert result.metadata["input_issues"] == len(sample_issues)
        assert result.metadata["processed_issues"] == len(sample_issues)

    def test_output_agent_execute_exception_handling(self, base_config, sample_issues):
        """Test OutputAgent exception handling."""
        class TestOutputAgent(OutputAgent):
            def process_issues(self, issues, **kwargs):
                raise RuntimeError("Processing failed")
            
            def is_available(self):
                return True
        
        agent = TestOutputAgent(base_config)
        result = agent.execute([], issues=sample_issues)
        
        assert result.success is False
        assert "Processing failed" in result.error_message
