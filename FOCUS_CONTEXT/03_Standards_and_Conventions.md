# Standards and Conventions

## Python Package Structure

- Follow **PEP 8** coding standards for Python code style
- Use **PEP 517/518** compliant `pyproject.toml` for package configuration
- Implement proper `__init__.py` files for package structure
- Use **type hints** throughout the codebase for better code documentation
- **Beta Versioning**: Use semantic versioning with beta suffix (e.g., 0.1.0b1)
- **Python Support**: Target Python 3.10-3.12 with explicit version constraints

## CLI Framework Standards

- Use **Click framework** for all CLI command implementations
- Follow consistent command naming: `codetective <command>`
- Implement proper help text and argument validation
- Use consistent option naming patterns (`-a/--agents`, `-t/--timeout`, etc.)

## JSON Output Format Standardization

```json
{
  "semgrep_results": [...],
  "trivy_results": [...],
  "ai_review_results": [...]
}
```

- Always maintain the three-property structure
- Use consistent field naming across all agents
- Include metadata fields: timestamp, version, scan_path

## LangGraph Node/Edge Conventions

- **Node Naming**: Use descriptive names (e.g., `semgrep_scan`, `ai_review`, `apply_fixes`)
- **Edge Conditions**: Implement clear conditional logic for agent selection
- **State Management**: Use typed state objects for agent communication
- **Error Handling**: Implement graceful failure modes for each node

## Code Style Standards

- **Formatting**: Use Black formatter with default settings
- **Import Organization**: Use isort for consistent import ordering
- **Docstrings**: Follow Google-style docstring format
- **Variable Naming**: Use descriptive names, avoid abbreviations

## Error Handling and Logging

- Use Python's `logging` module with structured logging
- Implement consistent error message formats
- Provide user-friendly error messages in CLI
- Log debug information for troubleshooting


## Git Integration Standards

- **Git-Aware File Selection**: Respect .gitignore patterns
- **Smart File Discovery**: Distinguish git-tracked vs untracked files
- **Diff-Only Mode**: Support scanning only modified files
- **Repository Detection**: Automatic git repository identification
- **Fallback Behavior**: Graceful handling of non-git directories

## PyPI Distribution Standards

- **Modern Packaging**: Use pyproject.toml
- **Build System**: setuptools with wheel distribution
- **Version Management**: Semantic versioning with beta releases
- **Dependency Specification**: Explicit version ranges with compatibility
- **Metadata Completeness**: Full PyPI classifier and URL information
- **Development Dependencies**: Separate dev dependencies for testing/linting

## Makefile Automation Standards

- **Target Naming**: Use descriptive, hyphenated target names
- **Help System**: Comprehensive help target with command descriptions
- **Build Pipeline**: clean → build → check → upload workflow
- **Development Workflow**: install-dev → format → lint → test
- **Release Automation**: Separate beta-release and production-release targets
- **Tool Integration**: Automated external tool setup and verification

## Testing Standards (Module 3 Requirement)

### Test Framework
- **Framework**: pytest with plugins (pytest-cov, pytest-asyncio, pytest-mock)
- **Coverage Target**: Minimum 70% for core functionality
- **Test Organization**: Separate unit, integration, and e2e test directories
- **Naming Convention**: `test_*.py` for test files, `test_*` for test functions

### Unit Testing Standards
- **Isolation**: Each unit test should test one component in isolation
- **Mocking**: Use pytest fixtures and mocks for external dependencies
- **Assertions**: Clear, descriptive assertion messages
- **Parametrization**: Use `@pytest.mark.parametrize` for multiple test cases
- **Fast Execution**: Unit tests should complete in milliseconds

### Integration Testing Standards
- **Real Dependencies**: Test with actual tool integrations (SemGrep, Trivy)
- **Setup/Teardown**: Use fixtures for test data and cleanup
- **State Management**: Ensure tests don't depend on execution order
- **Test Data**: Use realistic test data and sample code repositories

### End-to-End Testing Standards
- **Complete Workflows**: Test full user journeys (scan → fix → verify)
- **Real Scenarios**: Use actual vulnerable code samples
- **Performance**: Set reasonable timeouts for E2E tests
- **Cleanup**: Always clean up generated files and backups

### Test Coverage Standards
- **Minimum Coverage**: 70% overall, 85% for critical paths
- **Critical Components**: 100% coverage for security layer
- **Branch Coverage**: Measure and report branch coverage
- **Coverage Reports**: Generate HTML and XML coverage reports

## Security & Safety Standards (Module 3 Requirement)

### Input Validation Standards
- **Path Validation**: Prevent directory traversal attacks
  - Use `os.path.abspath()` and validate against allowed directories
  - Reject paths containing `..` or suspicious patterns
- **File Size Limits**: Enforce maximum file size (default: 10MB)
- **File Type Whitelist**: Only process supported file extensions
- **JSON Validation**: Use Pydantic schemas for all JSON inputs

### Prompt Injection Prevention
- **Input Sanitization**: Remove/escape potential prompt injection patterns
- **Token Limits**: Enforce maximum token counts for LLM inputs
- **Content Filtering**: Block suspicious patterns before sending to LLM
- **Output Validation**: Verify LLM outputs match expected format
- **Prompt Templates**: Use parameterized prompts, never string concatenation

### Output Safety Standards
- **Sensitive Data Filtering**: Remove API keys, tokens, passwords from logs
- **Code Validation**: Verify AI-generated fixes compile/parse correctly
- **Malicious Pattern Detection**: Scan fixes for dangerous code patterns
- **Backup Before Modify**: Always create backups before file modifications
- **Rollback Capability**: Provide mechanism to undo changes

### Rate Limiting Standards
- **LLM API Rate Limits**: Enforce rate limits for AI provider calls
- **Resource Limits**: Monitor CPU, memory, disk usage
- **Per-Session Limits**: Limit files processed per session
- **Circuit Breakers**: Stop processing if error rate exceeds threshold

## Resilience & Monitoring Standards (Module 3 Requirement)

### Retry Logic Standards
- **Exponential Backoff**: Use exponential backoff with jitter
- **Retry Attempts**: 3 attempts for network operations, 2 for LLM calls
- **Retry Conditions**: Retry only on transient errors (timeout, connection)
- **Circuit Breaker**: Stop retrying after consistent failures

### Timeout Standards
- **Default Timeouts**: 900s for full scan, 60s per agent, 30s for LLM calls
- **Progressive Warnings**: Warn at 50%, 75%, 90% of timeout
- **Timeout Recovery**: Graceful shutdown on timeout with partial results
- **Per-Agent Timeouts**: Allow custom timeout per agent type

### Logging Standards
- **Structured Logging**: Use JSON format for logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Component Tags**: Tag logs with component name (agent, cli, gui)
- **Performance Logs**: Log execution time for all operations
- **Sensitive Data**: Never log passwords, API keys, or tokens
- **Log Rotation**: Rotate logs daily, keep 7 days of history

### Metrics Standards
- **Agent Metrics**: Track success/failure rate per agent
- **Performance Metrics**: Execution time, memory usage, file count
- **LLM Metrics**: Token usage, response time, error rate
- **Resource Metrics**: CPU, memory, disk usage
- **Export Format**: Prometheus-compatible format (optional)

### Health Check Standards
- **Tool Availability**: Check SemGrep, Trivy, LLM service availability
- **Resource Health**: Monitor CPU, memory, disk space
- **Service Health**: Check LLM API connectivity and response time
- **Health Endpoint**: Provide health check CLI command and API endpoint

## Multi-LLM Support Standards (Module 3 Enhancement)

### LLM Provider Abstraction
- **Provider Interface**: All providers implement common interface
- **Configuration**: Unified configuration for all providers
- **Error Handling**: Consistent error handling across providers
- **Fallback Logic**: Automatic fallback to alternative providers

### Provider Integration Standards
- **API Keys**: Store in environment variables, never in code
- **Authentication**: Use secure authentication methods
- **Rate Limits**: Respect provider-specific rate limits
- **Error Messages**: Provide clear, actionable error messages

### Supported Providers
- **Ollama**: Local LLM server (existing)
- **Google Gemini**: Cloud API with API key authentication
- **xAI Grok**: Cloud API with API key authentication
- **Provider Selection**: Allow user to choose preferred provider

## Documentation Standards (Module 3 Requirement)

### Code Documentation
- **Docstrings**: Required for all public functions, classes, modules
- **Type Hints**: Required for all function signatures
- **Inline Comments**: Explain complex logic and algorithms
- **Docstring Format**: Google-style docstrings

### API Documentation
- **API Reference**: Auto-generated from docstrings
- **Examples**: Include usage examples for all public APIs
- **Parameter Documentation**: Document all parameters and return values
- **Exception Documentation**: Document all raised exceptions

### Operational Documentation
- **README**: High-level overview and quick start
- **ARCHITECTURE**: System architecture and component interaction
- **TROUBLESHOOTING**: Common issues and solutions
- **OPERATIONS**: Deployment, monitoring, maintenance procedures
- **CONTRIBUTING**: Development workflow and guidelines
