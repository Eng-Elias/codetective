"""
Output comment agent for generating review comments.
"""

import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from codetective.agents.base import BaseAgent, AnalysisResult
from codetective.models.workflow_state import WorkflowState
from codetective.models.configuration import AgentConfig
from codetective.models.agent_results import OutputResults
from codetective.utils.result_aggregator import ResultAggregator


class OutputCommentAgent(BaseAgent):
    """
    Output comment agent for generating structured review comments.
    
    This agent aggregates findings from all analysis agents and formats
    them into structured comments that can be used for code review
    platforms or documentation.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the output comment agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(config, "output_comment")
        self.result_aggregator = None
    
    def _initialize(self) -> None:
        """Initialize output comment agent."""
        self.logger.info("Initializing output comment agent")
        self.result_aggregator = ResultAggregator()
    
    async def analyze(self, state: WorkflowState) -> AnalysisResult:
        """
        Generate structured comments from analysis results.
        
        Args:
            state: Current workflow state with analysis results
            
        Returns:
            Analysis result with generated comments
        """
        start_time = time.time()
        
        try:
            # Aggregate all results
            aggregated_results = self.result_aggregator.aggregate_workflow_results(state)
            
            if aggregated_results["summary"].total_findings == 0:
                return AnalysisResult(
                    success=True,
                    data={"results": OutputResults([], "No findings to comment on", "comment").to_dict()},
                    processing_time=time.time() - start_time,
                    metadata={"message": "No findings to generate comments for"}
                )
            
            # Generate comments for each file
            comments = []
            
            # Group findings by file
            findings_by_file = self._group_findings_by_file(aggregated_results)
            
            for file_path, file_findings in findings_by_file.items():
                file_comments = self._generate_file_comments(file_path, file_findings)
                comments.extend(file_comments)
            
            # Generate summary comment
            summary_comment = self._generate_summary_comment(aggregated_results)
            if summary_comment:
                comments.append(summary_comment)
            
            # Create output results
            output_results = OutputResults(
                outputs=comments,
                summary=f"Generated {len(comments)} review comments",
                output_type="comment"
            )
            
            # Update workflow state
            state.output_results = output_results
            
            return AnalysisResult(
                success=True,
                data={"results": output_results.to_dict()},
                processing_time=time.time() - start_time,
                metadata={
                    "comments_generated": len(comments),
                    "files_with_comments": len(findings_by_file),
                    "total_findings": aggregated_results["summary"].total_findings,
                }
            )
        
        except Exception as e:
            error_msg = f"Comment generation failed: {str(e)}"
            self.logger.exception(error_msg)
            
            return AnalysisResult(
                success=False,
                error=error_msg,
                processing_time=time.time() - start_time
            )
    
    def _group_findings_by_file(self, aggregated_results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group findings by file path.
        
        Args:
            aggregated_results: Aggregated results from all agents
            
        Returns:
            Dictionary mapping file paths to their findings
        """
        findings_by_file = {}
        
        # Process Semgrep findings
        if "semgrep" in aggregated_results and aggregated_results["semgrep"]:
            for finding in aggregated_results["semgrep"]:
                file_path = finding.get("path", "unknown")
                if file_path not in findings_by_file:
                    findings_by_file[file_path] = []
                findings_by_file[file_path].append({
                    "source": "semgrep",
                    "type": "static_analysis",
                    "data": finding
                })
        
        # Process Trivy findings
        if "trivy" in aggregated_results and aggregated_results["trivy"]:
            for result in aggregated_results["trivy"]:
                target = result.get("target", "unknown")
                if target not in findings_by_file:
                    findings_by_file[target] = []
                
                for vuln in result.get("vulnerabilities", []):
                    findings_by_file[target].append({
                        "source": "trivy",
                        "type": "vulnerability",
                        "data": vuln
                    })
        
        # Process AI review findings
        if "ai_review" in aggregated_results and aggregated_results["ai_review"]:
            for issue in aggregated_results["ai_review"]:
                file_path = issue.get("file_path", "unknown")
                if file_path not in findings_by_file:
                    findings_by_file[file_path] = []
                findings_by_file[file_path].append({
                    "source": "ai_review",
                    "type": "code_review",
                    "data": issue
                })
        
        return findings_by_file
    
    def _generate_file_comments(self, file_path: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate comments for a specific file.
        
        Args:
            file_path: Path to the file
            findings: List of findings for this file
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        # Group findings by line number for better organization
        findings_by_line = {}
        general_findings = []
        
        for finding in findings:
            line_number = self._extract_line_number(finding)
            if line_number:
                if line_number not in findings_by_line:
                    findings_by_line[line_number] = []
                findings_by_line[line_number].append(finding)
            else:
                general_findings.append(finding)
        
        # Generate line-specific comments
        for line_number, line_findings in sorted(findings_by_line.items()):
            comment = self._create_line_comment(file_path, line_number, line_findings)
            if comment:
                comments.append(comment)
        
        # Generate general file comment if there are general findings
        if general_findings:
            comment = self._create_file_comment(file_path, general_findings)
            if comment:
                comments.append(comment)
        
        return comments
    
    def _extract_line_number(self, finding: Dict[str, Any]) -> Optional[int]:
        """
        Extract line number from a finding.
        
        Args:
            finding: Finding dictionary
            
        Returns:
            Line number or None if not available
        """
        data = finding.get("data", {})
        
        if finding["source"] == "semgrep":
            start = data.get("start", {})
            return start.get("line")
        
        elif finding["source"] == "ai_review":
            return data.get("line_start")
        
        # Trivy findings typically don't have line numbers
        return None
    
    def _create_line_comment(self, file_path: str, line_number: int, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a comment for a specific line.
        
        Args:
            file_path: Path to the file
            line_number: Line number
            findings: Findings for this line
            
        Returns:
            Comment dictionary
        """
        comment_parts = []
        severity_levels = []
        
        for finding in findings:
            source = finding["source"]
            data = finding["data"]
            
            if source == "semgrep":
                message = data.get("message", "Static analysis issue")
                severity = data.get("extra", {}).get("severity", "INFO")
                rule_id = data.get("check_id", "unknown")
                
                comment_parts.append(f"**{source.upper()}** ({severity}): {message}")
                comment_parts.append(f"Rule: `{rule_id}`")
                severity_levels.append(severity)
            
            elif source == "ai_review":
                description = data.get("description", "Code review issue")
                suggestion = data.get("suggestion", "")
                severity = data.get("severity", "medium")
                issue_type = data.get("issue_type", "general")
                
                comment_parts.append(f"**AI REVIEW** ({severity}): {description}")
                if suggestion:
                    comment_parts.append(f"💡 Suggestion: {suggestion}")
                comment_parts.append(f"Category: {issue_type}")
                severity_levels.append(severity)
        
        # Determine overall severity
        overall_severity = self._determine_overall_severity(severity_levels)
        
        return {
            "file_path": file_path,
            "line_number": line_number,
            "severity": overall_severity,
            "content": "\n".join(comment_parts),
            "finding_count": len(findings),
            "sources": [f["source"] for f in findings]
        }
    
    def _create_file_comment(self, file_path: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a general comment for a file.
        
        Args:
            file_path: Path to the file
            findings: General findings for this file
            
        Returns:
            Comment dictionary
        """
        comment_parts = [f"## Security and Quality Issues in {Path(file_path).name}"]
        severity_levels = []
        
        # Group by source
        findings_by_source = {}
        for finding in findings:
            source = finding["source"]
            if source not in findings_by_source:
                findings_by_source[source] = []
            findings_by_source[source].append(finding)
        
        for source, source_findings in findings_by_source.items():
            comment_parts.append(f"\n### {source.upper()} Findings:")
            
            for finding in source_findings:
                data = finding["data"]
                
                if source == "trivy":
                    vuln_id = data.get("vulnerability_id", "unknown")
                    severity = data.get("severity", "UNKNOWN")
                    title = data.get("title", "Vulnerability")
                    pkg_name = data.get("pkg_name", "unknown")
                    
                    comment_parts.append(f"- **{vuln_id}** ({severity}): {title}")
                    comment_parts.append(f"  Package: {pkg_name}")
                    severity_levels.append(severity)
        
        # Determine overall severity
        overall_severity = self._determine_overall_severity(severity_levels)
        
        return {
            "file_path": file_path,
            "line_number": None,
            "severity": overall_severity,
            "content": "\n".join(comment_parts),
            "finding_count": len(findings),
            "sources": list(findings_by_source.keys())
        }
    
    def _generate_summary_comment(self, aggregated_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a summary comment for the entire review.
        
        Args:
            aggregated_results: Aggregated results from all agents
            
        Returns:
            Summary comment dictionary or None
        """
        summary = aggregated_results.get("summary")
        if not summary or summary.total_findings == 0:
            return None
        
        comment_parts = [
            "# Code Review Summary",
            f"**Total Issues Found**: {summary.total_findings}",
            ""
        ]
        
        # Add breakdown by agent
        if summary.semgrep_findings > 0:
            comment_parts.append(f"- **Static Analysis (Semgrep)**: {summary.semgrep_findings} issues")
        
        if summary.trivy_findings > 0:
            comment_parts.append(f"- **Security Scan (Trivy)**: {summary.trivy_findings} vulnerabilities")
        
        if summary.ai_review_findings > 0:
            comment_parts.append(f"- **AI Review**: {summary.ai_review_findings} code quality issues")
        
        # Add severity breakdown if available
        if hasattr(summary, 'severity_breakdown') and summary.severity_breakdown:
            comment_parts.extend([
                "",
                "## Severity Breakdown:"
            ])
            for severity, count in summary.severity_breakdown.items():
                comment_parts.append(f"- **{severity.upper()}**: {count}")
        
        # Add recommendations
        comment_parts.extend([
            "",
            "## Recommendations:",
            "1. Address critical and high severity issues first",
            "2. Review AI suggestions for code quality improvements", 
            "3. Update dependencies to fix security vulnerabilities",
            "4. Consider implementing additional security measures"
        ])
        
        return {
            "file_path": "SUMMARY",
            "line_number": None,
            "severity": "info",
            "content": "\n".join(comment_parts),
            "finding_count": summary.total_findings,
            "sources": ["summary"]
        }
    
    def _determine_overall_severity(self, severity_levels: List[str]) -> str:
        """
        Determine overall severity from a list of individual severities.
        
        Args:
            severity_levels: List of severity strings
            
        Returns:
            Overall severity level
        """
        if not severity_levels:
            return "info"
        
        # Define severity hierarchy
        severity_order = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1,
            "unknown": 1
        }
        
        # Find highest severity
        max_severity = 0
        result_severity = "info"
        
        for severity in severity_levels:
            severity_lower = severity.lower()
            severity_value = severity_order.get(severity_lower, 1)
            if severity_value > max_severity:
                max_severity = severity_value
                result_severity = severity_lower
        
        return result_severity
    
    def get_capabilities(self) -> List[str]:
        """Return list of output comment agent capabilities."""
        return [
            "comment_generation",
            "result_aggregation",
            "severity_analysis",
            "markdown_formatting",
            "multi_source_integration"
        ]
    
    def get_supported_file_extensions(self) -> Optional[List[str]]:
        """Output comment agent supports all file types."""
        return None  # Supports all files
    
    def get_comment_stats(self) -> Dict[str, Any]:
        """Get statistics about comment generation capabilities."""
        return {
            "supported_sources": ["semgrep", "trivy", "ai_review"],
            "comment_types": ["line_specific", "file_general", "summary"],
            "severity_levels": ["critical", "high", "medium", "low", "info"],
        }
