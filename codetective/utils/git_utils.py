"""
Git utilities for Codetective - handle git repository operations.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class GitUtils:
    """Utility class for git repository operations."""

    @staticmethod
    def is_git_repo(path: str) -> bool:
        """Check if a directory is a git repository."""
        try:
            git_dir = Path(path) / ".git"
            if git_dir.exists():
                return True

            # Check if we're in a git worktree
            result = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=path, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
            return False

    @staticmethod
    def get_git_root(path: str) -> Optional[str]:
        """Get the root directory of the git repository."""
        try:
            result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None

    @staticmethod
    def get_tracked_files(repo_path: str, file_extensions: Optional[List[str]] = None) -> List[str]:
        """Get all tracked files in the git repository."""
        try:
            # Get git root to ensure we're working from the right directory
            git_root = GitUtils.get_git_root(repo_path)
            if not git_root:
                return []

            result = subprocess.run(["git", "ls-files"], cwd=git_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return []

            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    file_path = Path(git_root) / line
                    if file_path.exists() and file_path.is_file():
                        # Filter by extensions if provided
                        if file_extensions:
                            if any(line.endswith(ext) for ext in file_extensions):
                                files.append(str(file_path))
                        else:
                            files.append(str(file_path))

            return files
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
            return []

    @staticmethod
    def get_diff_files(repo_path: Optional[str] = None) -> List[str]:
        """Get list of new/modified files from git diff."""
        try:
            cwd = repo_path or os.getcwd()
            all_files = []

            # Collect files from different git states
            all_files.extend(GitUtils._get_staged_files(cwd))
            all_files.extend(GitUtils._get_unstaged_files(cwd))
            all_files.extend(GitUtils._get_untracked_files(cwd))

            # Convert to absolute paths
            return GitUtils._convert_to_absolute_paths(all_files, cwd)

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError):
            return []

    @staticmethod
    def _get_staged_files(cwd: str) -> List[str]:
        """Get staged files from git diff --cached."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"], cwd=cwd, capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split("\n") if f.strip()]
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        return []

    @staticmethod
    def _get_unstaged_files(cwd: str) -> List[str]:
        """Get unstaged files from git diff."""
        try:
            result = subprocess.run(["git", "diff", "--name-only"], cwd=cwd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split("\n") if f.strip()]
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        return []

    @staticmethod
    def _get_untracked_files(cwd: str) -> List[str]:
        """Get untracked files from git ls-files."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split("\n") if f.strip()]
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        return []

    @staticmethod
    def _convert_to_absolute_paths(files: List[str], cwd: str) -> List[str]:
        """Convert relative file paths to absolute paths and filter existing files."""
        git_root = GitUtils.get_git_root(cwd)
        if not git_root:
            return []

        absolute_files = []
        for file_path in set(files):  # Remove duplicates
            abs_path = Path(git_root) / file_path
            if abs_path.exists() and abs_path.is_file():
                absolute_files.append(str(abs_path))

        return absolute_files

    @staticmethod
    def get_git_tracked_and_new_files(repo_path: str) -> List[str]:
        """Get all tracked and new files in the repository."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            result_files = []

            if result.returncode == 0:
                result_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            return GitUtils._convert_to_absolute_paths(result_files, repo_path)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        return []

    @staticmethod
    def get_code_files(repo_path: str) -> List[str]:
        """Get all tracked code files in the repository."""
        code_extensions = [
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
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".sh",
            ".yaml",
            ".yml",
            ".json",
            ".xml",
            ".html",
            ".css",
            ".scss",
            ".less",
            ".md",
            ".txt",
            ".sql",
            ".r",
            ".m",
            ".pl",
            ".lua",
            ".dart",
            ".vue",
        ]

        return GitUtils.get_tracked_files(repo_path, code_extensions)

    @staticmethod
    def build_git_tree_structure(repo_path: str, max_depth: int = 3) -> List[dict]:
        """Build a tree structure of git-tracked files for UI components."""
        try:
            git_root = GitUtils.get_git_root(repo_path)
            if not git_root:
                return []

            # Get all tracked code files
            tracked_files = GitUtils.get_code_files(git_root)
            if not tracked_files:
                return []

            # Build tree structure
            tree: Dict[str, Dict[str, List[str]]] = {}
            root_path = Path(git_root)

            for file_path in tracked_files:
                try:
                    rel_path = Path(file_path).relative_to(root_path)
                    parts = rel_path.parts

                    # Skip files that are too deep
                    if len(parts) > max_depth:
                        continue

                    current = tree
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:  # It's a file
                            if "files" not in current:
                                current["files"] = []
                            current["files"].append({"name": part, "path": str(rel_path), "full_path": file_path})
                        else:  # It's a directory
                            if "dirs" not in current:
                                current["dirs"] = {}
                            if part not in current["dirs"]:
                                current["dirs"][part] = {}
                            current = current["dirs"][part]
                except ValueError:
                    # File is not under git root, skip
                    continue

            # Convert tree structure to nicegui_tree_select format
            return GitUtils._convert_tree_to_nodes(tree, root_path)

        except Exception:
            return []

    @staticmethod
    def _convert_tree_to_nodes(tree: dict, root_path: Path, current_path: str = "") -> List[dict]:
        """Convert internal tree structure to nicegui_tree_select nodes."""
        nodes = []

        # Add directories first
        if "dirs" in tree:
            for dir_name, subtree in sorted(tree["dirs"].items()):
                dir_path = f"{current_path}/{dir_name}" if current_path else dir_name
                children = GitUtils._convert_tree_to_nodes(subtree, root_path, dir_path)

                node = {
                    "label": f"📁 {dir_name}",
                    "value": f"dir_{dir_path}",
                }
                if children:
                    node["children"] = children
                nodes.append(node)

        # Add files
        if "files" in tree:
            for file_info in sorted(tree["files"], key=lambda x: x["name"]):
                file_path = f"{current_path}/{file_info['name']}" if current_path else file_info["name"]
                node = {"label": f"📄 {file_info['name']}", "value": f"file_{file_path}"}
                nodes.append(node)

        return nodes

    @staticmethod
    def get_file_count(repo_path: str) -> int:
        """Get count of tracked code files in the repository."""
        try:
            tracked_files = GitUtils.get_code_files(repo_path)
            return len(tracked_files)
        except Exception:
            return 0
