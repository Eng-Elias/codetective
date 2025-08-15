"""
Utility functions for Codetective.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
import fnmatch
from ..models.schemas import SystemInfo
from .. import __version__


def check_tool_availability(tool_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a tool is available in PATH and get its version."""
    try:
        if tool_name == "ollama":
            # Check Ollama via multiple methods
            # Method 1: Try HTTP API
            try:
                response = requests.get("http://localhost:11434/api/version", timeout=3)
                if response.status_code == 200:
                    version_info = response.json()
                    return True, version_info.get("version", "running")
            except requests.RequestException:
                pass
            
            # Method 2: Try command line
            try:
                result = subprocess.run(["ollama", "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_line = result.stdout.strip().split('\n')[0]
                    return True, version_line
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Method 3: Check if ollama process is running
            try:
                result = subprocess.run(["ollama", "list"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True, "available"
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            return False, None
        else:
            # Check other tools via subprocess
            result = subprocess.run([tool_name, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract version from output (first line usually contains version)
                version_line = result.stdout.strip().split('\n')[0]
                return True, version_line
            return False, None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, 
            requests.RequestException, FileNotFoundError):
        return False, None


def get_system_info() -> SystemInfo:
    """Get comprehensive system information."""
    semgrep_available, semgrep_version = check_tool_availability("semgrep")
    trivy_available, trivy_version = check_tool_availability("trivy")
    ollama_available, ollama_version = check_tool_availability("ollama")
    
    return SystemInfo(
        semgrep_available=semgrep_available,
        trivy_available=trivy_available,
        ollama_available=ollama_available,
        semgrep_version=semgrep_version,
        trivy_version=trivy_version,
        ollama_version=ollama_version,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        codetective_version=__version__
    )


def validate_paths(paths: List[str]) -> List[str]:
    """Validate and normalize file/directory paths."""
    validated_paths = []
    
    for path_str in paths:
        path = Path(path_str).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if not (path.is_file() or path.is_dir()):
            raise ValueError(f"Path is neither a file nor directory: {path}")
        
        validated_paths.append(str(path))
    
    return validated_paths


def load_gitignore_patterns(project_path: str) -> List[str]:
    """Load .gitignore patterns from project directory."""
    gitignore_path = Path(project_path) / ".gitignore"
    patterns = []
    
    # Always ignore codetective results file
    patterns.extend([
        "codetective_scan_results.json",
        "codetective_scan_results*.json",
        "*.codetective.backup"
    ])
    
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception:
            pass
    
    return patterns


def is_ignored_by_git(file_path: Path, project_root: Path, gitignore_patterns: List[str]) -> bool:
    """Check if a file should be ignored based on .gitignore patterns."""
    try:
        # Get relative path from project root
        rel_path = file_path.relative_to(project_root)
        rel_path_str = str(rel_path).replace('\\', '/')
        
        for pattern in gitignore_patterns:
            # Handle directory patterns
            if pattern.endswith('/'):
                dir_pattern = pattern[:-1]
                # Check if any parent directory matches
                for parent in rel_path.parents:
                    parent_str = str(parent).replace('\\', '/')
                    if fnmatch.fnmatch(parent_str, dir_pattern) or parent_str == dir_pattern:
                        return True
            else:
                # Check file patterns
                if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                    return True
                # Check if pattern matches any parent directory
                for parent in rel_path.parents:
                    parent_str = str(parent).replace('\\', '/')
                    if fnmatch.fnmatch(parent_str, pattern):
                        return True
    except ValueError:
        # File is not under project root
        pass
    
    return False


def get_file_list(paths: List[str], include_patterns: List[str] = None, 
                  exclude_patterns: List[str] = None, max_size: int = None,
                  respect_gitignore: bool = True) -> List[str]:
    """Get list of files to scan based on paths and patterns."""
    files = []
    include_patterns = include_patterns or ["*"]
    exclude_patterns = exclude_patterns or []
    
    for path_str in paths:
        path = Path(path_str)
        
        if path.is_file():
            files.append(str(path))
        elif path.is_dir():
            # Load .gitignore patterns if respecting git
            gitignore_patterns = []
            project_root = path
            if respect_gitignore:
                gitignore_patterns = load_gitignore_patterns(str(path))
            
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    # Check if ignored by git
                    if respect_gitignore and gitignore_patterns:
                        if is_ignored_by_git(file_path, project_root, gitignore_patterns):
                            continue
                    
                    # Check file size
                    if max_size and file_path.stat().st_size > max_size:
                        continue
                    
                    # Check include patterns
                    if not any(fnmatch.fnmatch(file_path.name, pattern) 
                              for pattern in include_patterns):
                        continue
                    
                    # Check exclude patterns
                    if any(fnmatch.fnmatch(str(file_path), pattern) 
                          for pattern in exclude_patterns):
                        continue
                    
                    files.append(str(file_path))
    
    return files


def create_backup(file_path: str) -> str:
    """Create a backup of a file before modification."""
    backup_path = f"{file_path}.codetective.backup"
    shutil.copy2(file_path, backup_path)
    return backup_path


def ensure_directory(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def run_command(command: List[str], cwd: str = None, timeout: int = 300) -> Tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr."""
    import signal
    import os
    
    process = None
    try:
        # Start the process
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace invalid characters instead of failing
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        # Wait for completion with timeout
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode == 0, stdout, stderr
        
    except subprocess.TimeoutExpired:
        # Force terminate the process on timeout
        if process:
            try:
                if os.name == 'nt':  # Windows
                    process.terminate()
                else:  # Unix/Linux
                    process.send_signal(signal.SIGTERM)
                process.wait(timeout=5)  # Give it 5 seconds to terminate gracefully
            except:
                if os.name == 'nt':
                    process.kill()
                else:
                    process.send_signal(signal.SIGKILL)
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        if process:
            try:
                process.terminate()
            except:
                pass
        return False, "", str(e)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 1:
        return f"{seconds:.2f}s"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def get_file_content(file_path: str, max_lines: int = None) -> str:
    """Get file content with optional line limit."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                return ''.join(lines)
            else:
                return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def safe_json_dump(data: Any) -> str:
    """Safely dump data to JSON string with error handling."""
    import json
    from datetime import datetime
    
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    try:
        return json.dumps(data, indent=2, default=json_serializer)
    except Exception as e:
        return f'{{"error": "Failed to serialize data: {e}"}}'
