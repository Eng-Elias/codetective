"""
AI review agent for intelligent code analysis.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from codetective.agents.base import BaseAgent, AnalysisResult
from codetective.models.workflow_state import WorkflowState
from codetective.models.configuration import AIReviewConfig
from codetective.models.agent_results import AIReviewResults, AIReviewIssue
from codetective.utils.file_processor import FileProcessor


class AIReviewAgent(BaseAgent):
    """
    AI review agent for intelligent code analysis.
    
    This agent uses LLM providers to perform intelligent code review,
    identifying issues related to security, performance, maintainability,
    and best practices.
    """
    
    def __init__(self, config: AIReviewConfig):
        """
        Initialize the AI review agent.
        
        Args:
            config: AI review-specific configuration
        """
        super().__init__(config, "ai_review")
        self.ai_config = config
        self.file_processor = None
        
        # Initialize LLM client
        self._initialize_llm_client()
    
    def _initialize(self) -> None:
        """Initialize AI review-specific setup."""
        self.logger.info("Initializing AI review agent")
        self.logger.info(f"Provider: {self.ai_config.provider}")
        self.logger.info(f"Model: {self.ai_config.model}")
        self.logger.info(f"Focus areas: {self.ai_config.focus_areas}")
    
    def _initialize_llm_client(self) -> None:
        """Initialize the appropriate LLM client based on provider."""
        try:
            if self.ai_config.provider == "openai":
                self._initialize_openai_client()
            elif self.ai_config.provider == "anthropic":
                self._initialize_anthropic_client()
            elif self.ai_config.provider == "gemini":
                self._initialize_gemini_client()
            elif self.ai_config.provider == "ollama":
                self._initialize_ollama_client()
            elif self.ai_config.provider == "lmstudio":
                self._initialize_lmstudio_client()
            else:
                raise ValueError(f"Unsupported AI provider: {self.ai_config.provider}")
            
            self.logger.info(f"Initialized {self.ai_config.provider} client")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {e}")
            raise
    
    def _initialize_openai_client(self) -> None:
        """Initialize OpenAI client."""
        import openai
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.llm_client = openai.OpenAI(api_key=api_key)
    
    def _initialize_anthropic_client(self) -> None:
        """Initialize Anthropic client."""
        import anthropic
        import os
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.llm_client = anthropic.Anthropic(api_key=api_key)
    
    def _initialize_gemini_client(self) -> None:
        """Initialize Gemini client."""
        from google import genai
        import os
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.llm_client = genai.Client(api_key=api_key)
    
    def _initialize_ollama_client(self) -> None:
        """Initialize Ollama client."""
        # For Ollama, we'll use HTTP requests
        import requests
        
        # Test connection to Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                raise ValueError("Ollama server not accessible")
        except requests.RequestException:
            raise ValueError("Ollama server not running or not accessible")
        
        self.llm_client = "ollama"  # We'll handle requests manually
    
    def _initialize_lmstudio_client(self) -> None:
        """Initialize LM Studio client."""
        # For LM Studio, we'll use HTTP requests to the local server
        import requests
        
        # Test connection to LM Studio
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=5)
            if response.status_code != 200:
                raise ValueError("LM Studio server not accessible")
        except requests.RequestException:
            raise ValueError("LM Studio server not running or not accessible")
        
        self.llm_client = "lmstudio"  # We'll handle requests manually
    
    async def analyze(self, state: WorkflowState) -> AnalysisResult:
        """
        Perform AI-powered code review.
        
        Args:
            state: Current workflow state
            
        Returns:
            Analysis result with AI review findings
        """
        start_time = time.time()
        
        try:
            # Initialize file processor
            if not self.file_processor and state.target_files:
                root_path = state.target_files[0].parent
                self.file_processor = FileProcessor(root_path)
            
            # Validate input files
            valid_files = self.validate_input_files(state.target_files)
            if not valid_files:
                return AnalysisResult(
                    success=True,
                    data={"results": AIReviewResults([], "No files to review", self.ai_config.model, 0.0).to_dict()},
                    processing_time=time.time() - start_time,
                    metadata={"message": "No valid files for AI review"}
                )
            
            # Limit files to avoid token limits
            files_to_review = valid_files[:10]  # Limit to 10 files
            
            # Analyze files
            all_issues = []
            for file_path in files_to_review:
                issues = await self._analyze_file(file_path)
                all_issues.extend(issues)
            
            # Create summary
            summary = self._create_review_summary(all_issues, len(files_to_review))
            
            # Create results
            ai_results = AIReviewResults(
                issues=all_issues,
                summary=summary,
                model_used=self.ai_config.model,
                processing_time=time.time() - start_time
            )
            
            # Update workflow state
            state.ai_review_results = ai_results
            
            return AnalysisResult(
                success=True,
                data={"results": ai_results.to_dict()},
                processing_time=time.time() - start_time,
                metadata={
                    "files_reviewed": len(files_to_review),
                    "issues_found": len(all_issues),
                    "provider": self.ai_config.provider,
                    "model": self.ai_config.model,
                }
            )
        
        except Exception as e:
            error_msg = f"AI review failed: {str(e)}"
            self.logger.exception(error_msg)
            
            return AnalysisResult(
                success=False,
                error=error_msg,
                processing_time=time.time() - start_time
            )
    
    async def _analyze_file(self, file_path: Path) -> List[AIReviewIssue]:
        """
        Analyze a single file with AI.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of identified issues
        """
        try:
            # Read file content
            content = self.file_processor.read_file_content(file_path)
            if not content:
                self.logger.warning(f"Could not read file: {file_path}")
                return []
            
            # Limit content size to avoid token limits
            if len(content) > 8000:  # Rough character limit
                content = content[:8000] + "\n... (truncated)"
            
            # Create review prompt
            prompt = self._create_review_prompt(file_path, content)
            
            # Get AI response
            response = await self._call_llm(prompt)
            
            # Parse response into issues
            issues = self._parse_ai_response(response, file_path)
            
            self.logger.info(f"Found {len(issues)} issues in {file_path.name}")
            return issues
        
        except Exception as e:
            self.logger.error(f"Failed to analyze file {file_path}: {e}")
            return []
    
    def _create_review_prompt(self, file_path: Path, content: str) -> str:
        """
        Create a review prompt for the AI.
        
        Args:
            file_path: Path to the file being reviewed
            content: File content
            
        Returns:
            Formatted prompt string
        """
        focus_areas_str = ", ".join(self.ai_config.focus_areas)
        
        prompt = f"""
Please review the following {file_path.suffix} code file for issues related to: {focus_areas_str}.

File: {file_path.name}

Code:
```{file_path.suffix.lstrip('.')}
{content}
```

Please identify specific issues and provide suggestions for improvement. For each issue, provide:
1. Line number(s) where the issue occurs
2. Issue type (security, performance, maintainability, readability, testing, documentation, architecture, best_practices)
3. Severity level (critical, high, medium, low)
4. Description of the issue
5. Specific suggestion for improvement
6. Confidence level (0.0 to 1.0)

Format your response as JSON with this structure:
{{
  "issues": [
    {{
      "line_start": <number>,
      "line_end": <number>,
      "issue_type": "<type>",
      "severity": "<severity>",
      "description": "<description>",
      "suggestion": "<suggestion>",
      "confidence": <number>
    }}
  ]
}}

Focus on actionable, specific issues rather than general observations.
"""
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call the configured LLM with the prompt.
        
        Args:
            prompt: Prompt to send to the LLM
            
        Returns:
            LLM response text
        """
        try:
            if self.ai_config.provider == "openai":
                return await self._call_openai(prompt)
            elif self.ai_config.provider == "anthropic":
                return await self._call_anthropic(prompt)
            elif self.ai_config.provider == "gemini":
                return await self._call_gemini(prompt)
            elif self.ai_config.provider == "ollama":
                return await self._call_ollama(prompt)
            elif self.ai_config.provider == "lmstudio":
                return await self._call_lmstudio(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.ai_config.provider}")
        
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = await asyncio.to_thread(
            self.llm_client.chat.completions.create,
            model=self.ai_config.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.ai_config.max_tokens,
            temperature=self.ai_config.temperature
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        response = await asyncio.to_thread(
            self.llm_client.messages.create,
            model=self.ai_config.model,
            max_tokens=self.ai_config.max_tokens,
            temperature=self.ai_config.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        response = await asyncio.to_thread(
            self.llm_client.models.generate_content,
            model=self.ai_config.model,
            contents=prompt
        )
        return response.text
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama local API."""
        import requests
        
        payload = {
            "model": self.ai_config.model,
            "prompt": prompt,
            "stream": False
        }
        
        response = await asyncio.to_thread(
            requests.post,
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise RuntimeError(f"Ollama API error: {response.status_code}")
    
    async def _call_lmstudio(self, prompt: str) -> str:
        """Call LM Studio local API."""
        import requests
        
        payload = {
            "model": self.ai_config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.ai_config.max_tokens,
            "temperature": self.ai_config.temperature
        }
        
        response = await asyncio.to_thread(
            requests.post,
            "http://localhost:1234/v1/chat/completions",
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise RuntimeError(f"LM Studio API error: {response.status_code}")
    
    def _parse_ai_response(self, response: str, file_path: Path) -> List[AIReviewIssue]:
        """
        Parse AI response into structured issues.
        
        Args:
            response: AI response text
            file_path: Path to the file being reviewed
            
        Returns:
            List of parsed issues
        """
        issues = []
        
        try:
            import json
            
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                for issue_data in data.get("issues", []):
                    try:
                        issue = AIReviewIssue(
                            file_path=str(file_path),
                            line_start=issue_data.get("line_start", 1),
                            line_end=issue_data.get("line_end", issue_data.get("line_start", 1)),
                            issue_type=issue_data.get("issue_type", "general"),
                            severity=issue_data.get("severity", "medium"),
                            description=issue_data.get("description", "No description"),
                            suggestion=issue_data.get("suggestion", "No suggestion"),
                            confidence=float(issue_data.get("confidence", 0.5))
                        )
                        issues.append(issue)
                    
                    except Exception as e:
                        self.logger.warning(f"Failed to parse issue: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            self.logger.debug(f"Response content: {response[:500]}...")
        
        return issues
    
    def _create_review_summary(self, issues: List[AIReviewIssue], files_count: int) -> str:
        """
        Create a summary of the review results.
        
        Args:
            issues: List of identified issues
            files_count: Number of files reviewed
            
        Returns:
            Summary string
        """
        if not issues:
            return f"Reviewed {files_count} files. No significant issues found."
        
        severity_counts = {}
        type_counts = {}
        
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
        
        summary_parts = [
            f"Reviewed {files_count} files and found {len(issues)} issues."
        ]
        
        if severity_counts:
            severity_summary = ", ".join([
                f"{count} {severity}" for severity, count in severity_counts.items()
            ])
            summary_parts.append(f"Severity breakdown: {severity_summary}.")
        
        if type_counts:
            top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            type_summary = ", ".join([f"{count} {issue_type}" for issue_type, count in top_types])
            summary_parts.append(f"Top issue types: {type_summary}.")
        
        return " ".join(summary_parts)
    
    def get_capabilities(self) -> List[str]:
        """Return list of AI review agent capabilities."""
        return [
            "intelligent_analysis",
            "security_review",
            "performance_analysis",
            "maintainability_check",
            "best_practices_validation",
            "architecture_review",
            "documentation_analysis"
        ]
    
    def get_supported_file_extensions(self) -> Optional[List[str]]:
        """Get list of file extensions supported by AI review."""
        return [
            ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h",
            ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala"
        ]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the AI provider configuration."""
        return {
            "provider": self.ai_config.provider,
            "model": self.ai_config.model,
            "max_tokens": self.ai_config.max_tokens,
            "temperature": self.ai_config.temperature,
            "focus_areas": self.ai_config.focus_areas,
        }
