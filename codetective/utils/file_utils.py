"""
File utilities for Codetective - handle file operations and path validation.
"""

import fnmatch
import shutil
from pathlib import Path
from typing import List, Optional


class FileUtils:
    """Utility class for file-related operations."""

    @staticmethod
    def validate_paths(paths: List[str]) -> List[str]:
        """Validate and normalize file/directory paths."""
        validated_paths = []

        for path_str in paths:
            path = Path(path_str).resolve()

            if not path.exists():
                continue

            if not (path.is_file() or path.is_dir()):
                continue

            validated_paths.append(str(path))

        return validated_paths

    @staticmethod
    def load_gitignore_patterns(project_path: str) -> List[str]:
        """Load .gitignore patterns from project directory."""
        gitignore_path = Path(project_path) / ".gitignore"
        patterns = []

        # Always ignore codetective results file
        patterns.extend(["codetective_scan_results.json", "codetective_scan_results*.json", "*.codetective.backup"])

        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except Exception as e:
                print(f"Error loading .gitignore patterns: {e}")
                pass

        return patterns

    @staticmethod
    def is_ignored_by_git(file_path: Path, project_root: Path, gitignore_patterns: List[str]) -> bool:
        """Check if a file should be ignored based on .gitignore patterns."""
        try:
            # Get relative path from project root
            rel_path = file_path.relative_to(project_root)
            rel_path_str = str(rel_path).replace("\\", "/")

            for pattern in gitignore_patterns:
                # Handle directory patterns
                if pattern.endswith("/"):
                    dir_pattern = pattern[:-1]
                    # Check if any parent directory matches
                    for parent in rel_path.parents:
                        parent_str = str(parent).replace("\\", "/")
                        if fnmatch.fnmatch(parent_str, dir_pattern) or parent_str == dir_pattern:
                            return True
                else:
                    # Check file patterns
                    if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                        return True
                    # Check if pattern matches any parent directory
                    for parent in rel_path.parents:
                        parent_str = str(parent).replace("\\", "/")
                        if fnmatch.fnmatch(parent_str, pattern):
                            return True
        except ValueError:
            # File is not under project root
            pass

        return False

    @staticmethod
    def get_file_list(
        paths: List[str],
        include_patterns: List[str] = [],
        exclude_patterns: List[str] = [],
        max_size: Optional[int] = None,
        respect_gitignore: bool = True,
    ) -> List[str]:
        """Get list of files to scan based on paths and patterns."""
        files = []
        include_patterns = include_patterns or ["*"]
        exclude_patterns = exclude_patterns or []

        for path_str in paths:
            path = Path(path_str)

            if path.is_file():
                files.append(str(path))
            elif path.is_dir():
                dir_files = FileUtils._scan_directory(path, include_patterns, exclude_patterns, max_size, respect_gitignore)
                files.extend(dir_files)

        return files

    @staticmethod
    def _scan_directory(
        directory: Path,
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_size: Optional[int] = None,
        respect_gitignore: bool = True,
    ) -> List[str]:
        """Scan a directory for files matching the given criteria."""
        files = []
        gitignore_patterns = []

        if respect_gitignore:
            gitignore_patterns = FileUtils.load_gitignore_patterns(str(directory))

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                if FileUtils._should_include_file(
                    file_path,
                    directory,
                    gitignore_patterns,
                    include_patterns,
                    exclude_patterns,
                    max_size,
                    respect_gitignore,
                ):
                    files.append(str(file_path))

        return files

    @staticmethod
    def _should_include_file(
        file_path: Path,
        project_root: Path,
        gitignore_patterns: List[str],
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_size: Optional[int] = None,
        respect_gitignore: bool = True,
    ) -> bool:
        """Check if a file should be included based on all criteria."""
        # Check if ignored by git
        if respect_gitignore and gitignore_patterns:
            if FileUtils.is_ignored_by_git(file_path, project_root, gitignore_patterns):
                return False

        # Check file size
        if max_size and file_path.stat().st_size > max_size:
            return False

        # Check include patterns
        if not any(fnmatch.fnmatch(file_path.name, pattern) for pattern in include_patterns):
            return False

        # Check exclude patterns
        if any(fnmatch.fnmatch(str(file_path), pattern) for pattern in exclude_patterns):
            return False

        return True

    @staticmethod
    def create_backup(file_path: str) -> str:
        """Create a backup of a file before modification."""
        backup_path = f"{file_path}.codetective.backup"
        shutil.copy2(file_path, backup_path)
        return backup_path

    @staticmethod
    def ensure_directory(directory: str) -> None:
        """Ensure a directory exists, creating it if necessary."""
        Path(directory).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_content(file_path: str, max_lines: Optional[int] = None) -> str:
        """Get file content with optional line limit."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line)
                    return "".join(lines)
                else:
                    return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
