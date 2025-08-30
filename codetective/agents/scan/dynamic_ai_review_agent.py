"""
Dynamic AI Review agent using LangChain with autonomous tool use.
"""

from pathlib import Path
from typing import Any, Dict, List

from langchain.tools import Tool
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from codetective.agents.ai_base import AIAgent
from codetective.agents.base import ScanAgent
from codetective.core.config import Config
from codetective.core.search import SearchTool
from codetective.models.schemas import AgentType, Issue
from codetective.utils import FileUtils
from codetective.utils.prompt_builder import PromptBuilder


class DynamicAIReviewAgent(ScanAgent, AIAgent):
    """Dynamic AI Review agent with autonomous tool use."""

    def __init__(self, config: Config):
        ScanAgent.__init__(self, config)
        AIAgent.__init__(self, config)
        self.agent_type = AgentType.AI_REVIEW
        self.search_tool = SearchTool()

        # Try to create agent with tool calling, fallback if not supported
        try:
            self.agent: CompiledStateGraph | None = self._create_agent()
            self.supports_tools = True
        except Exception as e:
            print(f"Warning: Model {self.model} doesn't support tool calling: {e}")
            print("Falling back to simple agent without tools")
            self.agent = None
            self.supports_tools = False

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return self.is_ai_available()

    def _create_agent(self) -> CompiledStateGraph:
        """Create LangGraph ReAct agent with search tools."""
        tools = [
            Tool(
                name="search",
                description="""
                    Search the web for information about security vulnerabilities, best practices, or code patterns.
                    Use this when you need current information about security issues, coding standards, or documentation.
                """,
                func=self._search_tool,
            ),
            Tool(
                name="search_with_content",
                description="""
                    Search the web and fetch full content from URLs for detailed information.
                    Use this when you need comprehensive details about
                    security vulnerabilities, documentation, or best practices.
                """,
                func=self._search_with_content_tool,
            ),
            Tool(
                name="search_security",
                description="""
                    Search for specific security vulnerability information.
                    Provide CVE ID or vulnerability type.
                """,
                func=self._search_security_tool,
            ),
        ]

        # Create LangGraph ReAct agent
        return create_react_agent(
            model=self.llm,
            tools=tools,
            prompt="""
            You are an expert code security reviewer.
            Analyze code for security vulnerabilities, code quality issues, and best practice violations.
            Use the available search tools to get current information about security patterns
            and best practices when needed.
            """,
        )

    def _search_tool(self, query: str) -> str:
        """Search tool for the agent."""
        try:
            results = self.search_tool.search(query)
            if not results:
                return "No search results found."

            formatted_results = []
            for i, result in enumerate(results[:3], 1):
                formatted_results.append(f"{i}. {result['title']}\n   {result['body']}\n   URL: {result['url']}\n")

            return "\n".join(formatted_results)
        except Exception as e:
            return f"Search failed: {e}"

    def _search_with_content_tool(self, query: str) -> str:
        """Search with full content fetching."""
        try:
            results = self.search_tool.search_with_content(query, fetch_content=True)
            if not results:
                return "No search results found."

            formatted_results = []
            for i, result in enumerate(results[:2], 1):  # Limit to 2 for content fetching
                content = result.get("full_content", result.get("body", ""))
                formatted_results.append(f"{i}. {result['title']}\n   Content: {content[:1000]}...\n   URL: {result['url']}\n")

            return "\n".join(formatted_results)
        except Exception as e:
            return f"Content search failed: {e}"

    def _search_security_tool(self, query: str) -> List[Dict[str, Any]] | None:
        """Search for security vulnerability information."""
        try:
            # Add security-specific keywords
            security_query = f"security vulnerability {query} CVE"
            return self.search_tool.search(security_query)
        except Exception:
            return None

    def scan_files(self, files: List[str], **kwargs: Any) -> List[Issue]:
        """Scan files using dynamic AI review."""
        issues = []

        # Get supported files
        supported_extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".sh",
        ]

        supported_files = self._get_supported_files(files, supported_extensions)

        # Limit number of files to avoid overwhelming
        max_files = 10  # Reduced for better performance
        if len(supported_files) > max_files:
            supported_files = supported_files[:max_files]

        for file_path in supported_files:
            try:
                file_issues = self._review_file_dynamic(file_path)
                issues.extend(file_issues)
            except Exception as e:
                print(f"Error reviewing {file_path}: {e}")
                continue

        return issues

    def _review_file_dynamic(self, file_path: str) -> List[Issue]:
        """Review a single file using dynamic AI agent."""
        issues: List[Issue] = []

        # Read file content
        content = FileUtils.get_file_content(file_path)  # Limit for better processing

        if not content or content.startswith("Error reading file"):
            return issues

        # Create dynamic prompt for the agent
        file_extension = Path(file_path).suffix
        language = self._detect_language(file_extension)

        input_data = f"""File: {file_path}
Language: {language}
Code:
```{file_extension[1:] if file_extension else 'text'}
{content}
```"""

        config = {
            "role": "an expert code security reviewer",
            "instruction": f"Analyze this {language} code file for security issues and code quality problems.",
            "output_constraints": [
                "Keep response under 500 words",
                "Focus on the most critical issues only",
                "No thinking tags or extra text",
                "Provide specific line numbers when applicable",
            ],
            "output_format": [
                "SECURITY ISSUES:",
                "- [Issue description with line number if applicable]",
                "",
                "CODE QUALITY:",
                "- [Quality issue description]",
                "",
                "RECOMMENDATIONS:",
                "- [Specific actionable fixes]",
            ],
        }

        prompt = PromptBuilder.build_prompt_from_config(config, input_data)

        try:
            if self.supports_tools and self.agent:
                # Use the LangGraph agent to analyze the code
                messages = self.agent.invoke({"messages": [("human", prompt)]})

                # Get the last message content as response
                response = messages["messages"][-1].content
            else:
                # Fallback: Use direct LLM call with search context
                search_context = self._get_search_context(file_path, content)
                enhanced_prompt = f"{search_context}\n\n{prompt}"

                response = self.call_ai(enhanced_prompt)

            # Clean response using base class method
            cleaned_response = self.clean_ai_response(response)

            # Parse the response to create Issue objects
            ai_issues = self._parse_agent_response(cleaned_response, file_path)
            issues.extend(ai_issues)

        except Exception as e:
            print(f"Error in dynamic review: {e}")
            pass

        return issues

    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension."""
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React JSX",
            ".tsx": "React TSX",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C Header",
            ".hpp": "C++ Header",
            ".cs": "C#",
            ".php": "PHP",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".sh": "Shell Script",
        }
        return language_map.get(file_extension, "Unknown")

    def _parse_agent_response(self, response: str, file_path: str) -> List[Issue]:
        """Parse agent response into simplified Issue objects."""
        issues = []

        # Generate a simple title from file path and agent name
        file_name = Path(file_path).name
        title = f"AI Review: {file_name}"

        # Create a single Issue object with the AI response as description
        issue = Issue(id=f"ai-review-{hash(file_path + response)}", title=title, description=response, file_path=file_path)
        issues.append(issue)

        return issues

    def _get_search_context(self, file_path: str, content: str) -> str:
        """Get search context for fallback mode when tools aren't supported."""
        try:
            # Detect language and common patterns
            file_extension = Path(file_path).suffix.lower()
            language = self._detect_language(file_extension)

            # Search for security best practices for this language
            security_context = self.search_tool.search(f"{language} security best practices vulnerabilities")

            # Look for specific patterns that might need context
            patterns_to_search = []
            if "sql" in content.lower() or "query" in content.lower():
                patterns_to_search.append("SQL injection prevention")
            if "password" in content.lower() or "auth" in content.lower():
                patterns_to_search.append("authentication security best practices")
            if "input" in content.lower() or "request" in content.lower():
                patterns_to_search.append("input validation security")

            pattern_context = ""
            for pattern in patterns_to_search[:2]:  # Limit to 2 searches
                try:
                    result = self.search_tool.search(pattern)
                    pattern_context += f"\n{pattern}: {result[:300]}..."
                except Exception as e:
                    print(f"Error searching for pattern {pattern}: {e}")
                    continue

            return f"""
SECURITY CONTEXT (from web search):
{language} Security Best Practices:
{security_context[:500]}...

Specific Pattern Context:
{pattern_context}

Use this context to inform your analysis of the code below.
"""
        except Exception as e:
            return f"Search context unavailable: {str(e)}"
