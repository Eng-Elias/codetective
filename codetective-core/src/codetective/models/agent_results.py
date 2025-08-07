"""
Agent result models based on external tool JSON schemas.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SemgrepFinding:
    """Individual Semgrep finding based on JSON schema."""
    
    check_id: str
    path: str
    start: Dict[str, int]  # {"line": int, "col": int}
    end: Dict[str, int]    # {"line": int, "col": int}
    message: str
    severity: str  # ERROR, WARNING, INFO
    metadata: Dict[str, Any]
    extra: Dict[str, Any]
    
    def __post_init__(self) -> None:
        """Validate finding after initialization."""
        if not self.check_id:
            raise ValueError("check_id cannot be empty")
        
        if not self.path:
            raise ValueError("path cannot be empty")
        
        if self.severity not in ["ERROR", "WARNING", "INFO"]:
            raise ValueError(f"Invalid severity: {self.severity}")
    
    def get_line_range(self) -> str:
        """Get formatted line range string."""
        start_line = self.start.get("line", 0)
        end_line = self.end.get("line", 0)
        
        if start_line == end_line:
            return str(start_line)
        return f"{start_line}-{end_line}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "check_id": self.check_id,
            "path": self.path,
            "start": self.start,
            "end": self.end,
            "message": self.message,
            "severity": self.severity,
            "metadata": self.metadata,
            "extra": self.extra,
            "line_range": self.get_line_range(),
        }


@dataclass
class SemgrepResults:
    """Semgrep scan results container."""
    
    findings: List[SemgrepFinding]
    errors: List[str]
    stats: Dict[str, Any]
    version: str
    
    def __post_init__(self) -> None:
        """Validate results after initialization."""
        if not isinstance(self.findings, list):
            raise ValueError("findings must be a list")
        
        if not isinstance(self.errors, list):
            raise ValueError("errors must be a list")
    
    def get_findings_by_severity(self, severity: str) -> List[SemgrepFinding]:
        """Get findings filtered by severity."""
        return [f for f in self.findings if f.severity.upper() == severity.upper()]
    
    def get_findings_by_file(self, file_path: str) -> List[SemgrepFinding]:
        """Get findings for a specific file."""
        return [f for f in self.findings if f.path == file_path]
    
    def get_unique_files(self) -> List[str]:
        """Get list of unique files with findings."""
        return list(set(f.path for f in self.findings))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "errors": self.errors,
            "stats": self.stats,
            "version": self.version,
            "summary": {
                "total_findings": len(self.findings),
                "error_count": len(self.get_findings_by_severity("ERROR")),
                "warning_count": len(self.get_findings_by_severity("WARNING")),
                "info_count": len(self.get_findings_by_severity("INFO")),
                "unique_files": len(self.get_unique_files()),
            }
        }


@dataclass
class TrivyVulnerability:
    """Individual Trivy vulnerability based on JSON schema v2."""
    
    vulnerability_id: str
    pkg_name: str
    installed_version: str
    fixed_version: Optional[str]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
    title: str
    description: str
    references: List[str]
    
    def __post_init__(self) -> None:
        """Validate vulnerability after initialization."""
        if not self.vulnerability_id:
            raise ValueError("vulnerability_id cannot be empty")
        
        if not self.pkg_name:
            raise ValueError("pkg_name cannot be empty")
        
        valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}")
    
    def is_fixable(self) -> bool:
        """Check if vulnerability has a fix available."""
        return self.fixed_version is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "vulnerability_id": self.vulnerability_id,
            "pkg_name": self.pkg_name,
            "installed_version": self.installed_version,
            "fixed_version": self.fixed_version,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "references": self.references,
            "is_fixable": self.is_fixable(),
        }


@dataclass
class TrivyResult:
    """Individual Trivy scan target result."""
    
    target: str
    class_type: str  # os-pkgs, lang-pkgs
    type: str  # alpine, java, etc.
    vulnerabilities: List[TrivyVulnerability]
    
    def __post_init__(self) -> None:
        """Validate result after initialization."""
        if not self.target:
            raise ValueError("target cannot be empty")
        
        if not isinstance(self.vulnerabilities, list):
            raise ValueError("vulnerabilities must be a list")
    
    def get_vulnerabilities_by_severity(self, severity: str) -> List[TrivyVulnerability]:
        """Get vulnerabilities filtered by severity."""
        return [v for v in self.vulnerabilities if v.severity.upper() == severity.upper()]
    
    def get_fixable_vulnerabilities(self) -> List[TrivyVulnerability]:
        """Get vulnerabilities that have fixes available."""
        return [v for v in self.vulnerabilities if v.is_fixable()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target": self.target,
            "class_type": self.class_type,
            "type": self.type,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "summary": {
                "total_vulnerabilities": len(self.vulnerabilities),
                "critical_count": len(self.get_vulnerabilities_by_severity("CRITICAL")),
                "high_count": len(self.get_vulnerabilities_by_severity("HIGH")),
                "medium_count": len(self.get_vulnerabilities_by_severity("MEDIUM")),
                "low_count": len(self.get_vulnerabilities_by_severity("LOW")),
                "fixable_count": len(self.get_fixable_vulnerabilities()),
            }
        }


@dataclass
class TrivyResults:
    """Trivy scan results container."""
    
    schema_version: int
    artifact_name: str
    artifact_type: str
    metadata: Dict[str, Any]
    results: List[TrivyResult]
    
    def __post_init__(self) -> None:
        """Validate results after initialization."""
        if not self.artifact_name:
            raise ValueError("artifact_name cannot be empty")
        
        if not isinstance(self.results, list):
            raise ValueError("results must be a list")
    
    def get_all_vulnerabilities(self) -> List[TrivyVulnerability]:
        """Get all vulnerabilities across all results."""
        all_vulns = []
        for result in self.results:
            all_vulns.extend(result.vulnerabilities)
        return all_vulns
    
    def get_vulnerabilities_by_severity(self, severity: str) -> List[TrivyVulnerability]:
        """Get all vulnerabilities filtered by severity."""
        return [v for v in self.get_all_vulnerabilities() if v.severity.upper() == severity.upper()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        all_vulns = self.get_all_vulnerabilities()
        return {
            "schema_version": self.schema_version,
            "artifact_name": self.artifact_name,
            "artifact_type": self.artifact_type,
            "metadata": self.metadata,
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "total_vulnerabilities": len(all_vulns),
                "critical_count": len(self.get_vulnerabilities_by_severity("CRITICAL")),
                "high_count": len(self.get_vulnerabilities_by_severity("HIGH")),
                "medium_count": len(self.get_vulnerabilities_by_severity("MEDIUM")),
                "low_count": len(self.get_vulnerabilities_by_severity("LOW")),
                "fixable_count": len([v for v in all_vulns if v.is_fixable()]),
            }
        }


@dataclass
class AIReviewIssue:
    """AI-identified code issue."""
    
    file_path: str
    line_start: int
    line_end: int
    issue_type: str  # security, performance, maintainability, etc.
    severity: str    # critical, high, medium, low
    description: str
    suggestion: str
    confidence: float  # 0.0 to 1.0
    
    def __post_init__(self) -> None:
        """Validate issue after initialization."""
        if not self.file_path:
            raise ValueError("file_path cannot be empty")
        
        if self.line_start < 1:
            raise ValueError("line_start must be >= 1")
        
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
    
    def get_line_range(self) -> str:
        """Get formatted line range string."""
        if self.line_start == self.line_end:
            return str(self.line_start)
        return f"{self.line_start}-{self.line_end}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "line_range": self.get_line_range(),
        }


@dataclass
class AIReviewResults:
    """AI review results container."""
    
    issues: List[AIReviewIssue]
    summary: str
    model_used: str
    processing_time: float
    
    def __post_init__(self) -> None:
        """Validate results after initialization."""
        if not isinstance(self.issues, list):
            raise ValueError("issues must be a list")
        
        if self.processing_time < 0:
            raise ValueError("processing_time must be >= 0")
    
    def get_issues_by_severity(self, severity: str) -> List[AIReviewIssue]:
        """Get issues filtered by severity."""
        return [i for i in self.issues if i.severity.upper() == severity.upper()]
    
    def get_issues_by_type(self, issue_type: str) -> List[AIReviewIssue]:
        """Get issues filtered by type."""
        return [i for i in self.issues if i.issue_type.lower() == issue_type.lower()]
    
    def get_high_confidence_issues(self, threshold: float = 0.8) -> List[AIReviewIssue]:
        """Get issues with confidence above threshold."""
        return [i for i in self.issues if i.confidence >= threshold]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary,
            "model_used": self.model_used,
            "processing_time": self.processing_time,
            "statistics": {
                "total_issues": len(self.issues),
                "critical_count": len(self.get_issues_by_severity("CRITICAL")),
                "high_count": len(self.get_issues_by_severity("HIGH")),
                "medium_count": len(self.get_issues_by_severity("MEDIUM")),
                "low_count": len(self.get_issues_by_severity("LOW")),
                "high_confidence_count": len(self.get_high_confidence_issues()),
                "avg_confidence": sum(i.confidence for i in self.issues) / len(self.issues) if self.issues else 0.0,
            }
        }


@dataclass
class OutputResults:
    """Final output from comment or update agents."""
    
    output_type: str  # comment, update
    files_modified: List[str]
    comments_added: List[Dict[str, Any]]
    success: bool
    message: str
    
    def __post_init__(self) -> None:
        """Validate results after initialization."""
        if self.output_type not in ["comment", "update"]:
            raise ValueError("output_type must be 'comment' or 'update'")
        
        if not isinstance(self.files_modified, list):
            raise ValueError("files_modified must be a list")
        
        if not isinstance(self.comments_added, list):
            raise ValueError("comments_added must be a list")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "output_type": self.output_type,
            "files_modified": self.files_modified,
            "comments_added": self.comments_added,
            "success": self.success,
            "message": self.message,
            "summary": {
                "files_modified_count": len(self.files_modified),
                "comments_added_count": len(self.comments_added),
            }
        }
