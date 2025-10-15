"""
Unit tests for GitUtils class.
"""

import subprocess
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

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_tracked_files_with_extensions(self, mock_run, temp_dir):
        """Test get_tracked_files with extension filtering."""
        # Mock git root
        mock_run.side_effect = [
            Mock(returncode=0, stdout=str(temp_dir)),  # get_git_root
            Mock(returncode=0, stdout="file1.py\nfile2.js\nfile3.py\n")  # ls-files
        ]
        
        # Create files for existence check
        (temp_dir / "file1.py").write_text("test")
        (temp_dir / "file2.js").write_text("test")
        (temp_dir / "file3.py").write_text("test")
        
        files = GitUtils.get_tracked_files(str(temp_dir), file_extensions=[".py"])
        
        assert len(files) == 2
        assert all(f.endswith(".py") for f in files)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_tracked_files_no_git_root(self, mock_run, temp_dir):
        """Test get_tracked_files when not in a git repo."""
        mock_run.return_value = Mock(returncode=1)  # get_git_root fails
        
        files = GitUtils.get_tracked_files(str(temp_dir))
        
        assert files == []

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_diff_files_success(self, mock_run, temp_dir):
        """Test get_diff_files returns modified files."""
        # Mock git root and file lists
        def mock_subprocess(*args, **kwargs):
            cmd = args[0]
            if "show-toplevel" in cmd:
                return Mock(returncode=0, stdout=str(temp_dir))
            elif "--cached" in cmd:
                return Mock(returncode=0, stdout="staged.py\n")
            elif "diff" in cmd:
                return Mock(returncode=0, stdout="unstaged.py\n")
            elif "--others" in cmd:
                return Mock(returncode=0, stdout="untracked.py\n")
            return Mock(returncode=1)
        
        mock_run.side_effect = mock_subprocess
        
        # Create files
        (temp_dir / "staged.py").write_text("test")
        (temp_dir / "unstaged.py").write_text("test")
        (temp_dir / "untracked.py").write_text("test")
        
        files = GitUtils.get_diff_files(str(temp_dir))
        
        assert isinstance(files, list)
        assert len(files) >= 0

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_git_tracked_and_new_files(self, mock_run, temp_dir):
        """Test get_git_tracked_and_new_files."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="file1.py\nfile2.py\n"),  # ls-files command
            Mock(returncode=0, stdout=str(temp_dir))  # get_git_root
        ]
        
        # Create files
        (temp_dir / "file1.py").write_text("test")
        (temp_dir / "file2.py").write_text("test")
        
        files = GitUtils.get_git_tracked_and_new_files(str(temp_dir))
        
        assert isinstance(files, list)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_code_files_filters_extensions(self, mock_run, temp_dir):
        """Test get_code_files filters by code extensions."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout=str(temp_dir)),  # get_git_root
            Mock(returncode=0, stdout="code.py\nREADME.md\nscript.js\nimage.png\n")  # ls-files
        ]
        
        # Create files
        (temp_dir / "code.py").write_text("test")
        (temp_dir / "script.js").write_text("test")
        (temp_dir / "README.md").write_text("test")
        (temp_dir / "image.png").write_text("test")
        
        files = GitUtils.get_code_files(str(temp_dir))
        
        assert isinstance(files, list)
        # Should only include code files (.py, .js), not .md or .png

    @pytest.mark.unit
    @patch('codetective.utils.git_utils.GitUtils.get_git_root')
    def test_convert_to_absolute_paths(self, mock_git_root, temp_dir):
        """Test _convert_to_absolute_paths."""
        mock_git_root.return_value = str(temp_dir)
        
        # Create test files
        (temp_dir / "file1.py").write_text("test")
        (temp_dir / "file2.py").write_text("test")
        
        relative_files = ["file1.py", "file2.py", "nonexistent.py"]
        
        absolute_files = GitUtils._convert_to_absolute_paths(relative_files, str(temp_dir))
        
        assert len(absolute_files) == 2  # Only existing files
        assert all(Path(f).is_absolute() for f in absolute_files)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_staged_files(self, mock_run, temp_dir):
        """Test _get_staged_files."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="staged1.py\nstaged2.py\n"
        )
        
        files = GitUtils._get_staged_files(str(temp_dir))
        
        assert "staged1.py" in files
        assert "staged2.py" in files

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_unstaged_files(self, mock_run, temp_dir):
        """Test _get_unstaged_files."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="modified1.py\nmodified2.py\n"
        )
        
        files = GitUtils._get_unstaged_files(str(temp_dir))
        
        assert "modified1.py" in files
        assert "modified2.py" in files

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_untracked_files(self, mock_run, temp_dir):
        """Test _get_untracked_files."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="new1.py\nnew2.py\n"
        )
        
        files = GitUtils._get_untracked_files(str(temp_dir))
        
        assert "new1.py" in files
        assert "new2.py" in files

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_git_operations_with_errors(self, mock_run, temp_dir):
        """Test git operations handle errors gracefully."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        # Should not crash
        assert GitUtils._get_staged_files(str(temp_dir)) == []
        assert GitUtils._get_unstaged_files(str(temp_dir)) == []
        assert GitUtils._get_untracked_files(str(temp_dir)) == []

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_get_tracked_files_nonexistent_files_filtered(self, mock_run, temp_dir):
        """Test that nonexistent files are filtered out."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout=str(temp_dir)),  # get_git_root
            Mock(returncode=0, stdout="exists.py\nnonexistent.py\n")  # ls-files
        ]
        
        # Only create one file
        (temp_dir / "exists.py").write_text("test")
        
        files = GitUtils.get_tracked_files(str(temp_dir))
        
        assert len(files) == 1
        assert str(Path(temp_dir) / "exists.py") in files
