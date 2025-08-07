# Windsurf Rules for Codetective Multi-Agent Code Review Tool

## Project Context
Codetective is a multi-agent code review tool that automates static analysis, security scanning, and AI-powered code improvements with multiple interfaces (GUI/CLI/MCP).

## Core Architecture Rules

### Multi-Agent Framework
- **BaseAgent Pattern**: All agents MUST inherit from `BaseAgent` abstract class
- **LangGraph Integration**: Use LangGraph for workflow orchestration and state management
- **Agent Isolation**: Each agent should be independently testable and fail gracefully
- **State Management**: Use dataclasses for agent state with proper typing
- **Result Standardization**: All agents return structured `AnalysisResult` objects

### Clean Code Architecture (CRITICAL)
- **NO Standalone Functions**: ALL utilities MUST be implemented as classes with properties and methods
- **SOLID Principles**: Follow Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion
- **Class-Based Design**: Every utility module must contain classes, not loose functions
- **Type Safety**: Full type hints with mypy validation

### Code Quality Standards
- **Python Style**: PEP 8 with Black formatter (100 character line length)
- **Linting**: Use ruff, black, mypy, and isort with zero violations
- **Import Organization**: isort with "black" profile
- **Naming Conventions**:
  - Variables/Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Agent Classes: Suffix with "Agent" (e.g., `SemgrepAgent`)
  - Interface Classes: Suffix with "Interface" (e.g., `CLIInterface`)

## Agent Implementation Rules

### Required Agent Structure
```python
# ✅ CORRECT Agent Implementation
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AgentState:
    files_to_analyze: List[Path]
    analysis_results: Dict[str, Any]
    configuration: Dict[str, Any]
    execution_context: Dict[str, Any]

class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = self._setup_logging()
    
    @abstractmethod
    async def analyze(self, state: AgentState) -> AnalysisResult:
        """Perform agent-specific analysis"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
```

### Specific Agent Requirements
- **SemgrepAgent**: Static code analysis with custom rule support
- **TrivyAgent**: Security vulnerability scanning with multiple scan types
- **AIReviewAgent**: LLM integration with multiple providers (OpenAI/Anthropic/Gemini/Ollama/LM_Studio)
- **OutputCommentAgent**: Generate explanatory comments for issues
- **OutputUpdateAgent**: Apply code fixes with backup and rollback capabilities

## Interface Implementation Rules

### Multi-Interface Support
- **GUI (Streamlit)**: Web-based interface with project browsing and real-time progress
- **CLI (Click/Typer)**: Command-line tool with CI/CD integration and multiple output formats
- **MCP**: Model Context Protocol for AI assistant integration

### Interface Standards
- **Consistent API**: All interfaces should provide the same core functionality
- **Error Handling**: User-friendly error messages with recovery options
- **Configuration**: Support for configuration files and environment variables
- **Output Formats**: JSON, SARIF, and text formats for CLI; interactive for GUI

## Development Workflow Rules

### File Organization
```
src/
├── agents/          # Multi-agent implementations
├── core/           # LangGraph orchestrator and state management
├── interfaces/     # GUI, CLI, MCP implementations
├── utils/          # Class-based utilities
└── models/         # Dataclasses and type definitions
```

### Security and Safety
- **Read-Only Analysis**: Default to read-only mode for all agents
- **Backup Creation**: Always create backups before code modifications
- **API Key Protection**: Never log or expose API keys
- **Input Validation**: Sanitize all user inputs
- **Privilege Limitation**: Run with minimal required privileges

## Code Generation Rules

### When Creating New Files
1. **Check Architecture**: Ensure file fits the multi-agent architecture
2. **Follow Naming**: Use consistent naming conventions
3. **Add Type Hints**: Full type annotations required
4. **Include Docstrings**: Comprehensive documentation for all public methods
5. **Error Handling**: Implement proper exception handling
6. **Logging**: Add structured logging with appropriate levels

### When Modifying Existing Code
1. **Preserve Architecture**: Don't break the multi-agent pattern
2. **Maintain Compatibility**: Ensure changes don't break other agents
3. **Check Dependencies**: Verify no circular dependencies
4. **Validate Types**: Run mypy after changes

## Integration Rules

### External Tool Integration
- **Semgrep**: CLI wrapper with custom rule support
- **Trivy**: Multiple scan types (fs, config, dependency)
- **Git**: Repository management and file selection
- **LLM APIs**: Multiple provider support with rate limiting

### Configuration Management
- **Environment Variables**: Use for API keys and sensitive data
- **YAML Configuration**: Support for complex configuration scenarios
- **Validation**: Comprehensive configuration validation with helpful errors
- **Profiles**: Support for different configuration profiles

## Quality Assurance Rules

### Pre-Commit Checks
- **Linting**: ruff, black, isort must pass
- **Type Checking**: mypy validation required
- **Security Scan**: No high/critical security issues
- **Test Execution**: Relevant unit tests must pass

### Code Review Requirements
- **Architecture Review**: Ensure multi-agent patterns are followed
- **Security Review**: Check for security vulnerabilities
- **Performance Review**: Validate performance implications
- **Documentation Review**: Ensure documentation is updated

## Prohibited Patterns

### ❌ NEVER DO THIS
```python
# Standalone functions in utility modules
def process_file(file_path):
    pass

def analyze_code(code):
    pass
```

### ✅ ALWAYS DO THIS
```python
# Class-based utilities
class FileProcessor:
    def __init__(self, config: ProcessorConfig):
        self.config = config
    
    def process_file(self, file_path: Path) -> ProcessResult:
        pass

class CodeAnalyzer:
    def __init__(self, analyzer_config: AnalyzerConfig):
        self.config = analyzer_config
    
    def analyze_code(self, code: str) -> AnalysisResult:
        pass
```

## Emergency Procedures

### If Agent Fails
1. **Isolate Failure**: Prevent cascade to other agents
2. **Log Context**: Capture full error context
3. **Graceful Degradation**: Continue with partial results
4. **User Notification**: Inform user of failure and options

### If Code Modification Fails
1. **Immediate Rollback**: Restore from backup
2. **Damage Assessment**: Check for any corrupted files
3. **User Notification**: Inform user of failure and recovery
4. **Incident Logging**: Log for post-incident analysis

## Performance Guidelines

### Optimization Targets
- **Small Projects** (< 100 files): Complete analysis within 2 minutes
- **Medium Projects** (100-1000 files): Complete analysis within 10 minutes
- **Large Projects** (> 1000 files): Complete analysis within 30 minutes
- **Memory Usage**: Stay below 2GB for typical projects
- **Parallel Execution**: Reduce total time by at least 30%

### Resource Management
- **Cleanup**: Proper cleanup of temporary files and resources
- **Memory Monitoring**: Monitor memory usage during analysis
- **Timeout Handling**: Implement timeouts for external tool calls
- **Rate Limiting**: Respect API rate limits for LLM services
