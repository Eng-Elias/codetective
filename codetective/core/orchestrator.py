"""
LangGraph orchestrator for coordinating Codetective agents.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from codetective.agents import CommentAgent, EditAgent, SemGrepAgent, TrivyAgent
from codetective.agents.scan.dynamic_ai_review_agent import DynamicAIReviewAgent
from codetective.core.config import Config
from codetective.models.schemas import (
    AgentResult,
    AgentType,
    FixConfig,
    FixResult,
    Issue,
    IssueStatus,
    ScanConfig,
    ScanResult,
)


class ScanState(TypedDict):
    """State for scan operations."""

    config: ScanConfig
    paths: List[str]
    agent_results: List[AgentResult]
    semgrep_issues: List[Issue]
    trivy_issues: List[Issue]
    ai_review_issues: List[Issue]
    total_issues: int
    scan_duration: float
    error_messages: List[str]


class FixState(TypedDict):
    """State for fix operations."""

    config: FixConfig
    scan_data: Dict[str, Any]
    issues_to_fix: List[Issue]
    fixed_issues: List[Issue]
    failed_issues: List[Issue]
    modified_files: List[str]
    fix_duration: float
    error_messages: List[str]


class CodeDetectiveOrchestrator:
    """Main orchestrator for Codetective using LangGraph."""

    def __init__(self, config: Config):
        self.config = config
        self._initialize_agents()
        self._build_scan_graph()
        self._build_fix_graph()

    def _initialize_agents(self) -> None:
        # Initialize agents
        self.semgrep_agent = SemGrepAgent(self.config)
        self.trivy_agent = TrivyAgent(self.config)
        self.ai_review_agent = DynamicAIReviewAgent(self.config)
        self.comment_agent = CommentAgent(self.config)
        self.edit_agent = EditAgent(self.config)

    def _build_scan_graph(self) -> None:
        """Build the LangGraph for scan operations."""
        workflow = StateGraph(ScanState)

        # Add nodes
        workflow.add_node("start_scan", self._start_scan)
        # Sequential execution (default)
        workflow.add_node("run_agents", self._run_all_agents)
        workflow.add_node("aggregate_results", self._aggregate_scan_results)

        workflow.set_entry_point("start_scan")
        workflow.add_edge("start_scan", "run_agents")
        workflow.add_edge("run_agents", "aggregate_results")
        workflow.add_edge("aggregate_results", END)

        self.scan_graph = workflow.compile()

    def _build_fix_graph(self) -> None:
        """Build the LangGraph for fix operations."""
        workflow = StateGraph(FixState)

        # Add nodes
        workflow.add_node("start_fix", self._start_fix)
        workflow.add_node("comment_fix", self._run_comment_agent)
        workflow.add_node("edit_fix", self._run_edit_agent)
        workflow.add_node("aggregate_fixes", self._aggregate_fix_results)

        # Add edges
        workflow.set_entry_point("start_fix")
        workflow.add_conditional_edges(
            "start_fix",
            self._route_fix_agents,
            {
                "comment": "comment_fix",
                "edit": "edit_fix",
            },
        )
        workflow.add_edge("comment_fix", "aggregate_fixes")
        workflow.add_edge("edit_fix", "aggregate_fixes")
        workflow.add_edge("aggregate_fixes", END)

        self.fix_graph = workflow.compile()

    def run_scan(self, scan_config: ScanConfig) -> ScanResult:
        """Run the scan workflow."""
        start_time = time.time()

        # Check if parallel execution is enabled
        if getattr(scan_config, "parallel_execution", False):
            return self._run_scan_parallel(scan_config, start_time)
        else:
            return self._run_scan_sequential(scan_config, start_time)

    def _run_scan_parallel(self, scan_config: ScanConfig, start_time: float) -> ScanResult:
        """Run agents in parallel using ThreadPoolExecutor."""
        agent_results = []
        semgrep_issues = []
        trivy_issues = []
        ai_review_issues = []

        # Define agent execution functions
        def run_semgrep() -> Tuple[Optional[AgentResult], List[Issue]]:
            if AgentType.SEMGREP in scan_config.agents:
                agent_start = time.time()
                try:
                    issues = self.semgrep_agent.scan_files(scan_config.paths)
                    execution_time = time.time() - agent_start
                    return (
                        AgentResult(agent_type=AgentType.SEMGREP, success=True, issues=issues, execution_time=execution_time),
                        issues,
                    )
                except Exception as e:
                    execution_time = time.time() - agent_start
                    return (
                        AgentResult(
                            agent_type=AgentType.SEMGREP,
                            success=False,
                            issues=[],
                            execution_time=execution_time,
                            error_message=str(e),
                        ),
                        [],
                    )
            return None, []

        def run_trivy() -> Tuple[Optional[AgentResult], List[Issue]]:
            if AgentType.TRIVY in scan_config.agents:
                agent_start = time.time()
                try:
                    issues = self.trivy_agent.scan_files(scan_config.paths)
                    execution_time = time.time() - agent_start
                    return (
                        AgentResult(agent_type=AgentType.TRIVY, success=True, issues=issues, execution_time=execution_time),
                        issues,
                    )
                except Exception as e:
                    execution_time = time.time() - agent_start
                    return (
                        AgentResult(
                            agent_type=AgentType.TRIVY,
                            success=False,
                            issues=[],
                            execution_time=execution_time,
                            error_message=str(e),
                        ),
                        [],
                    )
            return None, []

        def run_ai_review() -> Tuple[Optional[AgentResult], List[Issue]]:
            if AgentType.AI_REVIEW in scan_config.agents:
                agent_start = time.time()
                try:
                    issues = self.ai_review_agent.scan_files(scan_config.paths)
                    execution_time = time.time() - agent_start
                    return (
                        AgentResult(agent_type=AgentType.AI_REVIEW, success=True, issues=issues, execution_time=execution_time),
                        issues,
                    )
                except Exception as e:
                    execution_time = time.time() - agent_start
                    return (
                        AgentResult(
                            agent_type=AgentType.AI_REVIEW,
                            success=False,
                            issues=[],
                            execution_time=execution_time,
                            error_message=str(e),
                        ),
                        [],
                    )
            return None, []

        # Execute agents in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all agent tasks
            futures = []
            if AgentType.SEMGREP in scan_config.agents:
                futures.append(executor.submit(run_semgrep))
            if AgentType.TRIVY in scan_config.agents:
                futures.append(executor.submit(run_trivy))
            if AgentType.AI_REVIEW in scan_config.agents:
                futures.append(executor.submit(run_ai_review))

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    agent_result, issues = future.result()
                    if agent_result:
                        agent_results.append(agent_result)
                        if getattr(agent_result, "agent_type", None) == AgentType.SEMGREP:
                            semgrep_issues.extend(issues)
                        elif getattr(agent_result, "agent_type", None) == AgentType.TRIVY:
                            trivy_issues.extend(issues)
                        elif getattr(agent_result, "agent_type", None) == AgentType.AI_REVIEW:
                            ai_review_issues.extend(issues)
                except Exception as e:
                    print(f"Error in parallel agent execution: {e}")

        # Calculate total duration
        total_duration = time.time() - start_time
        total_issues = len(semgrep_issues) + len(trivy_issues) + len(ai_review_issues)

        # Create scan result
        scan_result = ScanResult(
            scan_path=", ".join(scan_config.paths),
            config=scan_config,
            semgrep_results=semgrep_issues,
            trivy_results=trivy_issues,
            ai_review_results=ai_review_issues,
            agent_results=agent_results,
            total_issues=total_issues,
            scan_duration=total_duration,
        )

        return scan_result

    def _run_scan_sequential(self, scan_config: ScanConfig, start_time: float) -> ScanResult:
        """Run agents sequentially using LangGraph."""
        initial_state: Any = ScanState(
            config=scan_config,
            paths=scan_config.paths,
            agent_results=[],
            semgrep_issues=[],
            trivy_issues=[],
            ai_review_issues=[],
            total_issues=0,
            scan_duration=0.0,
            error_messages=[],
        )

        # Execute the scan graph
        final_state = self.scan_graph.invoke(initial_state)

        # Calculate total duration
        total_duration = time.time() - start_time

        # Create scan result
        scan_result = ScanResult(
            scan_path=", ".join(scan_config.paths),
            config=scan_config,
            semgrep_results=final_state["semgrep_issues"],
            trivy_results=final_state["trivy_issues"],
            ai_review_results=final_state["ai_review_issues"],
            agent_results=final_state["agent_results"],
            total_issues=final_state["total_issues"],
            scan_duration=total_duration,
        )

        return scan_result

    def run_fix(self, scan_data: Dict[str, Any], fix_config: FixConfig, scan_results_file: Optional[str] = None) -> FixResult:
        """Run the fix workflow."""
        start_time = time.time()

        # Extract issues from scan data
        all_issues = []
        all_issues.extend(self._parse_issues_from_scan_data(scan_data.get("semgrep_results", [])))
        all_issues.extend(self._parse_issues_from_scan_data(scan_data.get("trivy_results", [])))
        all_issues.extend(self._parse_issues_from_scan_data(scan_data.get("ai_review_results", [])))

        initial_state: Any = FixState(
            config=fix_config,
            scan_data=scan_data,
            issues_to_fix=all_issues,
            fixed_issues=[],
            failed_issues=[],
            modified_files=[],
            fix_duration=0.0,
            error_messages=[],
        )

        # Execute the fix graph
        final_state = self.fix_graph.invoke(initial_state)

        # Calculate total duration
        total_duration = time.time() - start_time

        # Update scan results file with fix status if provided
        if scan_results_file and Path(scan_results_file).exists():
            self._update_scan_results_file(scan_results_file, final_state["fixed_issues"], final_state["failed_issues"])

        # Create fix result
        fix_result = FixResult(
            config=fix_config,
            fixed_issues=final_state["fixed_issues"],
            failed_issues=final_state["failed_issues"],
            modified_files=final_state["modified_files"],
            fix_duration=total_duration,
        )

        return fix_result

    # Scan workflow nodes
    def _start_scan(self, state: ScanState) -> ScanState:
        """Initialize scan state."""
        return state

    def _run_all_agents(self, state: ScanState) -> Dict[str, Any]:
        """Run all selected agents sequentially to avoid duplicates."""
        updates: Dict[str, Any] = {
            "agent_results": [],
            "semgrep_issues": [],
            "trivy_issues": [],
            "ai_review_issues": [],
            "error_messages": [],
        }

        # Run SemGrep if selected
        if AgentType.SEMGREP in state["config"].agents and self.semgrep_agent.is_available():
            try:
                result = self.semgrep_agent.execute(state["paths"])
                updates["agent_results"].append(result)
                if result.success:
                    updates["semgrep_issues"].extend(result.issues)
                else:
                    updates["error_messages"].append(result.error_message or "SemGrep failed")
            except Exception as e:
                updates["error_messages"].append(f"SemGrep error: {e}")

        # Run Trivy if selected
        if AgentType.TRIVY in state["config"].agents and self.trivy_agent.is_available():
            try:
                result = self.trivy_agent.execute(state["paths"])
                updates["agent_results"].append(result)
                if result.success:
                    updates["trivy_issues"].extend(result.issues)
                else:
                    updates["error_messages"].append(result.error_message or "Trivy failed")
            except Exception as e:
                updates["error_messages"].append(f"Trivy error: {e}")

        # Run AI Review if selected
        if AgentType.AI_REVIEW in state["config"].agents and self.ai_review_agent.is_available():
            try:
                result = self.ai_review_agent.execute(state["paths"])
                updates["agent_results"].append(result)
                if result.success:
                    updates["ai_review_issues"].extend(result.issues)
                else:
                    updates["error_messages"].append(result.error_message or "AI Review failed")
            except Exception as e:
                updates["error_messages"].append(f"AI Review error: {e}")

        return updates

    def _aggregate_scan_results(self, state: ScanState) -> ScanState:
        """Aggregate all scan results."""
        total_issues = len(state["semgrep_issues"]) + len(state["trivy_issues"]) + len(state["ai_review_issues"])
        state["total_issues"] = total_issues
        return state

    # Fix workflow nodes
    def _start_fix(self, state: FixState) -> FixState:
        """Initialize fix state."""
        return state

    def _route_fix_agents(self, state: FixState) -> str:
        """Route to appropriate fix agents."""
        agents = state["config"].agents

        if AgentType.COMMENT in agents:
            return "comment"
        else:
            return "edit"  # Default to edit

    def _run_comment_agent(self, state: FixState) -> Dict[str, Any]:
        """Run Comment agent."""
        updates: Dict[str, Any] = {}

        if self.comment_agent.is_available():
            try:
                result = self.comment_agent.execute([], issues=state["issues_to_fix"])
                if result.success:
                    # Comment agent doesn't actually fix, just enhances descriptions
                    updates["fixed_issues"] = result.issues
            except Exception as e:
                updates["error_messages"] = [f"Comment agent error: {e}"]

        return updates

    def _run_edit_agent(self, state: FixState) -> Dict[str, Any]:
        """Run Edit agent."""
        updates: Dict[str, Any] = {}

        if self.edit_agent.is_available():
            try:
                # Process issues directly with the edit agent
                processed_issues = self.edit_agent.process_issues(state["issues_to_fix"])

                # Separate fixed and failed issues
                fixed_issues = []
                failed_issues = []

                for issue in processed_issues:
                    if issue.status == IssueStatus.FIXED:
                        fixed_issues.append(issue)
                    elif issue.status == IssueStatus.FAILED:
                        failed_issues.append(issue)

                updates["fixed_issues"] = fixed_issues
                updates["failed_issues"] = failed_issues

                # Track modified files
                modified_files = set()
                for issue in processed_issues:
                    if issue.status == IssueStatus.FIXED and issue.file_path:
                        modified_files.add(issue.file_path)
                updates["modified_files"] = list(modified_files)

            except Exception as e:
                print(f"Edit agent error: {e}")
                updates["error_messages"] = [f"Edit agent error: {e}"]
        else:
            print("Edit agent is not available (Ollama not running or not accessible)")
            updates["error_messages"] = ["Edit agent is not available"]

        return updates

    def _aggregate_fix_results(self, state: FixState) -> FixState:
        """Aggregate all fix results."""
        return state

    def _parse_issues_from_scan_data(self, issues_data: List[Dict[str, Any]]) -> List[Issue]:
        """Parse issues from scan data dictionary."""
        issues = []

        for issue_data in issues_data:
            try:
                if isinstance(issue_data, dict):
                    issue = Issue(**issue_data)
                    issues.append(issue)
            except Exception as e:
                print(f"Error parsing issue data: {e}")
                # Skip invalid issue data
                continue

        return issues

    def _update_scan_results_file(self, scan_results_file: str, fixed_issues: List[Issue], failed_issues: List[Issue]) -> None:
        """Update the scan results JSON file with fix statuses."""
        try:
            # Read current scan results
            with open(scan_results_file, "r", encoding="utf-8") as f:
                scan_data = json.load(f)

            # Create a mapping of issue IDs to their new status
            issue_status_updates = {}

            for issue in fixed_issues:
                # Create a unique identifier for the issue
                issue_id = self._create_issue_id(issue)
                issue_status_updates[issue_id] = IssueStatus.FIXED

            for issue in failed_issues:
                issue_id = self._create_issue_id(issue)
                issue_status_updates[issue_id] = IssueStatus.FAILED

            # Update issues in each category
            for category in ["semgrep_results", "trivy_results", "ai_review_results"]:
                if category in scan_data:
                    for issue_data in scan_data[category]:
                        issue_id = self._create_issue_id_from_dict(issue_data)
                        if issue_id in issue_status_updates:
                            issue_data["status"] = issue_status_updates[issue_id].value

            # Write updated scan results back to file
            with open(scan_results_file, "w", encoding="utf-8") as f:
                json.dump(scan_data, f, indent=2, ensure_ascii=False)

            print(f"Updated scan results file: {scan_results_file}")

        except Exception as e:
            print(f"Warning: Could not update scan results file {scan_results_file}: {e}")

    def _create_issue_id(self, issue: Issue) -> str:
        """Create a unique identifier for an issue."""
        return f"{issue.file_path}:{issue.line_number}:{issue.title}:{issue.rule_id}"

    def _create_issue_id_from_dict(self, issue_data: Dict[str, Any]) -> str:
        """Create a unique identifier for an issue from dictionary data."""
        file_path = issue_data.get("file_path", "")
        line_number = issue_data.get("line_number", "")
        title = issue_data.get("title", "")
        rule_id = issue_data.get("rule_id", "")
        return f"{file_path}:{line_number}:{title}:{rule_id}"
