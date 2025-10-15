"""
Input validation and sanitization for Codetective.

Provides security controls for:
- Path validation (prevent directory traversal)
- File size limits (prevent memory exhaustion)
- File type validation (whitelist supported extensions)
- JSON schema validation
- Command injection prevention
"""

import json
import os
import re
from pathlib import Path
from typing import Any, List, Optional

from codetective.models.schemas import FixConfig, ScanConfig


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class InputValidator:
    """Validates and sanitizes user inputs for security."""

    # Supported code file extensions
    ALLOWED_CODE_EXTENSIONS = {
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
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".scala",
        ".r",
        ".sh",
        ".bash",
        ".zsh",
        ".yaml",
        ".yml",
        ".json",
        ".xml",
        ".toml",
        ".ini",
        ".sql",
        ".html",
        ".css",
        ".scss",
        ".vue",
        ".svelte",
        ".dart",
        ".lua",
    }

    # Maximum file size (100MB)
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024

    # Maximum number of files to scan
    MAX_FILES_PER_SCAN = 1000

    # Patterns that indicate directory traversal attempts
    TRAVERSAL_PATTERNS = [
        r"\.\./",  # Parent directory traversal (../)
        r"\.\.$",  # Ends with ..
        r"^~/",  # Starts with ~/ (home directory expansion)
        r"\${",  # Environment variable expansion
    ]

    # Dangerous command patterns
    DANGEROUS_COMMAND_PATTERNS = [
        r"rm\s+-rf\s+/",  # rm -rf / (root deletion)
        r";\s*rm\s+-rf",  # ; rm -rf (chained command)
        r"&&\s*rm\s+-rf",  # && rm -rf (conditional)
        r"\|\s*sh",  # | sh (pipe to shell)
        r"`.*`",  # `command` (backticks)
        r"\$\(",  # $(command) (command substitution)
        r">\s*/dev/",  # > /dev/ (device write)
    ]

    @staticmethod
    def validate_file_path(file_path: str, base_dir: Optional[str] = None) -> Path:
        """
        Validate a file path for security issues.

        Args:
            file_path: The file path to validate
            base_dir: Optional base directory to restrict paths to

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is invalid or dangerous
        """
        if not file_path:
            raise ValidationError("File path cannot be empty")

        # Convert to Path object
        try:
            path = Path(file_path).resolve()
        except (ValueError, OSError) as e:
            raise ValidationError(f"Invalid path format: {e}")

        # Check for directory traversal patterns
        for pattern in InputValidator.TRAVERSAL_PATTERNS:
            if re.search(pattern, str(file_path)):
                raise ValidationError(f"Path contains suspicious pattern: {pattern}")

        # If base_dir provided, ensure path is within it
        if base_dir:
            try:
                base_path = Path(base_dir).resolve()
                path.relative_to(base_path)
            except (ValueError, OSError):
                raise ValidationError(f"Path is outside allowed directory: {base_dir}")

        # Check if path exists
        if not path.exists():
            raise ValidationError(f"Path does not exist: {file_path}")

        return path

    @staticmethod
    def validate_file_size(file_path: Path) -> None:
        """
        Validate that a file is not too large.

        Args:
            file_path: Path to the file

        Raises:
            ValidationError: If file is too large
        """
        if not file_path.is_file():
            raise ValidationError(f"Not a file: {file_path}")

        file_size = file_path.stat().st_size
        if file_size > InputValidator.MAX_FILE_SIZE_BYTES:
            max_mb = InputValidator.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise ValidationError(f"File too large: {actual_mb:.1f}MB (max: {max_mb}MB)")

    @staticmethod
    def validate_file_extension(file_path: Path) -> None:
        """
        Validate that a file has an allowed extension.

        Args:
            file_path: Path to the file

        Raises:
            ValidationError: If file extension is not allowed
        """
        extension = file_path.suffix.lower()
        if extension not in InputValidator.ALLOWED_CODE_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file type: {extension}. " f"Allowed: {', '.join(sorted(InputValidator.ALLOWED_CODE_EXTENSIONS))}"
            )

    @staticmethod
    def validate_file(file_path: str, base_dir: Optional[str] = None) -> Path:
        """
        Comprehensive file validation.

        Args:
            file_path: The file path to validate
            base_dir: Optional base directory to restrict paths to

        Returns:
            Validated Path object

        Raises:
            ValidationError: If file fails any validation check
        """
        # Validate path
        path = InputValidator.validate_file_path(file_path, base_dir)

        # Validate size
        InputValidator.validate_file_size(path)

        # Validate extension
        InputValidator.validate_file_extension(path)

        return path

    @staticmethod
    def validate_file_list(file_paths: List[str], base_dir: Optional[str] = None) -> List[Path]:
        """
        Validate a list of files.

        Args:
            file_paths: List of file paths to validate
            base_dir: Optional base directory to restrict paths to

        Returns:
            List of validated Path objects

        Raises:
            ValidationError: If any file fails validation
        """
        if len(file_paths) > InputValidator.MAX_FILES_PER_SCAN:
            raise ValidationError(f"Too many files: {len(file_paths)} " f"(max: {InputValidator.MAX_FILES_PER_SCAN})")

        validated_paths = []
        for file_path in file_paths:
            try:
                path = InputValidator.validate_file(file_path, base_dir)
                validated_paths.append(path)
            except ValidationError as e:
                # Log warning but continue with other files
                print(f"Skipping invalid file {file_path}: {e}")

        if not validated_paths:
            raise ValidationError("No valid files found after validation")

        return validated_paths

    @staticmethod
    def validate_directory(directory_path: str) -> Path:
        """
        Validate a directory path.

        Args:
            directory_path: The directory path to validate

        Returns:
            Validated Path object

        Raises:
            ValidationError: If directory is invalid
        """
        if not directory_path:
            raise ValidationError("Directory path cannot be empty")

        try:
            path = Path(directory_path).resolve()
        except (ValueError, OSError) as e:
            raise ValidationError(f"Invalid directory format: {e}")

        # Check for directory traversal patterns
        for pattern in InputValidator.TRAVERSAL_PATTERNS:
            if re.search(pattern, str(directory_path)):
                raise ValidationError(f"Path contains suspicious pattern: {pattern}")

        if not path.exists():
            raise ValidationError(f"Directory does not exist: {directory_path}")

        if not path.is_dir():
            raise ValidationError(f"Not a directory: {directory_path}")

        return path

    @staticmethod
    def validate_command(command: str) -> None:
        """
        Validate a command for dangerous patterns.

        Args:
            command: The command to validate

        Raises:
            ValidationError: If command contains dangerous patterns
        """
        for pattern in InputValidator.DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValidationError(f"Command contains dangerous pattern: {pattern}")

    @staticmethod
    def validate_json_data(data: str, max_size_mb: float = 10.0) -> Any:
        """
        Validate and parse JSON data.

        Args:
            data: JSON string to validate
            max_size_mb: Maximum size in megabytes

        Returns:
            Parsed JSON data

        Raises:
            ValidationError: If JSON is invalid or too large
        """
        # Check size
        data_size = len(data.encode("utf-8"))
        max_size_bytes = max_size_mb * 1024 * 1024

        if data_size > max_size_bytes:
            actual_mb = data_size / (1024 * 1024)
            raise ValidationError(f"JSON data too large: {actual_mb:.1f}MB (max: {max_size_mb}MB)")

        # Parse JSON
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")

        return parsed_data

    @staticmethod
    def validate_scan_config(config: ScanConfig) -> None:
        """
        Validate a scan configuration.

        Args:
            config: Scan configuration to validate

        Raises:
            ValidationError: If configuration is invalid
        """
        # Validate paths
        if config.paths:
            for path in config.paths:
                InputValidator.validate_file_path(path)

        # Validate file count
        if hasattr(config, "max_files") and config.max_files:
            if config.max_files > InputValidator.MAX_FILES_PER_SCAN:
                raise ValidationError(f"max_files too high: {config.max_files} " f"(max: {InputValidator.MAX_FILES_PER_SCAN})")

    @staticmethod
    def validate_fix_config(config: FixConfig) -> None:
        """
        Validate a fix configuration.

        Args:
            config: Fix configuration to validate

        Raises:
            ValidationError: If configuration is invalid
        """
        # Add fix-specific validation if needed
        pass

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename by removing dangerous characters.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = filename.replace(os.sep, "_")
        filename = filename.replace("/", "_")
        filename = filename.replace("\\", "_")

        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', "_", filename)

        # Remove control characters
        filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)

        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            name = name[: max_length - len(ext)]
            filename = name + ext

        return filename

    @staticmethod
    def is_safe_path(path: str, base_dir: str) -> bool:
        """
        Check if a path is safe (within base directory).

        Args:
            path: Path to check
            base_dir: Base directory

        Returns:
            True if path is safe, False otherwise
        """
        try:
            InputValidator.validate_file_path(path, base_dir)
            return True
        except ValidationError:
            return False
