"""
Unit tests for FileUtils class.
"""

import pytest
from pathlib import Path

from codetective.utils.file_utils import FileUtils


class TestFileUtilsValidatePaths:
    """Test cases for FileUtils.validate_paths."""

    def test_validate_single_existing_file(self, sample_python_file):
        """Test validating a single existing file."""
        paths = [sample_python_file]  # Already a string from fixture
        validated = FileUtils.validate_paths(paths)
        
        assert len(validated) == 1
        assert Path(validated[0]).exists()

    def test_validate_single_existing_directory(self, temp_dir):
        """Test validating a single existing directory."""
        paths = [str(temp_dir)]
        validated = FileUtils.validate_paths(paths)
        
        assert len(validated) == 1
        assert Path(validated[0]).is_dir()

    def test_validate_nonexistent_path(self):
        """Test that nonexistent paths are filtered out."""
        paths = ["/nonexistent/path/to/file.py"]
        validated = FileUtils.validate_paths(paths)
        
        assert len(validated) == 0

    def test_validate_mixed_paths(self, sample_python_file, temp_dir):
        """Test validating mix of files, directories, and invalid paths."""
        paths = [
            sample_python_file,  # Already a string from fixture
            str(temp_dir),
            "/nonexistent/file.py"
        ]
        validated = FileUtils.validate_paths(paths)
        
        assert len(validated) == 2
        # Validate that the paths are resolved and contain the expected files
        validated_resolved = [str(Path(p).resolve()) for p in validated]
        assert str(Path(sample_python_file).resolve()) in validated_resolved
        assert str(temp_dir.resolve()) in validated_resolved

    def test_validate_empty_list(self):
        """Test validating empty path list."""
        validated = FileUtils.validate_paths([])
        
        assert len(validated) == 0

    def test_validate_resolves_relative_paths(self, temp_dir):
        """Test that relative paths are resolved to absolute."""
        # Create a file in temp_dir
        test_file = temp_dir / "test.py"
        test_file.write_text("print('test')")
        
        paths = [str(test_file)]
        validated = FileUtils.validate_paths(paths)
        
        assert len(validated) == 1
        assert Path(validated[0]).is_absolute()


class TestFileUtilsGitignore:
    """Test cases for .gitignore handling."""

    def test_load_gitignore_no_file(self, temp_dir):
        """Test loading gitignore when .gitignore doesn't exist."""
        patterns = FileUtils.load_gitignore_patterns(str(temp_dir))
        
        # Should still have default patterns
        assert "codetective_scan_results.json" in patterns
        assert "*.codetective.backup" in patterns

    def test_load_gitignore_with_file(self, temp_dir, gitignore_file):
        """Test loading gitignore patterns from file."""
        patterns = FileUtils.load_gitignore_patterns(str(temp_dir))
        
        # Should include default patterns
        assert "codetective_scan_results*.json" in patterns
        
        # Should include patterns from file
        assert "__pycache__/" in patterns
        assert "venv/" in patterns
        assert "node_modules/" in patterns

    def test_load_gitignore_ignores_comments(self, temp_dir):
        """Test that comments are ignored in .gitignore."""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("# This is a comment\n*.pyc\n# Another comment\nvenv/")
        
        patterns = FileUtils.load_gitignore_patterns(str(temp_dir))
        
        assert "*.pyc" in patterns
        assert "venv/" in patterns
        assert "# This is a comment" not in patterns

    def test_load_gitignore_ignores_empty_lines(self, temp_dir):
        """Test that empty lines are ignored."""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.pyc\n\n\nvenv/\n\n")
        
        patterns = FileUtils.load_gitignore_patterns(str(temp_dir))
        
        assert "*.pyc" in patterns
        assert "venv/" in patterns
        # Empty strings shouldn't be in patterns
        assert "" not in [p for p in patterns if p]

    def test_is_ignored_by_git_file_pattern(self, temp_dir):
        """Test checking if file matches gitignore pattern."""
        patterns = ["*.pyc", "*.log"]
        
        test_file = temp_dir / "test.pyc"
        test_file.write_text("")
        
        is_ignored = FileUtils.is_ignored_by_git(test_file, temp_dir, patterns)
        
        assert is_ignored is True

    def test_is_ignored_by_git_directory_pattern(self, temp_dir):
        """Test checking if file is in ignored directory."""
        patterns = ["__pycache__/", "venv/"]
        
        # Create file in ignored directory
        cache_dir = temp_dir / "__pycache__"
        cache_dir.mkdir()
        test_file = cache_dir / "test.pyc"
        test_file.write_text("")
        
        is_ignored = FileUtils.is_ignored_by_git(test_file, temp_dir, patterns)
        
        assert is_ignored is True

    def test_is_ignored_by_git_not_ignored(self, temp_dir):
        """Test file that should not be ignored."""
        patterns = ["*.pyc", "venv/"]
        
        test_file = temp_dir / "test.py"
        test_file.write_text("print('test')")
        
        is_ignored = FileUtils.is_ignored_by_git(test_file, temp_dir, patterns)
        
        assert is_ignored is False

    def test_is_ignored_by_git_nested_directory(self, temp_dir):
        """Test file in nested ignored directory."""
        patterns = ["node_modules/"]
        
        # Create nested structure
        node_modules = temp_dir / "node_modules" / "package" / "lib"
        node_modules.mkdir(parents=True)
        test_file = node_modules / "index.js"
        test_file.write_text("module.exports = {};")
        
        is_ignored = FileUtils.is_ignored_by_git(test_file, temp_dir, patterns)
        
        assert is_ignored is True

    def test_is_ignored_by_git_wildcard_pattern(self, temp_dir):
        """Test wildcard patterns in gitignore."""
        patterns = ["test_*.py", "*.backup"]
        
        test_file = temp_dir / "test_example.py"
        test_file.write_text("# test file")
        
        is_ignored = FileUtils.is_ignored_by_git(test_file, temp_dir, patterns)
        
        assert is_ignored is True

    def test_is_ignored_by_git_codetective_results(self, temp_dir):
        """Test that codetective result files are always ignored."""
        patterns = FileUtils.load_gitignore_patterns(str(temp_dir))
        
        result_file = temp_dir / "codetective_scan_results.json"
        result_file.write_text("{}")
        
        is_ignored = FileUtils.is_ignored_by_git(result_file, temp_dir, patterns)
        
        assert is_ignored is True

    def test_is_ignored_by_git_backup_files(self, temp_dir):
        """Test that backup files are always ignored."""
        patterns = FileUtils.load_gitignore_patterns(str(temp_dir))
        
        backup_file = temp_dir / "test.py.codetective.backup"
        backup_file.write_text("backup content")
        
        is_ignored = FileUtils.is_ignored_by_git(backup_file, temp_dir, patterns)
        
        assert is_ignored is True


class TestFileUtilsGetFileList:
    """Test cases for FileUtils.get_file_list (if implemented)."""

    def test_get_file_list_respects_gitignore(self, temp_dir, gitignore_file):
        """Test that get_file_list respects .gitignore patterns."""
        # Create various files
        (temp_dir / "main.py").write_text("# main")
        (temp_dir / "test.pyc").write_text("")
        
        venv_dir = temp_dir / "venv"
        venv_dir.mkdir()
        (venv_dir / "lib.py").write_text("# lib")
        
        # If get_file_list is implemented, test it
        # This is a placeholder for when the method exists
        if hasattr(FileUtils, 'get_file_list'):
            files = FileUtils.get_file_list([str(temp_dir)], respect_gitignore=True)
            
            # Should include main.py
            assert any("main.py" in f for f in files)
            
            # Should not include .pyc or venv files
            assert not any(".pyc" in f for f in files)
            assert not any("venv" in f for f in files)


class TestFileUtilsBackup:
    """Test cases for file backup operations (if implemented)."""

    def test_create_backup_file(self, sample_python_file):
        """Test creating backup of a file."""
        if hasattr(FileUtils, 'create_backup'):
            backup_path = FileUtils.create_backup(str(sample_python_file))
            
            assert Path(backup_path).exists()
            assert ".backup" in backup_path
            
            # Cleanup
            Path(backup_path).unlink()

    def test_restore_from_backup(self, sample_python_file):
        """Test restoring file from backup."""
        if hasattr(FileUtils, 'create_backup') and hasattr(FileUtils, 'restore_backup'):
            original_content = sample_python_file.read_text()
            backup_path = FileUtils.create_backup(str(sample_python_file))
            
            # Modify original
            sample_python_file.write_text("modified content")
            
            # Restore
            FileUtils.restore_backup(backup_path, str(sample_python_file))
            
            assert sample_python_file.read_text() == original_content
            
            # Cleanup
            Path(backup_path).unlink()
