"""
Output update agent for applying code fixes automatically.
"""

import time
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

from codetective.agents.base import BaseAgent, AnalysisResult
from codetective.models.workflow_state import WorkflowState
from codetective.models.configuration import AgentConfig
from codetective.models.agent_results import OutputResults
from codetective.utils.result_aggregator import ResultAggregator
from codetective.utils.file_processor import FileProcessor


class OutputUpdateAgent(BaseAgent):
    """
    Output update agent for applying automatic code fixes.
    
    This agent analyzes findings from other agents and applies
    safe, automatic fixes where possible. It creates backups
    before making changes and provides detailed change logs.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the output update agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(config, "output_update")
        self.result_aggregator = None
        self.file_processor = None
        self.backup_dir = None
    
    def _initialize(self) -> None:
        """Initialize output update agent."""
        self.logger.info("Initializing output update agent")
        self.result_aggregator = ResultAggregator()
    
    async def analyze(self, state: WorkflowState) -> AnalysisResult:
        """
        Apply automatic fixes to code based on analysis results.
        
        Args:
            state: Current workflow state with analysis results
            
        Returns:
            Analysis result with applied updates
        """
        start_time = time.time()
        
        try:
            # Initialize file processor if needed
            if not self.file_processor and state.target_files:
                root_path = state.target_files[0].parent
                self.file_processor = FileProcessor(root_path)
            
            # Aggregate all results
            aggregated_results = self.result_aggregator.aggregate_workflow_results(state)
            
            if aggregated_results["summary"].total_findings == 0:
                return AnalysisResult(
                    success=True,
                    data={"results": OutputResults([], "No findings to fix", "update").to_dict()},
                    processing_time=time.time() - start_time,
                    metadata={"message": "No findings to apply fixes for"}
                )
            
            # Create backup directory
            self._create_backup_directory(state.target_files)
            
            # Identify fixable issues
            fixable_issues = self._identify_fixable_issues(aggregated_results)
            
            if not fixable_issues:
                return AnalysisResult(
                    success=True,
                    data={"results": OutputResults([], "No automatically fixable issues found", "update").to_dict()},
                    processing_time=time.time() - start_time,
                    metadata={"message": "No automatically fixable issues identified"}
                )
            
            # Apply fixes
            applied_fixes = []
            for issue in fixable_issues:
                fix_result = await self._apply_fix(issue)
                if fix_result:
                    applied_fixes.append(fix_result)
            
            # Create output results
            output_results = OutputResults(
                outputs=applied_fixes,
                summary=f"Applied {len(applied_fixes)} automatic fixes",
                output_type="update"
            )
            
            # Update workflow state
            state.output_results = output_results
            
            return AnalysisResult(
                success=True,
                data={"results": output_results.to_dict()},
                processing_time=time.time() - start_time,
                metadata={
                    "fixes_applied": len(applied_fixes),
                    "fixable_issues_found": len(fixable_issues),
                    "backup_directory": str(self.backup_dir) if self.backup_dir else None,
                }
            )
        
        except Exception as e:
            error_msg = f"Code update failed: {str(e)}"
            self.logger.exception(error_msg)
            
            return AnalysisResult(
                success=False,
                error=error_msg,
                processing_time=time.time() - start_time
            )
    
    def _create_backup_directory(self, target_files: List[Path]) -> None:
        """
        Create backup directory for files before modification.
        
        Args:
            target_files: List of files that might be modified
        """
        try:
            if not target_files:
                return
            
            # Create backup directory in the project root
            project_root = target_files[0].parent
            while project_root.parent != project_root and not (project_root / ".git").exists():
                project_root = project_root.parent
            
            self.backup_dir = project_root / ".codetective_backups" / f"backup_{int(time.time())}"
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Created backup directory: {self.backup_dir}")
        
        except Exception as e:
            self.logger.warning(f"Failed to create backup directory: {e}")
            self.backup_dir = None
    
    def _identify_fixable_issues(self, aggregated_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify issues that can be automatically fixed.
        
        Args:
            aggregated_results: Aggregated results from all agents
            
        Returns:
            List of fixable issues
        """
        fixable_issues = []
        
        # Check Semgrep findings for auto-fixable rules
        if "semgrep" in aggregated_results and aggregated_results["semgrep"]:
            for finding in aggregated_results["semgrep"]:
                if self._is_semgrep_fixable(finding):
                    fixable_issues.append({
                        "source": "semgrep",
                        "type": "static_analysis_fix",
                        "data": finding,
                        "fix_type": "pattern_replacement"
                    })
        
        # Check AI review findings for simple fixes
        if "ai_review" in aggregated_results and aggregated_results["ai_review"]:
            for issue in aggregated_results["ai_review"]:
                if self._is_ai_review_fixable(issue):
                    fixable_issues.append({
                        "source": "ai_review",
                        "type": "code_improvement",
                        "data": issue,
                        "fix_type": "suggestion_based"
                    })
        
        self.logger.info(f"Identified {len(fixable_issues)} fixable issues")
        return fixable_issues
    
    def _is_semgrep_fixable(self, finding: Dict[str, Any]) -> bool:
        """
        Check if a Semgrep finding can be automatically fixed.
        
        Args:
            finding: Semgrep finding data
            
        Returns:
            True if fixable, False otherwise
        """
        # Check if the rule provides a fix
        extra = finding.get("extra", {})
        if "fix" in extra:
            return True
        
        # Check for common fixable patterns
        check_id = finding.get("check_id", "")
        fixable_patterns = [
            "python.lang.security.audit.dangerous-system-call",
            "python.lang.correctness.useless-comparison",
            "python.lang.best-practice.unused-import",
            "python.lang.security.audit.hardcoded-password",
        ]
        
        return any(pattern in check_id for pattern in fixable_patterns)
    
    def _is_ai_review_fixable(self, issue: Dict[str, Any]) -> bool:
        """
        Check if an AI review issue can be automatically fixed.
        
        Args:
            issue: AI review issue data
            
        Returns:
            True if fixable, False otherwise
        """
        # Only fix issues with high confidence and specific types
        confidence = issue.get("confidence", 0.0)
        issue_type = issue.get("issue_type", "")
        severity = issue.get("severity", "")
        
        # Conservative approach - only fix high-confidence, low-risk issues
        if confidence < 0.8:
            return False
        
        fixable_types = [
            "documentation",
            "formatting",
            "imports",
            "unused_variables"
        ]
        
        return issue_type in fixable_types and severity in ["low", "medium"]
    
    async def _apply_fix(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Apply a fix for a specific issue.
        
        Args:
            issue: Issue to fix
            
        Returns:
            Fix result dictionary or None if fix failed
        """
        try:
            if issue["source"] == "semgrep":
                return await self._apply_semgrep_fix(issue)
            elif issue["source"] == "ai_review":
                return await self._apply_ai_review_fix(issue)
            else:
                self.logger.warning(f"Unknown issue source: {issue['source']}")
                return None
        
        except Exception as e:
            self.logger.error(f"Failed to apply fix: {e}")
            return None
    
    async def _apply_semgrep_fix(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Apply a Semgrep-based fix.
        
        Args:
            issue: Semgrep issue data
            
        Returns:
            Fix result or None if failed
        """
        finding = issue["data"]
        file_path = Path(finding["path"])
        
        # Create backup
        if not self._create_file_backup(file_path):
            return None
        
        # Check if Semgrep provides a direct fix
        extra = finding.get("extra", {})
        if "fix" in extra:
            return await self._apply_semgrep_direct_fix(file_path, finding, extra["fix"])
        
        # Apply pattern-based fixes
        check_id = finding.get("check_id", "")
        if "unused-import" in check_id:
            return await self._fix_unused_import(file_path, finding)
        elif "hardcoded-password" in check_id:
            return await self._fix_hardcoded_password(file_path, finding)
        
        return None
    
    async def _apply_semgrep_direct_fix(self, file_path: Path, finding: Dict[str, Any], fix: str) -> Dict[str, Any]:
        """
        Apply a direct Semgrep fix.
        
        Args:
            file_path: Path to the file
            finding: Semgrep finding
            fix: Fix string provided by Semgrep
            
        Returns:
            Fix result dictionary
        """
        # Read file content
        content = self.file_processor.read_file_content(file_path)
        if not content:
            raise ValueError(f"Could not read file: {file_path}")
        
        # Get the location of the issue
        start = finding.get("start", {})
        end = finding.get("end", {})
        start_line = start.get("line", 1) - 1  # Convert to 0-based
        end_line = end.get("line", 1) - 1
        start_col = start.get("col", 1) - 1
        end_col = end.get("col", 1) - 1
        
        # Split content into lines
        lines = content.split('\n')
        
        # Replace the problematic code
        if start_line == end_line:
            # Single line replacement
            line = lines[start_line]
            lines[start_line] = line[:start_col] + fix + line[end_col:]
        else:
            # Multi-line replacement
            lines[start_line] = lines[start_line][:start_col] + fix
            # Remove intermediate lines
            for i in range(end_line - start_line):
                lines.pop(start_line + 1)
        
        # Write back to file
        new_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "file_path": str(file_path),
            "fix_type": "semgrep_direct",
            "description": f"Applied Semgrep fix for {finding.get('check_id', 'unknown')}",
            "lines_affected": f"{start_line + 1}-{end_line + 1}",
            "original_code": finding.get("extra", {}).get("lines", ""),
            "fixed_code": fix
        }
    
    async def _fix_unused_import(self, file_path: Path, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix unused import statements.
        
        Args:
            file_path: Path to the file
            finding: Semgrep finding
            
        Returns:
            Fix result dictionary
        """
        content = self.file_processor.read_file_content(file_path)
        lines = content.split('\n')
        
        start_line = finding.get("start", {}).get("line", 1) - 1
        
        # Remove the import line
        removed_line = lines[start_line]
        lines.pop(start_line)
        
        # Write back to file
        new_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "file_path": str(file_path),
            "fix_type": "unused_import_removal",
            "description": "Removed unused import statement",
            "lines_affected": str(start_line + 1),
            "original_code": removed_line.strip(),
            "fixed_code": "(removed)"
        }
    
    async def _fix_hardcoded_password(self, file_path: Path, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix hardcoded password by adding a comment warning.
        
        Args:
            file_path: Path to the file
            finding: Semgrep finding
            
        Returns:
            Fix result dictionary
        """
        content = self.file_processor.read_file_content(file_path)
        lines = content.split('\n')
        
        start_line = finding.get("start", {}).get("line", 1) - 1
        
        # Add warning comment above the line
        warning_comment = "# WARNING: Hardcoded password detected - consider using environment variables"
        lines.insert(start_line, warning_comment)
        
        # Write back to file
        new_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "file_path": str(file_path),
            "fix_type": "hardcoded_password_warning",
            "description": "Added warning comment for hardcoded password",
            "lines_affected": str(start_line + 1),
            "original_code": lines[start_line + 1].strip(),
            "fixed_code": f"{warning_comment}\n{lines[start_line + 1].strip()}"
        }
    
    async def _apply_ai_review_fix(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Apply an AI review-based fix.
        
        Args:
            issue: AI review issue data
            
        Returns:
            Fix result or None if failed
        """
        issue_data = issue["data"]
        file_path = Path(issue_data["file_path"])
        
        # Create backup
        if not self._create_file_backup(file_path):
            return None
        
        issue_type = issue_data.get("issue_type", "")
        
        if issue_type == "documentation":
            return await self._fix_documentation_issue(file_path, issue_data)
        elif issue_type == "formatting":
            return await self._fix_formatting_issue(file_path, issue_data)
        
        return None
    
    async def _fix_documentation_issue(self, file_path: Path, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix documentation issues by adding basic docstrings.
        
        Args:
            file_path: Path to the file
            issue_data: Issue data
            
        Returns:
            Fix result dictionary
        """
        content = self.file_processor.read_file_content(file_path)
        lines = content.split('\n')
        
        line_start = issue_data.get("line_start", 1) - 1
        suggestion = issue_data.get("suggestion", "")
        
        # Add a basic docstring comment
        if "function" in suggestion.lower() or "method" in suggestion.lower():
            docstring = '    """Add function description here."""'
            lines.insert(line_start + 1, docstring)
        
        # Write back to file
        new_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "file_path": str(file_path),
            "fix_type": "documentation_improvement",
            "description": "Added basic docstring",
            "lines_affected": str(line_start + 1),
            "original_code": lines[line_start].strip(),
            "fixed_code": f"{lines[line_start].strip()}\n{docstring}"
        }
    
    async def _fix_formatting_issue(self, file_path: Path, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix basic formatting issues.
        
        Args:
            file_path: Path to the file
            issue_data: Issue data
            
        Returns:
            Fix result dictionary
        """
        # For now, just log that we would fix formatting
        # In a real implementation, you might use tools like black or autopep8
        
        return {
            "file_path": str(file_path),
            "fix_type": "formatting_improvement",
            "description": "Formatting issue identified (manual fix recommended)",
            "lines_affected": str(issue_data.get("line_start", 1)),
            "original_code": "formatting issue",
            "fixed_code": "manual formatting fix recommended"
        }
    
    def _create_file_backup(self, file_path: Path) -> bool:
        """
        Create a backup of a file before modification.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            if not self.backup_dir:
                return False
            
            # Create backup file path
            relative_path = file_path.relative_to(file_path.anchor)
            backup_file_path = self.backup_dir / relative_path
            
            # Create backup directory structure
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to backup location
            shutil.copy2(file_path, backup_file_path)
            
            self.logger.debug(f"Created backup: {backup_file_path}")
            return True
        
        except Exception as e:
            self.logger.warning(f"Failed to create backup for {file_path}: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """Return list of output update agent capabilities."""
        return [
            "automatic_fixes",
            "backup_creation",
            "semgrep_fixes",
            "ai_review_fixes",
            "import_cleanup",
            "documentation_improvement",
            "security_warnings"
        ]
    
    def get_supported_file_extensions(self) -> Optional[List[str]]:
        """Get list of file extensions supported for updates."""
        return [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h"]
    
    def get_fix_stats(self) -> Dict[str, Any]:
        """Get statistics about fix capabilities."""
        return {
            "supported_sources": ["semgrep", "ai_review"],
            "fix_types": [
                "pattern_replacement",
                "unused_import_removal", 
                "hardcoded_password_warning",
                "documentation_improvement",
                "formatting_improvement"
            ],
            "backup_enabled": True,
        }
