"""
Trivy agent for vulnerability scanning.
"""

import json
import subprocess
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import time

from codetective.agents.base import BaseAgent, AnalysisResult
from codetective.models.workflow_state import WorkflowState
from codetective.models.configuration import TrivyConfig
from codetective.models.agent_results import TrivyResults, TrivyResult, TrivyVulnerability


class TrivyAgent(BaseAgent):
    """
    Trivy agent for vulnerability scanning.
    
    This agent runs Trivy security scanner to identify vulnerabilities
    in dependencies, container images, and configuration files.
    """
    
    def __init__(self, config: TrivyConfig):
        """
        Initialize the Trivy agent.
        
        Args:
            config: Trivy-specific configuration
        """
        super().__init__(config, "trivy")
        self.trivy_config = config
        
        # Verify Trivy is available
        self._verify_trivy_installation()
    
    def _initialize(self) -> None:
        """Initialize Trivy-specific setup."""
        self.logger.info("Initializing Trivy agent")
        
        # Set default scan types if none specified
        if not self.trivy_config.scan_types:
            self.trivy_config.scan_types = ["vuln"]
            self.logger.info("Using default vulnerability scanning")
    
    def _verify_trivy_installation(self) -> None:
        """Verify that Trivy is installed and accessible."""
        try:
            result = subprocess.run(
                ["trivy", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logger.info(f"Trivy version: {version}")
            else:
                raise RuntimeError("Trivy version check failed")
        
        except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError) as e:
            error_msg = f"Trivy is not installed or not accessible: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def analyze(self, state: WorkflowState) -> AnalysisResult:
        """
        Perform Trivy vulnerability scanning.
        
        Args:
            state: Current workflow state
            
        Returns:
            Analysis result with Trivy findings
        """
        start_time = time.time()
        
        try:
            # Determine scan targets
            scan_targets = self._determine_scan_targets(state.target_files)
            if not scan_targets:
                return AnalysisResult(
                    success=True,
                    data={"results": TrivyResults(2, "no-targets", "filesystem", {}, []).to_dict()},
                    processing_time=time.time() - start_time,
                    metadata={"message": "No valid targets for Trivy scanning"}
                )
            
            # Run Trivy scans
            all_results = []
            for target in scan_targets:
                result = await self._scan_target(target)
                if result:
                    all_results.extend(result.results)
            
            # Create combined results
            trivy_results = TrivyResults(
                schema_version=2,
                artifact_name=str(scan_targets[0]) if scan_targets else "unknown",
                artifact_type="filesystem",
                metadata={"scan_targets": [str(t) for t in scan_targets]},
                results=all_results
            )
            
            processing_time = time.time() - start_time
            
            # Update workflow state
            state.trivy_results = trivy_results
            
            return AnalysisResult(
                success=True,
                data={"results": trivy_results.to_dict()},
                processing_time=processing_time,
                metadata={
                    "targets_scanned": len(scan_targets),
                    "vulnerabilities_found": len(trivy_results.get_all_vulnerabilities()),
                    "scan_types": self.trivy_config.scan_types,
                }
            )
        
        except Exception as e:
            error_msg = f"Trivy analysis failed: {str(e)}"
            self.logger.exception(error_msg)
            
            return AnalysisResult(
                success=False,
                error=error_msg,
                processing_time=time.time() - start_time
            )
    
    def _determine_scan_targets(self, files: List[Path]) -> List[Path]:
        """
        Determine appropriate scan targets for Trivy.
        
        Args:
            files: List of input files
            
        Returns:
            List of scan targets (directories or specific files)
        """
        targets = []
        
        # Look for common dependency files
        dependency_files = [
            "requirements.txt", "Pipfile", "pyproject.toml", "setup.py",
            "package.json", "package-lock.json", "yarn.lock",
            "Gemfile", "Gemfile.lock",
            "pom.xml", "build.gradle", "gradle.lockfile",
            "go.mod", "go.sum",
            "Cargo.toml", "Cargo.lock",
            "composer.json", "composer.lock"
        ]
        
        # Check for dependency files in the file list
        for file_path in files:
            if file_path.name in dependency_files:
                targets.append(file_path.parent)
                break
        
        # If no dependency files found, use parent directories
        if not targets:
            directories = set()
            for file_path in files:
                directories.add(file_path.parent)
            
            # Limit to avoid scanning too many directories
            targets = list(directories)[:5]
        
        self.logger.info(f"Determined scan targets: {[str(t) for t in targets]}")
        return targets
    
    async def _scan_target(self, target: Path) -> Optional[TrivyResults]:
        """
        Scan a specific target with Trivy.
        
        Args:
            target: Target path to scan
            
        Returns:
            Trivy results or None if scan failed
        """
        try:
            # Build Trivy command
            cmd = self._build_trivy_command(target)
            self.logger.info(f"Running Trivy command: {' '.join(cmd)}")
            
            # Execute Trivy
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target.parent if target.is_file() else target
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse results
            return self._parse_trivy_output(
                stdout.decode('utf-8'),
                stderr.decode('utf-8'),
                process.returncode,
                target
            )
        
        except Exception as e:
            self.logger.error(f"Failed to scan target {target}: {e}")
            return None
    
    def _build_trivy_command(self, target: Path) -> List[str]:
        """
        Build Trivy command with appropriate arguments.
        
        Args:
            target: Target to scan
            
        Returns:
            Command arguments list
        """
        cmd = ["trivy"]
        
        # Determine scan type based on target
        if target.is_file():
            cmd.append("fs")
        else:
            cmd.append("fs")
        
        # Add configuration-based arguments
        cmd.extend(self.trivy_config.get_cli_args())
        
        # Add target
        cmd.append(str(target))
        
        return cmd
    
    def _parse_trivy_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        target: Path
    ) -> Optional[TrivyResults]:
        """
        Parse Trivy JSON output into structured results.
        
        Args:
            stdout: Standard output from Trivy
            stderr: Standard error from Trivy
            return_code: Process return code
            target: Scanned target
            
        Returns:
            Parsed Trivy results or None if parsing failed
        """
        try:
            if not stdout.strip():
                self.logger.warning(f"No output from Trivy for target: {target}")
                return None
            
            # Parse JSON output
            output_data = json.loads(stdout)
            
            # Handle different Trivy output formats
            if "Results" in output_data:
                # New format with Results array
                results = []
                for result_data in output_data["Results"]:
                    result = self._parse_trivy_result(result_data)
                    if result:
                        results.append(result)
                
                return TrivyResults(
                    schema_version=output_data.get("SchemaVersion", 2),
                    artifact_name=output_data.get("ArtifactName", str(target)),
                    artifact_type=output_data.get("ArtifactType", "filesystem"),
                    metadata=output_data.get("Metadata", {}),
                    results=results
                )
            
            elif isinstance(output_data, list):
                # Legacy format - direct list of results
                results = []
                for result_data in output_data:
                    result = self._parse_trivy_result(result_data)
                    if result:
                        results.append(result)
                
                return TrivyResults(
                    schema_version=2,
                    artifact_name=str(target),
                    artifact_type="filesystem",
                    metadata={},
                    results=results
                )
            
            else:
                self.logger.warning(f"Unexpected Trivy output format for {target}")
                return None
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Trivy JSON output: {e}")
            return None
        
        except Exception as e:
            self.logger.error(f"Unexpected error parsing Trivy output: {e}")
            return None
    
    def _parse_trivy_result(self, result_data: Dict[str, Any]) -> Optional[TrivyResult]:
        """
        Parse individual Trivy result from JSON data.
        
        Args:
            result_data: JSON data for a single result
            
        Returns:
            Parsed TrivyResult or None if parsing fails
        """
        try:
            target = result_data.get("Target", "unknown")
            class_type = result_data.get("Class", "unknown")
            result_type = result_data.get("Type", "unknown")
            
            vulnerabilities = []
            vuln_data = result_data.get("Vulnerabilities", [])
            
            if vuln_data:
                for vuln in vuln_data:
                    vulnerability = self._parse_trivy_vulnerability(vuln)
                    if vulnerability:
                        vulnerabilities.append(vulnerability)
            
            return TrivyResult(
                target=target,
                class_type=class_type,
                type=result_type,
                vulnerabilities=vulnerabilities
            )
        
        except Exception as e:
            self.logger.warning(f"Failed to parse Trivy result: {e}")
            return None
    
    def _parse_trivy_vulnerability(self, vuln_data: Dict[str, Any]) -> Optional[TrivyVulnerability]:
        """
        Parse individual Trivy vulnerability from JSON data.
        
        Args:
            vuln_data: JSON data for a single vulnerability
            
        Returns:
            Parsed TrivyVulnerability or None if parsing fails
        """
        try:
            vulnerability_id = vuln_data.get("VulnerabilityID", "unknown")
            pkg_name = vuln_data.get("PkgName", "unknown")
            installed_version = vuln_data.get("InstalledVersion", "unknown")
            fixed_version = vuln_data.get("FixedVersion")
            severity = vuln_data.get("Severity", "UNKNOWN")
            title = vuln_data.get("Title", "No title")
            description = vuln_data.get("Description", "No description")
            references = vuln_data.get("References", [])
            
            return TrivyVulnerability(
                vulnerability_id=vulnerability_id,
                pkg_name=pkg_name,
                installed_version=installed_version,
                fixed_version=fixed_version,
                severity=severity,
                title=title,
                description=description,
                references=references
            )
        
        except Exception as e:
            self.logger.warning(f"Failed to parse Trivy vulnerability: {e}")
            return None
    
    def get_capabilities(self) -> List[str]:
        """Return list of Trivy agent capabilities."""
        return [
            "vulnerability_scanning",
            "dependency_analysis",
            "container_scanning",
            "configuration_scanning",
            "license_scanning",
            "secret_detection"
        ]
    
    def get_supported_file_extensions(self) -> Optional[List[str]]:
        """Get list of file extensions supported by Trivy."""
        return [
            # Python
            "requirements.txt", "Pipfile", "pyproject.toml", "setup.py",
            # JavaScript/Node.js
            "package.json", "package-lock.json", "yarn.lock",
            # Ruby
            "Gemfile", "Gemfile.lock",
            # Java
            "pom.xml", "build.gradle", "gradle.lockfile",
            # Go
            "go.mod", "go.sum",
            # Rust
            "Cargo.toml", "Cargo.lock",
            # PHP
            "composer.json", "composer.lock",
            # Docker
            "Dockerfile",
            # Kubernetes
            ".yaml", ".yml"
        ]
    
    def get_scan_info(self) -> Dict[str, Any]:
        """Get information about configured scan types."""
        return {
            "scan_types": self.trivy_config.scan_types,
            "severity_filter": self.trivy_config.severity_filter,
            "ignore_unfixed": self.trivy_config.ignore_unfixed,
        }
