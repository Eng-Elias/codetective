"""
Output filtering and sanitization for Codetective.

Provides OUTPUT VALIDATION security controls for:
- Filtering sensitive information from AI OUTPUTS and logs
- Sanitizing AI-generated responses
- Validating AI-generated code fixes BEFORE applying to files
- Detecting malicious code in GENERATED outputs
- Filtering sensitive data from scan results and file outputs

NOTE: This module is for OUTPUT validation only.
For INPUT validation (user prompts, prompt injection), use PromptGuard.
"""

import re
from pathlib import Path
from typing import Any, List, Optional, Tuple


class MaliciousCodeDetected(Exception):
    """Raised when malicious code is detected."""

    pass


class OutputFilter:
    """Filters and sanitizes outputs for security and safety."""

    # Patterns for sensitive data
    SENSITIVE_PATTERNS = {
        "api_key": r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
        "secret_key": r"(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
        "password": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?",
        "token": r"(?i)(token|auth[_-]?token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
        "access_key": r"(?i)(access[_-]?key|accesskey)\s*[:=]\s*['\"]?([A-Z0-9]{16,})['\"]?",
        "private_key": r"(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        "jwt": r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
        "aws_key": r"(?i)(AKIA|ASIA)[A-Z0-9]{16}",
    }

    # Malicious code patterns
    MALICIOUS_PATTERNS = {
        "rm_rf": r"rm\s+-rf\s+/",
        "fork_bomb": r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}",
        "backdoor": r"nc\s+-[a-z]*l[a-z]*\s+",
        "reverse_shell": r"bash\s+-i\s*>&\s*/dev/tcp/",
        "data_exfiltration": r"curl\s+.*\|\s*bash",
        "privilege_escalation": r"sudo\s+.*\|\s*sh",
        "file_overwrite": r">\s*/etc/",
        "cron_backdoor": r"crontab\s+-[a-z]*e",
    }

    # Dangerous function calls in code fixes
    DANGEROUS_FUNCTIONS = {
        "eval": r"\beval\s*\(",
        "exec": r"\bexec\s*\(",
        "compile": r"\bcompile\s*\(",
        "__import__": r"__import__\s*\(",
        "globals": r"\bglobals\s*\(\)",
        "locals": r"\blocals\s*\(\)",
        "os.system": r"os\.system\s*\(",
        "subprocess.call": r"subprocess\.(call|run|Popen)\s*\(",
        "open_write": r"open\s*\([^,]+,\s*['\"]w",
        "pickle": r"\bpickle\.(loads?|dumps?)\s*\(",
        "marshal": r"\bmarshal\.(loads?|dumps?)\s*\(",
    }

    @staticmethod
    def filter_sensitive_data(text: str, redaction_text: str = "***REDACTED***") -> str:
        """
        Filter sensitive data from text.

        Args:
            text: Text to filter
            redaction_text: Text to replace sensitive data with

        Returns:
            Filtered text with sensitive data removed
        """
        filtered = text

        for pattern_name, pattern in OutputFilter.SENSITIVE_PATTERNS.items():
            # Replace with redaction while keeping the key name
            # Use lambda to avoid backreference issues
            filtered = re.sub(
                pattern,
                lambda m: f"{m.group(1)}={redaction_text}" if m.lastindex and m.lastindex >= 1 else redaction_text,
                filtered,
            )

        return filtered

    @staticmethod
    def detect_sensitive_data(text: str) -> Tuple[bool, List[str]]:
        """
        Detect if text contains sensitive data.

        Args:
            text: Text to check

        Returns:
            Tuple of (has_sensitive_data, detected_types)
        """
        detected_types = []

        for pattern_name, pattern in OutputFilter.SENSITIVE_PATTERNS.items():
            if re.search(pattern, text):
                detected_types.append(pattern_name)

        return len(detected_types) > 0, detected_types

    @staticmethod
    def detect_malicious_code(code: str) -> Tuple[bool, List[str]]:
        """
        Detect malicious code patterns.

        Args:
            code: Code to check

        Returns:
            Tuple of (is_malicious, detected_patterns)
        """
        detected_patterns = []

        for pattern_name, pattern in OutputFilter.MALICIOUS_PATTERNS.items():
            if re.search(pattern, code, re.MULTILINE):
                detected_patterns.append(pattern_name)

        return len(detected_patterns) > 0, detected_patterns

    @staticmethod
    def detect_dangerous_functions(code: str) -> Tuple[bool, List[str]]:
        """
        Detect dangerous function calls in code.

        Args:
            code: Code to check

        Returns:
            Tuple of (has_dangerous_functions, detected_functions)
        """
        detected_functions = []

        for func_name, pattern in OutputFilter.DANGEROUS_FUNCTIONS.items():
            if re.search(pattern, code):
                detected_functions.append(func_name)

        return len(detected_functions) > 0, detected_functions

    @staticmethod
    def validate_code_fix(code: str, allow_dangerous_functions: bool = False) -> None:
        """
        Validate that a code fix is safe to apply.

        Args:
            code: Code to validate
            allow_dangerous_functions: Whether to allow dangerous functions

        Raises:
            MaliciousCodeDetected: If malicious code is detected
        """
        # Check for malicious patterns
        is_malicious, malicious_patterns = OutputFilter.detect_malicious_code(code)
        if is_malicious:
            raise MaliciousCodeDetected(f"Malicious code detected: {', '.join(malicious_patterns)}")

        # Check for dangerous functions
        if not allow_dangerous_functions:
            has_dangerous, dangerous_funcs = OutputFilter.detect_dangerous_functions(code)
            if has_dangerous:
                raise MaliciousCodeDetected(
                    f"Dangerous functions detected: {', '.join(dangerous_funcs)}. "
                    f"Use allow_dangerous_functions=True if these are intentional."
                )

    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """
        Sanitize a log message by removing sensitive data.

        Args:
            message: Log message to sanitize

        Returns:
            Sanitized log message
        """
        # Filter sensitive data
        sanitized = OutputFilter.filter_sensitive_data(message)

        # Remove file system paths that might be sensitive
        # Unix-style home paths
        sanitized = re.sub(r"/home/[^/\s]+", "/home/***", sanitized)

        # Windows paths - use lambda to avoid escape sequence issues
        # Match C:\Users\<username> or C:/Users/<username>
        sanitized = re.sub(
            r"[Cc]:[/\\][Uu]sers[/\\][^/\\\s]+", lambda m: "C:\\Users\\***", sanitized  # Use lambda to return literal string
        )

        return sanitized

    @staticmethod
    def sanitize_file_path(file_path: str, project_root: Optional[str] = None) -> str:
        """
        Sanitize a file path for display.

        Args:
            file_path: File path to sanitize
            project_root: Optional project root to make path relative to

        Returns:
            Sanitized file path
        """
        if project_root:
            try:
                path = Path(file_path)
                root = Path(project_root)
                relative_path = path.relative_to(root)
                return str(relative_path)
            except ValueError:
                # Path is not relative to project root
                pass

        # Just return the basename if no project root
        return Path(file_path).name

    @staticmethod
    def sanitize_ai_response(response: str) -> str:
        """
        Sanitize an AI-generated response.

        Args:
            response: AI response to sanitize

        Returns:
            Sanitized response
        """
        # Filter sensitive data
        sanitized = OutputFilter.filter_sensitive_data(response)

        # Remove excessive whitespace
        sanitized = re.sub(r"\n\n\n+", "\n\n", sanitized)

        # Remove potential prompt leakage
        sanitized = re.sub(r"(?i)(system|assistant|user):\s*$", "", sanitized, flags=re.MULTILINE)

        return sanitized.strip()

    @staticmethod
    def validate_fix_output(original_code: str, fixed_code: str, max_change_ratio: float = 0.8) -> None:
        """
        Validate that a fix is reasonable and not replacing too much code.

        Args:
            original_code: Original code
            fixed_code: Fixed code
            max_change_ratio: Maximum ratio of changed lines (0.8 = 80%)

        Raises:
            ValueError: If fix changes too much code
        """
        original_lines = original_code.splitlines()
        fixed_lines = fixed_code.splitlines()

        # Check if fix is completely replacing the file
        if len(original_lines) > 10:  # Only check for non-trivial files
            # Count changed lines
            changed_lines = 0
            max_lines = max(len(original_lines), len(fixed_lines))

            for i in range(max_lines):
                orig_line = original_lines[i] if i < len(original_lines) else ""
                fixed_line = fixed_lines[i] if i < len(fixed_lines) else ""

                if orig_line != fixed_line:
                    changed_lines += 1

            change_ratio = changed_lines / max_lines if max_lines > 0 else 0

            if change_ratio > max_change_ratio:
                raise ValueError(
                    f"Fix changes too much code: {change_ratio:.1%} "
                    f"(max: {max_change_ratio:.1%}). "
                    f"This might indicate an AI hallucination or error."
                )

    @staticmethod
    def extract_code_from_markdown(markdown: str) -> Any:
        """
        Safely extract code from markdown code blocks.

        Args:
            markdown: Markdown text containing code blocks

        Returns:
            Extracted code or None if no code blocks found
        """
        # Match code blocks with optional language specifier
        code_block_pattern = r"```(?:[a-z]*\n)?(.*?)```"
        matches = re.findall(code_block_pattern, markdown, re.DOTALL)

        if not matches:
            return None

        # Return the first code block
        code = matches[0].strip()

        # Validate the extracted code
        OutputFilter.validate_code_fix(code)

        return code

    @staticmethod
    def create_safe_output(content: str, filter_sensitive: bool = True, validate_code: bool = False) -> str:
        """
        Create a safe output by applying all necessary filters.

        Args:
            content: Content to make safe
            filter_sensitive: Whether to filter sensitive data
            validate_code: Whether to validate as code

        Returns:
            Safe output

        Raises:
            MaliciousCodeDetected: If malicious code detected
        """
        safe_content = content

        # Filter sensitive data
        if filter_sensitive:
            safe_content = OutputFilter.filter_sensitive_data(safe_content)

        # Validate as code if requested
        if validate_code:
            OutputFilter.validate_code_fix(safe_content)

        # Sanitize AI response patterns
        safe_content = OutputFilter.sanitize_ai_response(safe_content)

        return safe_content
