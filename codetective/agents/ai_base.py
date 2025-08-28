"""
Base class for AI-powered agents using ChatOllama.
"""

from langchain.schema import HumanMessage
from langchain_ollama import ChatOllama

from codetective.core.config import Config
from codetective.utils import SystemUtils
from codetective.utils.system_utils import RequiredTools


class AIAgent:
    """Base class for agents that use AI capabilities."""

    def __init__(self, config: Config):
        self.config = config
        self.ollama_url = config.ollama_base_url
        self.model = config.ollama_model or "qwen3:4b"
        self._llm: ChatOllama | None = None

    @property
    def llm(self) -> ChatOllama:
        """Lazy initialization of ChatOllama instance."""
        if self._llm is None:
            self._llm = ChatOllama(base_url=self.ollama_url, model=self.model, temperature=0.1)
        return self._llm

    def is_ai_available(self) -> bool:
        """Check if Ollama is available for AI operations."""
        available, _ = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)
        return available

    def call_ai(self, prompt: str, temperature: float = 0.1) -> str:
        """Call AI with consistent error handling."""
        try:
            # Update temperature if different from default
            if temperature != 0.1:
                self._llm = ChatOllama(base_url=self.ollama_url, model=self.model, temperature=temperature)

            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            return str(response.content)
        except Exception as e:
            error_msg = self._format_ai_error(e)
            raise Exception(error_msg)

    def _format_ai_error(self, error: Exception) -> str:
        """Format AI errors consistently."""
        error_str = str(error).lower()

        if "connection" in error_str or "connect" in error_str:
            return f"Cannot connect to Ollama server at {self.ollama_url}. Please ensure Ollama is running and accessible."
        elif "timeout" in error_str:
            return f"Ollama request timed out after {self.config.agent_timeout} seconds"
        elif "404" in error_str or "not found" in error_str:
            return f"Model '{self.model}' not found in Ollama. Please pull the model first: ollama pull {self.model}"
        else:
            return f"Unexpected error calling Ollama: {str(error)}"

    def clean_ai_response(self, response: str) -> str:
        """Clean AI response by removing thinking tags and extra content."""
        if not response:
            return ""

        # Remove thinking tags and content between them
        import re

        cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<thinking>.*?</thinking>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Remove extra whitespace and newlines
        cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned.strip())

        return cleaned if cleaned else response.strip()
