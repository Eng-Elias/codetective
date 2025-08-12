"""
SemGrep agent for static code analysis.
"""

import json
import subprocess
from typing import List
from pathlib import Path

from ...models.schemas import AgentType, Issue, SeverityLevel, IssueStatus
from ...core.utils import run_command, check_tool_availability
from ..base import ScanAgent


class SemGrepAgent(ScanAgent):
    """Agent for running SemGrep static analysis."""
    
    def __init__(self, config):
        super().__init__(config)
        self.agent_type = AgentType.SEMGREP
    
    def is_available(self) -> bool:
        """Check if SemGrep is available."""
        available, _ = check_tool_availability("semgrep")
        return available
    
    def scan_files(self, files: List[str]) -> List[Issue]:
        """Scan files using SemGrep."""
        issues = []
        
        # Get supported files (common programming languages)
        supported_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh',
            '.yaml', '.yml', '.json', '.xml', '.html', '.css', '.sql'
        ]
        
        supported_files = self._get_supported_files(files, supported_extensions)
        
        if not supported_files:
            return issues
        
        try:
            # Run SemGrep with JSON output
            cmd = [
                "semgrep",
                "--config=auto",  # Use automatic rule selection
                "--json",
                "--no-git-ignore",
                "--timeout", str(self.config.agent_timeout)
            ] + supported_files
            
            success, stdout, stderr = run_command(cmd, timeout=self.config.agent_timeout)
            
            if not success:
                raise Exception(f"SemGrep execution failed: {stderr}")
            
            # Parse SemGrep JSON output
            if stdout.strip():
                semgrep_data = json.loads(stdout)
                issues = self._parse_semgrep_results(semgrep_data)
        
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse SemGrep JSON output: {e}")
        except Exception as e:
            raise Exception(f"SemGrep scan failed: {e}")
        
        return issues
    
    def _parse_semgrep_results(self, semgrep_data: dict) -> List[Issue]:
        """Parse SemGrep JSON results into Issue objects."""
        issues = []
        
        results = semgrep_data.get("results", [])
        
        for result in results:
            try:
                # Extract issue information
                rule_id = result.get("check_id", "unknown")
                message = result.get("message", "SemGrep finding")
                severity = self._map_severity(result.get("extra", {}).get("severity", "INFO"))
                
                # File and location information
                file_path = result.get("path", "")
                start_line = result.get("start", {}).get("line", 1)
                
                # Create fix suggestion from SemGrep autofix if available
                fix_suggestion = None
                if "fix" in result.get("extra", {}):
                    fix_suggestion = result["extra"]["fix"]
                elif "autofix" in result.get("extra", {}):
                    fix_suggestion = result["extra"]["autofix"].get("fix", "")
                
                issue = Issue(
                    id=f"semgrep-{rule_id}-{file_path}-{start_line}",
                    title=f"SemGrep: {rule_id}",
                    description=message,
                    severity=severity,
                    file_path=file_path,
                    line_number=start_line,
                    rule_id=rule_id,
                    fix_suggestion=fix_suggestion,
                    status=IssueStatus.DETECTED
                )
                
                issues.append(issue)
            
            except Exception as e:
                # Log parsing error but continue with other results
                continue
        
        return issues
    
    def _map_severity(self, semgrep_severity: str) -> SeverityLevel:
        """Map SemGrep severity to our severity levels."""
        severity_map = {
            "ERROR": SeverityLevel.HIGH,
            "WARNING": SeverityLevel.MEDIUM,
            "INFO": SeverityLevel.LOW,
            "EXPERIMENT": SeverityLevel.LOW
        }
        
        return severity_map.get(semgrep_severity.upper(), SeverityLevel.MEDIUM)
