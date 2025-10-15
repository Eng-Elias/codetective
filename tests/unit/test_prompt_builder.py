"""
Unit tests for PromptBuilder.
"""

import pytest
from unittest.mock import patch
import io

from codetective.utils.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Test cases for PromptBuilder."""

    @pytest.mark.unit
    def test_lowercase_first_char(self):
        """Test lowercasing the first character."""
        assert PromptBuilder.lowercase_first_char("Hello") == "hello"
        assert PromptBuilder.lowercase_first_char("WORLD") == "wORLD"
        assert PromptBuilder.lowercase_first_char("a") == "a"

    @pytest.mark.unit
    def test_lowercase_first_char_empty_string(self):
        """Test lowercasing first character of empty string."""
        assert PromptBuilder.lowercase_first_char("") == ""

    @pytest.mark.unit
    def test_lowercase_first_char_single_char(self):
        """Test lowercasing single character."""
        assert PromptBuilder.lowercase_first_char("A") == "a"

    @pytest.mark.unit
    def test_format_prompt_section_with_string(self):
        """Test formatting section with string value."""
        result = PromptBuilder.format_prompt_section(
            "Introduction:",
            "This is the content"
        )
        
        assert "Introduction:" in result
        assert "This is the content" in result
        assert result.startswith("Introduction:")

    @pytest.mark.unit
    def test_format_prompt_section_with_list(self):
        """Test formatting section with list value."""
        result = PromptBuilder.format_prompt_section(
            "Rules:",
            ["Rule 1", "Rule 2", "Rule 3"]
        )
        
        assert "Rules:" in result
        assert "- Rule 1" in result
        assert "- Rule 2" in result
        assert "- Rule 3" in result

    @pytest.mark.unit
    def test_format_prompt_section_empty_list(self):
        """Test formatting section with empty list."""
        result = PromptBuilder.format_prompt_section("Title:", [])
        
        assert "Title:" in result
        # Should have lead-in and newline even with empty list
        assert len(result.split("\n")) >= 1

    @pytest.mark.unit
    def test_build_prompt_from_config_minimal(self):
        """Test building prompt with minimal config."""
        config = {"instruction": "Do something"}
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Your task is as follows:" in prompt
        assert "Do something" in prompt
        assert "Now perform the task as instructed above" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_missing_instruction(self):
        """Test building prompt without instruction raises error."""
        config = {"role": "a helpful assistant"}
        
        with pytest.raises(ValueError, match="Missing required field: 'instruction'"):
            PromptBuilder.build_prompt_from_config(config)

    @pytest.mark.unit
    def test_build_prompt_from_config_with_role(self):
        """Test building prompt with role."""
        config = {
            "role": "A helpful assistant",
            "instruction": "Help the user"
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "You are a helpful assistant" in prompt  # Lowercased first char

    @pytest.mark.unit
    def test_build_prompt_from_config_with_context(self):
        """Test building prompt with context."""
        config = {
            "instruction": "Analyze code",
            "context": "This is a Python project"
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Here's some background that may help you:" in prompt
        assert "This is a Python project" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_constraints(self):
        """Test building prompt with output constraints."""
        config = {
            "instruction": "Generate code",
            "output_constraints": ["Be concise", "Use proper formatting"]
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Ensure your response follows these rules:" in prompt
        assert "- Be concise" in prompt
        assert "- Use proper formatting" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_tone(self):
        """Test building prompt with style/tone."""
        config = {
            "instruction": "Write a response",
            "style_or_tone": "Professional and friendly"
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Follow these style and tone guidelines" in prompt
        assert "Professional and friendly" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_format(self):
        """Test building prompt with output format."""
        config = {
            "instruction": "Provide analysis",
            "output_format": "JSON with keys: summary, details"
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Structure your response as follows:" in prompt
        assert "JSON with keys" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_examples_list(self):
        """Test building prompt with list of examples."""
        config = {
            "instruction": "Format text",
            "examples": ["Example 1 text", "Example 2 text"]
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Here are some examples to guide your response:" in prompt
        assert "Example 1:" in prompt
        assert "Example 1 text" in prompt
        assert "Example 2:" in prompt
        assert "Example 2 text" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_examples_string(self):
        """Test building prompt with string example."""
        config = {
            "instruction": "Do task",
            "examples": "Single example"
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Here are some examples to guide your response:" in prompt
        assert "Single example" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_goal(self):
        """Test building prompt with goal."""
        config = {
            "instruction": "Process data",
            "goal": "Achieve maximum accuracy"
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        assert "Your goal is to achieve the following outcome:" in prompt
        assert "Achieve maximum accuracy" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_input_data(self):
        """Test building prompt with input data."""
        config = {"instruction": "Analyze this"}
        input_data = "Some code to analyze"
        
        prompt = PromptBuilder.build_prompt_from_config(config, input_data=input_data)
        
        assert "Here is the content you need to work with:" in prompt
        assert "<<<BEGIN CONTENT>>>" in prompt
        assert "Some code to analyze" in prompt
        assert "<<<END CONTENT>>>" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_with_reasoning_strategy(self):
        """Test building prompt with reasoning strategy."""
        config = {
            "instruction": "Think deeply",
            "reasoning_strategy": "chain_of_thought"
        }
        app_config = {
            "reasoning_strategies": {
                "chain_of_thought": "Think step by step"
            }
        }
        
        prompt = PromptBuilder.build_prompt_from_config(
            config,
            app_config=app_config
        )
        
        assert "Think step by step" in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_reasoning_strategy_none(self):
        """Test reasoning strategy with 'None' value."""
        config = {
            "instruction": "Do task",
            "reasoning_strategy": "None"
        }
        app_config = {
            "reasoning_strategies": {
                "None": "Should not appear"
            }
        }
        
        prompt = PromptBuilder.build_prompt_from_config(
            config,
            app_config=app_config
        )
        
        # "None" strategy should be skipped
        assert "Should not appear" not in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_reasoning_missing_strategy(self):
        """Test reasoning strategy not in app_config."""
        config = {
            "instruction": "Task",
            "reasoning_strategy": "nonexistent"
        }
        app_config = {
            "reasoning_strategies": {
                "other": "Other strategy"
            }
        }
        
        prompt = PromptBuilder.build_prompt_from_config(
            config,
            app_config=app_config
        )
        
        # Should not crash, just skip missing strategy
        assert "nonexistent" not in prompt

    @pytest.mark.unit
    def test_build_prompt_from_config_complete(self):
        """Test building prompt with all components."""
        config = {
            "role": "Expert Code Reviewer",
            "instruction": "Review the code for security issues",
            "context": "This is a web application",
            "output_constraints": ["Be specific", "Provide examples"],
            "style_or_tone": "Professional",
            "output_format": "JSON format",
            "examples": ["Example review"],
            "goal": "Find all vulnerabilities"
        }
        input_data = "def vulnerable_function(): pass"
        
        prompt = PromptBuilder.build_prompt_from_config(config, input_data=input_data)
        
        # Check all sections are present
        assert "You are expert code reviewer".lower() in prompt.lower()
        assert "Your task is as follows:".lower() in prompt.lower()
        assert "Review the code for security issues".lower() in prompt.lower()
        assert "Here's some background".lower() in prompt.lower()
        assert "Ensure your response follows these rules:".lower() in prompt.lower()
        assert "Follow these style and tone guidelines".lower() in prompt.lower()
        assert "Structure your response as follows:".lower() in prompt.lower()
        assert "Here are some examples".lower() in prompt.lower()
        assert "Your goal is to achieve".lower() in prompt.lower()
        assert "Here is the content you need to work with:".lower() in prompt.lower()
        assert "def vulnerable_function".lower() in prompt.lower()
        assert "Now perform the task as instructed above".lower() in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_from_config_minimal(self):
        """Test building system prompt with minimal config."""
        config = {"role": "A helpful assistant"}
        
        prompt = PromptBuilder.build_system_prompt_from_config(config)
        
        assert "You are a helpful assistant".lower() in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_from_config_missing_role(self):
        """Test building system prompt without role raises error."""
        config = {"instruction": "Help users"}
        
        with pytest.raises(ValueError, match="Missing required field: 'role'"):
            PromptBuilder.build_system_prompt_from_config(config)

    @pytest.mark.unit
    def test_build_system_prompt_from_config_with_constraints(self):
        """Test building system prompt with constraints."""
        config = {
            "role": "Security Expert",
            "output_constraints": ["Always verify sources", "Be thorough"]
        }
        
        prompt = PromptBuilder.build_system_prompt_from_config(config)
        
        assert "Follow these important guidelines:".lower() in prompt.lower()
        assert "- Always verify sources".lower() in prompt.lower()
        assert "- Be thorough".lower() in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_from_config_with_tone(self):
        """Test building system prompt with tone."""
        config = {
            "role": "Code Reviewer",
            "style_or_tone": "Constructive and encouraging"
        }
        
        prompt = PromptBuilder.build_system_prompt_from_config(config)
        
        assert "Communication style:".lower() in prompt.lower()
        assert "Constructive and encouraging".lower() in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_from_config_with_format(self):
        """Test building system prompt with format."""
        config = {
            "role": "Analyzer",
            "output_format": "Structured JSON output"
        }
        
        prompt = PromptBuilder.build_system_prompt_from_config(config)
        
        assert "Response formatting:".lower() in prompt.lower()
        assert "Structured JSON output".lower() in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_from_config_with_goal(self):
        """Test building system prompt with goal."""
        config = {
            "role": "Assistant",
            "goal": "Maximize user satisfaction"
        }
        
        prompt = PromptBuilder.build_system_prompt_from_config(config)
        
        assert "Your primary objective:".lower() in prompt.lower()
        assert "Maximize user satisfaction".lower() in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_from_config_with_document(self):
        """Test building system prompt with document content."""
        config = {"role": "Document Assistant"}
        document = "# Documentation\nSome content here"
        
        prompt = PromptBuilder.build_system_prompt_from_config(
            config,
            document_content=document
        )
        
        assert "Base your responses on this document content:".lower() in prompt.lower()
        assert "=== DOCUMENT CONTENT ===".lower() in prompt.lower()
        assert "# Documentation".lower() in prompt.lower()
        assert "=== END DOCUMENT CONTENT ===".lower() in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_from_config_complete(self):
        """Test building system prompt with all components."""
        config = {
            "role": "Expert AI Assistant",
            "output_constraints": ["Be accurate", "Cite sources"],
            "style_or_tone": "Professional and clear",
            "output_format": "Markdown with headers",
            "goal": "Provide comprehensive assistance"
        }
        document = "API Documentation"
        
        prompt = PromptBuilder.build_system_prompt_from_config(
            config,
            document_content=document
        )
        
        # Verify all sections
        assert "You are expert AI assistant".lower() in prompt.lower()
        assert "Follow these important guidelines:".lower() in prompt.lower()
        assert "Communication style:".lower() in prompt.lower()
        assert "Response formatting:".lower() in prompt.lower()
        assert "Your primary objective:".lower() in prompt.lower()
        assert "Base your responses on this document content:".lower() in prompt.lower()

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_print_prompt_preview_short(self, mock_stdout):
        """Test printing short prompt preview."""
        prompt = "Short prompt"
        
        PromptBuilder.print_prompt_preview(prompt, max_length=500)
        
        output = mock_stdout.getvalue()
        assert "CONSTRUCTED PROMPT:".lower() in output.lower()
        assert "Short prompt".lower() in output.lower()
        assert "Truncated".lower() not in output.lower()

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_print_prompt_preview_long(self, mock_stdout):
        """Test printing long prompt preview with truncation."""
        prompt = "a" * 1000  # Long prompt
        
        PromptBuilder.print_prompt_preview(prompt, max_length=100)
        
        output = mock_stdout.getvalue()
        assert "CONSTRUCTED PROMPT:".lower() in output.lower()
        assert "[Truncated".lower() in output.lower()
        assert "1000 characters]".lower() in output.lower()

    @pytest.mark.unit
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_print_prompt_preview_exactly_max_length(self, mock_stdout):
        """Test printing prompt exactly at max length."""
        prompt = "a" * 500
        
        PromptBuilder.print_prompt_preview(prompt, max_length=500)
        
        output = mock_stdout.getvalue()
        # Should not truncate if exactly at max length
        assert "Truncated".lower() not in output.lower()

    @pytest.mark.unit
    def test_build_prompt_input_data_strips_whitespace(self):
        """Test that input data is stripped of surrounding whitespace."""
        config = {"instruction": "Process"}
        input_data = "\n\n   Code here   \n\n"
        
        prompt = PromptBuilder.build_prompt_from_config(config, input_data=input_data)
        
        # Should have trimmed whitespace
        assert "Code here".lower() in prompt.lower()
        assert "   Code here   ".lower() not in prompt.lower()

    @pytest.mark.unit
    def test_build_system_prompt_document_strips_whitespace(self):
        """Test that document content is stripped of whitespace."""
        config = {"role": "Assistant"}
        document = "\n\n  Document content  \n\n"
        
        prompt = PromptBuilder.build_system_prompt_from_config(
            config,
            document_content=document
        )
        
        # Should have trimmed whitespace
        assert "Document content".lower() in prompt.lower()
        assert "  Document content  ".lower() not in prompt.lower()

    @pytest.mark.unit
    def test_build_prompt_role_strips_whitespace(self):
        """Test that role is stripped of whitespace."""
        config = {
            "role": "  Code Expert  ",
            "instruction": "Review code"
        }
        
        prompt = PromptBuilder.build_prompt_from_config(config)
        
        # Should be trimmed and lowercased first char
        assert "You are code expert".lower() in prompt.lower()
