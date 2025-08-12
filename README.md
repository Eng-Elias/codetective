# 🔍 Codetective - Multi-Agent Code Review Tool

A comprehensive code analysis tool that combines multiple scanning engines (SemGrep, Trivy, AI) with automated fixing capabilities using LangGraph orchestration.

## Features

- **Multi-Agent Scanning**: Combines SemGrep, Trivy, and AI-powered analysis
- **Automated Fixing**: AI-powered code fixes and explanatory comments
- **CLI Interface**: Command-line interface for automation and CI/CD integration
- **Web GUI**: Streamlit-based web interface for interactive use
- **LangGraph Orchestration**: Intelligent agent coordination and workflow management
- **Configurable**: Flexible configuration via files and environment variables

## Installation

### Prerequisites

Before installing Codetective, ensure you have the following tools installed:

1. **Python 3.8+**
2. **SemGrep** (optional but recommended):
   ```bash
   pip install semgrep
   ```
3. **Trivy** (optional but recommended):
   - Follow installation instructions at: https://aquasecurity.github.io/trivy/latest/getting-started/installation/
4. **Ollama** (optional, for AI features):
   - Download from: https://ollama.ai/download
   - Install a code model: `ollama pull codellama`

### Install Codetective

```bash
# Clone the repository
git clone https://github.com/codetective/codetective.git
cd codetective

# Install the package
pip install -e .

# Or install from PyPI (when available)
pip install codetective
```

## Quick Start

### 1. Check System Compatibility

```bash
codetective info
```

This will show you which tools are available and their versions.

### 2. Run a Code Scan

```bash
# Scan current directory with all agents
codetective scan .

# Scan specific paths with selected agents
codetective scan /path/to/code --agents semgrep,trivy --timeout 600

# Custom output file
codetective scan . --output my_scan_results.json
```

### 3. Apply Fixes

```bash
# Apply automatic fixes
codetective fix codetective_scan_results.json --agents edit

# Add explanatory comments instead
codetective fix codetective_scan_results.json --agents comment
```

### 4. Launch Web GUI

```bash
codetective gui
```

Then open your browser to `http://localhost:8501`

## CLI Commands

### `codetective info`
Check system compatibility and tool availability.

### `codetective scan [paths]`
Execute multi-agent code scanning.

**Options:**
- `-a, --agents`: Comma-separated agents (semgrep,trivy,ai_review)
- `-t, --timeout`: Timeout in seconds (default: 300)
- `-o, --output`: Output JSON file (default: codetective_scan_results.json)

**Examples:**
```bash
codetective scan .
codetective scan src/ tests/ --agents semgrep,trivy --timeout 600
codetective scan . --output security_scan.json
```

### `codetective fix <json_file>`
Apply automated fixes to identified issues.

**Options:**
- `-a, --agents`: Fix agents (comment,edit) (default: edit)

**Examples:**
```bash
codetective fix scan_results.json
codetective fix scan_results.json --agents comment
```

### `codetective gui`
Launch Streamlit web interface.

**Options:**
- `--host`: Host to run on (default: localhost)
- `--port`: Port to run on (default: 8501)

## Configuration

### Configuration File

Create a `.codetective.yaml` file in your project root or home directory:

```yaml
# Agent configuration
semgrep_enabled: true
trivy_enabled: true
ai_review_enabled: true

# Timeout settings
default_timeout: 300
agent_timeout: 120

# Ollama configuration
ollama_base_url: "http://localhost:11434"
ollama_model: "codellama"

# File handling
max_file_size: 10485760  # 10MB
backup_files: true

# Output configuration
output_format: "json"
verbose: false
```

### Environment Variables

All configuration options can be set via environment variables with the `CODETECTIVE_` prefix:

```bash
export CODETECTIVE_SEMGREP_ENABLED=true
export CODETECTIVE_TRIVY_ENABLED=true
export CODETECTIVE_AI_REVIEW_ENABLED=true
export CODETECTIVE_DEFAULT_TIMEOUT=300
export CODETECTIVE_OLLAMA_BASE_URL="http://localhost:11434"
export CODETECTIVE_OLLAMA_MODEL="codellama"
```

## Web GUI Usage

The Streamlit GUI provides three main pages:

### 1. Project Selection
- Enter or browse to your project path
- Select which agents to run
- Configure scan timeout
- Start the scanning process

### 2. Scan Results
- View results in tabbed interface (one tab per agent)
- See detailed issue information
- Select issues for fixing
- Export results

### 3. Fix Application
- Choose fix strategy (edit or comment)
- Configure backup options
- Apply fixes with progress tracking
- View fix results and modified files

## JSON Output Format

Codetective always outputs results in a standardized JSON format:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "scan_path": "/path/to/project",
  "semgrep_results": [
    {
      "id": "semgrep-rule-file-line",
      "title": "Issue title",
      "description": "Detailed description",
      "severity": "high",
      "file_path": "/path/to/file.py",
      "line_number": 42,
      "rule_id": "rule.id",
      "fix_suggestion": "Suggested fix",
      "status": "detected"
    }
  ],
  "trivy_results": [...],
  "ai_review_results": [...],
  "total_issues": 15,
  "scan_duration": 45.2
}
```

## Agent Types

### Scan Agents

- **SemGrep Agent**: Static analysis using SemGrep rules
- **Trivy Agent**: Security vulnerability and misconfiguration scanning
- **AI Review Agent**: Intelligent code review using Ollama

### Output Agents

- **Comment Agent**: Generates explanatory comments for issues
- **Edit Agent**: Automatically applies code fixes

## Development

### Setting up Development Environment

```bash
# Clone and install in development mode
git clone https://github.com/codetective/codetective.git
cd codetective
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black codetective/
isort codetective/

# Type checking
mypy codetective/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=codetective

# Run specific test file
pytest tests/test_agents.py
```

## Architecture

Codetective uses a multi-agent architecture orchestrated by LangGraph:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI/GUI       │    │   Orchestrator   │    │   Config        │
│   Interface     │───▶│   (LangGraph)    │◀───│   Management    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │ Scan Agents  │ │Output Agents│ │   Utils    │
        │              │ │             │ │            │
        │ • SemGrep    │ │ • Comment   │ │ • File I/O │
        │ • Trivy      │ │ • Edit      │ │ • Validation│
        │ • AI Review  │ │             │ │ • System   │
        └──────────────┘ └─────────────┘ └────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 Documentation: [GitHub Wiki](https://github.com/codetective/codetective/wiki)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/codetective/codetective/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/codetective/codetective/discussions)

## Acknowledgments

- [SemGrep](https://semgrep.dev/) for static analysis capabilities
- [Trivy](https://trivy.dev/) for security vulnerability scanning
- [Ollama](https://ollama.ai/) for local AI model serving
- [LangGraph](https://langchain-ai.github.io/langgraph/) for agent orchestration
- [Streamlit](https://streamlit.io/) for the web interface
