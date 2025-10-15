"""
Unit tests for AIAgent base class.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from codetective.agents.ai_base import AIAgent
from codetective.core.config import Config


class TestAIAgent:
    """Test cases for AIAgent base class."""

    def test_ai_agent_init(self, base_config):
        """Test AIAgent initialization."""
        agent = AIAgent(base_config)
        
        assert agent.config == base_config
        assert agent.ollama_url == base_config.ollama_base_url
        assert agent.model == base_config.ollama_model
        assert agent._llm is None

    def test_llm_lazy_initialization(self, base_config, mock_chat_ollama):
        """Test lazy initialization of ChatOllama."""
        agent = AIAgent(base_config)
        
        # LLM should be None initially
        assert agent._llm is None
        
        # Accessing llm property should initialize it
        llm = agent.llm
        assert llm is not None

    def test_is_ai_available_true(self, base_config):
        """Test is_ai_available when Ollama is available."""
        agent = AIAgent(base_config)
        
        with patch('codetective.utils.SystemUtils.check_tool_availability', return_value=(True, "1.0.0")):
            assert agent.is_ai_available() is True

    def test_is_ai_available_false(self, base_config):
        """Test is_ai_available when Ollama is unavailable."""
        agent = AIAgent(base_config)
        
        with patch('codetective.utils.SystemUtils.check_tool_availability', return_value=(False, None)):
            assert agent.is_ai_available() is False

    def test_call_ai_success(self, base_config, mock_chat_ollama, mock_ollama_response):
        """Test successful AI call."""
        agent = AIAgent(base_config)
        
        result = agent.call_ai("Test prompt")
        
        assert result == "This is a test AI response"
        mock_chat_ollama.invoke.assert_called_once()

    def test_call_ai_with_custom_temperature(self, base_config):
        """Test AI call with custom temperature."""
        agent = AIAgent(base_config)
        
        mock_response = Mock()
        mock_response.content = "Response with custom temp"
        
        with patch('codetective.agents.ai_base.ChatOllama') as MockChatOllama:
            mock_instance = Mock()
            mock_instance.invoke.return_value = mock_response
            MockChatOllama.return_value = mock_instance
            
            result = agent.call_ai("Test prompt", temperature=0.7)
            
            assert result == "Response with custom temp"
            # Verify new ChatOllama instance was created with custom temperature
            MockChatOllama.assert_called_with(
                base_url=base_config.ollama_base_url,
                model=base_config.ollama_model,
                temperature=0.7
            )

    def test_call_ai_connection_error(self, base_config, mock_chat_ollama):
        """Test AI call with connection error."""
        agent = AIAgent(base_config)
        mock_chat_ollama.invoke.side_effect = Exception("Connection refused")
        
        with pytest.raises(Exception) as exc_info:
            agent.call_ai("Test prompt")
        
        assert "cannot connect to ollama" in str(exc_info.value).lower()

    def test_call_ai_timeout_error(self, base_config, mock_chat_ollama):
        """Test AI call with timeout error."""
        agent = AIAgent(base_config)
        mock_chat_ollama.invoke.side_effect = Exception("Request timeout")
        
        with pytest.raises(Exception) as exc_info:
            agent.call_ai("Test prompt")
        
        error_msg = str(exc_info.value).lower()
        assert "timed out" in error_msg or "timeout" in error_msg

    def test_call_ai_model_not_found_error(self, base_config, mock_chat_ollama):
        """Test AI call with model not found error."""
        agent = AIAgent(base_config)
        mock_chat_ollama.invoke.side_effect = Exception("404 not found")
        
        with pytest.raises(Exception) as exc_info:
            agent.call_ai("Test prompt")
        
        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg
        assert "pull" in error_msg

    def test_format_ai_error_connection(self, base_config):
        """Test formatting connection error."""
        agent = AIAgent(base_config)
        
        error = Exception("Connection refused by server")
        formatted = agent._format_ai_error(error)
        
        assert "cannot connect" in formatted.lower()
        assert agent.ollama_url in formatted

    def test_format_ai_error_timeout(self, base_config):
        """Test formatting timeout error."""
        agent = AIAgent(base_config)
        
        error = Exception("Request timed out")
        formatted = agent._format_ai_error(error)
        
        error_msg = formatted.lower()
        assert "timed out" in error_msg or "timeout" in error_msg

    def test_format_ai_error_model_not_found(self, base_config):
        """Test formatting model not found error."""
        agent = AIAgent(base_config)
        
        error = Exception("404: Model not found")
        formatted = agent._format_ai_error(error)
        
        assert "not found" in formatted.lower()
        assert agent.model in formatted
        assert "pull" in formatted.lower()

    def test_format_ai_error_generic(self, base_config):
        """Test formatting generic error."""
        agent = AIAgent(base_config)
        
        error = Exception("Some unexpected error")
        formatted = agent._format_ai_error(error)
        
        assert "unexpected error" in formatted.lower()
        assert "Some unexpected error" in formatted

    def test_clean_ai_response_basic(self, base_config):
        """Test cleaning basic AI response."""
        agent = AIAgent(base_config)
        
        response = "This is a clean response"
        cleaned = agent.clean_ai_response(response)
        
        assert cleaned == "This is a clean response"

    def test_clean_ai_response_with_thinking_tags(self, base_config):
        """Test cleaning response with thinking tags."""
        agent = AIAgent(base_config)
        
        response = "<think>Internal thoughts here</think>The actual response"
        cleaned = agent.clean_ai_response(response)
        
        assert "<think>" not in cleaned
        assert "Internal thoughts" not in cleaned
        assert "actual response" in cleaned

    def test_clean_ai_response_with_thinking_tags_uppercase(self, base_config):
        """Test cleaning response with uppercase THINKING tags."""
        agent = AIAgent(base_config)
        
        response = "<THINKING>Processing...</THINKING>Final answer"
        cleaned = agent.clean_ai_response(response)
        
        assert "<THINKING>" not in cleaned
        assert "Processing" not in cleaned
        assert "Final answer" in cleaned

    def test_clean_ai_response_multiple_tags(self, base_config):
        """Test cleaning response with multiple thinking tags."""
        agent = AIAgent(base_config)
        
        response = """
        <think>First thought</think>
        Some content
        <thinking>Second thought</thinking>
        More content
        """
        cleaned = agent.clean_ai_response(response)
        
        assert "<think>" not in cleaned
        assert "<thinking>" not in cleaned
        assert "First thought" not in cleaned
        assert "Second thought" not in cleaned
        assert "Some content" in cleaned
        assert "More content" in cleaned

    def test_clean_ai_response_removes_extra_whitespace(self, base_config):
        """Test cleaning response removes extra whitespace."""
        agent = AIAgent(base_config)
        
        response = "Line 1\n\n\n\nLine 2\n\n\nLine 3"
        cleaned = agent.clean_ai_response(response)
        
        # Should reduce multiple newlines to double newlines
        assert "\n\n\n" not in cleaned
        assert "Line 1" in cleaned
        assert "Line 2" in cleaned
        assert "Line 3" in cleaned

    def test_clean_ai_response_empty_string(self, base_config):
        """Test cleaning empty response."""
        agent = AIAgent(base_config)
        
        cleaned = agent.clean_ai_response("")
        
        assert cleaned == ""

    def test_clean_ai_response_none_value(self, base_config):
        """Test cleaning None response."""
        agent = AIAgent(base_config)
        
        cleaned = agent.clean_ai_response(None)
        
        assert cleaned == ""

    def test_clean_ai_response_multiline_thinking(self, base_config):
        """Test cleaning multiline thinking content."""
        agent = AIAgent(base_config)
        
        response = """
        <think>
        This is a long
        multi-line thinking process
        with lots of details
        </think>
        This is the actual answer.
        """
        cleaned = agent.clean_ai_response(response)
        
        assert "multi-line thinking" not in cleaned
        assert "lots of details" not in cleaned
        assert "actual answer" in cleaned
