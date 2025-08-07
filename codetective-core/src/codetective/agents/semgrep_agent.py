"""
Semgrep agent for static code analysis.
"""

import json
import subprocess
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import time

from codetective.agents.base import BaseAgent, AnalysisResult
from codetective.models.workflow_state import WorkflowState
from codetective.models.configuration import SemgrepConfig
from codetective.models.agent_results import SemgrepResults, SemgrepFinding


class SemgrepAgent(BaseAgent):
    """
    Semgrep agent for static code analysis.
    
    This agent runs Semgrep static analysis tool to identify bugs,
    security issues, and code quality problems.
    """
    
    def __init__(self, config: SemgrepConfig):
        """
        Initialize the Semgrep agent.
        
        Args:
            config: Semgrep-specific configuration
        """
        super().__init__(config, "semgrep")
        self.semgrep_config = config
        
        # Verify Semgrep is available
        self._verify_semgrep_installation()
    
    def _initialize(self) -> None:
        """Initialize Semgrep-specific setup."""
        self.logger.info("Initializing Semgrep agent")
        
        # Set default rules if none specified
        if not self.semgrep_config.rules and not self.semgrep_config.config_path:
            self.semgrep_config.rules = ["auto"]
            self.logger.info("Using default 'auto' ruleset")
    
    def _verify_semgrep_installation(self) -> None:
        """Verify that Semgrep is installed and accessible."""
        try:
            result = subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logger.info(f"Semgrep version: {version}")
            else:
                raise RuntimeError("Semgrep version check failed")
        
        except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError) as e:
            error_msg = f"Semgrep is not installed or not accessible: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def analyze(self, state: WorkflowState) -> AnalysisResult:
        """
        Perform Semgrep static analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Analysis result with Semgrep findings
        """
        start_time = time.time()
        
        try:
            # Validate input files
            valid_files = self.validate_input_files(state.target_files)
            if not valid_files:
                return AnalysisResult(
                    success=True,
                    data={"results": SemgrepResults([], [], {}, "unknown").to_dict()},
                    processing_time=time.time() - start_time,
                    metadata={"message": "No valid files for Semgrep analysis"}
                )
            
            # Build Semgrep command
            cmd = self._build_semgrep_command(valid_files)
            self.logger.info(f"Running Semgrep command: {' '.join(cmd)}")
            
            # Execute Semgrep
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=valid_files[0].parent if valid_files else Path.cwd()
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse results
            results = self._parse_semgrep_output(
                stdout.decode('utf-8'),
                stderr.decode('utf-8'),
                process.returncode
            )
            
            processing_time = time.time() - start_time
            
            # Update workflow state
            state.semgrep_results = results
            
            return AnalysisResult(
                success=True,
                data={"results": results.to_dict()},
                processing_time=processing_time,
                metadata={
                    "files_analyzed": len(valid_files),
                    "findings_count": len(results.findings),
                    "errors_count": len(results.errors),
                }
            )
        
        except Exception as e:
            error_msg = f"Semgrep analysis failed: {str(e)}"
            self.logger.exception(error_msg)
            
            return AnalysisResult(
                success=False,
                error=error_msg,
                processing_time=time.time() - start_time
            )
    
    def _build_semgrep_command(self, files: List[Path]) -> List[str]:
        """
        Build Semgrep command with appropriate arguments.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Command arguments list
        """
        cmd = ["semgrep"]
        
        # Add configuration-based arguments
        cmd.extend(self.semgrep_config.get_cli_args())
        
        # Add target files or directories
        if len(files) == 1 and files[0].is_dir():
            cmd.append(str(files[0]))
        else:
            # Find common parent directory to avoid long command lines
            if len(files) > 10:
                # Use parent directory and let Semgrep filter
                common_parent = self._find_common_parent(files)
                cmd.append(str(common_parent))
            else:
                # Add individual files
                cmd.extend(str(f) for f in files)
        
        return cmd
    
    def _find_common_parent(self, files: List[Path]) -> Path:
        """Find the common parent directory of a list of files."""
        if not files:
            return Path.cwd()
        
        common_parts = files[0].parts
        
        for file_path in files[1:]:
            file_parts = file_path.parts
            common_parts = common_parts[:len(file_parts)]
            
            for i, (part1, part2) in enumerate(zip(common_parts, file_parts)):
                if part1 != part2:
                    common_parts = common_parts[:i]
                    break
        
        return Path(*common_parts) if common_parts else Path.cwd()
    
    def _parse_semgrep_output(self, stdout: str, stderr: str, return_code: int) -> SemgrepResults:
        """
        Parse Semgrep JSON output into structured results.
        
        Args:
            stdout: Standard output from Semgrep
            stderr: Standard error from Semgrep
            return_code: Process return code
            
        Returns:
            Parsed Semgrep results
        """
        findings = []
        errors = []
        stats = {}
        version = "unknown"
        
        try:
            if stdout.strip():
                # Parse JSON output
                output_data = json.loads(stdout)
                
                # Extract results based on Semgrep output format
                if "results" in output_data:
                    # New format
                    for result in output_data["results"]:
                        finding = self._parse_semgrep_finding(result)
                        if finding:
                            findings.append(finding)
                    
                    # Extract metadata
                    if "errors" in output_data:
                        errors = [error.get("message", str(error)) for error in output_data["errors"]]
                    
                    if "paths" in output_data:
                        stats["files_scanned"] = len(output_data["paths"]["scanned"])
                    
                    version = output_data.get("version", "unknown")
                
                elif isinstance(output_data, list):
                    # Legacy format - direct list of findings
                    for result in output_data:
                        finding = self._parse_semgrep_finding(result)
                        if finding:
                            findings.append(finding)
            
            # Parse stderr for additional errors
            if stderr.strip():
                stderr_lines = stderr.strip().split('\n')
                for line in stderr_lines:
                    if line and not line.startswith("Scanning"):
                        errors.append(line)
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Semgrep JSON output: {e}")
            errors.append(f"JSON parsing error: {e}")
            
            # Try to extract any useful information from stdout
            if stdout.strip():
                errors.append(f"Raw output: {stdout[:500]}...")
        
        except Exception as e:
            self.logger.error(f"Unexpected error parsing Semgrep output: {e}")
            errors.append(f"Parsing error: {e}")
        
        # Add return code information
        if return_code != 0:
            errors.append(f"Semgrep exited with code {return_code}")
        
        stats.update({
            "return_code": return_code,
            "findings_count": len(findings),
            "errors_count": len(errors),
        })
        
        return SemgrepResults(
            findings=findings,
            errors=errors,
            stats=stats,
            version=version
        )
    
    def _parse_semgrep_finding(self, result_data: Dict[str, Any]) -> Optional[SemgrepFinding]:
        """
        Parse individual Semgrep finding from JSON data.
        
        Args:
            result_data: JSON data for a single finding
            
        Returns:
            Parsed SemgrepFinding or None if parsing fails
        """
        try:
            # Extract required fields
            check_id = result_data.get("check_id", "unknown")
            path = result_data.get("path", "unknown")
            message = result_data.get("message", "No message")
            
            # Extract position information
            start_info = result_data.get("start", {})
            end_info = result_data.get("end", {})
            
            start = {
                "line": start_info.get("line", 0),
                "col": start_info.get("col", 0)
            }
            
            end = {
                "line": end_info.get("line", 0),
                "col": end_info.get("col", 0)
            }
            
            # Map Semgrep severity to standard levels
            severity_map = {
                "ERROR": "ERROR",
                "WARNING": "WARNING", 
                "INFO": "INFO",
                "error": "ERROR",
                "warning": "WARNING",
                "info": "INFO"
            }
            
            raw_severity = result_data.get("extra", {}).get("severity", "INFO")
            severity = severity_map.get(raw_severity, "INFO")
            
            # Extract metadata and extra information
            metadata = result_data.get("extra", {}).get("metadata", {})
            extra = result_data.get("extra", {})
            
            return SemgrepFinding(
                check_id=check_id,
                path=path,
                start=start,
                end=end,
                message=message,
                severity=severity,
                metadata=metadata,
                extra=extra
            )
        
        except Exception as e:
            self.logger.warning(f"Failed to parse Semgrep finding: {e}")
            self.logger.debug(f"Raw finding data: {result_data}")
            return None
    
    def get_capabilities(self) -> List[str]:
        """Return list of Semgrep agent capabilities."""
        return [
            "static_analysis",
            "security_scanning",
            "bug_detection",
            "code_quality",
            "custom_rules",
            "multiple_languages"
        ]
    
    def get_supported_file_extensions(self) -> Optional[List[str]]:
        """Get list of file extensions supported by Semgrep."""
        return [
            # Python
            ".py", ".pyi",
            # JavaScript/TypeScript
            ".js", ".jsx", ".ts", ".tsx", ".mjs",
            # Java
            ".java",
            # C/C++
            ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
            # C#
            ".cs",
            # Go
            ".go",
            # Rust
            ".rs",
            # Ruby
            ".rb",
            # PHP
            ".php",
            # Shell
            ".sh", ".bash",
            # YAML/JSON
            ".yaml", ".yml", ".json",
            # Docker
            "Dockerfile",
        ]
    
    def get_rule_info(self) -> Dict[str, Any]:
        """Get information about configured rules."""
        return {
            "rules": self.semgrep_config.rules,
            "exclude_rules": self.semgrep_config.exclude_rules,
            "config_path": self.semgrep_config.config_path,
            "severity_filter": self.semgrep_config.severity_filter,
        }
