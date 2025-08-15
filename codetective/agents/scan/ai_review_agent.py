"""
AI Review agent using Ollama for intelligent code analysis.
"""

import json
import requests
from typing import List
from pathlib import Path

from codetective.models.schemas import AgentType, Issue, SeverityLevel
from codetective.utils import SystemUtils, FileUtils
from codetective.core.search import create_search_tool
from codetective.agents.base import ScanAgent
from codetective.utils.system_utils import RequiredTools


class AIReviewAgent(ScanAgent):
    """Agent for AI-powered code review using Ollama."""
    
    def __init__(self, config):
        super().__init__(config)
        self.agent_type = AgentType.AI_REVIEW
        self.ollama_url = config.ollama_base_url
        self.model = config.ollama_model or "qwen3:4b"  # Default to qwen3:4b
        self.search_tool = create_search_tool(config.__dict__ if hasattr(config, '__dict__') else {})
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        available, _ = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)
        return available
    
    def scan_files(self, files: List[str]) -> List[Issue]:
        """Scan files using AI review."""
        issues = []
        
        # Get supported files (focus on code files)
        supported_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh'
        ]
        
        supported_files = self._get_supported_files(files, supported_extensions)
        
        # Limit number of files to avoid overwhelming the AI
        max_files = 20
        if len(supported_files) > max_files:
            supported_files = supported_files[:max_files]
        
        for file_path in supported_files:
            try:
                file_issues = self._review_file(file_path)
                issues.extend(file_issues)
            except Exception as e:
                # Log error but continue with other files
                continue
        
        return issues
    
    def _review_file(self, file_path: str) -> List[Issue]:
        """Review a single file using AI."""
        issues = []
        
        # Read file content
        content = FileUtils.get_file_content(file_path, max_lines=500)  # Limit content size
        
        if not content or content.startswith("Error reading file"):
            return issues
        
        # Create AI review prompt
        prompt = self._create_review_prompt(file_path, content)
        
        try:
            # Call Ollama API
            response = self._call_ollama(prompt)
            
            # Parse AI response into issues
            ai_issues = self._parse_ai_response(response, file_path)
            issues.extend(ai_issues)
        
        except Exception as e:
            # If AI review fails, create a general issue
            pass
        
        return issues
    
    def _create_review_prompt(self, file_path: str, content: str) -> str:
        """Create a prompt for AI code review."""
        file_extension = Path(file_path).suffix
        language = self._detect_language(file_extension)
        
        # Get relevant search context if search tool is available
        search_context = ""
        if self.search_tool:
            search_context = self._get_search_context(language, content)
        
        prompt = f"""
You are an expert code reviewer with access to current security best practices and coding standards. Please analyze the following {file_extension} file and identify potential issues.

Focus on:
1. Security vulnerabilities (SQL injection, XSS, CSRF, etc.)
2. Code quality issues (maintainability, readability)
3. Performance problems (inefficient algorithms, memory leaks)
4. Best practice violations (coding standards, design patterns)
5. Potential bugs (null pointer exceptions, race conditions)

File: {file_path}
Language: {language}

{search_context}

Code:
```{file_extension[1:] if file_extension else 'text'}
{content}
```

Please respond with a JSON array of issues found. Each issue should have:
- "title": Brief title of the issue
- "description": Detailed description with context from best practices
- "severity": "low", "medium", "high", or "critical"
- "line_number": Line number where issue occurs (if applicable)
- "suggestion": Specific fix or improvement recommendation
- "references": Any relevant documentation or security advisories

If no issues are found, return an empty array [].

Response (JSON only):
"""
        return prompt
    
    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension."""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C Header',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.sh': 'Shell Script'
        }
        return language_map.get(file_extension, 'Unknown')
    
    def _get_search_context(self, language: str, content: str) -> str:
        """Get relevant search context for code review."""
        if not self.search_tool:
            return ""
        
        # Extract potential security patterns or frameworks from code
        search_queries = []
        
        # Look for common security-sensitive patterns
        if 'sql' in content.lower() or 'query' in content.lower():
            search_queries.append(f"{language} SQL injection prevention")
        
        if 'password' in content.lower() or 'auth' in content.lower():
            search_queries.append(f"{language} authentication security best practices")
        
        if 'input' in content.lower() or 'request' in content.lower():
            search_queries.append(f"{language} input validation security")
        
        # Get search results
        search_results = []
        for query in search_queries[:2]:  # Limit to 2 searches to avoid delays
            results = self.search_tool.search(query)
            search_results.extend(results[:2])  # Take top 2 results per query
        
        if search_results:
            context = "\nRelevant Security Context:\n"
            for i, result in enumerate(search_results[:3], 1):  # Max 3 results
                context += f"{i}. {result['title']}: {result['body']}...\n"
            return context
        
        return ""
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API for code review."""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent results
                "top_p": 0.9,
                "num_predict": 2048
            }
        }
        
        response = requests.post(url, json=payload, timeout=self.config.agent_timeout)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def _parse_ai_response(self, response: str, file_path: str) -> List[Issue]:
        """Parse AI response into Issue objects."""
        issues = []
        
        try:
            # Try to extract JSON from the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                ai_issues = json.loads(json_str)
                
                for i, ai_issue in enumerate(ai_issues):
                    if isinstance(ai_issue, dict):
                        issue = self._create_issue_from_ai(ai_issue, file_path, i)
                        if issue:
                            issues.append(issue)
        
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, try to extract issues from text
            issues = self._parse_text_response(response, file_path)
        
        return issues
    
    def _create_issue_from_ai(self, ai_issue: dict, file_path: str, index: int) -> Issue:
        """Create an Issue object from AI response."""
        try:
            title = ai_issue.get("title", f"AI Review Issue {index + 1}")
            description = ai_issue.get("description", "No description provided")
            severity = self._map_ai_severity(ai_issue.get("severity", "medium"))
            line_number = ai_issue.get("line_number")
            suggestion = ai_issue.get("suggestion", "")
            
            # Ensure line_number is valid
            if line_number is not None:
                try:
                    line_number = int(line_number)
                    if line_number <= 0:
                        line_number = None
                except (ValueError, TypeError):
                    line_number = None
            
            return Issue(
                id=f"ai-review-{file_path}-{index}",
                title=f"AI Review: {title}",
                description=description,
                severity=severity,
                file_path=file_path,
                line_number=line_number,
                rule_id=f"ai-review-{index}",
                fix_suggestion=suggestion,
                status=IssueStatus.DETECTED
            )
        
        except Exception:
            return None
    
    def _parse_text_response(self, response: str, file_path: str) -> List[Issue]:
        """Parse text response when JSON parsing fails."""
        issues = []
        
        # Simple text parsing for common issue patterns
        lines = response.split('\n')
        current_issue = {}
        
        for line in lines:
            line = line.strip()
            
            if line.lower().startswith(('issue:', 'problem:', 'warning:', 'error:')):
                if current_issue:
                    issue = self._create_text_issue(current_issue, file_path, len(issues))
                    if issue:
                        issues.append(issue)
                
                current_issue = {"title": line}
            elif line and current_issue:
                current_issue["description"] = current_issue.get("description", "") + " " + line
        
        # Add the last issue
        if current_issue:
            issue = self._create_text_issue(current_issue, file_path, len(issues))
            if issue:
                issues.append(issue)
        
        return issues
    
    def _create_text_issue(self, text_issue: dict, file_path: str, index: int) -> Issue:
        """Create an Issue from text parsing."""
        try:
            title = text_issue.get("title", f"AI Review Issue {index + 1}")
            description = text_issue.get("description", "No description provided")
            
            return Issue(
                id=f"ai-review-text-{file_path}-{index}",
                title=f"AI Review: {title}",
                description=description.strip(),
                severity=SeverityLevel.MEDIUM,
                file_path=file_path,
                line_number=None,
                rule_id=f"ai-review-text-{index}",
                fix_suggestion="Review the code based on AI feedback",
                status=IssueStatus.DETECTED
            )
        
        except Exception:
            return None
    
    def _map_ai_severity(self, ai_severity: str) -> SeverityLevel:
        """Map AI severity to our severity levels."""
        severity_map = {
            "critical": SeverityLevel.CRITICAL,
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW
        }
        
        return severity_map.get(ai_severity.lower(), SeverityLevel.MEDIUM)
