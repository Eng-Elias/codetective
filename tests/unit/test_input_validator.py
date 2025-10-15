"""
Unit tests for InputValidator.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from codetective.security.input_validator import InputValidator, ValidationError
from codetective.models.schemas import ScanConfig, FixConfig, AgentType


class TestInputValidator:
    """Test cases for InputValidator."""

    @pytest.mark.unit
    def test_validate_file_path_valid(self, temp_dir):
        """Test validating a valid file path."""
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")
        
        result = InputValidator.validate_file_path(str(test_file))
        
        assert result.exists()
        assert result.is_file()

    @pytest.mark.unit
    def test_validate_file_path_empty(self):
        """Test validating empty file path."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_file_path("")

    @pytest.mark.unit
    def test_validate_file_path_nonexistent(self):
        """Test validating non-existent file path."""
        with pytest.raises(ValidationError, match="does not exist"):
            InputValidator.validate_file_path("/nonexistent/file.py")

    @pytest.mark.unit
    def test_validate_file_path_with_traversal(self):
        """Test detecting directory traversal in path."""
        with pytest.raises(ValidationError, match="suspicious pattern"):
            InputValidator.validate_file_path("../../../etc/passwd")

    @pytest.mark.unit
    def test_validate_file_path_with_base_dir(self, temp_dir):
        """Test validating path within base directory."""
        test_file = temp_dir / "test.py"
        test_file.write_text("test")
        
        result = InputValidator.validate_file_path(str(test_file), base_dir=str(temp_dir))
        
        assert result.exists()

    @pytest.mark.unit
    def test_validate_file_path_outside_base_dir(self, temp_dir):
        """Test rejecting path outside base directory."""
        # Create a file outside temp_dir
        other_file = Path(__file__)  # This test file
        
        with pytest.raises(ValidationError, match="outside allowed directory"):
            InputValidator.validate_file_path(str(other_file), base_dir=str(temp_dir))

    @pytest.mark.unit
    def test_validate_file_size_valid(self, temp_dir):
        """Test validating file size within limits."""
        test_file = temp_dir / "small.py"
        test_file.write_text("x = 1")
        
        # Should not raise
        InputValidator.validate_file_size(test_file)

    @pytest.mark.unit
    def test_validate_file_size_too_large(self, temp_dir):
        """Test rejecting file that's too large."""
        test_file = temp_dir / "large.py"
        
        # Create a large file (mock by setting MAX_FILE_SIZE_BYTES temporarily)
        original_max = InputValidator.MAX_FILE_SIZE_BYTES
        InputValidator.MAX_FILE_SIZE_BYTES = 100  # 100 bytes
        
        test_file.write_text("x" * 200)  # 200 bytes
        
        try:
            with pytest.raises(ValidationError, match="File too large"):
                InputValidator.validate_file_size(test_file)
        finally:
            InputValidator.MAX_FILE_SIZE_BYTES = original_max

    @pytest.mark.unit
    def test_validate_file_size_not_a_file(self, temp_dir):
        """Test rejecting directory for file size validation."""
        with pytest.raises(ValidationError, match="Not a file"):
            InputValidator.validate_file_size(temp_dir)

    @pytest.mark.unit
    def test_validate_file_extension_allowed(self, temp_dir):
        """Test validating allowed file extension."""
        test_file = temp_dir / "test.py"
        test_file.write_text("test")
        
        # Should not raise
        InputValidator.validate_file_extension(test_file)

    @pytest.mark.unit
    def test_validate_file_extension_not_allowed(self, temp_dir):
        """Test rejecting unsupported file extension."""
        test_file = temp_dir / "test.exe"
        test_file.write_text("test")
        
        with pytest.raises(ValidationError, match="Unsupported file type"):
            InputValidator.validate_file_extension(test_file)

    @pytest.mark.unit
    def test_validate_file_comprehensive(self, temp_dir):
        """Test comprehensive file validation."""
        test_file = temp_dir / "valid.py"
        test_file.write_text("print('valid')")
        
        result = InputValidator.validate_file(str(test_file), base_dir=str(temp_dir))
        
        assert result.exists()
        assert result.is_file()
        assert result.suffix == ".py"

    @pytest.mark.unit
    def test_validate_file_list_valid(self, temp_dir):
        """Test validating list of files."""
        files = []
        for i in range(3):
            f = temp_dir / f"test{i}.py"
            f.write_text(f"test{i}")
            files.append(str(f))
        
        result = InputValidator.validate_file_list(files, base_dir=str(temp_dir))
        
        assert len(result) == 3
        assert all(isinstance(p, Path) for p in result)

    @pytest.mark.unit
    def test_validate_file_list_too_many(self, temp_dir):
        """Test rejecting too many files."""
        # Create list exceeding MAX_FILES_PER_SCAN
        files = [f"file{i}.py" for i in range(InputValidator.MAX_FILES_PER_SCAN + 1)]
        
        with pytest.raises(ValidationError, match="Too many files"):
            InputValidator.validate_file_list(files)

    @pytest.mark.unit
    def test_validate_file_list_with_invalid_files(self, temp_dir):
        """Test validating list with some invalid files."""
        # Create mix of valid and invalid files
        valid_file = temp_dir / "valid.py"
        valid_file.write_text("test")
        
        files = [
            str(valid_file),
            "/nonexistent/file.py",  # Invalid
            "../../../etc/passwd",   # Invalid
        ]
        
        # Should return only valid files
        result = InputValidator.validate_file_list(files, base_dir=str(temp_dir))
        
        assert len(result) == 1
        # Compare resolved paths (handles Windows 8.3 short names)
        assert result[0].resolve() == valid_file.resolve()

    @pytest.mark.unit
    def test_validate_file_list_no_valid_files(self):
        """Test error when no valid files in list."""
        files = ["/nonexistent1.py", "/nonexistent2.py"]
        
        with pytest.raises(ValidationError, match="No valid files found"):
            InputValidator.validate_file_list(files)

    @pytest.mark.unit
    def test_validate_directory_valid(self, temp_dir):
        """Test validating valid directory."""
        result = InputValidator.validate_directory(str(temp_dir))
        
        assert result.exists()
        assert result.is_dir()

    @pytest.mark.unit
    def test_validate_directory_empty(self):
        """Test validating empty directory path."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_directory("")

    @pytest.mark.unit
    def test_validate_directory_nonexistent(self):
        """Test validating non-existent directory."""
        with pytest.raises(ValidationError, match="does not exist"):
            InputValidator.validate_directory("/nonexistent/directory")

    @pytest.mark.unit
    def test_validate_directory_not_a_directory(self, temp_dir):
        """Test rejecting file when directory expected."""
        test_file = temp_dir / "file.py"
        test_file.write_text("test")
        
        with pytest.raises(ValidationError, match="Not a directory"):
            InputValidator.validate_directory(str(test_file))

    @pytest.mark.unit
    def test_validate_directory_with_traversal(self):
        """Test detecting directory traversal."""
        with pytest.raises(ValidationError, match="suspicious pattern"):
            InputValidator.validate_directory("../../../tmp")

    @pytest.mark.unit
    def test_validate_command_safe(self):
        """Test validating safe command."""
        # Should not raise
        InputValidator.validate_command("git status")
        InputValidator.validate_command("python -m pytest")

    @pytest.mark.unit
    def test_validate_command_dangerous_rm(self):
        """Test detecting dangerous rm command."""
        with pytest.raises(ValidationError, match="dangerous pattern"):
            InputValidator.validate_command("rm -rf /")

    @pytest.mark.unit
    def test_validate_command_dangerous_pipe(self):
        """Test detecting dangerous pipe to shell."""
        with pytest.raises(ValidationError, match="dangerous pattern"):
            InputValidator.validate_command("cat file | sh")

    @pytest.mark.unit
    def test_validate_command_dangerous_backticks(self):
        """Test detecting backtick command injection."""
        with pytest.raises(ValidationError, match="dangerous pattern"):
            InputValidator.validate_command("echo `whoami`")

    @pytest.mark.unit
    def test_validate_json_data_valid(self):
        """Test validating valid JSON data."""
        json_str = '{"key": "value", "number": 123}'
        
        result = InputValidator.validate_json_data(json_str)
        
        assert result["key"] == "value"
        assert result["number"] == 123

    @pytest.mark.unit
    def test_validate_json_data_invalid(self):
        """Test rejecting invalid JSON."""
        with pytest.raises(ValidationError, match="Invalid JSON"):
            InputValidator.validate_json_data("{invalid json}")

    @pytest.mark.unit
    def test_validate_json_data_too_large(self):
        """Test rejecting JSON that's too large."""
        large_json = '{"data": "' + ('x' * 20 * 1024 * 1024) + '"}'  # >20MB
        
        with pytest.raises(ValidationError, match="too large"):
            InputValidator.validate_json_data(large_json, max_size_mb=10.0)

    @pytest.mark.unit
    def test_validate_scan_config_valid(self, temp_dir):
        """Test validating valid scan config."""
        test_file = temp_dir / "test.py"
        test_file.write_text("test")
        
        config = ScanConfig(
            agents=[AgentType.SEMGREP],
            paths=[str(test_file)]
        )
        
        # Should not raise
        InputValidator.validate_scan_config(config)

    @pytest.mark.unit
    def test_validate_fix_config(self):
        """Test validating fix config."""
        config = FixConfig(agents=[AgentType.EDIT])
        
        # Should not raise
        InputValidator.validate_fix_config(config)

    @pytest.mark.unit
    def test_sanitize_filename_basic(self):
        """Test sanitizing basic filename."""
        result = InputValidator.sanitize_filename("test.py")
        
        assert result == "test.py"

    @pytest.mark.unit
    def test_sanitize_filename_with_separators(self):
        """Test sanitizing filename with path separators."""
        result = InputValidator.sanitize_filename("path/to/file.py")
        
        assert "/" not in result
        assert "\\" not in result
        assert result == "path_to_file.py"

    @pytest.mark.unit
    def test_sanitize_filename_with_dangerous_chars(self):
        """Test sanitizing filename with dangerous characters."""
        result = InputValidator.sanitize_filename('file<>:"|?*.py')
        
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "?" not in result
        assert "*" not in result

    @pytest.mark.unit
    def test_sanitize_filename_too_long(self):
        """Test sanitizing filename that's too long."""
        long_name = "a" * 300 + ".py"
        
        result = InputValidator.sanitize_filename(long_name)
        
        assert len(result) <= 255
        assert result.endswith(".py")

    @pytest.mark.unit
    def test_is_safe_path_safe(self, temp_dir):
        """Test checking safe path."""
        test_file = temp_dir / "test.py"
        test_file.write_text("test")
        
        result = InputValidator.is_safe_path(str(test_file), str(temp_dir))
        
        assert result is True

    @pytest.mark.unit
    def test_is_safe_path_unsafe(self, temp_dir):
        """Test checking unsafe path."""
        outside_file = Path(__file__)
        
        result = InputValidator.is_safe_path(str(outside_file), str(temp_dir))
        
        assert result is False

    @pytest.mark.unit
    def test_allowed_code_extensions(self):
        """Test that common code extensions are allowed."""
        common_extensions = [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs"]
        
        for ext in common_extensions:
            assert ext in InputValidator.ALLOWED_CODE_EXTENSIONS

    @pytest.mark.unit
    def test_max_file_size_reasonable(self):
        """Test that max file size is reasonable."""
        # Should be at least 10MB for code files
        assert InputValidator.MAX_FILE_SIZE_BYTES >= 10 * 1024 * 1024

    @pytest.mark.unit
    def test_max_files_per_scan_reasonable(self):
        """Test that max files per scan is reasonable."""
        # Should allow at least 100 files
        assert InputValidator.MAX_FILES_PER_SCAN >= 100
