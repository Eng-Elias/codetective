"""
LangGraph orchestrator for coordinating Codetective agents.
"""

import time
from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

from ..models.schemas import (
    ScanConfig, FixConfig, ScanResult, FixResult, AgentResult, 
    AgentType, Issue, IssueStatus
)
from ..agents import (
    SemGrepAgent, TrivyAgent, AIReviewAgent, 
    CommentAgent, EditAgent
)
from .config import Config


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
    
    def _initialize_agents(self):
        """Initialize all agents."""
        self.semgrep_agent = SemGrepAgent(self.config)
        self.trivy_agent = TrivyAgent(self.config)
        self.ai_review_agent = AIReviewAgent(self.config)
        self.comment_agent = CommentAgent(self.config)
        self.edit_agent = EditAgent(self.config)
    
    def _build_scan_graph(self):
        """Build the LangGraph for scan operations."""
        workflow = StateGraph(ScanState)
        
        # Add nodes
        workflow.add_node("start_scan", self._start_scan)
        workflow.add_node("run_agents", self._run_all_agents)
        workflow.add_node("aggregate_results", self._aggregate_scan_results)
        
        # Add edges - simplified to avoid parallel execution issues
        workflow.set_entry_point("start_scan")
        workflow.add_edge("start_scan", "run_agents")
        workflow.add_edge("run_agents", "aggregate_results")
        workflow.add_edge("aggregate_results", END)
        
        self.scan_graph = workflow.compile()
    
    def _build_fix_graph(self):
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
                "both": "comment_fix"
            }
        )
        workflow.add_edge("comment_fix", "aggregate_fixes")
        workflow.add_edge("edit_fix", "aggregate_fixes")
        workflow.add_edge("aggregate_fixes", END)
        
        self.fix_graph = workflow.compile()
    
    def run_scan(self, scan_config: ScanConfig) -> ScanResult:
        """Run the scan workflow."""
        start_time = time.time()
        
        initial_state = ScanState(
            config=scan_config,
            paths=scan_config.paths,
            agent_results=[],
            semgrep_issues=[],
            trivy_issues=[],
            ai_review_issues=[],
            total_issues=0,
            scan_duration=0.0,
            error_messages=[]
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
            scan_duration=total_duration
        )
        
        return scan_result
    
    def run_fix(self, scan_data: Dict[str, Any], fix_config: FixConfig) -> FixResult:
        """Run the fix workflow."""
        start_time = time.time()
        
        # Extract issues from scan data
        all_issues = []
        all_issues.extend(self._parse_issues_from_scan_data(scan_data.get("semgrep_results", [])))
        all_issues.extend(self._parse_issues_from_scan_data(scan_data.get("trivy_results", [])))
        all_issues.extend(self._parse_issues_from_scan_data(scan_data.get("ai_review_results", [])))
        
        initial_state = FixState(
            config=fix_config,
            scan_data=scan_data,
            issues_to_fix=all_issues,
            fixed_issues=[],
            failed_issues=[],
            modified_files=[],
            fix_duration=0.0,
            error_messages=[]
        )
        
        # Execute the fix graph
        final_state = self.fix_graph.invoke(initial_state)
        
        # Calculate total duration
        total_duration = time.time() - start_time
        
        # Create fix result
        fix_result = FixResult(
            config=fix_config,
            fixed_issues=final_state["fixed_issues"],
            failed_issues=final_state["failed_issues"],
            modified_files=final_state["modified_files"],
            fix_duration=total_duration
        )
        
        return fix_result
    
    # Scan workflow nodes
    def _start_scan(self, state: ScanState) -> ScanState:
        """Initialize scan state."""
        return state
    
    def _run_all_agents(self, state: ScanState) -> Dict[str, Any]:
        """Run all selected agents sequentially to avoid duplicates."""
        updates = {
            "agent_results": [],
            "semgrep_issues": [],
            "trivy_issues": [],
            "ai_review_issues": [],
            "error_messages": []
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
        
        if AgentType.COMMENT in agents and AgentType.EDIT in agents:
            return "both"
        elif AgentType.COMMENT in agents:
            return "comment"
        elif AgentType.EDIT in agents:
            return "edit"
        else:
            return "edit"  # Default to edit
    
    def _run_comment_agent(self, state: FixState) -> Dict[str, Any]:
        """Run Comment agent."""
        updates = {}
        
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
        updates = {}
        
        if self.edit_agent.is_available():
            try:
                result = self.edit_agent.execute([], issues=state["issues_to_fix"])
                if result.success:
                    # Separate fixed and failed issues
                    fixed_issues = []
                    failed_issues = []
                    
                    for issue in result.issues:
                        if issue.status == IssueStatus.FIXED:
                            fixed_issues.append(issue)
                        else:
                            failed_issues.append(issue)
                    
                    updates["fixed_issues"] = fixed_issues
                    updates["failed_issues"] = failed_issues
                    
                    # Track modified files
                    modified_files = set()
                    for issue in result.issues:
                        if issue.status == IssueStatus.FIXED and issue.file_path:
                            modified_files.add(issue.file_path)
                    updates["modified_files"] = list(modified_files)
            except Exception as e:
                updates["error_messages"] = [f"Edit agent error: {e}"]
        
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
            except Exception:
                # Skip invalid issue data
                continue
        
        return issues
