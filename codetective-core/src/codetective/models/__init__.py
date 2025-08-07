"""
Data models for the codetective multi-agent system.
"""

from codetective.models.workflow_state import WorkflowState
from codetective.models.agent_results import (
    SemgrepFinding,
    SemgrepResults,
    TrivyVulnerability,
    TrivyResult,
    TrivyResults,
    AIReviewIssue,
    AIReviewResults,
    OutputResults,
)
from codetective.models.configuration import (
    AgentConfig,
    SemgrepConfig,
    TrivyConfig,
    AIReviewConfig,
)
from codetective.models.interface_models import (
    GUIState,
    CLIArgs,
    MCPRequest,
    MCPResponse,
)

__all__ = [
    "WorkflowState",
    "SemgrepFinding",
    "SemgrepResults",
    "TrivyVulnerability",
    "TrivyResult",
    "TrivyResults",
    "AIReviewIssue",
    "AIReviewResults",
    "OutputResults",
    "AgentConfig",
    "SemgrepConfig",
    "TrivyConfig",
    "AIReviewConfig",
    "GUIState",
    "CLIArgs",
    "MCPRequest",
    "MCPResponse",
]
