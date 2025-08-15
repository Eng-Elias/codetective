"""
Edit agent for automatically applying code fixes using AI.
"""

import requests
import shutil
from typing import List, Dict
from pathlib import Path

from codetective.models.schemas import AgentType, Issue, IssueStatus
from codetective.utils import SystemUtils, FileUtils
from codetective.core.search import create_search_tool
from codetective.agents.base import OutputAgent
from codetective.utils.system_utils import RequiredTools


class EditAgent(OutputAgent):
    """Agent for automatically applying code fixes."""
    
    def __init__(self, config):
        super().__init__(config)
        self.agent_type = AgentType.EDIT
        self.ollama_url = config.ollama_base_url
        self.model = config.ollama_model or "qwen3:4b"  # Default to qwen3:4b
        self.backup_files = config.backup_files
        self.search_tool = create_search_tool(config.__dict__ if hasattr(config, '__dict__') else {})
    
    def is_available(self) -> bool:
        """Check if Ollama is available for edit generation."""
        available, _ = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)
        return available
    
    def process_issues(self, issues: List[Issue], **kwargs) -> List[Issue]:
        """Process issues by applying automatic fixes."""
        processed_issues = []
        modified_files = set()
        
        # Group issues by file for efficient processing
        issues_by_file = self._group_issues_by_file(issues)
        
        for file_path, file_issues in issues_by_file.items():
            try:
                # Apply fixes to the file
                fixed_issues = self._fix_file_issues(file_path, file_issues)
                processed_issues.extend(fixed_issues)
                
                # Track modified files
                if any(issue.status == IssueStatus.FIXED for issue in fixed_issues):
                    modified_files.add(file_path)
            
            except Exception as e:
                # If fixing fails, mark issues as failed
                for issue in file_issues:
                    failed_issue = issue.model_copy()
                    failed_issue.status = IssueStatus.FAILED
                    processed_issues.append(failed_issue)
        
        return processed_issues
    
    def _group_issues_by_file(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Group issues by file path."""
        issues_by_file = {}
        
        for issue in issues:
            if issue.file_path:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)
        
        return issues_by_file
    
    def _fix_file_issues(self, file_path: str, issues: List[Issue]) -> List[Issue]:
        """Fix all issues in a single file."""
        if not Path(file_path).exists():
            return [self._mark_issue_failed(issue, "File not found") for issue in issues]
        
        try:
            # Create backup if enabled
            if self.backup_files:
                FileUtils.create_backup(file_path)
            
            # Read original file content
            original_content = FileUtils.get_file_content(file_path)
            if original_content.startswith("Error reading file"):
                return [self._mark_issue_failed(issue, "Cannot read file") for issue in issues]
            
            # Generate fixed content
            fixed_content = self._generate_fixed_content(file_path, original_content, issues)
            
            if fixed_content and fixed_content != original_content:
                # Write fixed content back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                # Mark issues as fixed
                return [self._mark_issue_fixed(issue) for issue in issues]
            else:
                # No changes made
                return [self._mark_issue_failed(issue, "No fix generated") for issue in issues]
        
        except Exception as e:
            return [self._mark_issue_failed(issue, str(e)) for issue in issues]
    
    def _generate_fixed_content(self, file_path: str, content: str, issues: List[Issue]) -> str:
        """Generate fixed content using AI."""
        prompt = self._create_fix_prompt(file_path, content, issues)
        
        try:
            response = self._call_ollama(prompt)
            return self._extract_fixed_code(response, content)
        except Exception:
            return ""
    
    def _create_fix_prompt(self, file_path: str, content: str, issues: List[Issue]) -> str:
        """Create a prompt for generating code fixes."""
        file_extension = Path(file_path).suffix
        
        # Create issues summary
        issues_summary = []
        for i, issue in enumerate(issues, 1):
            line_info = f" (line {issue.line_number})" if issue.line_number else ""
            issues_summary.append(f"{i}. {issue.title}{line_info}: {issue.description}")
            if issue.fix_suggestion:
                issues_summary.append(f"   Suggested fix: {issue.fix_suggestion}")
        
        issues_text = "\n".join(issues_summary)
        
        prompt = f"""
You are an expert code fixer. Please fix the following issues in the code file.

File: {file_path}

Issues to fix:
{issues_text}

Original code:
```{file_extension[1:] if file_extension else 'text'}
{content}
```

Please provide the complete fixed code. Make minimal changes to fix only the identified issues while preserving the original functionality and style.

Fixed code:
```{file_extension[1:] if file_extension else 'text'}
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for code fixing."""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent fixes
                "top_p": 0.9,
                "num_predict": 4096  # Allow longer responses for code
            }
        }
        
        response = requests.post(url, json=payload, timeout=self.config.agent_timeout * 2)  # Longer timeout for fixes
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def _extract_fixed_code(self, response: str, original_content: str) -> str:
        """Extract fixed code from AI response."""
        # Look for code blocks in the response
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    break  # End of code block
                else:
                    in_code_block = True  # Start of code block
                    continue
            
            if in_code_block:
                code_lines.append(line)
        
        if code_lines:
            fixed_content = '\n'.join(code_lines)
            
            # Basic validation: ensure the fixed content is reasonable
            if len(fixed_content.strip()) > 0 and len(fixed_content) > len(original_content) * 0.5:
                return fixed_content
        
        return ""
    
    def _mark_issue_fixed(self, issue: Issue) -> Issue:
        """Mark an issue as fixed."""
        fixed_issue = issue.model_copy()
        fixed_issue.status = IssueStatus.FIXED
        return fixed_issue
    
    def _mark_issue_failed(self, issue: Issue, error_message: str) -> Issue:
        """Mark an issue as failed to fix."""
        failed_issue = issue.model_copy()
        failed_issue.status = IssueStatus.FAILED
        # Add error message to description
        failed_issue.description = f"{failed_issue.description}\n\nFix failed: {error_message}"
        return failed_issue
