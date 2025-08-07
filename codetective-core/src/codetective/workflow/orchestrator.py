"""
LangGraph workflow orchestrator for the codetective multi-agent system.
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import time

from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from codetective.models.workflow_state import WorkflowState
from codetective.models.configuration import AgentConfig
from codetective.agents.base import BaseAgent
from codetective.agents.semgrep_agent import SemgrepAgent
from codetective.agents.trivy_agent import TrivyAgent
from codetective.agents.ai_review_agent import AIReviewAgent
from codetective.agents.output_comment_agent import OutputCommentAgent
from codetective.agents.output_update_agent import OutputUpdateAgent
from codetective.utils.configuration_manager import ConfigurationManager
from codetective.utils.logger import Logger
from codetective.workflow.graph_builder import GraphBuilder


class WorkflowOrchestrator:
    """
    LangGraph-based workflow orchestrator for multi-agent code review.
    
    This class manages the execution flow between different agents,
    handles state transitions, and provides coordination for the
    entire code review process.
    """
    
    def __init__(self, config_manager: ConfigurationManager):
        """
        Initialize the workflow orchestrator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = Logger.get_logger("workflow.orchestrator")
        
        # Initialize agents
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
        
        # Build LangGraph workflow
        self.graph: Optional[CompiledStateGraph] = self._build_workflow_graph()
    
    def _initialize_agents(self) -> None:
        """Initialize all available agents."""
        try:
            # Semgrep Agent
            semgrep_config = self.config_manager.get_agent_config("semgrep")
            if semgrep_config and isinstance(semgrep_config, type(SemgrepAgent.__init__.__annotations__['config'])):
                self.agents["semgrep"] = SemgrepAgent(semgrep_config)
            
            # Trivy Agent
            trivy_config = self.config_manager.get_agent_config("trivy")
            if trivy_config:
                self.agents["trivy"] = TrivyAgent(trivy_config)
            
            # AI Review Agent
            ai_config = self.config_manager.get_agent_config("ai_review")
            if ai_config:
                self.agents["ai_review"] = AIReviewAgent(ai_config)
            
            # Output Agents
            output_config = AgentConfig(enabled=True, timeout=60, retry_count=1)
            self.agents["output_comment"] = OutputCommentAgent(output_config)
            self.agents["output_update"] = OutputUpdateAgent(output_config)
            
            enabled_agents = [name for name, agent in self.agents.items() if agent.is_enabled]
            self.logger.info(f"Initialized agents: {enabled_agents}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def _build_workflow_graph(self) -> CompiledStateGraph:
        """Build the LangGraph workflow graph."""
        try:
            builder = GraphBuilder()
            graph = builder.create_workflow_graph()

            # Add nodes
            builder.add_analysis_node("validate_input", self._validate_input_node)
            builder.add_analysis_node("run_static_analysis", self._run_static_analysis_node)
            builder.add_analysis_node("run_security_scan", self._run_security_scan_node)
            builder.add_analysis_node("run_ai_review", self._run_ai_review_node)
            builder.add_control_node("aggregate_results", self._aggregate_results_node)
            builder.add_analysis_node("run_output_agents", self._run_output_agents_node)

            # Set entry point
            builder.set_entry_point("validate_input")

            # Define edges
            builder.add_conditional_edge(
                "validate_input",
                self._route_after_validation,
                {
                    "static_analysis": "run_static_analysis",
                    "security_scan": "run_security_scan",
                    "ai_review": "run_ai_review",
                    "aggregate": "aggregate_results",
                    "end": END
                }
            )
            builder.add_conditional_edge(
                "run_static_analysis",
                self._route_after_static_analysis,
                {
                    "security_scan": "run_security_scan",
                    "ai_review": "run_ai_review",
                    "aggregate": "aggregate_results"
                }
            )
            builder.add_conditional_edge(
                "run_security_scan",
                self._route_after_security_scan,
                {
                    "ai_review": "run_ai_review",
                    "aggregate": "aggregate_results"
                }
            )
            builder.add_simple_edge("run_ai_review", "aggregate_results")
            builder.add_conditional_edge(
                "aggregate_results",
                self._route_after_aggregation,
                {
                    "output": "run_output_agents",
                    "end": END
                }
            )
            builder.add_simple_edge("run_output_agents", END)

            # Compile and return the graph
            return builder.compile_graph()
        
        except Exception as e:
            self.logger.error(f"Failed to build workflow graph: {e}")
            raise
    
    async def execute_workflow(
        self,
        target_files: List[Path],
        selected_agents: List[str],
        scan_id: Optional[str] = None
    ) -> WorkflowState:
        """
        Execute the complete workflow.
        
        Args:
            target_files: List of files to analyze
            selected_agents: List of agent names to run
            scan_id: Optional scan identifier
            
        Returns:
            Final workflow state with results
        """
        if not self.graph:
            raise RuntimeError("Workflow graph not initialized")
        
        # Create initial state
        initial_state = WorkflowState(
            scan_id=scan_id or str(uuid.uuid4()),
            target_files=target_files,
            selected_agents=selected_agents,
            metadata={"start_time": time.time()}
        )
        
        self.logger.info(f"Starting workflow execution for scan {initial_state.scan_id}")
        self.logger.info(f"Target files: {len(target_files)}")
        self.logger.info(f"Selected agents: {selected_agents}")
        
        try:
            # Execute the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Add completion metadata
            final_state.metadata["end_time"] = time.time()
            final_state.metadata["duration"] = final_state.metadata["end_time"] - final_state.metadata["start_time"]
            
            self.logger.info(f"Workflow completed in {final_state.metadata['duration']:.2f} seconds")
            self.logger.info(f"Total findings: {final_state.get_total_findings_count()}")
            
            return final_state
        
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            initial_state.add_error(f"Workflow execution failed: {e}")
            return initial_state
    
    async def _validate_input_node(self, state: WorkflowState) -> WorkflowState:
        """Validate input files and configuration."""
        self.logger.info("Validating input files and configuration")
        
        try:
            # Validate files exist
            valid_files = []
            for file_path in state.target_files:
                if file_path.exists() and file_path.is_file():
                    valid_files.append(file_path)
                else:
                    state.add_error(f"File not found: {file_path}")
            
            state.target_files = valid_files
            
            # Validate selected agents
            valid_agents = []
            for agent_name in state.selected_agents:
                if agent_name in self.agents and self.agents[agent_name].is_enabled:
                    valid_agents.append(agent_name)
                else:
                    state.add_error(f"Agent not available: {agent_name}")
            
            state.selected_agents = valid_agents
            
            if not valid_files:
                state.add_error("No valid files to analyze")
            
            if not valid_agents:
                state.add_error("No valid agents selected")
            
            self.logger.info(f"Validation complete: {len(valid_files)} files, {len(valid_agents)} agents")
            
        except Exception as e:
            error_msg = f"Input validation failed: {e}"
            self.logger.error(error_msg)
            state.add_error(error_msg)
        
        return state
    
    async def _run_static_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Run static analysis agents (Semgrep)."""
        self.logger.info("Running static analysis")
        
        if "semgrep" in state.selected_agents and "semgrep" in self.agents:
            try:
                result = await self.agents["semgrep"].execute_with_retry(state)
                if not result.success:
                    state.add_error(f"Semgrep analysis failed: {result.error}")
            except Exception as e:
                state.add_error(f"Semgrep execution error: {e}")
        
        return state
    
    async def _run_security_scan_node(self, state: WorkflowState) -> WorkflowState:
        """Run security scanning agents (Trivy)."""
        self.logger.info("Running security scan")
        
        if "trivy" in state.selected_agents and "trivy" in self.agents:
            try:
                result = await self.agents["trivy"].execute_with_retry(state)
                if not result.success:
                    state.add_error(f"Trivy analysis failed: {result.error}")
            except Exception as e:
                state.add_error(f"Trivy execution error: {e}")
        
        return state
    
    async def _run_ai_review_node(self, state: WorkflowState) -> WorkflowState:
        """Run AI review agent."""
        self.logger.info("Running AI review")
        
        if "ai_review" in state.selected_agents and "ai_review" in self.agents:
            try:
                result = await self.agents["ai_review"].execute_with_retry(state)
                if not result.success:
                    state.add_error(f"AI review failed: {result.error}")
            except Exception as e:
                state.add_error(f"AI review execution error: {e}")
        
        return state
    
    async def _aggregate_results_node(self, state: WorkflowState) -> WorkflowState:
        """Aggregate results from all completed agents."""
        self.logger.info("Aggregating results")
        
        try:
            from codetective.utils.result_aggregator import ResultAggregator
            
            aggregator = ResultAggregator()
            aggregated_results = aggregator.aggregate_workflow_results(state)
            
            # Store aggregated results in metadata
            state.metadata["aggregated_results"] = aggregated_results
            
            self.logger.info(f"Aggregated {aggregated_results['summary'].total_findings} findings")
            
        except Exception as e:
            error_msg = f"Result aggregation failed: {e}"
            self.logger.error(error_msg)
            state.add_error(error_msg)
        
        return state
    
    async def _run_output_agents_node(self, state: WorkflowState) -> WorkflowState:
        """Run output agents for comments or updates."""
        self.logger.info("Running output agents")
        
        # Check which output agents are requested
        output_agents = [agent for agent in state.selected_agents if agent.startswith("output_")]
        
        for agent_name in output_agents:
            if agent_name in self.agents:
                try:
                    result = await self.agents[agent_name].execute_with_retry(state)
                    if not result.success:
                        state.add_error(f"{agent_name} failed: {result.error}")
                except Exception as e:
                    state.add_error(f"{agent_name} execution error: {e}")
        
        return state
    
    def _route_after_validation(self, state: WorkflowState) -> str:
        """Route after input validation."""
        if state.has_errors():
            return "end"
        
        if "semgrep" in state.selected_agents:
            return "static_analysis"
        elif "trivy" in state.selected_agents:
            return "security_scan"
        elif "ai_review" in state.selected_agents:
            return "ai_review"
        else:
            return "aggregate"
    
    def _route_after_static_analysis(self, state: WorkflowState) -> str:
        """Route after static analysis."""
        if "trivy" in state.selected_agents:
            return "security_scan"
        elif "ai_review" in state.selected_agents:
            return "ai_review"
        else:
            return "aggregate"
    
    def _route_after_security_scan(self, state: WorkflowState) -> str:
        """Route after security scan."""
        if "ai_review" in state.selected_agents:
            return "ai_review"
        else:
            return "aggregate"
    
    def _route_after_aggregation(self, state: WorkflowState) -> str:
        """Route after result aggregation."""
        output_agents = [agent for agent in state.selected_agents if agent.startswith("output_")]
        if output_agents:
            return "output"
        else:
            return "end"
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available agents."""
        return {
            name: agent.get_agent_info()
            for name, agent in self.agents.items()
        }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "graph_compiled": self.graph is not None,
            "available_agents": list(self.agents.keys()),
            "enabled_agents": [name for name, agent in self.agents.items() if agent.is_enabled],
            "configuration_valid": len(self.config_manager.validate_configuration()) == 0,
        }
