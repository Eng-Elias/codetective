# Codetective Test Suite

Comprehensive test suite for Codetective Multi-Agent Code Review Tool as part of Module 3 Productionization (AAIDC Certificate).

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── unit/                    # Unit tests (70%+ coverage target)
│   ├── test_base_agent.py   # Base agent classes
│   ├── test_ai_base.py      # AI agent base functionality
│   ├── test_config.py       # Configuration management
│   ├── test_schemas.py      # Pydantic models
│   ├── test_file_utils.py   # File utility functions
│   ├── test_semgrep_agent.py    # SemGrep agent
│   ├── test_trivy_agent.py      # Trivy agent
│   └── test_output_agents.py    # Comment & Edit agents
├── integration/             # Integration tests
│   ├── test_scan_workflow.py
│   ├── test_fix_workflow.py
│   └── test_multi_agent_coordination.py
└── e2e/                     # End-to-end tests
    ├── test_vulnerable_code_detection.py
    ├── test_automated_fix_application.py
    └── test_complete_user_journey.py
```

## Running Tests

### Run All Tests
```bash
make test
# or
pytest tests/ -v --cov=codetective
```

### Run Specific Test Categories
```bash
# Unit tests only
make test-unit
pytest tests/unit/ -v -m unit

# Integration tests
make test-integration
pytest tests/integration/ -v -m integration

# End-to-end tests
make test-e2e
pytest tests/e2e/ -v -m e2e
```

### Run Tests Without Slow Tests
```bash
make test-fast
pytest tests/ -v -m "not slow"
```

### Generate Coverage Report
```bash
make coverage
make coverage-report  # Opens HTML report in browser
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_ollama` - Tests requiring Ollama
- `@pytest.mark.requires_semgrep` - Tests requiring SemGrep
- `@pytest.mark.requires_trivy` - Tests requiring Trivy
- `@pytest.mark.security` - Security-related tests

## Test Fixtures

### Configuration Fixtures
- `base_config` - Basic Config instance
- `scan_config` - ScanConfig instance

### File System Fixtures
- `temp_dir` - Temporary directory for testing
- `sample_python_file` - Python file with security issues
- `sample_javascript_file` - JavaScript test file
- `gitignore_file` - .gitignore file for testing

### Data Fixtures
- `sample_issue` - Single Issue instance
- `sample_issues` - List of Issues
- `sample_agent_result` - AgentResult instance
- `sample_scan_results_json` - JSON scan results file

### Mock Fixtures
- `mock_ollama_response` - Mock Ollama API response
- `mock_chat_ollama` - Mock ChatOllama instance
- `mock_semgrep_output` - Mock SemGrep JSON output
- `mock_trivy_output` - Mock Trivy JSON output
- `mock_process_success` - Successful process execution
- `mock_process_failure` - Failed process execution

## Coverage Requirements

**Module 3 Target**: 70%+ test coverage for core functionality

Current coverage areas:
- ✅ Base agent classes (BaseAgent, ScanAgent, OutputAgent)
- ✅ AI base functionality (AIAgent)
- ✅ Configuration management (Config, ScanConfig, FixConfig)
- ✅ Data models (Issue, AgentResult, ScanResult)
- ✅ File utilities (FileUtils)
- ✅ Agent implementations (SemGrep, Trivy, Comment, Edit)
- 🔄 Core orchestrator (pending)
- 🔄 Git utilities (pending)
- 🔄 Process utilities (pending)

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test
```python
import pytest
from codetective.agents.base import BaseAgent

class TestMyComponent:
    """Test cases for MyComponent."""
    
    @pytest.mark.unit
    def test_basic_functionality(self, base_config):
        """Test basic functionality."""
        component = MyComponent(base_config)
        result = component.execute()
        assert result is not None
    
    @pytest.mark.integration
    @pytest.mark.requires_ollama
    def test_with_real_ollama(self, base_config):
        """Test with real Ollama service."""
        # Skip if Ollama not available
        component = MyComponent(base_config)
        if not component.is_ai_available():
            pytest.skip("Ollama not available")
        
        result = component.run_with_ai()
        assert result.success is True
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=codetective --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Test Data

Test data files are located in `tests/fixtures/` (if needed):
- Sample vulnerable code files
- Mock API responses
- Configuration examples

## Troubleshooting

### Tests Failing Due to Missing Tools
```bash
# Install required tools
make setup-tools
pip install semgrep
# Install Trivy from: https://aquasecurity.github.io/trivy/
# Install Ollama from: https://ollama.ai/
```

### Coverage Not Meeting Target
```bash
# Generate detailed coverage report
pytest --cov=codetective --cov-report=html
# Open htmlcov/index.html to see uncovered lines
```

### Slow Test Execution
```bash
# Run without slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/unit/test_config.py -v
```

## Contributing

When adding new features to Codetective:
1. Write tests first (TDD approach)
2. Ensure 70%+ coverage for new code
3. Add appropriate pytest markers
4. Update this README if adding new test categories
5. Run full test suite before committing

## Module 3 Compliance

This test suite meets the requirements for:
- ✅ **Comprehensive Testing Suite** (70%+ coverage)
- ✅ Unit tests for individual components
- ✅ Integration tests for workflows
- ✅ End-to-end tests for user journeys
- ✅ Test fixtures and mocking
- ✅ CI/CD ready configuration

Part of the Agentic AI Developer Certification (AAIDC) Module 3 Project.
