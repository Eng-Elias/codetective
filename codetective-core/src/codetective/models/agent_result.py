"""
Defines the result model for agent executions.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, List


@dataclass
class AgentResult:
    """Standardized result object for agent executions."""
    
    agent_name: str
    success: bool
    execution_time: float
    results: Any = None
    error: Optional[str] = None
    log_messages: List[str] = field(default_factory=list)
