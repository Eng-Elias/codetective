"""
File processing utilities for the codetective system.
"""

import os
import mimetypes
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass

from loguru import logger


@dataclass
class FileInfo:
    """Information about a processed file."""
    
    path: Path
    size: int
    mime_type: str
    is_text: bool
    encoding: Optional[str] = None
    line_count: Optional[int] = None


class FileProcessor:
    """
    Handles file discovery, filtering, and processing operations.
    
    This class provides methods for finding files, filtering by type,
    reading content, and managing file operations for code analysis.
    """
    
    def __init__(self, root_path: Path, exclude_patterns: Optional[List[str]] = None):
        """
        Initialize the file processor.
        
        Args:
            root_path: Root directory for file operations
            exclude_patterns: List of glob patterns to exclude
        """
        self.root_path = Path(root_path)
        self.exclude_patterns = exclude_patterns or self._get_default_exclude_patterns()
        self._supported_extensions = self._get_supported_extensions()
        
        if not self.root_path.exists():
            raise ValueError(f"Root path does not exist: {root_path}")
        
        if not self.root_path.is_dir():
            raise ValueError(f"Root path is not a directory: {root_path}")
    
    @property
    def supported_extensions(self) -> Set[str]:
        """Get set of supported file extensions."""
        return self._supported_extensions.copy()
    
    def _get_default_exclude_patterns(self) -> List[str]:
        """Get default patterns to exclude from processing."""
        return [
            "*.pyc", "*.pyo", "*.pyd", "__pycache__",
            ".git", ".svn", ".hg", ".bzr",
            "node_modules", ".npm", ".yarn",
            ".venv", "venv", ".env",
            "*.log", "*.tmp", "*.temp",
            ".DS_Store", "Thumbs.db",
            "*.min.js", "*.min.css",
            "dist", "build", "target",
            ".pytest_cache", ".mypy_cache", ".ruff_cache",
        ]
    
    def _get_supported_extensions(self) -> Set[str]:
        """Get set of supported file extensions for analysis."""
        return {
            # Python
            ".py", ".pyx", ".pyi",
            # JavaScript/TypeScript
            ".js", ".jsx", ".ts", ".tsx", ".mjs",
            # Java
            ".java", ".scala", ".kt",
            # C/C++
            ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
            # C#
            ".cs",
            # Go
            ".go",
            # Rust
            ".rs",
            # Ruby
            ".rb",
            # PHP
            ".php",
            # Shell
            ".sh", ".bash", ".zsh", ".fish",
            # Configuration
            ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
            # Docker
            "Dockerfile", ".dockerfile",
            # Other
            ".sql", ".xml", ".html", ".css",
        }
    
    def discover_files(self, file_patterns: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Discover files in the root directory matching criteria.
        
        Args:
            file_patterns: Optional list of glob patterns to match
            
        Returns:
            List of FileInfo objects for discovered files
        """
        discovered_files = []
        
        try:
            for file_path in self._walk_directory():
                if self._should_include_file(file_path, file_patterns):
                    file_info = self._create_file_info(file_path)
                    if file_info:
                        discovered_files.append(file_info)
        
        except Exception as e:
            logger.error(f"Error discovering files: {e}")
            raise
        
        logger.info(f"Discovered {len(discovered_files)} files for analysis")
        return discovered_files
    
    def _walk_directory(self) -> List[Path]:
        """Walk directory tree and return all file paths."""
        file_paths = []
        
        for root, dirs, files in os.walk(self.root_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._is_excluded(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if not self._is_excluded(file_path):
                    file_paths.append(file_path)
        
        return file_paths
    
    def _should_include_file(self, file_path: Path, patterns: Optional[List[str]]) -> bool:
        """Check if file should be included based on patterns and extensions."""
        # Check if file has supported extension
        if file_path.suffix.lower() not in self._supported_extensions:
            # Special case for files without extensions (like Dockerfile)
            if file_path.name not in ["Dockerfile", "Makefile", "Jenkinsfile"]:
                return False
        
        # Check against include patterns if provided
        if patterns:
            return any(file_path.match(pattern) for pattern in patterns)
        
        return True
    
    def _is_excluded(self, path: Path) -> bool:
        """Check if path matches any exclude pattern."""
        relative_path = path.relative_to(self.root_path)
        
        for pattern in self.exclude_patterns:
            if relative_path.match(pattern) or path.name.startswith('.'):
                return True
        
        return False
    
    def _create_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """Create FileInfo object for a file."""
        try:
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or "application/octet-stream"
            
            is_text = self._is_text_file(file_path, mime_type)
            encoding = None
            line_count = None
            
            if is_text:
                encoding = self._detect_encoding(file_path)
                line_count = self._count_lines(file_path, encoding)
            
            return FileInfo(
                path=file_path,
                size=stat.st_size,
                mime_type=mime_type,
                is_text=is_text,
                encoding=encoding,
                line_count=line_count,
            )
        
        except Exception as e:
            logger.warning(f"Could not process file {file_path}: {e}")
            return None
    
    def _is_text_file(self, file_path: Path, mime_type: str) -> bool:
        """Determine if file is a text file."""
        if mime_type.startswith("text/"):
            return True
        
        # Check for known text file extensions
        text_extensions = {".py", ".js", ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".ini"}
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # Try to read a small portion to detect if it's text
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' not in chunk
        except Exception:
            return False
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding."""
        try:
            # Try common encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)  # Try to read a chunk
                    return encoding
                except UnicodeDecodeError:
                    continue
            
            return 'utf-8'  # Default fallback
        
        except Exception:
            return 'utf-8'
    
    def _count_lines(self, file_path: Path, encoding: str) -> int:
        """Count lines in a text file."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def read_file_content(self, file_path: Path, max_size: int = 1024 * 1024) -> Optional[str]:
        """
        Read content of a text file.
        
        Args:
            file_path: Path to the file
            max_size: Maximum file size to read (default 1MB)
            
        Returns:
            File content as string, or None if file cannot be read
        """
        try:
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return None
            
            stat = file_path.stat()
            if stat.st_size > max_size:
                logger.warning(f"File too large to read: {file_path} ({stat.st_size} bytes)")
                return None
            
            encoding = self._detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about files in the root directory."""
        files = self.discover_files()
        
        total_size = sum(f.size for f in files)
        total_lines = sum(f.line_count or 0 for f in files if f.is_text)
        
        extensions = {}
        for file_info in files:
            ext = file_info.path.suffix.lower() or "no_extension"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_lines": total_lines,
            "text_files": len([f for f in files if f.is_text]),
            "binary_files": len([f for f in files if not f.is_text]),
            "extensions": extensions,
            "largest_file": max(files, key=lambda f: f.size) if files else None,
        }
    
    def filter_files_by_extension(self, files: List[FileInfo], extensions: List[str]) -> List[FileInfo]:
        """Filter files by extension."""
        ext_set = {ext.lower() for ext in extensions}
        return [f for f in files if f.path.suffix.lower() in ext_set]
    
    def filter_files_by_size(self, files: List[FileInfo], min_size: int = 0, max_size: int = float('inf')) -> List[FileInfo]:
        """Filter files by size range."""
        return [f for f in files if min_size <= f.size <= max_size]
