"""
Comment agent for generating explanatory comments using AI.
"""

import requests
from typing import List
from pathlib import Path

from codetective.models.schemas import AgentType, Issue, IssueStatus
from codetective.utils import SystemUtils
from codetective.core.search import create_search_tool
from codetective.agents.base import OutputAgent
from codetective.utils.system_utils import RequiredTools


class CommentAgent(OutputAgent):
    """Agent for generating explanatory comments for issues."""
    
    def __init__(self, config):
        super().__init__(config)
        self.agent_type = AgentType.COMMENT
        self.ollama_url = config.ollama_base_url
        self.model = config.ollama_model or "qwen3:4b"  # Default to qwen3:4b
        self.search_tool = create_search_tool(config.__dict__ if hasattr(config, '__dict__') else {})
    
    def is_available(self) -> bool:
        """Check if Ollama is available for comment generation."""
        available, _ = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)
        return available
    
    def process_issues(self, issues: List[Issue], **kwargs) -> List[Issue]:
        """Process issues by adding explanatory comments."""
        processed_issues = []
        
        for issue in issues:
            try:
                # Generate explanatory comment for the issue
                enhanced_issue = self._add_explanatory_comment(issue)
                processed_issues.append(enhanced_issue)
            except Exception as e:
                # If comment generation fails, return original issue
                processed_issues.append(issue)
        
        return processed_issues
    
    def _add_explanatory_comment(self, issue: Issue) -> Issue:
        """Add an explanatory comment to an issue."""
        # Get file content around the issue line for context
        context = self._get_issue_context(issue)
        
        # Generate explanatory comment using AI
        comment = self._generate_comment(issue, context)
        
        # Create a new issue with enhanced description
        enhanced_description = f"{issue.description}\n\n**Explanation:**\n{comment}"
        
        # Update the issue with enhanced description
        enhanced_issue = issue.model_copy()
        enhanced_issue.description = enhanced_description
        enhanced_issue.status = IssueStatus.DETECTED
        
        return enhanced_issue
    
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
            response = self._call_ollama(prompt)
            return self._extract_comment(response)
        except Exception:
            return self._generate_fallback_comment(issue)
    
    def _create_comment_prompt(self, issue: Issue, context: str) -> str:
        """Create a prompt for generating explanatory comments."""
        prompt = f"""
You are a helpful code reviewer. Please provide a clear, educational explanation for the following code issue.

Issue Details:
- Title: {issue.title}
- Description: {issue.description}
- Severity: {issue.severity.value}
- File: {issue.file_path}
- Line: {issue.line_number or 'N/A'}

Code Context:
```
{context}
```

Please provide:
1. A clear explanation of what the issue is
2. Why it's a problem
3. Potential consequences if not fixed
4. Best practices to avoid this issue

Keep the explanation educational and helpful for developers to learn from.

Response:
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for comment generation."""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Slightly higher for more natural explanations
                "top_p": 0.9,
                "num_predict": 1024
            }
        }
        
        response = requests.post(url, json=payload, timeout=self.config.agent_timeout)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def _extract_comment(self, response: str) -> str:
        """Extract the comment from AI response."""
        # Clean up the response
        comment = response.strip()
        
        # Remove any markdown formatting for cleaner output
        comment = comment.replace("**", "").replace("*", "")
        
        # Limit length
        max_length = 1000
        if len(comment) > max_length:
            comment = comment[:max_length] + "..."
        
        return comment
    
    def _generate_fallback_comment(self, issue: Issue) -> str:
        """Generate a fallback comment when AI is not available."""
        severity_explanations = {
            "critical": "This is a critical issue that requires immediate attention as it could lead to severe security vulnerabilities or system failures.",
            "high": "This is a high-priority issue that should be addressed soon as it may impact security or functionality.",
            "medium": "This is a medium-priority issue that should be reviewed and addressed to improve code quality.",
            "low": "This is a low-priority issue that can be addressed when convenient to improve code maintainability."
        }
        
        base_comment = f"This issue was detected by {issue.rule_id or 'code analysis'}. "
        severity_comment = severity_explanations.get(issue.severity.value, "This issue should be reviewed.")
        
        fix_comment = ""
        if issue.fix_suggestion:
            fix_comment = f"\n\nSuggested fix: {issue.fix_suggestion}"
        
        return base_comment + severity_comment + fix_comment
