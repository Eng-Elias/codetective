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

        scan_path = "."
        if files:
            scan_path = " ".join(files)

        try:
            # Run SemGrep with the exact command that works: semgrep --config=r/all
            cmd = [
                "semgrep",
                "--config=r/all",
                "--json",
                "--timeout", "60",  # SemGrep internal timeout
                scan_path
            ]
            
            # Use shorter timeout and set working directory
            timeout = min(self.config.agent_timeout, 90)  # Max 90 seconds
            success, stdout, stderr = run_command(cmd, timeout=timeout)

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
    
    def _prepare_scan_paths(self, files: List[str]) -> List[str]:
        """Prepare paths for SemGrep scanning to avoid filename length issues."""
        scan_paths = []
        processed_dirs = set()
        
        for file_path in files:
            path = Path(file_path)
            
            if path.is_dir():
                # Use directory directly
                if str(path) not in processed_dirs:
                    scan_paths.append(str(path))
                    processed_dirs.add(str(path))
            else:
                # For individual files, use the parent directory
                parent_dir = path.parent
                if str(parent_dir) not in processed_dirs:
                    scan_paths.append(str(parent_dir))
                    processed_dirs.add(str(parent_dir))
        
        return scan_paths
    
    def _parse_semgrep_results(self, semgrep_data: dict) -> List[Issue]:
        """Parse SemGrep JSON results into Issue objects."""
        issues = []
        
        results = semgrep_data.get("results", [])
        
        for result in results:
            try:
                # Extract issue information
                rule_id = result.get("check_id", "unknown")
                message = result.get("extra", {}).get("message", "SemGrep finding")
                severity = self._map_severity(result.get("extra", {}).get("severity", "INFO"))
                
                # File and location information
                file_path = result.get("path", "")
                start_line = result.get("start", {}).get("line", 1)
                
                # Create fix suggestion from SemGrep autofix if available
                fix_suggestion = None
                if "references" in result.get("extra", {}).get("metadata", {}):
                    fix_suggestion = ", ".join(result["extra"]["metadata"]["references"])
                
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
