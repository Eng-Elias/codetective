"""
Workflow state management for the codetective multi-agent system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from codetective.models.agent_results import (
    AIReviewResults,
    OutputResults,
    SemgrepResults,
    TrivyResults,
)


@dataclass
class WorkflowState:
    """
    Central state object passed between agents in LangGraph workflow.
    
    This class maintains the shared state across all agents in the workflow,
    including input files, configuration, results, and execution metadata.
    """
    
    scan_id: str
    target_files: List[Path]
    selected_agents: List[str]
    semgrep_results: Optional[SemgrepResults] = None
    trivy_results: Optional[TrivyResults] = None
    ai_review_results: Optional[AIReviewResults] = None
    output_results: Optional[OutputResults] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate state after initialization."""
        if not self.scan_id:
            raise ValueError("scan_id cannot be empty")
        
        if not self.target_files:
            raise ValueError("target_files cannot be empty")
        
        if not self.selected_agents:
            raise ValueError("selected_agents cannot be empty")
    
    def add_error(self, error: str) -> None:
        """Add an error to the error list."""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Check if there are any errors in the workflow."""
        return len(self.errors) > 0
    
    def get_completed_agents(self) -> List[str]:
        """Get list of agents that have completed successfully."""
        completed = []
        
        if self.semgrep_results is not None:
            completed.append("semgrep")
        
        if self.trivy_results is not None:
            completed.append("trivy")
        
        if self.ai_review_results is not None:
            completed.append("ai_review")
        
        if self.output_results is not None:
            completed.append("output")
        
        return completed
    
    def get_pending_agents(self) -> List[str]:
        """Get list of agents that are still pending execution."""
        completed = set(self.get_completed_agents())
        selected = set(self.selected_agents)
        return list(selected - completed)
    
    def is_complete(self) -> bool:
        """Check if all selected agents have completed."""
        return len(self.get_pending_agents()) == 0
    
    def get_total_findings_count(self) -> int:
        """Get total count of findings across all completed agents."""
        total = 0
        
        if self.semgrep_results:
            total += len(self.semgrep_results.findings)
        
        if self.trivy_results:
            for result in self.trivy_results.results:
                total += len(result.vulnerabilities)
        
        if self.ai_review_results:
            total += len(self.ai_review_results.issues)
        
        return total
    
    def get_critical_findings_count(self) -> int:
        """Get count of critical/high severity findings."""
        critical_count = 0
        
        if self.semgrep_results:
            critical_count += len([
                f for f in self.semgrep_results.findings 
                if f.severity.upper() in ["ERROR", "CRITICAL"]
            ])
        
        if self.trivy_results:
            for result in self.trivy_results.results:
                critical_count += len([
                    v for v in result.vulnerabilities 
                    if v.severity.upper() in ["CRITICAL", "HIGH"]
                ])
        
        if self.ai_review_results:
            critical_count += len([
                i for i in self.ai_review_results.issues 
                if i.severity.upper() in ["CRITICAL", "HIGH"]
            ])
        
        return critical_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary for serialization."""
        return {
            "scan_id": self.scan_id,
            "target_files": [str(f) for f in self.target_files],
            "selected_agents": self.selected_agents,
            "semgrep_results": self.semgrep_results.to_dict() if self.semgrep_results else None,
            "trivy_results": self.trivy_results.to_dict() if self.trivy_results else None,
            "ai_review_results": self.ai_review_results.to_dict() if self.ai_review_results else None,
            "output_results": self.output_results.to_dict() if self.output_results else None,
            "errors": self.errors,
            "metadata": self.metadata,
            "completed_agents": self.get_completed_agents(),
            "pending_agents": self.get_pending_agents(),
            "total_findings": self.get_total_findings_count(),
            "critical_findings": self.get_critical_findings_count(),
        }
