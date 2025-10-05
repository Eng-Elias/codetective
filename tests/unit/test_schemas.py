"""
Unit tests for Pydantic schemas and data models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from codetective.models.schemas import (
    AgentResult,
    AgentType,
    FixResult,
    Issue,
    IssueStatus,
    ScanConfig,
    ScanResult,
    SeverityLevel,
    SystemInfo,
)


class TestEnums:
    """Test cases for enum types."""

    def test_agent_type_values(self):
        """Test AgentType enum values."""
        assert AgentType.SEMGREP.value == "semgrep"
        assert AgentType.TRIVY.value == "trivy"
        assert AgentType.AI_REVIEW.value == "ai_review"
        assert AgentType.COMMENT.value == "comment"
        assert AgentType.EDIT.value == "edit"
        assert AgentType.UNKOWN.value == "unknown"

    def test_severity_level_values(self):
        """Test SeverityLevel enum values."""
        assert SeverityLevel.INFO.value == "info"
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.CRITICAL.value == "critical"

    def test_issue_status_values(self):
        """Test IssueStatus enum values."""
        assert IssueStatus.DETECTED.value == "detected"
        assert IssueStatus.FIXED.value == "fixed"
        assert IssueStatus.IGNORED.value == "ignored"
        assert IssueStatus.FAILED.value == "failed"


class TestIssue:
    """Test cases for Issue model."""

    def test_issue_creation_required_fields(self):
        """Test creating Issue with required fields only."""
        issue = Issue(
            id="test-1",
            title="Test Issue",
            description="Test description",
            file_path="/path/to/file.py"
        )
        
        assert issue.id == "test-1"
        assert issue.title == "Test Issue"
        assert issue.description == "Test description"
        assert issue.file_path == "/path/to/file.py"
        assert issue.severity is None
        assert issue.line_number is None
        assert issue.rule_id is None
        assert issue.fix_suggestion is None
        assert issue.status == IssueStatus.DETECTED

    def test_issue_creation_all_fields(self):
        """Test creating Issue with all fields."""
        issue = Issue(
            id="test-1",
            title="SQL Injection",
            description="Potential SQL injection vulnerability",
            file_path="/app/database.py",
            severity=SeverityLevel.HIGH,
            line_number=42,
            rule_id="python.sql-injection",
            fix_suggestion="Use parameterized queries",
            status=IssueStatus.DETECTED
        )
        
        assert issue.id == "test-1"
        assert issue.severity == SeverityLevel.HIGH
        assert issue.line_number == 42
        assert issue.rule_id == "python.sql-injection"
        assert issue.fix_suggestion is not None

    def test_issue_validation_error(self):
        """Test Issue validation with missing required fields."""
        with pytest.raises(ValidationError):
            Issue(title="No ID")

    def test_issue_model_dump(self):
        """Test serializing Issue to dict."""
        issue = Issue(
            id="test-1",
            title="Test",
            description="Desc",
            file_path="/test.py",
            severity=SeverityLevel.MEDIUM
        )
        
        data = issue.model_dump()
        
        assert isinstance(data, dict)
        assert data["id"] == "test-1"
        assert data["severity"] == "medium"

    def test_issue_status_update(self):
        """Test updating Issue status."""
        issue = Issue(
            id="test-1",
            title="Test",
            description="Desc",
            file_path="/test.py"
        )
        
        assert issue.status == IssueStatus.DETECTED
        
        issue.status = IssueStatus.FIXED
        assert issue.status == IssueStatus.FIXED


class TestAgentResult:
    """Test cases for AgentResult model."""

    def test_agent_result_creation(self):
        """Test creating AgentResult."""
        result = AgentResult(
            agent_type=AgentType.SEMGREP,
            success=True,
            issues=[],
            execution_time=1.5
        )
        
        assert result.agent_type == AgentType.SEMGREP
        assert result.success is True
        assert len(result.issues) == 0
        assert result.execution_time == 1.5
        assert result.error_message is None
        assert isinstance(result.metadata, dict)

    def test_agent_result_with_issues(self, sample_issues):
        """Test AgentResult with issues."""
        result = AgentResult(
            agent_type=AgentType.TRIVY,
            success=True,
            issues=sample_issues,
            execution_time=2.3
        )
        
        assert len(result.issues) == len(sample_issues)
        assert all(isinstance(issue, Issue) for issue in result.issues)

    def test_agent_result_failed(self):
        """Test failed AgentResult."""
        result = AgentResult(
            agent_type=AgentType.AI_REVIEW,
            success=False,
            execution_time=0.5,
            error_message="Ollama not available"
        )
        
        assert result.success is False
        assert result.error_message == "Ollama not available"
        assert len(result.issues) == 0

    def test_agent_result_with_metadata(self):
        """Test AgentResult with custom metadata."""
        result = AgentResult(
            agent_type=AgentType.SEMGREP,
            success=True,
            issues=[],
            execution_time=1.0,
            metadata={"files_scanned": 10, "rules_used": 50}
        )
        
        assert result.metadata["files_scanned"] == 10
        assert result.metadata["rules_used"] == 50


class TestScanResult:
    """Test cases for ScanResult model."""

    def test_scan_result_defaults(self):
        """Test ScanResult with default values."""
        result = ScanResult()
        
        assert isinstance(result.timestamp, datetime)
        assert result.scan_path == ""
        assert isinstance(result.config, ScanConfig)
        assert len(result.semgrep_results) == 0
        assert len(result.trivy_results) == 0
        assert len(result.ai_review_results) == 0
        assert result.total_issues == 0
        assert result.scan_duration == 0.0

    def test_scan_result_with_issues(self, sample_issues):
        """Test ScanResult with issues."""
        result = ScanResult(
            scan_path="/project",
            semgrep_results=[sample_issues[0]],
            trivy_results=[sample_issues[1]],
            total_issues=2,
            scan_duration=15.5
        )
        
        assert result.scan_path == "/project"
        assert len(result.semgrep_results) == 1
        assert len(result.trivy_results) == 1
        assert result.total_issues == 2
        assert result.scan_duration == 15.5

    def test_scan_result_with_agent_results(self, sample_agent_result):
        """Test ScanResult with agent_results."""
        result = ScanResult(
            agent_results=[sample_agent_result],
            total_issues=1
        )
        
        assert len(result.agent_results) == 1
        assert result.agent_results[0].agent_type == AgentType.SEMGREP

    def test_scan_result_serialization(self, sample_issues):
        """Test serializing ScanResult."""
        result = ScanResult(
            scan_path="/test",
            semgrep_results=sample_issues,
            total_issues=len(sample_issues),
            scan_duration=10.0
        )
        
        data = result.model_dump()
        
        assert isinstance(data, dict)
        assert data["scan_path"] == "/test"
        assert data["total_issues"] == len(sample_issues)
        assert "timestamp" in data


class TestFixResult:
    """Test cases for FixResult model."""

    def test_fix_result_creation(self):
        """Test creating FixResult."""
        from codetective.models.schemas import FixConfig
        
        config = FixConfig()
        result = FixResult(
            config=config,
            fixed_issues=[],
            failed_issues=[],
            modified_files=[],
            fix_duration=5.2
        )
        
        assert isinstance(result.timestamp, datetime)
        assert result.config == config
        assert len(result.fixed_issues) == 0
        assert len(result.failed_issues) == 0
        assert result.fix_duration == 5.2

    def test_fix_result_with_fixes(self, sample_issues):
        """Test FixResult with fixed and failed issues."""
        from codetective.models.schemas import FixConfig
        
        fixed_issue = sample_issues[0]
        fixed_issue.status = IssueStatus.FIXED
        
        failed_issue = sample_issues[1]
        failed_issue.status = IssueStatus.FAILED
        
        config = FixConfig()
        result = FixResult(
            config=config,
            fixed_issues=[fixed_issue],
            failed_issues=[failed_issue],
            modified_files=["/path/to/file1.py"],
            fix_duration=3.5
        )
        
        assert len(result.fixed_issues) == 1
        assert len(result.failed_issues) == 1
        assert len(result.modified_files) == 1
        assert result.fixed_issues[0].status == IssueStatus.FIXED


class TestSystemInfo:
    """Test cases for SystemInfo model."""

    def test_system_info_creation(self):
        """Test creating SystemInfo."""
        info = SystemInfo(
            semgrep_available=True,
            trivy_available=True,
            ollama_available=False,
            semgrep_version="1.0.0",
            trivy_version="0.45.0",
            python_version="3.10.0",
            codetective_version="0.1.0"
        )
        
        assert info.semgrep_available is True
        assert info.trivy_available is True
        assert info.ollama_available is False
        assert info.semgrep_version == "1.0.0"
        assert info.python_version == "3.10.0"

    def test_system_info_defaults(self):
        """Test SystemInfo with minimal fields."""
        info = SystemInfo(
            python_version="3.11.0",
            codetective_version="0.1.0"
        )
        
        assert info.semgrep_available is False
        assert info.trivy_available is False
        assert info.ollama_available is False
        assert info.semgrep_version is None

    def test_system_info_all_tools_available(self):
        """Test SystemInfo with all tools available."""
        info = SystemInfo(
            semgrep_available=True,
            trivy_available=True,
            ollama_available=True,
            semgrep_version="1.0.0",
            trivy_version="0.45.0",
            ollama_version="0.1.20",
            python_version="3.10.0",
            codetective_version="0.1.0"
        )
        
        assert all([
            info.semgrep_available,
            info.trivy_available,
            info.ollama_available
        ])
        assert info.ollama_version == "0.1.20"
