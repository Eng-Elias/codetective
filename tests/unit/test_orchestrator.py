"""
Unit tests for CodeDetectiveOrchestrator.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from codetective.core.orchestrator import CodeDetectiveOrchestrator, ScanState, FixState
from codetective.core.config import Config
from codetective.models.schemas import (
    AgentType,
    AgentResult,
    ScanConfig,
    FixConfig,
    Issue,
    IssueStatus,
    SeverityLevel,
)


class TestCodeDetectiveOrchestrator:
    """Test cases for CodeDetectiveOrchestrator."""

    @pytest.mark.unit
    def test_orchestrator_initialization(self, base_config):
        """Test orchestrator initializes properly."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        assert orchestrator.config == base_config
        assert orchestrator.semgrep_agent is not None
        assert orchestrator.trivy_agent is not None
        assert orchestrator.ai_review_agent is not None
        assert orchestrator.comment_agent is not None
        assert orchestrator.edit_agent is not None
        assert orchestrator.scan_graph is not None
        assert orchestrator.fix_graph is not None

    @pytest.mark.unit
    def test_initialize_agents(self, base_config):
        """Test agent initialization."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        # Verify agents are initialized with correct config
        assert orchestrator.semgrep_agent.config == base_config
        assert orchestrator.trivy_agent.config == base_config
        assert orchestrator.ai_review_agent.config == base_config
        assert orchestrator.comment_agent.config == base_config
        assert orchestrator.edit_agent.config == base_config

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.SemGrepAgent')
    @patch('codetective.core.orchestrator.TrivyAgent')
    @patch('codetective.core.orchestrator.DynamicAIReviewAgent')
    def test_run_scan_sequential_success(
        self, 
        mock_ai_agent_class,
        mock_trivy_class, 
        mock_semgrep_class,
        base_config,
        sample_issue
    ):
        """Test successful sequential scan execution."""
        # Setup mock agents
        mock_semgrep = Mock()
        mock_semgrep.is_available.return_value = True
        mock_semgrep.execute.return_value = AgentResult(
            agent_type=AgentType.SEMGREP,
            success=True,
            issues=[sample_issue],
            execution_time=0.5
        )
        mock_semgrep_class.return_value = mock_semgrep
        
        mock_trivy = Mock()
        mock_trivy.is_available.return_value = True
        mock_trivy.execute.return_value = AgentResult(
            agent_type=AgentType.TRIVY,
            success=True,
            issues=[],
            execution_time=0.3
        )
        mock_trivy_class.return_value = mock_trivy
        
        mock_ai = Mock()
        mock_ai.is_available.return_value = False
        mock_ai_agent_class.return_value = mock_ai
        
        # Create orchestrator with mocked agents
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        # Create scan config
        scan_config = ScanConfig(
            agents=[AgentType.SEMGREP, AgentType.TRIVY],
            paths=["/test/path"],
            parallel_execution=False
        )
        
        # Run scan
        result = orchestrator.run_scan(scan_config)
        
        # Verify results
        assert result is not None
        assert result.total_issues > 0
        assert len(result.semgrep_results) == 1
        assert len(result.agent_results) == 2
        assert result.scan_duration >= 0

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.SemGrepAgent')
    @patch('codetective.core.orchestrator.TrivyAgent')
    @patch('codetective.core.orchestrator.DynamicAIReviewAgent')
    def test_run_scan_parallel_success(
        self,
        mock_ai_agent_class,
        mock_trivy_class,
        mock_semgrep_class,
        base_config,
        sample_issue
    ):
        """Test successful parallel scan execution."""
        # Setup mock agents
        mock_semgrep = Mock()
        mock_semgrep.scan_files.return_value = [sample_issue]
        mock_semgrep_class.return_value = mock_semgrep
        
        mock_trivy = Mock()
        mock_trivy.scan_files.return_value = []
        mock_trivy_class.return_value = mock_trivy
        
        mock_ai = Mock()
        mock_ai.scan_files.return_value = []
        mock_ai_agent_class.return_value = mock_ai
        
        # Create orchestrator with mocked agents
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        # Create scan config with parallel execution
        scan_config = ScanConfig(
            agents=[AgentType.SEMGREP, AgentType.TRIVY],
            paths=["/test/path"],
            parallel_execution=True
        )
        
        # Run scan
        result = orchestrator.run_scan(scan_config)
        
        # Verify results
        assert result is not None
        assert result.total_issues > 0
        assert len(result.semgrep_results) == 1
        assert result.scan_duration >= 0

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.SemGrepAgent')
    @patch('codetective.core.orchestrator.TrivyAgent')
    @patch('codetective.core.orchestrator.DynamicAIReviewAgent')
    def test_run_scan_with_agent_error(
        self,
        mock_ai_agent_class,
        mock_trivy_class,
        mock_semgrep_class,
        base_config
    ):
        """Test scan handles agent errors gracefully."""
        # Setup mock agents with one failing
        mock_semgrep = Mock()
        mock_semgrep.is_available.return_value = True
        mock_semgrep.execute.side_effect = Exception("SemGrep failed")
        mock_semgrep_class.return_value = mock_semgrep
        
        mock_trivy = Mock()
        mock_trivy.is_available.return_value = True
        mock_trivy.execute.return_value = AgentResult(
            agent_type=AgentType.TRIVY,
            success=True,
            issues=[],
            execution_time=0.3
        )
        mock_trivy_class.return_value = mock_trivy
        
        mock_ai = Mock()
        mock_ai.is_available.return_value = False
        mock_ai_agent_class.return_value = mock_ai
        
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        scan_config = ScanConfig(
            agents=[AgentType.SEMGREP, AgentType.TRIVY],
            paths=["/test/path"],
            parallel_execution=False
        )
        
        # Should not raise exception
        result = orchestrator.run_scan(scan_config)
        
        # Verify partial results returned
        assert result is not None
        assert len(result.agent_results) >= 1  # At least Trivy succeeded

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.CommentAgent')
    @patch('codetective.core.orchestrator.EditAgent')
    def test_run_fix_with_comment_agent(
        self,
        mock_edit_class,
        mock_comment_class,
        base_config,
        sample_issue
    ):
        """Test fix workflow with CommentAgent."""
        # Setup mock comment agent
        mock_comment = Mock()
        mock_comment.is_available.return_value = True
        processed_issue = sample_issue.model_copy()
        processed_issue.status = IssueStatus.FIXED
        mock_comment.execute.return_value = AgentResult(
            agent_type=AgentType.COMMENT,
            success=True,
            issues=[processed_issue],
            execution_time=0.5
        )
        mock_comment_class.return_value = mock_comment
        
        mock_edit = Mock()
        mock_edit_class.return_value = mock_edit
        
        # Create orchestrator
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        # Create fix config
        fix_config = FixConfig(
            agents=[AgentType.COMMENT],
            backup_files=True
        )
        
        # Prepare scan data
        scan_data = {
            "semgrep_results": [sample_issue.model_dump()],
            "trivy_results": [],
            "ai_review_results": []
        }
        
        # Run fix
        result = orchestrator.run_fix(scan_data, fix_config)
        
        # Verify results
        assert result is not None
        assert result.fix_duration >= 0

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.CommentAgent')
    @patch('codetective.core.orchestrator.EditAgent')
    def test_run_fix_with_edit_agent(
        self,
        mock_edit_class,
        mock_comment_class,
        base_config,
        sample_issue
    ):
        """Test fix workflow with EditAgent."""
        # Setup mock edit agent
        mock_edit = Mock()
        mock_edit.is_available.return_value = True
        fixed_issue = sample_issue.model_copy()
        fixed_issue.status = IssueStatus.FIXED
        mock_edit.process_issues.return_value = [fixed_issue]
        mock_edit_class.return_value = mock_edit
        
        mock_comment = Mock()
        mock_comment_class.return_value = mock_comment
        
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        fix_config = FixConfig(
            agents=[AgentType.EDIT],
            backup_files=True
        )
        
        scan_data = {
            "semgrep_results": [sample_issue.model_dump()],
            "trivy_results": [],
            "ai_review_results": []
        }
        
        result = orchestrator.run_fix(scan_data, fix_config)
        
        assert result is not None
        assert len(result.fixed_issues) == 1
        assert result.fixed_issues[0].status == IssueStatus.FIXED

    @pytest.mark.unit
    def test_start_scan_node(self, base_config):
        """Test _start_scan node preserves state."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        initial_state = {
            "config": Mock(),
            "paths": ["/test"],
            "agent_results": [],
            "semgrep_issues": [],
            "trivy_issues": [],
            "ai_review_issues": [],
            "total_issues": 0,
            "scan_duration": 0.0,
            "error_messages": []
        }
        
        result_state = orchestrator._start_scan(initial_state)
        
        assert result_state == initial_state

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.SemGrepAgent')
    @patch('codetective.core.orchestrator.TrivyAgent')
    @patch('codetective.core.orchestrator.DynamicAIReviewAgent')
    def test_run_all_agents_node(
        self,
        mock_ai_class,
        mock_trivy_class,
        mock_semgrep_class,
        base_config,
        sample_issue
    ):
        """Test _run_all_agents node executes agents."""
        # Setup mocks
        mock_semgrep = Mock()
        mock_semgrep.is_available.return_value = True
        mock_semgrep.execute.return_value = AgentResult(
            agent_type=AgentType.SEMGREP,
            success=True,
            issues=[sample_issue],
            execution_time=0.5
        )
        mock_semgrep_class.return_value = mock_semgrep
        
        mock_trivy = Mock()
        mock_trivy.is_available.return_value = False
        mock_trivy_class.return_value = mock_trivy
        
        mock_ai = Mock()
        mock_ai.is_available.return_value = False
        mock_ai_class.return_value = mock_ai
        
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        scan_config = ScanConfig(
            agents=[AgentType.SEMGREP],
            paths=["/test/path"]
        )
        
        state = {
            "config": scan_config,
            "paths": ["/test/path"],
            "agent_results": [],
            "semgrep_issues": [],
            "trivy_issues": [],
            "ai_review_issues": [],
            "total_issues": 0,
            "scan_duration": 0.0,
            "error_messages": []
        }
        
        updates = orchestrator._run_all_agents(state)
        
        assert "agent_results" in updates
        assert "semgrep_issues" in updates
        assert len(updates["agent_results"]) == 1

    @pytest.mark.unit
    def test_aggregate_scan_results_node(self, base_config, sample_issue):
        """Test _aggregate_scan_results calculates totals."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        state = {
            "config": Mock(),
            "paths": ["/test"],
            "agent_results": [],
            "semgrep_issues": [sample_issue],
            "trivy_issues": [sample_issue],
            "ai_review_issues": [],
            "total_issues": 0,
            "scan_duration": 0.0,
            "error_messages": []
        }
        
        result_state = orchestrator._aggregate_scan_results(state)
        
        assert result_state["total_issues"] == 2

    @pytest.mark.unit
    def test_route_fix_agents_comment(self, base_config):
        """Test _route_fix_agents routes to comment agent."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        fix_config = FixConfig(agents=[AgentType.COMMENT])
        
        state = {
            "config": fix_config,
            "scan_data": {},
            "issues_to_fix": [],
            "fixed_issues": [],
            "failed_issues": [],
            "modified_files": [],
            "fix_duration": 0.0,
            "error_messages": []
        }
        
        route = orchestrator._route_fix_agents(state)
        
        assert route == "comment"

    @pytest.mark.unit
    def test_route_fix_agents_edit_default(self, base_config):
        """Test _route_fix_agents defaults to edit agent."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        fix_config = FixConfig(agents=[AgentType.EDIT])
        
        state = {
            "config": fix_config,
            "scan_data": {},
            "issues_to_fix": [],
            "fixed_issues": [],
            "failed_issues": [],
            "modified_files": [],
            "fix_duration": 0.0,
            "error_messages": []
        }
        
        route = orchestrator._route_fix_agents(state)
        
        assert route == "edit"

    @pytest.mark.unit
    def test_parse_issues_from_scan_data(self, base_config, sample_issue):
        """Test _parse_issues_from_scan_data parses correctly."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        issues_data = [sample_issue.model_dump()]
        
        parsed_issues = orchestrator._parse_issues_from_scan_data(issues_data)
        
        assert len(parsed_issues) == 1
        assert isinstance(parsed_issues[0], Issue)
        assert parsed_issues[0].title == sample_issue.title

    @pytest.mark.unit
    def test_parse_issues_handles_invalid_data(self, base_config):
        """Test _parse_issues_from_scan_data handles invalid data."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        # Mix of valid and invalid data
        issues_data = [
            {"title": "Valid Issue", "severity": "high"},
            "invalid_data",
            {"invalid": "structure"}
        ]
        
        # Should not raise exception
        parsed_issues = orchestrator._parse_issues_from_scan_data(issues_data)
        
        # May return empty or partial results depending on implementation
        assert isinstance(parsed_issues, list)

    @pytest.mark.unit
    def test_create_issue_id(self, base_config, sample_issue):
        """Test _create_issue_id generates unique identifiers."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        issue_id = orchestrator._create_issue_id(sample_issue)
        
        assert isinstance(issue_id, str)
        assert sample_issue.title in issue_id
        assert str(sample_issue.file_path) in issue_id

    @pytest.mark.unit
    def test_create_issue_id_from_dict(self, base_config, sample_issue):
        """Test _create_issue_id_from_dict generates identifiers from dict."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        issue_dict = sample_issue.model_dump()
        issue_id = orchestrator._create_issue_id_from_dict(issue_dict)
        
        assert isinstance(issue_id, str)
        assert sample_issue.title in issue_id

    @pytest.mark.unit
    def test_update_scan_results_file(self, base_config, sample_issue, temp_dir):
        """Test _update_scan_results_file updates JSON correctly."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        # Create test scan results file
        scan_file = temp_dir / "scan_results.json"
        scan_data = {
            "semgrep_results": [sample_issue.model_dump()],
            "trivy_results": [],
            "ai_review_results": []
        }
        scan_file.write_text(json.dumps(scan_data))
        
        # Update with fixed issue
        fixed_issue = sample_issue.model_copy()
        fixed_issue.status = IssueStatus.FIXED
        
        orchestrator._update_scan_results_file(
            str(scan_file),
            [fixed_issue],
            []
        )
        
        # Verify file was updated
        updated_data = json.loads(scan_file.read_text())
        assert updated_data["semgrep_results"][0]["status"] == "fixed"

    @pytest.mark.unit
    def test_update_scan_results_file_handles_missing_file(self, base_config, sample_issue):
        """Test _update_scan_results_file handles missing file gracefully."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        # Should not raise exception
        orchestrator._update_scan_results_file(
            "/nonexistent/file.json",
            [sample_issue],
            []
        )

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.SemGrepAgent')
    @patch('codetective.core.orchestrator.TrivyAgent')
    @patch('codetective.core.orchestrator.DynamicAIReviewAgent')
    def test_parallel_execution_error_handling(
        self,
        mock_ai_class,
        mock_trivy_class,
        mock_semgrep_class,
        base_config
    ):
        """Test parallel execution handles agent errors."""
        # Setup one failing agent
        mock_semgrep = Mock()
        mock_semgrep.scan_files.side_effect = Exception("Semgrep failed")
        mock_semgrep_class.return_value = mock_semgrep
        
        mock_trivy = Mock()
        mock_trivy.scan_files.return_value = []
        mock_trivy_class.return_value = mock_trivy
        
        mock_ai = Mock()
        mock_ai_class.return_value = mock_ai
        
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        scan_config = ScanConfig(
            agents=[AgentType.SEMGREP, AgentType.TRIVY],
            paths=["/test"],
            parallel_execution=True
        )
        
        # Should handle error gracefully
        result = orchestrator.run_scan(scan_config)
        
        assert result is not None
        # Should have at least one agent result (Trivy)
        assert len(result.agent_results) >= 1

    @pytest.mark.unit
    @patch('codetective.core.orchestrator.CommentAgent')
    @patch('codetective.core.orchestrator.EditAgent')
    def test_fix_with_unavailable_agent(
        self,
        mock_edit_class,
        mock_comment_class,
        base_config,
        sample_issue
    ):
        """Test fix workflow when agent is unavailable."""
        # Setup unavailable edit agent
        mock_edit = Mock()
        mock_edit.is_available.return_value = False
        mock_edit_class.return_value = mock_edit
        
        mock_comment = Mock()
        mock_comment_class.return_value = mock_comment
        
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        fix_config = FixConfig(agents=[AgentType.EDIT])
        scan_data = {"semgrep_results": [sample_issue.model_dump()]}
        
        result = orchestrator.run_fix(scan_data, fix_config)
        
        assert result is not None
        # Should have error messages about unavailable agent
        assert len(result.fixed_issues) == 0

    @pytest.mark.unit
    def test_aggregate_fix_results(self, base_config):
        """Test _aggregate_fix_results preserves state."""
        orchestrator = CodeDetectiveOrchestrator(base_config)
        
        state = {
            "config": Mock(),
            "scan_data": {},
            "issues_to_fix": [],
            "fixed_issues": [],
            "failed_issues": [],
            "modified_files": [],
            "fix_duration": 0.0,
            "error_messages": []
        }
        
        result_state = orchestrator._aggregate_fix_results(state)
        
        assert result_state == state
