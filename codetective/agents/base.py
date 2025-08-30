"""
Base agent class for Codetective agents.
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from codetective.core.config import Config
from codetective.models.schemas import AgentResult, AgentType, Issue
from codetective.utils.file_utils import FileUtils


class BaseAgent(ABC):
    """Base class for all Codetective agents."""

    def __init__(self, config: Config):
        """Initialize the agent with configuration."""
        self.config = config
        self.agent_type: AgentType = AgentType.UNKOWN
        self._execution_start_time: Optional[float] = None

    @abstractmethod
    def execute(self, paths: List[str], **kwargs: Any) -> AgentResult:
        """Execute the agent on the given paths."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the agent's dependencies are available."""
        pass

    def _start_execution(self) -> None:
        """Mark the start of execution for timing."""
        self._execution_start_time = time.time()

    def _create_result(
        self,
        success: bool,
        issues: Optional[List[Issue]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """Create an AgentResult with timing information."""
        execution_time = time.time() - self._execution_start_time if self._execution_start_time else 0.0

        return AgentResult(
            agent_type=self.agent_type,
            success=success,
            issues=issues or [],
            execution_time=execution_time,
            error_message=error_message,
            metadata=metadata or {},
        )

    def _get_supported_files(self, paths: List[str], extensions: Optional[List[str]] = None) -> List[str]:
        """Get list of supported files from paths."""
        supported_files = []

        def _is_supported_file(file_path: Path) -> bool:
            if extensions and file_path.suffix.lower() not in extensions:
                return False

            if self.config.max_file_size and file_path.stat().st_size > self.config.max_file_size:
                return False

            return True

        for path_str in paths:
            path = Path(path_str)

            if path.is_file():
                if _is_supported_file(path):
                    supported_files.append(str(path))
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        if _is_supported_file(file_path):
                            supported_files.append(str(file_path))

        return supported_files


class ScanAgent(BaseAgent):
    """Base class for scanning agents."""

    @abstractmethod
    def scan_files(self, files: List[str], **kwargs: Any) -> List[Issue]:
        """Scan files and return issues."""
        pass

    def execute(self, paths: List[str], **kwargs: Any) -> AgentResult:
        """Execute the scan agent."""
        self._start_execution()

        try:
            if not self.is_available():
                return self._create_result(success=False, error_message=f"{self.agent_type.value} is not available")

            validated_paths = FileUtils.validate_paths(paths)
            if not validated_paths:
                return self._create_result(success=False, error_message="No valid paths provided")

            issues = self.scan_files(validated_paths)

            return self._create_result(
                success=True,
                issues=issues,
                metadata={
                    "scanned_paths": validated_paths,
                    "files_processed": len(self._get_supported_files(validated_paths)),
                },
            )

        except Exception as e:
            return self._create_result(success=False, error_message=str(e))


class OutputAgent(BaseAgent):
    """Base class for output agents."""

    @abstractmethod
    def process_issues(self, issues: List[Issue], **kwargs: Any) -> List[Issue]:
        """Process issues and return modified issues."""
        pass

    def execute(self, paths: List[str], issues: Optional[List[Issue]] = None, **kwargs: Any) -> AgentResult:
        """Execute the output agent."""
        self._start_execution()

        try:
            if not self.is_available():
                return self._create_result(success=False, error_message=f"{self.agent_type.value} is not available")

            if not issues:
                return self._create_result(success=True, issues=[], metadata={"message": "No issues to process"})

            processed_issues = self.process_issues(issues, **kwargs)

            return self._create_result(
                success=True,
                issues=processed_issues,
                metadata={"input_issues": len(issues), "processed_issues": len(processed_issues)},
            )

        except Exception as e:
            return self._create_result(success=False, error_message=str(e))
