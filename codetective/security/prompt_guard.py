"""
Prompt injection protection for Codetective.

Provides INPUT VALIDATION security controls for:
- Detecting and preventing prompt injection attacks in USER INPUTS
- Input sanitization and length enforcement
- Validating prompts BEFORE sending to AI
- Protecting against malicious user-provided content

NOTE: This module is for INPUT validation only.
For OUTPUT validation (AI responses, generated code), use OutputFilter.
"""

import re
from typing import List, Tuple


class PromptInjectionDetected(Exception):
    """Raised when prompt injection is detected."""
    pass


class PromptGuard:
    """Guards against prompt injection and unsafe content in AI interactions."""

    # Maximum token count (approximate, 1 token ≈ 4 characters)
    MAX_PROMPT_LENGTH = 32000  # ~8000 tokens
    MAX_CODE_BLOCK_LENGTH = 50000  # Larger for code

    # Prompt injection patterns
    INJECTION_PATTERNS = [
        # Direct instruction override
        r"ignore\s+(all\s+)?(previous|above|all|the)\s+(instructions|prompts|commands)",
        r"disregard\s+(all\s+)?(previous|above|all|the)\s+(instructions|prompts)",
        r"forget\s+(everything|all)\s+(above|before|previous)",

        # Role manipulation
        r"you\s+are\s+now\s+a",
        r"act\s+as\s+(if\s+)?you\s+(are|were)",
        r"pretend\s+to\s+be",
        r"roleplay\s+as",
        r"from\s+now\s+on",

        # System prompt escape
        r"</system>",
        r"<system>",
        r"\[system\]",
        r"\[/system\]",
        r"<<<system>>>",

        # Delimiter escape
        r"---\s*end\s+of\s+(instructions|prompt|system)",
        r"\#\#\#\s*end",
        r"```\s*(end|system|admin)",

        # Instruction injection
        r"new\s+instructions?:",
        r"updated\s+instructions?:",
        r"admin\s+mode",
        r"developer\s+mode",
        r"debug\s+mode",

        # Jailbreak attempts
        r"DAN\s+mode",  # "Do Anything Now"
        r"opposite\s+mode",
        r"evil\s+mode",

        # Output manipulation
        r"print\s+(your|the)\s+(prompt|instructions|system|rules)",
        r"show\s+(your|the)\s+(prompt|instructions|system)",
        r"reveal\s+(your|the)\s+(prompt|instructions)",
        r"what\s+(are|were)\s+your\s+(original\s+)?(instructions|prompt)",
    ]

    # NOTE: Removed SUSPICIOUS_CODE_PATTERNS and SENSITIVE_PATTERNS.
    # These are now in OutputFilter for OUTPUT validation.
    # PromptGuard focuses on INPUT validation (prompt injection, sanitization).

    @staticmethod
    def check_prompt_injection(text: str, raise_on_detection: bool = True) -> Tuple[bool, List[str]]:
        """
        Check for prompt injection patterns.

        Args:
            text: Text to check for injection patterns
            raise_on_detection: Whether to raise exception on detection

        Returns:
            Tuple of (is_safe, detected_patterns)

        Raises:
            PromptInjectionDetected: If injection detected and raise_on_detection is True
        """
        detected_patterns = []

        for pattern in PromptGuard.INJECTION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                detected_patterns.append(pattern)

        if detected_patterns and raise_on_detection:
            raise PromptInjectionDetected(
                f"Potential prompt injection detected. Patterns: {detected_patterns[:3]}"
            )

        return len(detected_patterns) == 0, detected_patterns

    # REMOVED: check_suspicious_code() - moved to OutputFilter
    # Use OutputFilter.detect_dangerous_functions() for code validation

    @staticmethod
    def sanitize_prompt(text: str) -> str:
        """
        Sanitize a prompt by removing potentially dangerous content.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Remove control characters except common ones
        sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

        # Escape special delimiter sequences
        sanitized = sanitized.replace("</system>", "&lt;/system&gt;")
        sanitized = sanitized.replace("<system>", "&lt;system&gt;")
        sanitized = sanitized.replace("[system]", "[sys]")
        sanitized = sanitized.replace("[/system]", "[/sys]")

        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Limit length
        if len(sanitized) > PromptGuard.MAX_PROMPT_LENGTH:
            sanitized = sanitized[:PromptGuard.MAX_PROMPT_LENGTH] + "...[truncated]"

        return sanitized.strip()

    @staticmethod
    def sanitize_code_block(code: str) -> str:
        """
        Sanitize a code block for safe processing.

        Args:
            code: Code to sanitize

        Returns:
            Sanitized code
        """
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', code)

        # Limit length
        if len(sanitized) > PromptGuard.MAX_CODE_BLOCK_LENGTH:
            sanitized = sanitized[:PromptGuard.MAX_CODE_BLOCK_LENGTH] + "\n# [Code truncated]"

        return sanitized

    @staticmethod
    def validate_prompt_length(text: str, max_length: int = None) -> None:
        """
        Validate that a prompt is not too long.

        Args:
            text: Text to validate
            max_length: Maximum allowed length (default: MAX_PROMPT_LENGTH)

        Raises:
            ValueError: If prompt exceeds maximum length
        """
        max_length = max_length or PromptGuard.MAX_PROMPT_LENGTH

        if len(text) > max_length:
            raise ValueError(
                f"Prompt too long: {len(text)} characters (max: {max_length})"
            )

    # REMOVED: check_sensitive_data() - moved to OutputFilter
    # Use OutputFilter.detect_sensitive_data() for output validation

    # REMOVED: filter_sensitive_data() - moved to OutputFilter
    # Use OutputFilter.filter_sensitive_data() for output filtering

    @staticmethod
    def validate_ai_input(prompt: str, code: str = None) -> Tuple[str, str]:
        """
        Comprehensive validation and sanitization of AI inputs.

        Args:
            prompt: The prompt to send to the AI
            code: Optional code block to include

        Returns:
            Tuple of (sanitized_prompt, sanitized_code)

        Raises:
            PromptInjectionDetected: If prompt injection detected
            ValueError: If validation fails
        """
        # Check for prompt injection
        PromptGuard.check_prompt_injection(prompt, raise_on_detection=True)

        # Validate prompt length
        PromptGuard.validate_prompt_length(prompt)

        # Sanitize prompt
        sanitized_prompt = PromptGuard.sanitize_prompt(prompt)

        # Process code block if provided
        sanitized_code = None
        if code:
            # Sanitize code (length and control chars only)
            sanitized_code = PromptGuard.sanitize_code_block(code)

        return sanitized_prompt, sanitized_code

    # REMOVED: validate_ai_output() - AI output validation belongs in OutputFilter
    # Use OutputFilter.sanitize_ai_response() and OutputFilter.filter_sensitive_data()

    @staticmethod
    def create_safe_prompt(instruction: str, code: str = None, context: str = None) -> str:
        """
        Create a safe, validated prompt for AI processing.

        Args:
            instruction: The instruction/task for the AI
            code: Optional code to analyze
            context: Optional context information

        Returns:
            Safely constructed and validated prompt

        Raises:
            PromptInjectionDetected: If dangerous patterns detected
            ValueError: If prompt validation fails
        """
        # Build prompt parts
        prompt_parts = []

        # Add instruction
        if instruction:
            sanitized_instruction = PromptGuard.sanitize_prompt(instruction)
            prompt_parts.append(f"Task: {sanitized_instruction}")

        # Add context
        if context:
            sanitized_context = PromptGuard.sanitize_prompt(context)
            prompt_parts.append(f"Context: {sanitized_context}")

        # Add code
        if code:
            sanitized_code = PromptGuard.sanitize_code_block(code)
            prompt_parts.append(f"Code:\n```\n{sanitized_code}\n```")

        # Join parts
        full_prompt = "\n\n".join(prompt_parts)

        # Final validation
        PromptGuard.check_prompt_injection(full_prompt, raise_on_detection=True)
        PromptGuard.validate_prompt_length(full_prompt)

        return full_prompt
