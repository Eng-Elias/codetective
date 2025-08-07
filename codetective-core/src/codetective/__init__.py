"""
Codetective: Multi-agent code review tool.

A comprehensive code review tool that orchestrates multiple specialized agents
to perform static analysis, security scanning, and AI-powered code improvements.
"""

__version__ = "0.1.0"
__author__ = "Codetective Team"
__email__ = "team@codetective.dev"

from codetective.models.workflow_state import WorkflowState
from codetective.models.agent_results import (
    SemgrepResults,
    TrivyResults,
    AIReviewResults,
    OutputResults,
)
from codetective.agents.base import BaseAgent
from codetective.workflow.orchestrator import WorkflowOrchestrator

__all__ = [
    "WorkflowState",
    "SemgrepResults",
    "TrivyResults", 
    "AIReviewResults",
    "OutputResults",
    "BaseAgent",
    "WorkflowOrchestrator",
]
