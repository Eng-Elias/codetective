"""
Base agent class for the codetective multi-agent system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
from pathlib import Path

from loguru import logger

from codetective.models.workflow_state import WorkflowState
from codetective.models.configuration import AgentConfig
from codetective.utils.logger import Logger


@dataclass
class AnalysisResult:
    """Result from agent analysis."""
    
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """
    Abstract base class for all codetective agents.
    
    This class defines the common interface and behavior that all agents
    must implement, including initialization, analysis execution, and
    capability reporting.
    """
    
    def __init__(self, config: AgentConfig, agent_name: str):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
            agent_name: Name of the agent for logging
        """
        self.config = config
        self.agent_name = agent_name
        self.logger = Logger.get_logger(f"agent.{agent_name}")
        
        # Validate configuration
        self._validate_config()
        
        # Initialize agent-specific setup
        self._initialize()
    
    @property
    def is_enabled(self) -> bool:
        """Check if agent is enabled."""
        return self.config.enabled
    
    @property
    def timeout(self) -> int:
        """Get agent timeout in seconds."""
        return self.config.timeout
    
    @property
    def retry_count(self) -> int:
        """Get agent retry count."""
        return self.config.retry_count
    
    def _validate_config(self) -> None:
        """Validate agent configuration."""
        if not isinstance(self.config, AgentConfig):
            raise ValueError(f"Invalid config type for {self.agent_name}")
        
        if self.config.timeout <= 0:
            raise ValueError(f"Timeout must be > 0 for {self.agent_name}")
        
        if self.config.retry_count < 0:
            raise ValueError(f"Retry count must be >= 0 for {self.agent_name}")
    
    def _initialize(self) -> None:
        """Initialize agent-specific setup. Override in subclasses."""
        pass
    
    @abstractmethod
    async def analyze(self, state: WorkflowState) -> AnalysisResult:
        """
        Perform agent-specific analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Analysis result with findings and metadata
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        pass
    
    async def execute_with_retry(self, state: WorkflowState) -> AnalysisResult:
        """
        Execute analysis with retry logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Analysis result
        """
        if not self.is_enabled:
            self.logger.info(f"Agent {self.agent_name} is disabled, skipping")
            return AnalysisResult(
                success=True,
                data=None,
                metadata={"skipped": True, "reason": "disabled"}
            )
        
        last_error = None
        
        for attempt in range(self.retry_count + 1):
            try:
                self.logger.info(f"Starting analysis (attempt {attempt + 1}/{self.retry_count + 1})")
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.analyze(state),
                    timeout=self.timeout
                )
                
                if result.success:
                    self.logger.info(f"Analysis completed successfully")
                    return result
                else:
                    self.logger.warning(f"Analysis failed: {result.error}")
                    last_error = result.error
                    
                    if attempt < self.retry_count:
                        self.logger.info(f"Retrying in 2 seconds...")
                        await asyncio.sleep(2)
            
            except asyncio.TimeoutError:
                error_msg = f"Analysis timed out after {self.timeout} seconds"
                self.logger.error(error_msg)
                last_error = error_msg
                
                if attempt < self.retry_count:
                    self.logger.info(f"Retrying after timeout...")
                    await asyncio.sleep(2)
            
            except Exception as e:
                error_msg = f"Unexpected error during analysis: {str(e)}"
                self.logger.exception(error_msg)
                last_error = error_msg
                
                if attempt < self.retry_count:
                    self.logger.info(f"Retrying after error...")
                    await asyncio.sleep(2)
        
        # All retries exhausted
        self.logger.error(f"Analysis failed after {self.retry_count + 1} attempts")
        return AnalysisResult(
            success=False,
            error=last_error or "Unknown error",
            metadata={"attempts": self.retry_count + 1}
        )
    
    def validate_input_files(self, files: List[Path]) -> List[Path]:
        """
        Validate and filter input files for analysis.
        
        Args:
            files: List of file paths to validate
            
        Returns:
            List of valid file paths
        """
        valid_files = []
        supported_extensions = self.get_supported_file_extensions()
        
        for file_path in files:
            if not file_path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                continue
            
            if not file_path.is_file():
                self.logger.warning(f"Path is not a file: {file_path}")
                continue
            
            if supported_extensions and file_path.suffix.lower() not in supported_extensions:
                self.logger.debug(f"Unsupported file type: {file_path}")
                continue
            
            valid_files.append(file_path)
        
        self.logger.info(f"Validated {len(valid_files)} files out of {len(files)}")
        return valid_files
    
    def get_supported_file_extensions(self) -> Optional[List[str]]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of extensions (e.g., ['.py', '.js']) or None for all files
        """
        return None  # Default: support all files
    
    def create_backup(self, files: List[Path]) -> Optional[Path]:
        """
        Create backup of files before modification.
        
        Args:
            files: List of files to backup
            
        Returns:
            Path to backup directory or None if backup failed
        """
        try:
            import tempfile
            import shutil
            from datetime import datetime
            
            # Create backup directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(tempfile.gettempdir()) / f"codetective_backup_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            # Copy files to backup
            for file_path in files:
                if file_path.exists():
                    backup_file = backup_dir / file_path.name
                    shutil.copy2(file_path, backup_file)
            
            self.logger.info(f"Created backup at: {backup_dir}")
            return backup_dir
        
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent information and status.
        
        Returns:
            Dictionary with agent information
        """
        return {
            "name": self.agent_name,
            "enabled": self.is_enabled,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "capabilities": self.get_capabilities(),
            "supported_extensions": self.get_supported_file_extensions(),
            "config": self.config.to_dict(),
        }
    
    def __str__(self) -> str:
        """String representation of the agent."""
        status = "enabled" if self.is_enabled else "disabled"
        return f"{self.agent_name} ({status})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return f"{self.__class__.__name__}(name='{self.agent_name}', enabled={self.is_enabled})"
