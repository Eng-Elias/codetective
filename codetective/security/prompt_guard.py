"""
Prompt injection protection for Codetective.

Provides security controls for:
- Detecting and preventing prompt injection attacks
- Content safety filtering for AI inputs/outputs
- Token limit enforcement
- Suspicious pattern detection
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

    # Suspicious code patterns in comments
    SUSPICIOUS_CODE_PATTERNS = [
        r"eval\s*\(",  # Eval usage
        r"exec\s*\(",  # Exec usage
        r"__import__",  # Dynamic imports
        r"subprocess\.(call|run|Popen)",  # Subprocess execution
        r"os\.system",  # OS command execution
        r"open\s*\([^,]+,\s*['\"]w",  # File writing in suspicious context
    ]

    # Sensitive data patterns
    SENSITIVE_PATTERNS = [
        r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{8,})",
        r"(?i)(token|auth[_-]?token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"(?i)(access[_-]?key|accesskey)\s*[:=]\s*['\"]?([A-Z0-9]{16,})",
    ]

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

    @staticmethod
    def check_suspicious_code(code: str, context: str = "code") -> Tuple[bool, List[str]]:
        """
        Check for suspicious code patterns.

        Args:
            code: Code to check
            context: Context description for error messages

        Returns:
            Tuple of (is_safe, detected_patterns)
        """
        detected_patterns = []

        for pattern in PromptGuard.SUSPICIOUS_CODE_PATTERNS:
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                detected_patterns.append(pattern)

        return len(detected_patterns) == 0, detected_patterns

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

    @staticmethod
    def check_sensitive_data(text: str) -> Tuple[bool, List[str]]:
        """
        Check for potential sensitive data exposure.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_safe, detected_patterns)
        """
        detected_patterns = []

        for pattern in PromptGuard.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                # Don't include the actual matched values in the pattern
                detected_patterns.append(f"Potential sensitive data: {pattern[:50]}...")

        return len(detected_patterns) == 0, detected_patterns

    @staticmethod
    def filter_sensitive_data(text: str) -> str:
        """
        Filter out potential sensitive data from text.

        Args:
            text: Text to filter

        Returns:
            Filtered text with sensitive data redacted
        """
        filtered = text

        # Redact API keys and tokens
        filtered = re.sub(
            r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
            lambda m: f"{m.group(1)}=***REDACTED***",
            filtered
        )

        # Redact secrets
        filtered = re.sub(
            r"(?i)(secret[_-]?key|secretkey|password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?",
            lambda m: f"{m.group(1)}=***REDACTED***",
            filtered
        )

        # Redact tokens (including JWT)
        filtered = re.sub(
            r"(?i)(token|auth[_-]?token|access[_-]?key)\s*[:=]\s*['\"]?(Bearer\s+)?([a-zA-Z0-9_\-\.]{20,})['\"]?",
            lambda m: f"{m.group(1)}=***REDACTED***",
            filtered
        )

        return filtered

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
            # Check for suspicious code
            is_safe, patterns = PromptGuard.check_suspicious_code(code)
            if not is_safe:
                print(f"Warning: Suspicious code patterns detected: {patterns[:3]}")

            # Sanitize code
            sanitized_code = PromptGuard.sanitize_code_block(code)

        return sanitized_prompt, sanitized_code

    @staticmethod
    def validate_ai_output(output: str) -> str:
        """
        Validate and sanitize AI output.

        Args:
            output: AI-generated output

        Returns:
            Sanitized output

        Raises:
            ValueError: If output is invalid
        """
        if not output:
            return output

        # Check for sensitive data
        is_safe, patterns = PromptGuard.check_sensitive_data(output)
        if not is_safe:
            print(f"Warning: Potential sensitive data in output: {patterns[:3]}")

        # Filter sensitive data
        filtered_output = PromptGuard.filter_sensitive_data(output)

        return filtered_output

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
