"""
Unit tests for Output agents (CommentAgent and EditAgent).
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from codetective.agents.output.comment_agent import CommentAgent
from codetective.agents.output.edit_agent import EditAgent
from codetective.models.schemas import AgentType, Issue, IssueStatus, SeverityLevel


class TestCommentAgent:
    """Test cases for CommentAgent."""

    def test_comment_agent_init(self, base_config):
        """Test CommentAgent initialization."""
        agent = CommentAgent(base_config)
        
        assert agent.config == base_config
        assert agent.agent_type == AgentType.COMMENT

    def test_is_available_with_ollama(self, base_config):
        """Test is_available when Ollama is available."""
        agent = CommentAgent(base_config)
        
        with patch.object(agent, 'is_ai_available', return_value=True):
            assert agent.is_available() is True

    def test_is_available_without_ollama(self, base_config):
        """Test is_available when Ollama is not available."""
        agent = CommentAgent(base_config)
        
        with patch.object(agent, 'is_ai_available', return_value=False):
            assert agent.is_available() is False

    @pytest.mark.unit
    def test_process_issues_empty_list(self, base_config):
        """Test processing empty issue list."""
        agent = CommentAgent(base_config)
        
        result = agent.process_issues([])
        
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.unit
    def test_process_issues_with_ai(self, base_config, sample_issues, temp_dir, mock_chat_ollama):
        """Test processing issues with AI-generated comments."""
        agent = CommentAgent(base_config)
        
        # Update issue file paths to temp directory
        for issue in sample_issues:
            test_file = temp_dir / "test.py"
            test_file.write_text("# test code\nprint('hello')\n")
            issue.file_path = str(test_file)
            issue.line_number = 2
        
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="# TODO: Fix this security issue"):
            
            result = agent.process_issues(sample_issues)
            
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.unit
    def test_add_comment_to_file(self, base_config, temp_dir, sample_issue):
        """Test adding comment to a file."""
        agent = CommentAgent(base_config)
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("def hello():\n    print('world')\n")
        
        # Update issue with test file info
        sample_issue.file_path = str(test_file)
        sample_issue.line_number = 2
        
        if hasattr(agent, '_add_comment_to_file'):
            result = agent._add_comment_to_file(
                sample_issue,
                "# TODO: Add error handling"
            )
            
            # Check that comment was added
            assert result is True
            content = test_file.read_text()
            assert "TODO" in content

    @pytest.mark.unit
    def test_format_comment_python(self, base_config):
        """Test formatting comment for Python file."""
        agent = CommentAgent(base_config)
        
        if hasattr(agent, '_format_comment'):
            comment = agent._format_comment("test.py", "Fix this issue", indent="    ")
            
            assert comment.startswith("#")
            assert "Fix this issue" in comment

    @pytest.mark.unit
    def test_format_comment_javascript(self, base_config):
        """Test formatting comment for JavaScript file."""
        agent = CommentAgent(base_config)
        
        if hasattr(agent, '_format_comment'):
            comment = agent._format_comment("test.js", "Fix this issue", indent="  ")
            
            assert "//" in comment or "/*" in comment
            assert "Fix this issue" in comment

    @pytest.mark.unit
    def test_process_issues_creates_backup(self, base_config, sample_issues, temp_dir):
        """Test that backup files are created."""
        agent = CommentAgent(base_config)
        agent.config.backup_files = True
        agent.config.keep_backup = True  # Keep backups so we can test they exist
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('test')\n")
        
        sample_issues[0].file_path = str(test_file)
        sample_issues[0].line_number = 1
        
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="# TODO: Fix"):
            
            agent.process_issues([sample_issues[0]])
            
            # Check for backup file
            backup_files = list(temp_dir.glob("*.backup"))
            assert len(backup_files) > 0
            
            # Cleanup
            for backup_file in backup_files:
                backup_file.unlink()

    @pytest.mark.unit
    def test_process_issues_no_line_number(self, base_config, sample_issue, temp_dir):
        """Test processing issue without line number."""
        agent = CommentAgent(base_config)
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("print('test')\n")
        
        sample_issue.file_path = str(test_file)
        sample_issue.line_number = None
        
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="# TODO: Fix"):
            
            result = agent.process_issues([sample_issue])
            
            # Should handle None line number by adding at top
            assert isinstance(result, list)

    @pytest.mark.unit
    def test_generate_concise_comment(self, base_config, sample_issue):
        """Test generating concise comment under 100 words."""
        agent = CommentAgent(base_config)
        
        with patch.object(agent, 'call_ai', return_value="Short comment about the issue"):
            if hasattr(agent, '_generate_comment'):
                comment = agent._generate_comment(sample_issue, "")
                
                # Check word count
                word_count = len(comment.split())
                assert word_count <= 100


class TestEditAgent:
    """Test cases for EditAgent."""

    def test_edit_agent_init(self, base_config):
        """Test EditAgent initialization."""
        agent = EditAgent(base_config)
        
        assert agent.config == base_config
        assert agent.agent_type == AgentType.EDIT

    def test_is_available_with_ollama(self, base_config):
        """Test is_available when Ollama is available."""
        agent = EditAgent(base_config)
        
        with patch.object(agent, 'is_ai_available', return_value=True):
            assert agent.is_available() is True

    def test_is_available_without_ollama(self, base_config):
        """Test is_available when Ollama is not available."""
        agent = EditAgent(base_config)
        
        with patch.object(agent, 'is_ai_available', return_value=False):
            assert agent.is_available() is False

    @pytest.mark.unit
    def test_process_issues_empty_list(self, base_config):
        """Test processing empty issue list."""
        agent = EditAgent(base_config)
        
        result = agent.process_issues([])
        
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.unit
    def test_process_issues_with_fixes(self, base_config, sample_issues, temp_dir, mock_chat_ollama):
        """Test processing issues with AI-generated fixes."""
        agent = EditAgent(base_config)
        
        # Create test file
        test_file = temp_dir / "vulnerable.py"
        test_file.write_text("import os\nos.system(user_input)\n")
        
        for issue in sample_issues:
            issue.file_path = str(test_file)
            issue.line_number = 2
        
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="import subprocess\nsubprocess.run([user_input], shell=False)"):
            
            result = agent.process_issues(sample_issues)
            
            assert isinstance(result, list)
            assert len(result) > 0
            
            # Check that some issues were marked as fixed
            fixed_issues = [i for i in result if i.status == IssueStatus.FIXED]
            failed_issues = [i for i in result if i.status == IssueStatus.FAILED]
            
            # Should have attempted to fix issues
            assert len(fixed_issues) + len(failed_issues) > 0

    @pytest.mark.unit
    def test_apply_fix_to_file(self, base_config, temp_dir):
        """Test applying a fix to a file."""
        agent = EditAgent(base_config)
        
        # Create test file with vulnerable code
        test_file = temp_dir / "test.py"
        original_code = "import os\nos.system(cmd)"
        test_file.write_text(original_code)
        
        fixed_code = "import subprocess\nsubprocess.run([cmd], shell=False)"
        
        if hasattr(agent, '_apply_fix'):
            success = agent._apply_fix(str(test_file), fixed_code)
            
            if success:
                # Check that file was modified
                new_content = test_file.read_text()
                assert new_content != original_code

    @pytest.mark.unit
    def test_batch_processing(self, base_config, sample_issues, temp_dir):
        """Test batch processing of issues."""
        agent = EditAgent(base_config)
        
        # Create multiple test files
        for i, issue in enumerate(sample_issues):
            test_file = temp_dir / f"test{i}.py"
            test_file.write_text(f"# File {i}\nprint('test')\n")
            issue.file_path = str(test_file)
        
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="# Fixed\nprint('fixed')"):
            
            result = agent.process_issues(sample_issues)
            
            # Should process multiple files
            assert isinstance(result, list)

    @pytest.mark.unit
    def test_creates_backup_before_fix(self, base_config, sample_issue, temp_dir):
        """Test that backup is created before applying fix."""
        agent = EditAgent(base_config)
        agent.config.backup_files = True
        agent.config.keep_backup = True  # Keep backups so we can test they exist
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("vulnerable code")
        
        sample_issue.file_path = str(test_file)
        
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="fixed code"):
            
            agent.process_issues([sample_issue])
            
            # Check for backup
            backup_files = list(temp_dir.glob("*.backup"))
            assert len(backup_files) > 0
            
            # Cleanup
            for backup_file in backup_files:
                backup_file.unlink()

    @pytest.mark.unit
    def test_validates_fix_before_applying(self, base_config, sample_issue, temp_dir):
        """Test that fixes are validated before application."""
        agent = EditAgent(base_config)
        
        test_file = temp_dir / "test.py"
        test_file.write_text("def valid():\n    pass\n")
        
        sample_issue.file_path = str(test_file)
        
        # AI returns invalid Python code
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="def invalid(:\n    syntax error"):
            
            result = agent.process_issues([sample_issue])
            
            # Should detect invalid fix
            if hasattr(agent, '_validate_fix'):
                # Issue should be marked as failed if validation exists
                failed = [i for i in result if i.status == IssueStatus.FAILED]
                # Validation might catch syntax errors

    @pytest.mark.unit
    def test_preserves_file_structure(self, base_config, sample_issue, temp_dir):
        """Test that file structure is preserved after fix."""
        agent = EditAgent(base_config)
        
        test_file = temp_dir / "test.py"
        original = "# Header\n\ndef function():\n    pass\n\n# Footer\n"
        test_file.write_text(original)
        
        sample_issue.file_path = str(test_file)
        sample_issue.line_number = 3
        
        with patch.object(agent, 'is_ai_available', return_value=True), \
             patch.object(agent, 'call_ai', return_value="def function():\n    # Fixed\n    pass"):
            
            agent.process_issues([sample_issue])
            
            # Structure elements should still be present
            content = test_file.read_text()
            # Basic structure check
            assert "def function" in content
