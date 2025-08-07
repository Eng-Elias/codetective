"""
Result aggregation utilities for the codetective system.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

from loguru import logger

from codetective.models.agent_results import (
    SemgrepResults,
    TrivyResults,
    AIReviewResults,
    OutputResults,
)
from codetective.models.workflow_state import WorkflowState


@dataclass
class AggregatedFinding:
    """Aggregated finding from multiple agents."""
    
    file_path: str
    line_start: int
    line_end: int
    severity: str
    finding_type: str  # semgrep, trivy, ai_review
    source_agent: str
    description: str
    suggestion: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregationSummary:
    """Summary of aggregated results."""
    
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    files_affected: int
    agents_completed: List[str]
    processing_time: float
    top_issues: List[Dict[str, Any]] = field(default_factory=list)


class ResultAggregator:
    """
    Aggregates and analyzes results from multiple agents.
    
    This class combines results from different agents, identifies patterns,
    removes duplicates, and provides unified reporting capabilities.
    """
    
    def __init__(self):
        """Initialize the result aggregator."""
        self._severity_weights = {
            "CRITICAL": 4,
            "ERROR": 4,
            "HIGH": 3,
            "WARNING": 2,
            "MEDIUM": 2,
            "INFO": 1,
            "LOW": 1,
            "UNKNOWN": 0,
        }
    
    def aggregate_workflow_results(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """
        Aggregate all results from a workflow state.
        
        Args:
            workflow_state: Completed workflow state
            
        Returns:
            Aggregated results dictionary
        """
        aggregated_findings = []
        
        # Process Semgrep results
        if workflow_state.semgrep_results:
            semgrep_findings = self._process_semgrep_results(workflow_state.semgrep_results)
            aggregated_findings.extend(semgrep_findings)
        
        # Process Trivy results
        if workflow_state.trivy_results:
            trivy_findings = self._process_trivy_results(workflow_state.trivy_results)
            aggregated_findings.extend(trivy_findings)
        
        # Process AI Review results
        if workflow_state.ai_review_results:
            ai_findings = self._process_ai_review_results(workflow_state.ai_review_results)
            aggregated_findings.extend(ai_findings)
        
        # Remove duplicates and create summary
        deduplicated_findings = self._deduplicate_findings(aggregated_findings)
        summary = self._create_summary(deduplicated_findings, workflow_state)
        
        return {
            "scan_id": workflow_state.scan_id,
            "findings": [self._finding_to_dict(f) for f in deduplicated_findings],
            "summary": summary,
            "file_analysis": self._analyze_by_file(deduplicated_findings),
            "severity_analysis": self._analyze_by_severity(deduplicated_findings),
            "agent_analysis": self._analyze_by_agent(deduplicated_findings),
            "recommendations": self._generate_recommendations(deduplicated_findings),
        }
    
    def _process_semgrep_results(self, results: SemgrepResults) -> List[AggregatedFinding]:
        """Process Semgrep results into aggregated findings."""
        findings = []
        
        for finding in results.findings:
            aggregated = AggregatedFinding(
                file_path=finding.path,
                line_start=finding.start.get("line", 0),
                line_end=finding.end.get("line", 0),
                severity=finding.severity,
                finding_type="static_analysis",
                source_agent="semgrep",
                description=finding.message,
                metadata={
                    "check_id": finding.check_id,
                    "semgrep_metadata": finding.metadata,
                    "extra": finding.extra,
                }
            )
            findings.append(aggregated)
        
        logger.debug(f"Processed {len(findings)} Semgrep findings")
        return findings
    
    def _process_trivy_results(self, results: TrivyResults) -> List[AggregatedFinding]:
        """Process Trivy results into aggregated findings."""
        findings = []
        
        for result in results.results:
            for vuln in result.vulnerabilities:
                aggregated = AggregatedFinding(
                    file_path=result.target,
                    line_start=0,  # Trivy doesn't provide line numbers
                    line_end=0,
                    severity=vuln.severity,
                    finding_type="vulnerability",
                    source_agent="trivy",
                    description=f"{vuln.title}: {vuln.description}",
                    suggestion=f"Update {vuln.pkg_name} to {vuln.fixed_version}" if vuln.fixed_version else None,
                    metadata={
                        "vulnerability_id": vuln.vulnerability_id,
                        "package_name": vuln.pkg_name,
                        "installed_version": vuln.installed_version,
                        "fixed_version": vuln.fixed_version,
                        "references": vuln.references,
                    }
                )
                findings.append(aggregated)
        
        logger.debug(f"Processed {len(findings)} Trivy findings")
        return findings
    
    def _process_ai_review_results(self, results: AIReviewResults) -> List[AggregatedFinding]:
        """Process AI Review results into aggregated findings."""
        findings = []
        
        for issue in results.issues:
            aggregated = AggregatedFinding(
                file_path=issue.file_path,
                line_start=issue.line_start,
                line_end=issue.line_end,
                severity=issue.severity.upper(),
                finding_type=issue.issue_type,
                source_agent="ai_review",
                description=issue.description,
                suggestion=issue.suggestion,
                confidence=issue.confidence,
                metadata={
                    "model_used": results.model_used,
                    "processing_time": results.processing_time,
                }
            )
            findings.append(aggregated)
        
        logger.debug(f"Processed {len(findings)} AI Review findings")
        return findings
    
    def _deduplicate_findings(self, findings: List[AggregatedFinding]) -> List[AggregatedFinding]:
        """Remove duplicate findings based on file path and line range."""
        seen_findings = set()
        deduplicated = []
        
        for finding in findings:
            # Create a key for deduplication
            key = (
                finding.file_path,
                finding.line_start,
                finding.line_end,
                finding.finding_type,
                finding.description[:100]  # First 100 chars to handle similar issues
            )
            
            if key not in seen_findings:
                seen_findings.add(key)
                deduplicated.append(finding)
            else:
                logger.debug(f"Deduplicated finding: {finding.description[:50]}...")
        
        logger.info(f"Deduplicated {len(findings)} findings to {len(deduplicated)}")
        return deduplicated
    
    def _create_summary(self, findings: List[AggregatedFinding], workflow_state: WorkflowState) -> AggregationSummary:
        """Create summary of aggregated results."""
        severity_counts = defaultdict(int)
        files_affected = set()
        
        for finding in findings:
            severity_counts[finding.severity.upper()] += 1
            files_affected.add(finding.file_path)
        
        # Get top issues by severity weight
        top_issues = sorted(
            findings,
            key=lambda f: (
                self._severity_weights.get(f.severity.upper(), 0),
                f.confidence or 0.5
            ),
            reverse=True
        )[:10]
        
        return AggregationSummary(
            total_findings=len(findings),
            critical_findings=severity_counts.get("CRITICAL", 0) + severity_counts.get("ERROR", 0),
            high_findings=severity_counts.get("HIGH", 0),
            medium_findings=severity_counts.get("MEDIUM", 0) + severity_counts.get("WARNING", 0),
            low_findings=severity_counts.get("LOW", 0) + severity_counts.get("INFO", 0),
            files_affected=len(files_affected),
            agents_completed=workflow_state.get_completed_agents(),
            processing_time=0.0,  # Would be calculated from workflow metadata
            top_issues=[
                {
                    "file": issue.file_path,
                    "line_range": f"{issue.line_start}-{issue.line_end}" if issue.line_end > issue.line_start else str(issue.line_start),
                    "severity": issue.severity,
                    "type": issue.finding_type,
                    "description": issue.description[:100] + "..." if len(issue.description) > 100 else issue.description,
                }
                for issue in top_issues
            ]
        )
    
    def _analyze_by_file(self, findings: List[AggregatedFinding]) -> Dict[str, Any]:
        """Analyze findings grouped by file."""
        file_analysis = defaultdict(lambda: {
            "total_findings": 0,
            "severity_breakdown": defaultdict(int),
            "finding_types": defaultdict(int),
            "agents": set(),
        })
        
        for finding in findings:
            file_data = file_analysis[finding.file_path]
            file_data["total_findings"] += 1
            file_data["severity_breakdown"][finding.severity.upper()] += 1
            file_data["finding_types"][finding.finding_type] += 1
            file_data["agents"].add(finding.source_agent)
        
        # Convert to regular dict and format agents as list
        result = {}
        for file_path, data in file_analysis.items():
            result[file_path] = {
                "total_findings": data["total_findings"],
                "severity_breakdown": dict(data["severity_breakdown"]),
                "finding_types": dict(data["finding_types"]),
                "agents": list(data["agents"]),
            }
        
        return result
    
    def _analyze_by_severity(self, findings: List[AggregatedFinding]) -> Dict[str, Any]:
        """Analyze findings grouped by severity."""
        severity_analysis = defaultdict(lambda: {
            "count": 0,
            "files": set(),
            "agents": set(),
            "types": defaultdict(int),
        })
        
        for finding in findings:
            severity = finding.severity.upper()
            severity_data = severity_analysis[severity]
            severity_data["count"] += 1
            severity_data["files"].add(finding.file_path)
            severity_data["agents"].add(finding.source_agent)
            severity_data["types"][finding.finding_type] += 1
        
        # Convert to regular dict and format sets as lists
        result = {}
        for severity, data in severity_analysis.items():
            result[severity] = {
                "count": data["count"],
                "files_affected": len(data["files"]),
                "agents": list(data["agents"]),
                "types": dict(data["types"]),
            }
        
        return result
    
    def _analyze_by_agent(self, findings: List[AggregatedFinding]) -> Dict[str, Any]:
        """Analyze findings grouped by source agent."""
        agent_analysis = defaultdict(lambda: {
            "total_findings": 0,
            "severity_breakdown": defaultdict(int),
            "finding_types": defaultdict(int),
            "files_affected": set(),
        })
        
        for finding in findings:
            agent_data = agent_analysis[finding.source_agent]
            agent_data["total_findings"] += 1
            agent_data["severity_breakdown"][finding.severity.upper()] += 1
            agent_data["finding_types"][finding.finding_type] += 1
            agent_data["files_affected"].add(finding.file_path)
        
        # Convert to regular dict and format sets as counts
        result = {}
        for agent, data in agent_analysis.items():
            result[agent] = {
                "total_findings": data["total_findings"],
                "severity_breakdown": dict(data["severity_breakdown"]),
                "finding_types": dict(data["finding_types"]),
                "files_affected": len(data["files_affected"]),
            }
        
        return result
    
    def _generate_recommendations(self, findings: List[AggregatedFinding]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on findings."""
        recommendations = []
        
        # Count findings by type and severity
        critical_findings = [f for f in findings if f.severity.upper() in ["CRITICAL", "ERROR"]]
        security_findings = [f for f in findings if f.finding_type in ["vulnerability", "security"]]
        
        if critical_findings:
            recommendations.append({
                "priority": "HIGH",
                "category": "Critical Issues",
                "description": f"Address {len(critical_findings)} critical findings immediately",
                "action": "Review and fix critical security vulnerabilities and errors",
                "affected_files": len(set(f.file_path for f in critical_findings)),
            })
        
        if security_findings:
            recommendations.append({
                "priority": "HIGH",
                "category": "Security",
                "description": f"Review {len(security_findings)} security-related findings",
                "action": "Implement security best practices and update vulnerable dependencies",
                "affected_files": len(set(f.file_path for f in security_findings)),
            })
        
        # File-specific recommendations
        file_findings = defaultdict(list)
        for finding in findings:
            file_findings[finding.file_path].append(finding)
        
        # Find files with many issues
        problematic_files = [
            (file_path, len(file_findings))
            for file_path, file_findings in file_findings.items()
            if len(file_findings) >= 5
        ]
        
        if problematic_files:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Code Quality",
                "description": f"Focus on {len(problematic_files)} files with multiple issues",
                "action": "Refactor files with high issue density",
                "affected_files": len(problematic_files),
            })
        
        return recommendations
    
    def _finding_to_dict(self, finding: AggregatedFinding) -> Dict[str, Any]:
        """Convert AggregatedFinding to dictionary."""
        return {
            "file_path": finding.file_path,
            "line_start": finding.line_start,
            "line_end": finding.line_end,
            "line_range": f"{finding.line_start}-{finding.line_end}" if finding.line_end > finding.line_start else str(finding.line_start),
            "severity": finding.severity,
            "finding_type": finding.finding_type,
            "source_agent": finding.source_agent,
            "description": finding.description,
            "suggestion": finding.suggestion,
            "confidence": finding.confidence,
            "metadata": finding.metadata,
        }
    
    def export_results(self, aggregated_results: Dict[str, Any], output_path: Path, format: str = "json") -> None:
        """
        Export aggregated results to a file.
        
        Args:
            aggregated_results: Results from aggregate_workflow_results
            output_path: Path to save the results
            format: Output format ("json", "yaml", "csv")
        """
        try:
            if format.lower() == "json":
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(aggregated_results, f, indent=2, default=str)
            
            elif format.lower() == "yaml":
                import yaml
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(aggregated_results, f, default_flow_style=False, indent=2)
            
            elif format.lower() == "csv":
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "File", "Line Range", "Severity", "Type", "Agent", "Description", "Suggestion"
                    ])
                    
                    for finding in aggregated_results["findings"]:
                        writer.writerow([
                            finding["file_path"],
                            finding["line_range"],
                            finding["severity"],
                            finding["finding_type"],
                            finding["source_agent"],
                            finding["description"][:100],
                            finding["suggestion"][:100] if finding["suggestion"] else "",
                        ])
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Exported results to {output_path}")
        
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            raise
