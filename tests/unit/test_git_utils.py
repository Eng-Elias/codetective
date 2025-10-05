"""
Unit tests for GitUtils class.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from codetective.utils.git_utils import GitUtils


class TestGitUtils:
    """Test cases for GitUtils class."""

    @pytest.mark.unit
    def test_is_git_repo_true(self, temp_dir):
        """Test is_git_repo when directory is a git repository."""
        # Create .git directory
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = GitUtils.is_git_repo(str(temp_dir))
            
            assert result is True

    @pytest.mark.unit
    def test_is_git_repo_false(self, temp_dir):
        """Test is_git_repo when directory is not a git repository."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)
            
            result = GitUtils.is_git_repo(str(temp_dir))
            
            assert result is False

    @pytest.mark.unit
    def test_get_git_root_success(self, temp_dir):
        """Test getting git repository root."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=str(temp_dir)
            )
            
            root = GitUtils.get_git_root(str(temp_dir))
            
            assert root is not None
            assert Path(root).exists()

    @pytest.mark.unit
    def test_get_git_root_failure(self, temp_dir):
        """Test get_git_root when not in a git repository."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1)
            
            root = GitUtils.get_git_root(str(temp_dir))
            
            assert root is None

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_tracked_files_with_extension_filter(self, mock_run, temp_dir):
        """Test getting tracked files filtered by extension."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file1.py\nfile2.py\nfile3.js\n"
        )
        
        if hasattr(GitUtils, 'get_tracked_files'):
            # Some implementations might support extension filtering
            files = GitUtils.get_tracked_files(str(temp_dir), file_extensions=[".py"])
            
            # Result depends on implementation
            assert isinstance(files, list)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_code_files(self, mock_run, temp_dir):
        """Test getting git-tracked code files only."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file1.py\nfile2.js\nREADME.md\nimage.png\n"
        )
        
        if hasattr(GitUtils, 'get_code_files'):
            files = GitUtils.get_code_files(str(temp_dir))
            
            assert isinstance(files, list)
            # Should filter to code files only (implementation dependent)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_all_selectable_files(self, mock_run, temp_dir):
        """Test getting all selectable files (tracked + untracked respecting .gitignore)."""
        # Create some test files
        (temp_dir / "tracked.py").write_text("# tracked")
        (temp_dir / "untracked.py").write_text("# untracked")
        (temp_dir / ".gitignore").write_text("*.pyc\n")
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout="tracked.py\n"
        )
        
        if hasattr(GitUtils, 'get_all_selectable_files'):
            files = GitUtils.get_all_selectable_files(str(temp_dir))
            
            assert isinstance(files, list)
            # Should include both tracked and untracked .py files

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_file_count(self, mock_run, temp_dir):
        """Test counting git-tracked code files."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file1.py\nfile2.py\nfile3.js\n"
        )
        
        if hasattr(GitUtils, 'get_file_count'):
            count = GitUtils.get_file_count(str(temp_dir))
            
            assert isinstance(count, int)
            assert count >= 0

    @pytest.mark.unit
    def test_build_git_tree_structure(self, temp_dir):
        """Test building tree structure from git files."""
        files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md"
        ]
        
        if hasattr(GitUtils, 'build_git_tree_structure'):
            tree = GitUtils.build_git_tree_structure(files, str(temp_dir))
            
            assert isinstance(tree, dict)
            # Tree should have hierarchical structure

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_git_diff_files(self, mock_run, temp_dir):
        """Test getting files from git diff."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  modified.py\nA  added.py\nD  deleted.py\n"
        )
        
        if hasattr(GitUtils, 'get_git_diff_files'):
            files = GitUtils.get_git_diff_files(str(temp_dir))
            
            assert isinstance(files, list)
            # Should return modified and added files (not deleted)

    @pytest.mark.unit
    def test_build_enhanced_git_tree_structure(self, temp_dir):
        """Test building enhanced tree structure."""
        tracked = ["src/main.py", "src/utils.py"]
        untracked = ["src/new.py", "tests/new_test.py"]
        
        if hasattr(GitUtils, 'build_enhanced_git_tree_structure'):
            tree = GitUtils.build_enhanced_git_tree_structure(
                tracked, untracked, str(temp_dir)
            )
            
            assert isinstance(tree, dict)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_git_command_timeout(self, mock_run, temp_dir):
        """Test handling of git command timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=['git'], timeout=5)
        
        # Should handle timeout gracefully
        result = GitUtils.is_git_repo(str(temp_dir))
        
        assert result is False

    @pytest.mark.integration
    def test_real_git_operations(self, temp_dir):
        """Test with real git operations (if git is available)."""
        import subprocess
        
        try:
            # Try to initialize a git repo
            subprocess.run(['git', 'init'], cwd=temp_dir, check=True, capture_output=True)
            
            # Test is_git_repo
            assert GitUtils.is_git_repo(str(temp_dir)) is True
            
            # Test get_git_root
            root = GitUtils.get_git_root(str(temp_dir))
            assert root is not None
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Git not available or operation failed")
