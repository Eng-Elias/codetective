"""
Utility functions for Codetective - Legacy compatibility layer.
This module provides backward compatibility by importing from the new utils classes.
"""

# Import all utility classes
from codetective.utils import SystemUtils, FileUtils, ProcessUtils, StringUtils
from codetective.models.schemas import SystemInfo
from typing import List, Dict, Any, Optional, Tuple


# Legacy compatibility functions - delegate to utility classes
def check_tool_availability(tool_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a tool is available in PATH and get its version."""
    return SystemUtils.check_tool_availability(tool_name)


def get_system_info() -> SystemInfo:
    """Get comprehensive system information."""
    return SystemUtils.get_system_info()


def validate_paths(paths: List[str]) -> List[str]:
    """Validate and normalize file/directory paths."""
    return FileUtils.validate_paths(paths)


def load_gitignore_patterns(project_path: str) -> List[str]:
    """Load .gitignore patterns from project directory."""
    return FileUtils.load_gitignore_patterns(project_path)


def is_ignored_by_git(file_path, project_root, gitignore_patterns: List[str]) -> bool:
    """Check if a file should be ignored based on .gitignore patterns."""
    return FileUtils.is_ignored_by_git(file_path, project_root, gitignore_patterns)


def get_file_list(paths: List[str], include_patterns: List[str] = None, 
                  exclude_patterns: List[str] = None, max_size: int = None,
                  respect_gitignore: bool = True) -> List[str]:
    """Get list of files to scan based on paths and patterns."""
    return FileUtils.get_file_list(paths, include_patterns, exclude_patterns, max_size, respect_gitignore)


def create_backup(file_path: str) -> str:
    """Create a backup of a file before modification."""
    return FileUtils.create_backup(file_path)


def ensure_directory(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    return FileUtils.ensure_directory(directory)


def run_command(command: List[str], cwd: str = None, timeout: int = 300) -> Tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr."""
    return ProcessUtils.run_command(command, cwd, timeout)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    return StringUtils.format_duration(seconds)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis."""
    return StringUtils.truncate_text(text, max_length)


def get_file_content(file_path: str, max_lines: int = None) -> str:
    """Get file content with optional line limit."""
    return FileUtils.get_file_content(file_path, max_lines)


def safe_json_dump(data: Any) -> str:
    """Safely dump data to JSON string with error handling."""
    return StringUtils.safe_json_dump(data)
