"""
Interface-specific data models for GUI, CLI, and MCP.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from codetective.models.configuration import AgentConfig


@dataclass
class GUIState:
    """Streamlit GUI state management."""
    
    current_page: str = ""
    project_path: str = ""
    selected_files: List[str] = field(default_factory=list)
    selected_agents: List[str] = field(default_factory=list)
    agent_configs: Dict[str, AgentConfig] = field(default_factory=dict)
    scan_in_progress: bool = False
    results_available: bool = False
    
    def __post_init__(self) -> None:
        from codetective.interfaces.gui import PageEnum
        """Validate GUI state after initialization."""
        if not self.current_page:
            self.current_page = PageEnum.SETUP.value
        
        if not isinstance(self.selected_files, list):
            raise ValueError("selected_files must be a list")
        
        if not isinstance(self.selected_agents, list):
            raise ValueError("selected_agents must be a list")
        
        if not isinstance(self.agent_configs, dict):
            raise ValueError("agent_configs must be a dict")
    
    def add_selected_file(self, file_path: str) -> None:
        """Add a file to the selection."""
        if file_path not in self.selected_files:
            self.selected_files.append(file_path)
    
    def remove_selected_file(self, file_path: str) -> None:
        """Remove a file from the selection."""
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
    
    def toggle_agent(self, agent_name: str) -> None:
        """Toggle agent selection."""
        if agent_name in self.selected_agents:
            self.selected_agents.remove(agent_name)
        else:
            self.selected_agents.append(agent_name)
    
    def is_ready_for_scan(self) -> bool:
        """Check if state is ready for scanning."""
        return (
            len(self.selected_files) > 0 
            and len(self.selected_agents) > 0 
            and not self.scan_in_progress
        )
    
    def start_scan(self) -> None:
        """Mark scan as started."""
        self.scan_in_progress = True
        self.results_available = False
    
    def complete_scan(self) -> None:
        """Mark scan as completed."""
        self.scan_in_progress = False
        self.results_available = True
    
    def reset(self) -> None:
        """Reset state to initial values."""
        self.selected_files.clear()
        self.selected_agents.clear()
        self.agent_configs.clear()
        self.scan_in_progress = False
        self.results_available = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "selected_files": self.selected_files,
            "selected_agents": self.selected_agents,
            "agent_configs": {k: v.to_dict() for k, v in self.agent_configs.items()},
            "scan_in_progress": self.scan_in_progress,
            "results_available": self.results_available,
            "ready_for_scan": self.is_ready_for_scan(),
        }


@dataclass
class CLIArgs:
    """CLI command arguments."""
    
    target_path: str
    agents: List[str] = field(default_factory=list)
    output_format: str = "json"  # json, text, sarif
    output_file: str = ""
    config_file: str = ""
    verbose: bool = False
    
    def __post_init__(self) -> None:
        """Validate CLI arguments after initialization."""
        if not self.target_path:
            raise ValueError("target_path cannot be empty")
        
        valid_formats = ["json", "text", "sarif"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output format: {self.output_format}")
        
        if not isinstance(self.agents, list):
            raise ValueError("agents must be a list")
    
    def has_agent(self, agent_name: str) -> bool:
        """Check if specific agent is selected."""
        return agent_name in self.agents
    
    def should_output_to_file(self) -> bool:
        """Check if output should be written to file."""
        return bool(self.output_file)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_path": self.target_path,
            "agents": self.agents,
            "output_format": self.output_format,
            "output_file": self.output_file,
            "config_file": self.config_file,
            "verbose": self.verbose,
        }


@dataclass
class MCPRequest:
    """MCP protocol request structure."""
    
    method: str
    params: Dict[str, Any]
    id: str
    
    def __post_init__(self) -> None:
        """Validate MCP request after initialization."""
        if not self.method:
            raise ValueError("method cannot be empty")
        
        if not self.id:
            raise ValueError("id cannot be empty")
        
        if not isinstance(self.params, dict):
            raise ValueError("params must be a dict")
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get parameter value with optional default."""
        return self.params.get(key, default)
    
    def has_param(self, key: str) -> bool:
        """Check if parameter exists."""
        return key in self.params
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "method": self.method,
            "params": self.params,
            "id": self.id,
        }


@dataclass
class MCPResponse:
    """MCP protocol response structure."""
    
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Validate MCP response after initialization."""
        if not self.id:
            raise ValueError("id cannot be empty")
        
        if self.result is not None and self.error is not None:
            raise ValueError("response cannot have both result and error")
        
        if self.result is None and self.error is None:
            raise ValueError("response must have either result or error")
    
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.error is None
    
    def is_error(self) -> bool:
        """Check if response indicates error."""
        return self.error is not None
    
    def get_error_message(self) -> str:
        """Get error message if present."""
        if self.error:
            return self.error.get("message", "Unknown error")
        return ""
    
    def get_error_code(self) -> int:
        """Get error code if present."""
        if self.error:
            return self.error.get("code", -1)
        return 0
    
    @classmethod
    def success(cls, result: Dict[str, Any], request_id: str) -> "MCPResponse":
        """Create a success response."""
        return cls(result=result, error=None, id=request_id)
    
    @classmethod
    def error(cls, code: int, message: str, request_id: str, data: Optional[Dict[str, Any]] = None) -> "MCPResponse":
        """Create an error response."""
        error_dict = {"code": code, "message": message}
        if data:
            error_dict["data"] = data
        return cls(result=None, error=error_dict, id=request_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        response_dict = {"id": self.id}
        
        if self.result is not None:
            response_dict["result"] = self.result
        
        if self.error is not None:
            response_dict["error"] = self.error
        
        return response_dict
