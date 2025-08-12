"""
Base agent class for Codetective agents.
"""

import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models.schemas import AgentResult, AgentType, Issue
from ..core.config import Config


class BaseAgent(ABC):
    """Base class for all Codetective agents."""
    
    def __init__(self, config: Config):
        """Initialize the agent with configuration."""
        self.config = config
        self.agent_type: AgentType = None
        self._execution_start_time: Optional[float] = None
    
    @abstractmethod
    def execute(self, paths: List[str], **kwargs) -> AgentResult:
        """Execute the agent on the given paths."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the agent's dependencies are available."""
        pass
    
    def _start_execution(self) -> None:
        """Mark the start of execution for timing."""
        self._execution_start_time = time.time()
    
    def _get_execution_time(self) -> float:
        """Get the execution time since start."""
        if self._execution_start_time is None:
            return 0.0
        return time.time() - self._execution_start_time
    
    def _create_result(self, success: bool, issues: List[Issue] = None, 
                      error_message: str = None, metadata: Dict[str, Any] = None) -> AgentResult:
        """Create an AgentResult with timing information."""
        return AgentResult(
            agent_type=self.agent_type,
            success=success,
            issues=issues or [],
            execution_time=self._get_execution_time(),
            error_message=error_message,
            metadata=metadata or {}
        )
    
    def _validate_paths(self, paths: List[str]) -> List[str]:
        """Validate and filter paths that exist."""
        valid_paths = []
        for path_str in paths:
            path = Path(path_str)
            if path.exists():
                valid_paths.append(str(path))
        return valid_paths
    
    def _get_supported_files(self, paths: List[str], extensions: List[str] = None) -> List[str]:
        """Get list of supported files from paths."""
        supported_files = []
        
        for path_str in paths:
            path = Path(path_str)
            
            if path.is_file():
                if not extensions or path.suffix.lower() in extensions:
                    supported_files.append(str(path))
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        if not extensions or file_path.suffix.lower() in extensions:
                            # Skip files that are too large
                            if file_path.stat().st_size <= self.config.max_file_size:
                                supported_files.append(str(file_path))
        
        return supported_files


class ScanAgent(BaseAgent):
    """Base class for scanning agents."""
    
    @abstractmethod
    def scan_files(self, files: List[str]) -> List[Issue]:
        """Scan files and return issues."""
        pass
    
    def execute(self, paths: List[str], **kwargs) -> AgentResult:
        """Execute the scan agent."""
        self._start_execution()
        
        try:
            if not self.is_available():
                return self._create_result(
                    success=False,
                    error_message=f"{self.agent_type.value} is not available"
                )
            
            valid_paths = self._validate_paths(paths)
            if not valid_paths:
                return self._create_result(
                    success=False,
                    error_message="No valid paths provided"
                )
            
            issues = self.scan_files(valid_paths)
            
            return self._create_result(
                success=True,
                issues=issues,
                metadata={
                    "scanned_paths": valid_paths,
                    "files_processed": len(self._get_supported_files(valid_paths))
                }
            )
        
        except Exception as e:
            return self._create_result(
                success=False,
                error_message=str(e)
            )


class OutputAgent(BaseAgent):
    """Base class for output agents."""
    
    @abstractmethod
    def process_issues(self, issues: List[Issue], **kwargs) -> List[Issue]:
        """Process issues and return modified issues."""
        pass
    
    def execute(self, paths: List[str], issues: List[Issue] = None, **kwargs) -> AgentResult:
        """Execute the output agent."""
        self._start_execution()
        
        try:
            if not self.is_available():
                return self._create_result(
                    success=False,
                    error_message=f"{self.agent_type.value} is not available"
                )
            
            if not issues:
                return self._create_result(
                    success=True,
                    issues=[],
                    metadata={"message": "No issues to process"}
                )
            
            processed_issues = self.process_issues(issues, **kwargs)
            
            return self._create_result(
                success=True,
                issues=processed_issues,
                metadata={
                    "input_issues": len(issues),
                    "processed_issues": len(processed_issues)
                }
            )
        
        except Exception as e:
            return self._create_result(
                success=False,
                error_message=str(e)
            )
