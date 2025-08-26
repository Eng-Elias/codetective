"""
SemGrep agent for static code analysis.
"""

import json
from typing import List
from pathlib import Path

from codetective.models.schemas import AgentType, Issue, SeverityLevel, IssueStatus
from codetective.utils import ProcessUtils, SystemUtils
from codetective.agents.base import ScanAgent
from codetective.utils.system_utils import RequiredTools


class SemGrepAgent(ScanAgent):
    """Agent for running SemGrep static analysis."""
    
    def __init__(self, config):
        super().__init__(config)
        self.agent_type = AgentType.SEMGREP
    
    def is_available(self) -> bool:
        """Check if SemGrep is available."""
        available, _ = SystemUtils.check_tool_availability(RequiredTools.SEMGREP)
        return available
    
    def scan_files(self, files: List[str]) -> List[Issue]:
        """Scan files using SemGrep."""
        issues = []

        if not files:
            # Default to current directory
            try:
                issues = self._scan_directory(".")
            except Exception as e:
                print(f"Error scanning current directory: {e}")
            return issues

        # Separate files and directories
        individual_files = []
        directories = []
        
        for path in files:
            path_obj = Path(path)
            if path_obj.is_file():
                individual_files.append(path)
            elif path_obj.is_dir():
                directories.append(path)
            elif path_obj.exists():
                print(f"Warning: Path exists but is neither file nor directory: {path}")
            else:
                print(f"Warning: Path does not exist: {path}")

        # Scan all individual files in one batch command
        if individual_files:
            try:
                batch_issues = self._scan_files_batch(individual_files)
                issues.extend(batch_issues)
            except Exception as e:
                print(f"Error scanning individual files: {e}")

        # Scan directories
        for dir_path in directories:
            try:
                dir_issues = self._scan_directory(dir_path)
                issues.extend(dir_issues)
            except Exception as e:
                print(f"Error scanning directory {dir_path}: {e}")
                continue

        return issues
    
    def _scan_single_file(self, file_path: str) -> List[Issue]:
        """Scan a single file with SemGrep."""
        try:
            # Run SemGrep on a single file
            cmd = [
                "semgrep",
                "--config=r/all",
                "--json",
                "--metrics=off",
                "--timeout", str(self.config.agent_timeout),
                file_path
            ]
            
            success, stdout, stderr = ProcessUtils.run_command(cmd, timeout=self.config.agent_timeout)
            
            if not success:
                print(f"SemGrep failed for {file_path}: {stderr}")
                return []
            
            # Parse SemGrep JSON output
            if stdout.strip():
                semgrep_data = json.loads(stdout)
                return self._parse_semgrep_results(semgrep_data)
            
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
        
        return []
    
    def _scan_files_batch(self, file_paths: List[str]) -> List[Issue]:
        """Scan multiple individual files in a single SemGrep command for efficiency."""
        try:
            # Run SemGrep on multiple files at once
            cmd = [
                "semgrep",
                "--config=r/all",
                "--json",
                "--metrics=off",
                "--timeout", str(self.config.agent_timeout)
            ]
            # Add all file paths to the command
            cmd.extend(file_paths)
            
            success, stdout, stderr = ProcessUtils.run_command(cmd, timeout=self.config.agent_timeout)
            
            if not success:
                print(f"SemGrep batch scan failed: {stderr}")
                return []
            
            # Parse SemGrep JSON output
            if stdout.strip():
                semgrep_data = json.loads(stdout)
                return self._parse_semgrep_results(semgrep_data)
            
        except Exception as e:
            print(f"Error in batch file scanning: {e}")
        
        return []
    
    def _scan_directory(self, scan_path: str) -> List[Issue]:
        """Scan a directory with SemGrep."""
        try:
            # Run SemGrep with the exact command that works: semgrep --config=r/all
            cmd = [
                "semgrep",
                "--config=r/all",
                "--json",
                "--metrics=off",
                "--timeout", str(self.config.agent_timeout),
                scan_path
            ]
            
            success, stdout, stderr = ProcessUtils.run_command(cmd, timeout=self.config.agent_timeout)

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
                print(f"Error parsing SemGrep result: {e}")
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
