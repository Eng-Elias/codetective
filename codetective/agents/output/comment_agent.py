"""
Comment agent for generating explanatory comments using AI.
"""

from typing import List
from pathlib import Path

from codetective.models.schemas import AgentType, Issue, IssueStatus
from codetective.agents.base import OutputAgent
from codetective.agents.ai_base import AIAgent


class CommentAgent(OutputAgent, AIAgent):
    """Agent for generating explanatory comments for issues."""
    
    def __init__(self, config):
        OutputAgent.__init__(self, config)
        AIAgent.__init__(self, config)
        self.agent_type = AgentType.COMMENT
        self.backup_files_created = []  # Track backup files for cleanup
    
    def is_available(self) -> bool:
        """Check if Ollama is available for comment generation."""
        return self.is_ai_available()
    
    def process_issues(self, issues: List[Issue], **kwargs) -> List[Issue]:
        """Process issues by adding explanatory comments."""
        processed_issues = []
        
        # Filter out ignored and already processed issues
        issues_to_process = self._filter_processable_issues(issues)
        
        if not issues_to_process:
            print("No issues to process (all are ignored or already processed)")
            return issues
        
        # Group issues by file for efficient processing
        issues_by_file = self._group_issues_by_file(issues_to_process)
        
        for file_path, file_issues in issues_by_file.items():
            try:
                # Process all issues for this file together
                enhanced_issues = self._process_file_issues(file_path, file_issues)
                processed_issues.extend(enhanced_issues)
            except Exception as e:
                # If processing fails, mark all issues as failed
                error_msg = f"Comment processing failed: {str(e)}"
                print(f"Error processing file {file_path}: {error_msg}")
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
        if not self.config.keep_backup:
            self._cleanup_backup_files()
        
        return processed_issues
    
    def _group_issues_by_file(self, issues: List[Issue]) -> dict[str, List[Issue]]:
        """Group issues by file path."""
        issues_by_file = {}
        
        for issue in issues:
            if issue.file_path:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)
        
        return issues_by_file
    
    def _process_file_issues(self, file_path: str, issues: List[Issue]) -> List[Issue]:
        """Process all issues for a single file by adding individual comments."""
        if not Path(file_path).exists():
            error_msg = f"File not found: {file_path}"
            print(error_msg)
            return [self._mark_issue_failed(issue, "File not found") for issue in issues]
        
        try:
            # Create backup if enabled
            backup_path = None
            if self.config.backup_files:
                from codetective.utils import FileUtils
                backup_path = FileUtils.create_backup(file_path)
                if backup_path:
                    self.backup_files_created.append(backup_path)
                    print(f"Created backup: {backup_path}")
            
            # Sort issues by line number (descending) to avoid line number shifts
            # Issues with None/0 line numbers go to the end (will be added at beginning of file)
            sorted_issues = sorted(issues, key=lambda x: x.line_number if x.line_number else 0, reverse=True)
            
            # Process each issue individually
            processed_issues = []
            for issue in sorted_issues:
                enhanced_issue = self._add_individual_comment(issue)
                processed_issues.append(enhanced_issue)
            
            # Return in original order
            return sorted(processed_issues, key=lambda x: x.line_number or 0)
            
        except Exception as e:
            error_msg = f"Exception during file processing: {str(e)}"
            print(f"Error processing {file_path}: {error_msg}")
            return [self._mark_issue_failed(issue, str(e)) for issue in issues]
    
    def _add_individual_comment(self, issue: Issue) -> Issue:
        """Add an explanatory comment for a single issue."""
        # Get file content around the issue line for context
        context = self._get_issue_context(issue)
        
        # Generate explanatory comment using AI
        comment = self._generate_comment(issue, context)
        
        if not comment or comment.strip() == "":
            print(f"Warning: No comment generated for issue: {issue.title}")
            comment = self._generate_fallback_comment(issue)
        
        # Try to add comment to the source file
        success = self._add_comment_to_file(issue, comment)
        
        # Update the issue status and description
        enhanced_issue = issue.model_copy()
        if success:
            enhanced_issue.status = IssueStatus.FIXED
            enhanced_issue.description = f"{issue.description}\n\n**Comment Added:**\n{comment}"
            print(f"Added explanatory comment to file: {issue.file_path}:{issue.line_number}")
        else:
            enhanced_issue.status = IssueStatus.FAILED
            enhanced_issue.description = f"{issue.description}\n\n**Failed to add comment:**\n{comment}"
            print(f"Failed to add comment to file: {issue.file_path}:{issue.line_number}")
        
        return enhanced_issue
    
    def _mark_issue_failed(self, issue: Issue, error_message: str) -> Issue:
        """Mark an issue as failed to process."""
        failed_issue = issue.model_copy()
        failed_issue.status = IssueStatus.FAILED
        failed_issue.description = f"{failed_issue.description}\n\nComment failed: {error_message}"
        return failed_issue
    
    def _get_issue_context(self, issue: Issue) -> str:
        """Get code context around the issue location."""
        if not issue.file_path or not Path(issue.file_path).exists():
            return ""
        
        try:
            # Read file content
            with open(issue.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                return ""
            
            # Get context around the issue line
            if issue.line_number:
                start_line = max(0, issue.line_number - 6)  # 5 lines before
                end_line = min(len(lines), issue.line_number + 5)  # 5 lines after
                
                context_lines = []
                for i in range(start_line, end_line):
                    line_num = i + 1
                    marker = " >>> " if line_num == issue.line_number else "     "
                    context_lines.append(f"{line_num:4d}{marker}{lines[i].rstrip()}")
                
                return "\n".join(context_lines)
            else:
                # If no specific line, return first 10 lines
                return "\n".join(f"{i+1:4d}     {line.rstrip()}" for i, line in enumerate(lines[:10]))
        
        except Exception:
            return ""
    
    def _generate_comment(self, issue: Issue, context: str) -> str:
        """Generate an explanatory comment using AI."""
        prompt = self._create_comment_prompt(issue, context)
        
        try:
            response = self.call_ai(prompt, temperature=0.3)
            return self._extract_comment(response)
        except Exception:
            return self._generate_fallback_comment(issue)
    
    def _create_comment_prompt(self, issue: Issue, context: str) -> str:
        """Create a prompt for generating explanatory comments."""
        prompt = f"""
You are a helpful code reviewer. Provide a clear explanation for the following code issue.

Issue Details:
- Title: {issue.title}
- Description: {issue.description}
- Severity: {issue.severity.value if issue.severity else 'N/A'}
- File: {issue.file_path}
- Line: {issue.line_number or 'N/A'}

Code Context:
```
{context}
```

Generate a concise TODO comment (under 100 words) that explains:
1. What the issue is
2. Why it's dangerous
3. How to fix it

Format as a TODO comment with practical guidance for developers.

IMPORTANT: 
- Keep under 100 words
- Return ONLY the comment text, no additional formatting or explanations
- Focus on actionable advice
- Do NOT be influenced by existing comments or TODO comments in the code - focus only on the given issues.
"""
        return prompt
    
    
    def _extract_comment(self, response: str) -> str:
        """Extract the comment from AI response."""
        if not response or not response.strip():
            return ""
        
        # Clean response using base class method
        cleaned_response = self.clean_ai_response(response)
        
        # Remove any markdown formatting for cleaner output
        comment = cleaned_response.replace("**", "").replace("*", "")
        
        return comment
    
    def _generate_fallback_comment(self, issue: Issue) -> str:
        """Generate a fallback comment when AI generation fails."""
        return f"TODO: Fix {issue.severity} security issue - {issue.description}. Review code and apply appropriate security measures."
    
    def _filter_processable_issues(self, issues: List[Issue]) -> List[Issue]:
        """Filter out ignored and already processed issues."""
        processable_issues = []
        
        for issue in issues:
            # Skip ignored issues
            if issue.status == IssueStatus.IGNORED:
                print(f"Skipping ignored issue: {issue.title}")
                continue
            
            # Skip already fixed issues (comment agent doesn't change status to FIXED)
            if issue.status == IssueStatus.FIXED:
                print(f"Skipping already fixed issue: {issue.title}")
                continue
            
            processable_issues.append(issue)
        
        return processable_issues
    
    
    def _add_comment_to_file(self, issue: Issue, comment: str) -> bool:
        """Add explanatory comment to the source file."""
        if not issue.file_path or not Path(issue.file_path).exists():
            return False
        
        try:
            # Read the file content
            with open(issue.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                return False
            
            # Handle None or invalid line numbers - add comment at beginning of file
            if not issue.line_number or issue.line_number <= 0 or issue.line_number > len(lines):
                insert_line = 0  # Add at beginning of file
                target_line = lines[0] if lines else ""
            else:
                # Insert comment before the problematic line
                insert_line = issue.line_number - 1  # Convert to 0-based index
                target_line = lines[insert_line] if insert_line < len(lines) else ""
            
            # Format the comment for the specific file type
            formatted_comment = self._format_comment_for_file(issue.file_path, comment, issue.title)
            
            # Get indentation from the target line
            indent = self._get_line_indentation(target_line)
            
            # Add indentation to comment lines
            comment_lines = []
            for line in formatted_comment.split('\n'):
                if line.strip():  # Don't indent empty lines
                    comment_lines.append(f"{indent}{line}\n")
                else:
                    comment_lines.append("\n")
            
            # Insert the comment
            lines[insert_line:insert_line] = comment_lines
            
            # Write back to file
            with open(issue.file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Error adding comment to file {issue.file_path}: {e}")
            return False
    
    def _format_comment_for_file(self, file_path: str, comment: str, issue_title: str = "") -> str:
        """Format comment according to file type."""
        file_extension = Path(file_path).suffix.lower()
        
        # Limit comment length and split into lines
        max_line_length = 80
        words = comment.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_line_length - 10:  # Leave space for comment markers
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Create header with issue title if available
        header = f"CODETECTIVE: {issue_title}" if issue_title else "CODETECTIVE: Security Issue"
        
        # Format based on file type
        if file_extension in ['.py']:
            # Python comments
            formatted_lines = [f"# {header}"]
            for line in lines:
                formatted_lines.append(f"# {line}")
            return "\n".join(formatted_lines)
        
        elif file_extension in ['.js', '.ts', '.java', '.c', '.cpp', '.cs']:
            # C-style comments
            formatted_lines = [f"/* {header}"]
            for line in lines:
                formatted_lines.append(f" * {line}")
            formatted_lines.append(" */")
            return "\n".join(formatted_lines)
        
        elif file_extension in ['.html', '.xml']:
            # HTML/XML comments
            formatted_lines = [f"<!-- {header}"]
            for line in lines:
                formatted_lines.append(f"     {line}")
            formatted_lines.append("-->")
            return "\n".join(formatted_lines)
        
        elif file_extension in ['.sh', '.bash']:
            # Shell comments
            formatted_lines = [f"# {header}"]
            for line in lines:
                formatted_lines.append(f"# {line}")
            return "\n".join(formatted_lines)
        
        else:
            # Default to hash comments
            formatted_lines = [f"# {header}"]
            for line in lines:
                formatted_lines.append(f"# {line}")
            return "\n".join(formatted_lines)
    
    def _get_line_indentation(self, line: str) -> str:
        """Get the indentation (spaces/tabs) from a line."""
        indent = ""
        for char in line:
            if char in [' ', '\t']:
                indent += char
            else:
                break
        return indent
    
    def _cleanup_backup_files(self):
        """Clean up backup files that were created during comment processing."""
        for backup_path in self.backup_files_created:
            try:
                if Path(backup_path).exists():
                    Path(backup_path).unlink()
                    print(f"Deleted backup file: {backup_path}")
            except Exception as e:
                print(f"Warning: Could not delete backup file {backup_path}: {e}")
        
        self.backup_files_created.clear()
