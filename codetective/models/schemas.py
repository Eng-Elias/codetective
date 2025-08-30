"""
Pydantic models for Codetective data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Available agent types."""

    SEMGREP = "semgrep"
    TRIVY = "trivy"
    AI_REVIEW = "ai_review"
    COMMENT = "comment"
    EDIT = "edit"
    UNKOWN = "unknown"


class SeverityLevel(str, Enum):
    """Issue severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(str, Enum):
    """Issue processing status."""

    DETECTED = "detected"
    FIXED = "fixed"
    IGNORED = "ignored"
    FAILED = "failed"


class Issue(BaseModel):
    """Individual issue found by an agent."""

    id: str = Field(..., description="Unique issue identifier")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Detailed description")
    file_path: str = Field(..., description="Path to affected file")
    severity: Optional[SeverityLevel] = Field(default=None, description="Issue severity")
    line_number: Optional[int] = Field(default=None, description="Line number if applicable")
    rule_id: Optional[str] = Field(default=None, description="Rule or check ID")
    fix_suggestion: Optional[str] = Field(default=None, description="Suggested fix")
    status: IssueStatus = Field(default=IssueStatus.DETECTED, description="Issue status")


class AgentResult(BaseModel):
    """Result from a single agent execution."""

    agent_type: AgentType = Field(..., description="Type of agent")
    success: bool = Field(..., description="Whether agent executed successfully")
    issues: List[Issue] = Field(default_factory=list, description="Issues found")
    execution_time: float = Field(..., description="Execution time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ScanConfig(BaseModel):
    """Configuration for scan operations."""

    # used in this version
    agents: List[AgentType] = Field(default=[AgentType.SEMGREP, AgentType.TRIVY])
    parallel_execution: bool = Field(default=False, description="Run agents in parallel")
    paths: List[str] = Field(default=["."], description="Paths to scan")
    # only store values for now
    max_files: Optional[int] = Field(default=None, description="Maximum number of files to scan")
    output_file: Optional[str] = Field(default="codetective_scan_results.json", description="Output JSON file")
    # for future versions use
    include_patterns: List[str] = Field(default_factory=list, description="File patterns to include")
    exclude_patterns: List[str] = Field(default_factory=list, description="File patterns to exclude")


class ScanResult(BaseModel):
    """Complete scan results from all agents."""

    timestamp: datetime = Field(default_factory=datetime.now, description="Scan timestamp")
    scan_path: str = Field(default="", description="Scanned path")
    config: ScanConfig = Field(default=ScanConfig(), description="Scan configuration used")
    semgrep_results: List[Issue] = Field(default_factory=list, description="SemGrep scan results")
    trivy_results: List[Issue] = Field(default_factory=list, description="Trivy scan results")
    ai_review_results: List[Issue] = Field(default_factory=list, description="AI review results")
    agent_results: List[AgentResult] = Field(default_factory=list, description="Detailed agent results")
    total_issues: int = Field(default=0, description="Total number of issues found")
    scan_duration: float = Field(default=0.0, description="Total scan duration in seconds")


class FixConfig(BaseModel):
    """Configuration for fix operations."""

    agents: List[AgentType] = Field(default=[AgentType.EDIT], description="Fix agents to use")


class FixResult(BaseModel):
    """Result from fix operations."""

    timestamp: datetime = Field(default_factory=datetime.now, description="Fix timestamp")
    config: FixConfig = Field(..., description="Fix configuration used")
    fixed_issues: List[Issue] = Field(default_factory=list, description="Successfully fixed issues")
    failed_issues: List[Issue] = Field(default_factory=list, description="Issues that failed to fix")
    modified_files: List[str] = Field(default_factory=list, description="Files that were modified")
    fix_duration: float = Field(default=0.0, description="Total fix duration in seconds")


class SystemInfo(BaseModel):
    """System information and tool availability."""

    semgrep_available: bool = Field(default=False, description="SemGrep tool availability")
    trivy_available: bool = Field(default=False, description="Trivy tool availability")
    ollama_available: bool = Field(default=False, description="Ollama service availability")
    semgrep_version: Optional[str] = Field(None, description="SemGrep version")
    trivy_version: Optional[str] = Field(None, description="Trivy version")
    ollama_version: Optional[str] = Field(None, description="Ollama version")
    python_version: str = Field(..., description="Python version")
    codetective_version: str = Field(..., description="Codetective version")
