"""
Edit agent for automatically applying code fixes using AI.
"""

import requests
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
        self.keep_backup = getattr(config, 'keep_backup', False)  # New option to keep backup files
        self.search_tool = create_search_tool(config.__dict__ if hasattr(config, '__dict__') else {})
        self.backup_files_created = []  # Track backup files for cleanup
    
    def is_available(self) -> bool:
        """Check if Ollama is available for edit generation."""
        available, _ = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)
        return available
    
    def process_issues(self, issues: List[Issue], **kwargs) -> List[Issue]:
        """Process issues by applying automatic fixes."""
        processed_issues = []
        modified_files = set()
        
        # Filter out ignored and already fixed issues
        issues_to_process = self._filter_processable_issues(issues)
        
        if not issues_to_process:
            print("No issues to process (all are ignored or already fixed)")
            return issues
        
        # Group issues by file for efficient processing
        issues_by_file = self._group_issues_by_file(issues_to_process)
        
        for file_path, file_issues in issues_by_file.items():
            try:
                # Apply fixes to the file
                fixed_issues = self._fix_file_issues(file_path, file_issues)
                processed_issues.extend(fixed_issues)
                
                # Track modified files
                if any(issue.status == IssueStatus.FIXED for issue in fixed_issues):
                    modified_files.add(file_path)
            
            except Exception as e:
                # If fixing fails, mark issues as failed with detailed error
                error_msg = f"Fix failed: {str(e)}"
                print(f"Error fixing {file_path}: {error_msg}")
                for issue in file_issues:
                    failed_issue = issue.model_copy()
                    failed_issue.status = IssueStatus.FAILED
                    failed_issue.description = f"{failed_issue.description}\n\n{error_msg}"
                    processed_issues.append(failed_issue)
        
        # Add unprocessed issues back to results
        for issue in issues:
            if issue not in issues_to_process:
                processed_issues.append(issue)
        
        # Clean up backup files if not keeping them
        if not self.keep_backup:
            self._cleanup_backup_files()
        
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
            error_msg = f"File not found: {file_path}"
            print(error_msg)
            return [self._mark_issue_failed(issue, "File not found") for issue in issues]
        
        try:
            # Create backup if enabled
            backup_path = None
            if self.backup_files:
                backup_path = FileUtils.create_backup(file_path)
                if backup_path:
                    self.backup_files_created.append(backup_path)
                    print(f"Created backup: {backup_path}")
            
            # Read original file content
            original_content = FileUtils.get_file_content(file_path)
            if original_content.startswith("Error reading file"):
                error_msg = f"Cannot read file: {file_path}"
                print(error_msg)
                return [self._mark_issue_failed(issue, "Cannot read file") for issue in issues]
            
            # Generate fixed content
            fixed_content = self._generate_fixed_content(file_path, original_content, issues)

            if fixed_content and fixed_content != original_content:
                # Write fixed content back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                print(f"Applied fixes to: {file_path}")
                # Mark issues as fixed
                return [self._mark_issue_fixed(issue) for issue in issues]
            else:
                # No changes made
                error_msg = "No fix generated or content unchanged"
                print(f"Warning: {error_msg} for {file_path}")
                return [self._mark_issue_failed(issue, "No fix generated") for issue in issues]
        
        except Exception as e:
            error_msg = f"Exception during fix: {str(e)}"
            print(f"Error fixing {file_path}: {error_msg}")
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
You are an expert code fixer. Fix the following issues in the code file and return ONLY the complete fixed code without any explanations, markdown formatting, or additional text.

File: {file_path}

Issues to fix:
{issues_text}

Original code:
{content}

IMPORTANT INSTRUCTIONS:
- Return ONLY the complete fixed code
- Do NOT include any explanations, comments about the fixes, or markdown formatting before or after the code
- Do NOT wrap the code in ``` blocks
- Do NOT add any text before or after the code
- Preserve the original file structure and formatting
- Make minimal changes to fix only the identified issues
- Ensure the code is syntactically correct and functional
- Do NOT be influenced by existing comments or TODO comments in the code - focus only on the given issues.

Fixed code:
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
                "num_predict": -1  # Infinite length for responses
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.config.agent_timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Cannot connect to Ollama server at {self.ollama_url}. Please ensure Ollama is running and accessible.")
        except requests.exceptions.Timeout as e:
            raise Exception(f"Ollama request timed out after {self.config.agent_timeout} seconds")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception(f"Model '{self.model}' not found in Ollama. Please pull the model first: ollama pull {self.model}")
            else:
                raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Unexpected error calling Ollama: {str(e)}")
    
    def _extract_fixed_code(self, response: str, original_content: str) -> str:
        """Extract fixed code from AI response."""
        if not response or not response.strip():
            return ""
        
        # Remove thinking content for qwen3:4b model
        cleaned_response = self._remove_thinking_content(response)
        
        # Try multiple extraction methods
        fixed_content = self._try_extract_methods(cleaned_response, original_content)
        
        # Final validation
        if fixed_content and len(fixed_content.strip()) > 0:
            # Ensure it's not just whitespace or too short
            if len(fixed_content.strip()) > len(original_content) * 0.3:
                return fixed_content
        
        return ""
    
    def _remove_thinking_content(self, response: str) -> str:
        """Remove thinking content between <think></think> tags."""
        import re
        # Remove thinking tags and their content
        cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()
    
    def _try_extract_methods(self, response: str, original_content: str) -> str:
        """Try multiple methods to extract code from response."""
        # Method 1: Look for code blocks with ```
        code_block_result = self._extract_from_code_blocks(response)
        if code_block_result:
            return code_block_result
        
        # Method 2: Look for "Fixed code:" section
        fixed_code_result = self._extract_after_marker(response, "Fixed code:")
        if fixed_code_result:
            return fixed_code_result
        
        # Method 3: Look for code after common markers
        for marker in ["Here's the fixed code:", "The fixed code is:", "Fixed version:"]:
            marker_result = self._extract_after_marker(response, marker)
            if marker_result:
                return marker_result
        
        # Method 4: If response looks like pure code, use it directly
        if self._looks_like_code(response, original_content):
            return response.strip()
        
        # Method 5: Try to find the largest code-like block
        return self._extract_largest_code_block(response)
    
    def _extract_from_code_blocks(self, response: str) -> str:
        """Extract code from markdown code blocks."""
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                if in_code_block:
                    break  # End of code block
                else:
                    in_code_block = True  # Start of code block
                    continue
            
            if in_code_block:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines)
        return ""
    
    def _extract_after_marker(self, response: str, marker: str) -> str:
        """Extract code after a specific marker."""
        marker_pos = response.lower().find(marker.lower())
        if marker_pos == -1:
            return ""
        
        # Get content after marker
        after_marker = response[marker_pos + len(marker):].strip()
        
        # Remove any leading markdown or formatting
        lines = after_marker.split('\n')
        code_lines = []
        started = False
        
        for line in lines:
            stripped = line.strip()
            # Skip empty lines and markdown at the start
            if not started and (not stripped or stripped.startswith('```')):
                continue
            started = True
            
            # Stop at markdown end or explanatory text
            if stripped.startswith('```') and started:
                break
            if stripped.lower().startswith(('explanation:', 'note:', 'the above', 'this fixes')):
                break
                
            code_lines.append(line)
        
        return '\n'.join(code_lines).strip()
    
    def _looks_like_code(self, response: str, original_content: str) -> bool:
        """Check if response looks like pure code."""
        # Check for common code indicators
        code_indicators = ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', '{', '}', ';']
        explanation_indicators = ['here is', 'here\'s', 'the code', 'explanation', 'i fixed', 'i changed']
        
        response_lower = response.lower()
        
        # Count code vs explanation indicators
        code_count = sum(1 for indicator in code_indicators if indicator in response_lower)
        explanation_count = sum(1 for indicator in explanation_indicators if indicator in response_lower)
        
        # If it has code indicators and few explanation indicators, likely pure code
        return code_count > 2 and explanation_count < 2
    
    def _extract_largest_code_block(self, response: str) -> str:
        """Extract the largest block that looks like code."""
        lines = response.split('\n')
        current_block = []
        largest_block = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip obvious non-code lines
            if any(stripped.lower().startswith(phrase) for phrase in 
                   ['here is', 'here\'s', 'the code', 'explanation', 'note:', 'i fixed', 'i changed']):
                if len(current_block) > len(largest_block):
                    largest_block = current_block[:]
                current_block = []
                continue
            
            # Skip markdown markers
            if stripped.startswith('```'):
                continue
                
            current_block.append(line)
        
        # Check final block
        if len(current_block) > len(largest_block):
            largest_block = current_block
        
        return '\n'.join(largest_block).strip()
    
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
    
    def _filter_processable_issues(self, issues: List[Issue]) -> List[Issue]:
        """Filter out ignored and already fixed issues."""
        processable_issues = []
        
        for issue in issues:
            # Skip ignored issues
            if issue.status == IssueStatus.IGNORED:
                print(f"Skipping ignored issue: {issue.title}")
                continue
            
            # Skip already fixed issues
            if issue.status == IssueStatus.FIXED:
                print(f"Skipping already fixed issue: {issue.title}")
                continue
            
            processable_issues.append(issue)
        
        return processable_issues
    
    def _cleanup_backup_files(self):
        """Clean up backup files that were created during fixing."""
        for backup_path in self.backup_files_created:
            try:
                if Path(backup_path).exists():
                    Path(backup_path).unlink()
                    print(f"Deleted backup file: {backup_path}")
            except Exception as e:
                print(f"Warning: Could not delete backup file {backup_path}: {e}")
        
        self.backup_files_created.clear()
