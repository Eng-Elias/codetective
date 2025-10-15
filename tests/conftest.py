"""
Pytest configuration and shared fixtures for Codetective tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, Mock

import pytest

from codetective.core.config import Config
from codetective.models.schemas import (
    AgentResult,
    AgentType,
    Issue,
    IssueStatus,
    ScanConfig,
    SeverityLevel,
)


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def base_config():
    """Create a basic Config instance for testing."""
    return Config(
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        agent_timeout=60,
        max_file_size=1024 * 1024,  # 1MB for tests
    )


@pytest.fixture
def scan_config():
    """Create a ScanConfig instance for testing."""
    return ScanConfig(
        agents=[AgentType.SEMGREP, AgentType.TRIVY],
        parallel_execution=False,
        paths=["."],
    )


# ============================================================================
# File System Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file with security issues."""
    file_path = temp_dir / "vulnerable.py"
    content = """
import os
import pickle

# SQL Injection vulnerability
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

# Command injection vulnerability
def run_command(cmd):
    os.system(cmd)

# Pickle deserialization vulnerability
def load_data(data):
    return pickle.loads(data)
"""
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def sample_javascript_file(temp_dir):
    """Create a sample JavaScript file."""
    file_path = temp_dir / "app.js"
    content = """
// Potential XSS vulnerability
function renderHTML(userInput) {
    document.body.innerHTML = userInput;
}

// Hardcoded credentials
const API_KEY = "sk-1234567890abcdef";
"""
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def gitignore_file(temp_dir):
    """Create a .gitignore file for testing."""
    gitignore_path = temp_dir / ".gitignore"
    content = """
# Python
__pycache__/
*.pyc
*.pyo
venv/
.env

# Node
node_modules/
dist/

# Codetective
codetective_scan_results*.json
*.codetective.backup
"""
    gitignore_path.write_text(content, encoding="utf-8")
    return str(gitignore_path)


# ============================================================================
# Issue and Result Fixtures
# ============================================================================


@pytest.fixture
def sample_issue():
    """Create a sample Issue instance."""
    return Issue(
        id="test-issue-1",
        title="SQL Injection Vulnerability",
        description="User input is directly interpolated into SQL query",
        file_path="/path/to/file.py",
        severity=SeverityLevel.HIGH,
        line_number=10,
        rule_id="python.lang.security.sql-injection",
        fix_suggestion="Use parameterized queries",
        status=IssueStatus.DETECTED,
    )


@pytest.fixture
def sample_issues():
    """Create a list of sample issues."""
    return [
        Issue(
            id="semgrep-issue-1",
            title="SQL Injection",
            description="Potential SQL injection vulnerability",
            file_path="/path/to/file.py",
            severity=SeverityLevel.HIGH,
            line_number=10,
            rule_id="python.sql-injection",
            status=IssueStatus.DETECTED,
        ),
        Issue(
            id="trivy-issue-1",
            title="Outdated Dependency",
            description="requests library has known vulnerabilities",
            file_path="/path/to/requirements.txt",
            severity=SeverityLevel.MEDIUM,
            line_number=5,
            rule_id="CVE-2023-12345",
            status=IssueStatus.DETECTED,
        ),
    ]


@pytest.fixture
def sample_agent_result():
    """Create a sample AgentResult instance."""
    return AgentResult(
        agent_type=AgentType.SEMGREP,
        success=True,
        issues=[
            Issue(
                id="test-1",
                title="Test Issue",
                description="Test description",
                file_path="/test/file.py",
                severity=SeverityLevel.HIGH,
                line_number=10,
            )
        ],
        execution_time=1.5,
        metadata={"files_scanned": 5},
    )


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_ollama_response():
    """Create a mock Ollama response."""
    mock_response = Mock()
    mock_response.content = "This is a test AI response"
    return mock_response


@pytest.fixture
def mock_chat_ollama(monkeypatch, mock_ollama_response):
    """Mock ChatOllama for testing AI agents."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_ollama_response
    
    # Create a mock class that doesn't interfere with Pydantic
    class MockChatOllama:
        def __init__(self, base_url=None, model=None, temperature=0.1):
            self.base_url = base_url or "http://localhost:11434"
            self.model = model or "test-model"
            self.temperature = temperature
            self.invoke = mock_llm.invoke
    
    monkeypatch.setattr("codetective.agents.ai_base.ChatOllama", MockChatOllama)
    return mock_llm


@pytest.fixture
def mock_semgrep_output():
    """Mock SemGrep JSON output."""
    return {
        "results": [
            {
                "check_id": "python.lang.security.sql-injection",
                "path": "test.py",
                "start": {"line": 10, "col": 5},
                "end": {"line": 10, "col": 50},
                "extra": {
                    "message": "SQL injection vulnerability",
                    "severity": "ERROR",
                    "metadata": {"category": "security"},
                },
            }
        ]
    }


@pytest.fixture
def mock_trivy_output():
    """Mock Trivy JSON output."""
    return {
        "Results": [
            {
                "Target": "requirements.txt",
                "Type": "pip",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2023-12345",
                        "PkgName": "requests",
                        "InstalledVersion": "2.25.0",
                        "FixedVersion": "2.31.0",
                        "Severity": "HIGH",
                        "Title": "Security vulnerability in requests",
                        "Description": "A vulnerability exists in the requests library",
                    }
                ],
            }
        ]
    }


@pytest.fixture
def mock_process_success():
    """Mock successful process execution."""
    return (0, "Success output", "")


@pytest.fixture
def mock_process_failure():
    """Mock failed process execution."""
    return (1, "", "Error: Command failed")


# ============================================================================
# JSON Result Fixtures
# ============================================================================


@pytest.fixture
def sample_scan_results_json(temp_dir, sample_issues):
    """Create a sample scan results JSON file."""
    results_file = temp_dir / "scan_results.json"
    results_data = {
        "timestamp": "2024-01-01T12:00:00",
        "scan_path": str(temp_dir),
        "semgrep_results": [issue.model_dump() for issue in sample_issues[:1]],
        "trivy_results": [issue.model_dump() for issue in sample_issues[1:]],
        "ai_review_results": [],
        "total_issues": len(sample_issues),
        "scan_duration": 10.5,
    }
    results_file.write_text(json.dumps(results_data, indent=2))
    return results_file


# ============================================================================
# Helper Functions
# ============================================================================


def create_test_file(directory: Path, filename: str, content: str) -> Path:
    """Helper function to create test files."""
    file_path = directory / filename
    file_path.write_text(content)
    return file_path


def create_test_structure(base_dir: Path, structure: Dict) -> None:
    """
    Create a directory structure for testing.
    
    Args:
        base_dir: Base directory path
        structure: Dict where keys are paths and values are content or nested dicts
    """
    for path, content in structure.items():
        full_path = base_dir / path
        
        if isinstance(content, dict):
            # Create directory and recurse
            full_path.mkdir(parents=True, exist_ok=True)
            create_test_structure(full_path, content)
        else:
            # Create file with content
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)


# ============================================================================
# Skip Markers
# ============================================================================


def skip_if_no_ollama():
    """Skip test if Ollama is not available."""
    from codetective.utils import SystemUtils
    from codetective.utils.system_utils import RequiredTools
    
    available, _ = SystemUtils.check_tool_availability(RequiredTools.OLLAMA)
    return pytest.mark.skipif(not available, reason="Ollama not available")


def skip_if_no_semgrep():
    """Skip test if SemGrep is not available."""
    from codetective.utils import SystemUtils
    from codetective.utils.system_utils import RequiredTools
    
    available, _ = SystemUtils.check_tool_availability(RequiredTools.SEMGREP)
    return pytest.mark.skipif(not available, reason="SemGrep not available")


def skip_if_no_trivy():
    """Skip test if Trivy is not available."""
    from codetective.utils import SystemUtils
    from codetective.utils.system_utils import RequiredTools
    
    available, _ = SystemUtils.check_tool_availability(RequiredTools.TRIVY)
    return pytest.mark.skipif(not available, reason="Trivy not available")
