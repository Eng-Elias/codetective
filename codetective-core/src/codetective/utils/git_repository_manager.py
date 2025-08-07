"""
Git repository management utilities for the codetective system.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from loguru import logger


@dataclass
class GitFileInfo:
    """Information about a file in a Git repository."""
    
    path: Path
    status: str  # A=added, M=modified, D=deleted, R=renamed, C=copied, U=unmerged
    staged: bool
    is_tracked: bool


@dataclass
class GitCommitInfo:
    """Information about a Git commit."""
    
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]


class GitRepositoryManager:
    """
    Manages Git repository operations for code analysis.
    
    This class provides methods for interacting with Git repositories,
    including file status detection, diff analysis, and commit information.
    """
    
    def __init__(self, repo_path: Path):
        """
        Initialize the Git repository manager.
        
        Args:
            repo_path: Path to the Git repository root
        """
        self.repo_path = Path(repo_path)
        self._git_dir = self._find_git_directory()
        
        if not self._git_dir:
            raise ValueError(f"Not a Git repository: {repo_path}")
    
    @property
    def is_git_repository(self) -> bool:
        """Check if the path is a Git repository."""
        return self._git_dir is not None
    
    @property
    def git_root(self) -> Path:
        """Get the Git repository root directory."""
        if self._git_dir:
            return self._git_dir.parent
        return self.repo_path
    
    def _find_git_directory(self) -> Optional[Path]:
        """Find the .git directory by walking up the directory tree."""
        current_path = self.repo_path.resolve()
        
        while current_path != current_path.parent:
            git_dir = current_path / ".git"
            if git_dir.exists():
                return git_dir
            current_path = current_path.parent
        
        return None
    
    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None) -> str:
        """
        Run a Git command and return the output.
        
        Args:
            args: Git command arguments
            cwd: Working directory for the command
            
        Returns:
            Command output as string
        """
        cmd = ["git"] + args
        work_dir = cwd or self.git_root
        
        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            return result.stdout.strip()
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            raise
        
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: {' '.join(cmd)}")
            raise
    
    def get_repository_status(self) -> Dict[str, Any]:
        """
        Get overall repository status information.
        
        Returns:
            Dictionary with repository status details
        """
        try:
            # Get current branch
            current_branch = self._run_git_command(["branch", "--show-current"])
            
            # Get remote URL
            try:
                remote_url = self._run_git_command(["remote", "get-url", "origin"])
            except subprocess.CalledProcessError:
                remote_url = None
            
            # Get last commit info
            try:
                last_commit = self._run_git_command([
                    "log", "-1", "--format=%H|%an|%ad|%s", "--date=iso"
                ])
                commit_parts = last_commit.split("|", 3)
                last_commit_info = {
                    "hash": commit_parts[0],
                    "author": commit_parts[1],
                    "date": commit_parts[2],
                    "message": commit_parts[3] if len(commit_parts) > 3 else "",
                }
            except subprocess.CalledProcessError:
                last_commit_info = None
            
            # Get status summary
            status_output = self._run_git_command(["status", "--porcelain"])
            modified_files = len([line for line in status_output.split("\n") if line.strip()])
            
            return {
                "is_git_repo": True,
                "current_branch": current_branch,
                "remote_url": remote_url,
                "last_commit": last_commit_info,
                "modified_files_count": modified_files,
                "is_clean": modified_files == 0,
            }
        
        except Exception as e:
            logger.error(f"Error getting repository status: {e}")
            return {"is_git_repo": False, "error": str(e)}
    
    def get_modified_files(self, include_staged: bool = True, include_unstaged: bool = True) -> List[GitFileInfo]:
        """
        Get list of modified files in the repository.
        
        Args:
            include_staged: Include staged files
            include_unstaged: Include unstaged files
            
        Returns:
            List of GitFileInfo objects for modified files
        """
        try:
            status_output = self._run_git_command(["status", "--porcelain"])
            modified_files = []
            
            for line in status_output.split("\n"):
                if not line.strip():
                    continue
                
                # Parse git status format: XY filename
                staged_status = line[0] if len(line) > 0 else " "
                unstaged_status = line[1] if len(line) > 1 else " "
                filename = line[3:] if len(line) > 3 else ""
                
                # Determine if file should be included
                is_staged = staged_status != " "
                is_unstaged = unstaged_status != " "
                
                if (include_staged and is_staged) or (include_unstaged and is_unstaged):
                    file_info = GitFileInfo(
                        path=self.git_root / filename,
                        status=staged_status if is_staged else unstaged_status,
                        staged=is_staged,
                        is_tracked=True,
                    )
                    modified_files.append(file_info)
            
            return modified_files
        
        except Exception as e:
            logger.error(f"Error getting modified files: {e}")
            return []
    
    def get_tracked_files(self, path_filter: Optional[str] = None) -> List[Path]:
        """
        Get list of all tracked files in the repository.
        
        Args:
            path_filter: Optional path filter (glob pattern)
            
        Returns:
            List of tracked file paths
        """
        try:
            args = ["ls-files"]
            if path_filter:
                args.append(path_filter)
            
            output = self._run_git_command(args)
            tracked_files = []
            
            for line in output.split("\n"):
                if line.strip():
                    file_path = self.git_root / line.strip()
                    if file_path.exists():
                        tracked_files.append(file_path)
            
            return tracked_files
        
        except Exception as e:
            logger.error(f"Error getting tracked files: {e}")
            return []
    
    def get_untracked_files(self) -> List[Path]:
        """Get list of untracked files in the repository."""
        try:
            output = self._run_git_command(["ls-files", "--others", "--exclude-standard"])
            untracked_files = []
            
            for line in output.split("\n"):
                if line.strip():
                    file_path = self.git_root / line.strip()
                    if file_path.exists():
                        untracked_files.append(file_path)
            
            return untracked_files
        
        except Exception as e:
            logger.error(f"Error getting untracked files: {e}")
            return []
    
    def get_file_diff(self, file_path: Path, staged: bool = False) -> Optional[str]:
        """
        Get diff for a specific file.
        
        Args:
            file_path: Path to the file
            staged: Get staged diff instead of working directory diff
            
        Returns:
            Diff content as string, or None if no diff
        """
        try:
            relative_path = file_path.relative_to(self.git_root)
            
            args = ["diff"]
            if staged:
                args.append("--staged")
            args.append(str(relative_path))
            
            diff_output = self._run_git_command(args)
            return diff_output if diff_output else None
        
        except Exception as e:
            logger.error(f"Error getting diff for {file_path}: {e}")
            return None
    
    def get_commit_history(self, max_commits: int = 10, file_path: Optional[Path] = None) -> List[GitCommitInfo]:
        """
        Get commit history for the repository or a specific file.
        
        Args:
            max_commits: Maximum number of commits to retrieve
            file_path: Optional file path to get history for
            
        Returns:
            List of GitCommitInfo objects
        """
        try:
            args = [
                "log",
                f"-{max_commits}",
                "--format=%H|%an|%ad|%s",
                "--date=iso",
                "--name-only"
            ]
            
            if file_path:
                relative_path = file_path.relative_to(self.git_root)
                args.append(str(relative_path))
            
            output = self._run_git_command(args)
            commits = []
            
            commit_blocks = output.split("\n\n")
            for block in commit_blocks:
                if not block.strip():
                    continue
                
                lines = block.strip().split("\n")
                if not lines:
                    continue
                
                # Parse commit info line
                commit_line = lines[0]
                parts = commit_line.split("|", 3)
                if len(parts) < 4:
                    continue
                
                # Parse changed files
                files_changed = [line.strip() for line in lines[1:] if line.strip()]
                
                try:
                    commit_date = datetime.fromisoformat(parts[2].replace(" ", "T", 1))
                except ValueError:
                    commit_date = datetime.now()
                
                commit_info = GitCommitInfo(
                    hash=parts[0],
                    author=parts[1],
                    date=commit_date,
                    message=parts[3],
                    files_changed=files_changed,
                )
                commits.append(commit_info)
            
            return commits
        
        except Exception as e:
            logger.error(f"Error getting commit history: {e}")
            return []
    
    def is_file_ignored(self, file_path: Path) -> bool:
        """
        Check if a file is ignored by Git.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is ignored, False otherwise
        """
        try:
            relative_path = file_path.relative_to(self.git_root)
            self._run_git_command(["check-ignore", str(relative_path)])
            return True
        
        except subprocess.CalledProcessError:
            # File is not ignored
            return False
        
        except Exception as e:
            logger.error(f"Error checking if file is ignored: {e}")
            return False
    
    def get_branch_list(self) -> List[str]:
        """Get list of all branches in the repository."""
        try:
            output = self._run_git_command(["branch", "-a"])
            branches = []
            
            for line in output.split("\n"):
                line = line.strip()
                if line:
                    # Remove current branch marker and remote prefixes
                    branch = line.lstrip("* ").replace("remotes/origin/", "")
                    if branch not in branches and not branch.startswith("HEAD"):
                        branches.append(branch)
            
            return branches
        
        except Exception as e:
            logger.error(f"Error getting branch list: {e}")
            return []
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get comprehensive repository statistics."""
        try:
            status = self.get_repository_status()
            modified_files = self.get_modified_files()
            tracked_files = self.get_tracked_files()
            untracked_files = self.get_untracked_files()
            branches = self.get_branch_list()
            
            return {
                **status,
                "tracked_files_count": len(tracked_files),
                "untracked_files_count": len(untracked_files),
                "modified_files": [
                    {
                        "path": str(f.path.relative_to(self.git_root)),
                        "status": f.status,
                        "staged": f.staged,
                    }
                    for f in modified_files
                ],
                "branch_count": len(branches),
                "branches": branches,
            }
        
        except Exception as e:
            logger.error(f"Error getting repository stats: {e}")
            return {"error": str(e)}
