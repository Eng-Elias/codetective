"""
Trivy agent for security vulnerability scanning.
"""

import json
from typing import List
from pathlib import Path

from codetective.models.schemas import AgentType, Issue, SeverityLevel, IssueStatus
from codetective.utils import ProcessUtils, SystemUtils
from codetective.agents.base import ScanAgent
from codetective.utils.system_utils import RequiredTools


class TrivyAgent(ScanAgent):
    """Agent for running Trivy security vulnerability scanning."""
    
    def __init__(self, config):
        super().__init__(config)
        self.agent_type = AgentType.TRIVY
    
    def is_available(self) -> bool:
        """Check if Trivy is available."""
        available, _ = SystemUtils.check_tool_availability(RequiredTools.TRIVY)
        return available
    
    def scan_files(self, files: List[str]) -> List[Issue]:
        """Scan files using Trivy."""
        issues = []
        
        # Trivy works best on directories and specific file types
        paths_to_scan = self._prepare_scan_paths(files)
        
        for scan_path in paths_to_scan:
            try:
                # Run Trivy filesystem scan
                cmd = [
                    "trivy",
                    "fs",
                    "--format", "json",
                    "--scanners", "vuln,misconfig,secret,license",
                    "--timeout", f"{self.config.agent_timeout}s",
                    scan_path
                ]
                
                success, stdout, stderr = ProcessUtils.run_command(cmd, timeout=self.config.agent_timeout)
                
                if not success:
                    # Trivy might still produce useful output even with non-zero exit
                    if not stdout.strip():
                        continue
                
                # Parse Trivy JSON output
                if stdout.strip():
                    trivy_data = json.loads(stdout)
                    path_issues = self._parse_trivy_results(trivy_data, scan_path)
                    issues.extend(path_issues)
            
            except json.JSONDecodeError as e:
                # Log parsing error but continue with other paths
                continue
            except Exception as e:
                # Log scan error but continue with other paths
                continue
        
        return issues
    
    def _prepare_scan_paths(self, files: List[str]) -> List[str]:
        """Prepare paths for Trivy scanning."""
        paths_to_scan = []
        processed_dirs = set()
        
        for file_path in files:
            path = Path(file_path)
            
            if path.is_dir():
                if str(path) not in processed_dirs:
                    paths_to_scan.append(str(path))
                    processed_dirs.add(str(path))
            else:
                # For individual files, scan the parent directory if not already processed
                parent_dir = path.parent
                if str(parent_dir) not in processed_dirs:
                    paths_to_scan.append(str(parent_dir))
                    processed_dirs.add(str(parent_dir))
        
        return paths_to_scan
    
    def _parse_trivy_results(self, trivy_data: dict, scan_path: str) -> List[Issue]:
        """Parse Trivy JSON results into Issue objects."""
        issues = []
        
        results = trivy_data.get("Results", [])
        
        for result in results:
            target = result.get("Target", scan_path)
            
            # Process vulnerabilities
            vulnerabilities = result.get("Vulnerabilities", [])
            for vuln in vulnerabilities:
                issue = self._create_vulnerability_issue(vuln, target)
                if issue:
                    issues.append(issue)
            
            # Process secrets
            secrets = result.get("Secrets", [])
            for secret in secrets:
                issue = self._create_secret_issue(secret, target)
                if issue:
                    issues.append(issue)
            
            # Process misconfigurations
            misconfigs = result.get("Misconfigurations", [])
            for misconfig in misconfigs:
                issue = self._create_misconfig_issue(misconfig, target)
                if issue:
                    issues.append(issue)
        
        return issues
    
    def _create_vulnerability_issue(self, vuln: dict, target: str) -> Issue:
        """Create an Issue from a Trivy vulnerability."""
        try:
            vuln_id = vuln.get("VulnerabilityID", "unknown")
            pkg_name = vuln.get("PkgName", "unknown")
            title = vuln.get("Title", f"Vulnerability in {pkg_name}")
            description = vuln.get("Description", "No description available")
            severity = self._map_severity(vuln.get("Severity", "UNKNOWN"))
            
            # Create fix suggestion
            fix_suggestion = None
            fixed_version = vuln.get("FixedVersion", "")
            if fixed_version:
                fix_suggestion = f"Update {pkg_name} to version {fixed_version}"
            
            return Issue(
                id=f"trivy-vuln-{vuln_id}-{pkg_name}",
                title=f"Vulnerability: {title}",
                description=f"{description}\nPackage: {pkg_name}\nVulnerability ID: {vuln_id}",
                severity=severity,
                file_path=target,
                line_number=None,
                rule_id=vuln_id,
                fix_suggestion=fix_suggestion,
                status=IssueStatus.DETECTED
            )
        except Exception:
            return None
    
    def _create_secret_issue(self, secret: dict, target: str) -> Issue:
        """Create an Issue from a Trivy secret detection."""
        try:
            rule_id = secret.get("RuleID", "unknown")
            title = secret.get("Title", "Secret detected")
            severity = self._map_severity(secret.get("Severity", "HIGH"))
            start_line = secret.get("StartLine", 1)
            
            return Issue(
                id=f"trivy-secret-{rule_id}-{target}-{start_line}",
                title=f"Secret: {title}",
                description=f"Potential secret detected: {title}",
                severity=severity,
                file_path=target,
                line_number=start_line,
                rule_id=rule_id,
                fix_suggestion="Remove or encrypt the detected secret",
                status=IssueStatus.DETECTED
            )
        except Exception:
            return None
    
    def _create_misconfig_issue(self, misconfig: dict, target: str) -> Issue:
        """Create an Issue from a Trivy misconfiguration."""
        try:
            rule_id = misconfig.get("ID", "unknown")
            title = misconfig.get("Title", "Configuration issue")
            description = misconfig.get("Description", "No description available")
            severity = self._map_severity(misconfig.get("Severity", "MEDIUM"))
            start_line = misconfig.get("CauseMetadata", {}).get("StartLine", 1)
            
            return Issue(
                id=f"trivy-config-{rule_id}-{target}-{start_line}",
                title=f"Config: {title}",
                description=description,
                severity=severity,
                file_path=target,
                line_number=start_line,
                rule_id=rule_id,
                fix_suggestion="Review and fix the configuration issue",
                status=IssueStatus.DETECTED
            )
        except Exception:
            return None
    
    def _map_severity(self, trivy_severity: str) -> SeverityLevel:
        """Map Trivy severity to our severity levels."""
        severity_map = {
            "CRITICAL": SeverityLevel.CRITICAL,
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW,
            "UNKNOWN": SeverityLevel.LOW
        }
        
        return severity_map.get(trivy_severity.upper(), SeverityLevel.MEDIUM)
