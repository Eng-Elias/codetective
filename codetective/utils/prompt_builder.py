"""
Prompt template construction for Notebook-RAG application.
"""

from typing import Union, List, Dict, Any, Optional

class PromptBuilder:
    """Class for building and managing prompts."""
    
    @staticmethod
    def lowercase_first_char(text: str) -> str:
        """
        Lowercase the first character of a string.
        
        Args:
            text: Input string.
            
        Returns:
            The input string with the first character lowercased.
        """
        return text[0].lower() + text[1:] if text else text
    
    @staticmethod
    def format_prompt_section(lead_in: str, value: Union[str, List[str]]) -> str:
        """
        Format a prompt section by joining a lead-in with content.
        
        Args:
            lead_in: Introduction sentence for the section.
            value: Section content, as a string or list of strings.
            
        Returns:
            A formatted string with the lead-in followed by the content.
        """
        if isinstance(value, list):
            formatted_value = "\n".join(f"- {item}" for item in value)
        else:
            formatted_value = value
        return f"{lead_in}\n{formatted_value}"
    
    @staticmethod
    def build_prompt_from_config(
        config: Dict[str, Any],
        input_data: str = "",
        app_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build a complete prompt string based on a config dictionary.
        
        Args:
            config: Dictionary specifying prompt components.
            input_data: Content to be summarized or processed.
            app_config: Optional app-wide configuration (e.g., reasoning strategies).
            
        Returns:
            A fully constructed prompt as a string.
            
        Raises:
            ValueError: If the required 'instruction' field is missing.
        """
        prompt_parts = []
        
        if role := config.get("role"):
            prompt_parts.append(f"You are {PromptBuilder.lowercase_first_char(role.strip())}.")
        
        instruction = config.get("instruction")
        if not instruction:
            raise ValueError("Missing required field: 'instruction'")
        prompt_parts.append(PromptBuilder.format_prompt_section("Your task is as follows:", instruction))
        
        if context := config.get("context"):
            prompt_parts.append(f"Here's some background that may help you:\n{context}")
        
        if constraints := config.get("output_constraints"):
            prompt_parts.append(
                PromptBuilder.format_prompt_section(
                    "Ensure your response follows these rules:", constraints
                )
            )
        
        if tone := config.get("style_or_tone"):
            prompt_parts.append(
                PromptBuilder.format_prompt_section(
                    "Follow these style and tone guidelines in your response:", tone
                )
            )
        
        if format_ := config.get("output_format"):
            prompt_parts.append(
                PromptBuilder.format_prompt_section("Structure your response as follows:", format_)
            )
        
        if examples := config.get("examples"):
            prompt_parts.append("Here are some examples to guide your response:")
            if isinstance(examples, list):
                for i, example in enumerate(examples, 1):
                    prompt_parts.append(f"Example {i}:\n{example}")
            else:
                prompt_parts.append(str(examples))
        
        if goal := config.get("goal"):
            prompt_parts.append(f"Your goal is to achieve the following outcome:\n{goal}")
        
        if input_data:
            prompt_parts.append(
                "Here is the content you need to work with:\n"
                "<<<BEGIN CONTENT>>>\n"
                "```\n" + input_data.strip() + "\n```\n<<<END CONTENT>>>"
            )
        
        reasoning_strategy = config.get("reasoning_strategy")
        if reasoning_strategy and reasoning_strategy != "None" and app_config:
            strategies = app_config.get("reasoning_strategies", {})
            if strategy_text := strategies.get(reasoning_strategy):
                prompt_parts.append(strategy_text.strip())
        
        prompt_parts.append("Now perform the task as instructed above.")
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def build_system_prompt_from_config(
        config: Dict[str, Any],
        document_content: str = "",
    ) -> str:
        """
        Build a system prompt string based on a config dictionary.
        
        Args:
            config: Dictionary specifying system prompt components.
            document_content: The document content to include in the system prompt.
            
        Returns:
            A fully constructed system prompt as a string.
            
        Raises:
            ValueError: If the required 'role' field is missing.
        """
        prompt_parts = []
        
        # Role is required for system prompts
        role = config.get("role")
        if not role:
            raise ValueError("Missing required field: 'role'")
        prompt_parts.append(f"You are {PromptBuilder.lowercase_first_char(role.strip())}.")
        
        # Add behavioral constraints
        if constraints := config.get("output_constraints"):
            prompt_parts.append(
                PromptBuilder.format_prompt_section(
                    "Follow these important guidelines:", constraints
                )
            )
        
        # Add style and tone guidelines
        if tone := config.get("style_or_tone"):
            prompt_parts.append(
                PromptBuilder.format_prompt_section(
                    "Communication style:", tone
                )
            )
        
        # Add output format requirements
        if format_ := config.get("output_format"):
            prompt_parts.append(
                PromptBuilder.format_prompt_section("Response formatting:", format_)
            )
        
        # Add goal if specified
        if goal := config.get("goal"):
            prompt_parts.append(f"Your primary objective: {goal}")
        
        # Include document content if provided
        if document_content:
            prompt_parts.append(
                "Base your responses on this document content:\n\n"
                "=== DOCUMENT CONTENT ===\n"
                f"{document_content.strip()}\n"
                "=== END DOCUMENT CONTENT ==="
            )
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def print_prompt_preview(prompt: str, max_length: int = 500) -> None:
        """
        Print a preview of the constructed prompt for debugging purposes.
        
        Args:
            prompt: The constructed prompt string.
            max_length: Maximum number of characters to show.
        """
        print("=" * 60)
        print("CONSTRUCTED PROMPT:")
        print("=" * 60)
        if len(prompt) > max_length:
            print(prompt[:max_length] + "...")
            print(f"\n[Truncated - Full prompt is {len(prompt)} characters]")
        else:
            print(prompt)
        print("=" * 60)
