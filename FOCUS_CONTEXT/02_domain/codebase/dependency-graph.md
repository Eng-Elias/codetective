# Dependency Graph

## Purpose
Outlines the key internal and external dependencies for the codetective multi-agent code review tool to manage complexity and understand the impact of changes.

## Internal Dependencies

### Core Architecture
```
Interfaces (GUI/CLI/MCP)
    ↓
Workflow Orchestrator (LangGraph)
    ↓
Agents (Semgrep/Trivy/AI/Output)
    ↓
Utilities (File/Config/Logger)
    ↓
Models (Data Classes)
```

### Module Dependencies
- **`models`**: No dependencies on other internal modules (foundation layer)
- **`utils`**: Depends only on `models` for type definitions
- **`agents`**: Depends on `models` and `utils`
- **`workflow`**: Depends on `agents`, `models`, and `utils`
- **`interfaces`**: Depends on `workflow`, `agents`, `models`, and `utils`

### Agent Dependencies
```
BaseAgent (Abstract)
    ↑
├── SemgrepAgent
├── TrivyAgent
├── AIReviewAgent
├── OutputCommentAgent
└── OutputUpdateAgent
```

### Interface Dependencies
```
BaseInterface (Abstract)
    ↑
├── StreamlitGUI
├── ClickCLI
└── MCPServer
```

## External Dependencies

### Package Management
- **pip**: `requirements.txt` and `pyproject.toml`
- **Poetry**: Alternative dependency management (optional)

### Core Framework Dependencies
```python
# Workflow Orchestration
langgraph==0.6.3        # Multi-agent workflow management

# Interface Frameworks
streamlit==1.48.0       # GUI interface
click==8.1.8            # CLI interface
typer==0.16.0            # Enhanced CLI with type hints

# External Tool Integration
semgrep==1.131.0         # Static analysis
trivy==0.50.0           # Vulnerability scanning

# AI/LLM Providers
openai==1.99.1           # OpenAI GPT models
anthropic==0.61.0       # Claude models
google-genai==1.28.0     # Gemini models
requests==2.32.4        # HTTP client for API calls

# Data Processing
pydantic==2.11.7         # Data validation
dataclasses-json        # JSON serialization
pyyaml==6.0.2             # YAML configuration
jsonschema==4.25.0       # JSON schema validation

# Utilities
rich==13.5.3            # Terminal formatting
loguru==0.7.3           # Enhanced logging
typing-extensions==4.14.1       # Type hints backport
pathlib2==2.3.7.post1                # Path manipulation
```

### Development Dependencies
```python
# Code Quality
black==23.0.0           # Code formatting
ruff==0.1.0             # Linting and import sorting
mypy==1.5.0             # Type checking
bandit==1.7.0           # Security analysis
pre-commit==3.0.0       # Git hooks

# Documentation
sphinx==7.0.0           # Documentation generation
mkdocs==1.5.0           # Alternative docs
```

### Optional Dependencies
```python
# Local LLM Support
ollama                  # Local LLM server
lmstudio-api           # LM Studio integration

# Enhanced Security
cryptography>=41.0.0    # Encryption utilities
keyring>=24.0.0        # Secure credential storage

# Performance
numpy>=1.24.0          # Numerical operations
pandas>=2.0.0          # Data analysis (for large reports)
```

## Dependency Rules

### Architecture Rules
1. **Layered Dependencies**: Lower layers cannot depend on higher layers
2. **Interface Isolation**: Interfaces cannot depend on each other
3. **Agent Independence**: Agents cannot directly depend on other agents
4. **Utility Purity**: Utilities must be stateless and side-effect free

### External Dependency Rules
1. **Version Pinning**: Pin major versions, allow minor/patch updates
2. **Security Updates**: Use Dependabot for automated security updates
3. **License Compatibility**: All dependencies must use compatible licenses
4. **Minimal Dependencies**: Avoid unnecessary transitive dependencies

### LLM Provider Rules
1. **Provider Abstraction**: All LLM providers implement common interface
2. **Graceful Degradation**: System works with any single provider
3. **API Key Security**: Never log or expose API keys
4. **Rate Limiting**: Implement proper rate limiting for all providers

## Critical Paths

### Workflow Execution
```
Interface Input → WorkflowState → LangGraph → Agents → Results → Interface Output
```

### Agent Execution
```
Agent.execute() → External Tool → Parse Results → Update State
```

### Error Handling
```
Exception → Agent Error Handler → State Update → Workflow Continuation
```
