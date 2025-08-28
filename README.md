# 🔍 Codetective - Multi-Agent Code Review Tool

A comprehensive code analysis tool that combines multiple scanning engines (SemGrep, Trivy, AI) with automated fixing capabilities using LangGraph orchestration.

## Features

- **Multi-Agent Scanning**: Combines SemGrep, Trivy, and AI-powered analysis
- **Automated Fixing**: AI-powered code fixes and explanatory comments
- **CLI Interface**: Command-line interface for automation and CI/CD integration
- **Web GUI**: Modern web interface with NiceGUI
- **LangGraph Orchestration**: Intelligent agent coordination and workflow management
- **Smart Comment Generation**: Concise TODO comments under 100 words
- **Intelligent Issue Filtering**: Removes fixed issues from GUI automatically
- **Configurable**: Flexible configuration via files and environment variables

## Installation

### Prerequisites

Before installing Codetective, ensure you have the following tools installed:

1. **Python 3.9+**
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

### 4. Apply Fixes

```bash
# Apply automatic fixes
codetective fix codetective_scan_results.json --agents edit

# Add explanatory comments instead
codetective fix codetective_scan_results.json --agents comment
```

### 5. Launch Web GUI

```bash
# Launch NiceGUI interface (default)
codetective gui

# Custom host and port
codetective gui --host 0.0.0.0 --port 7891
```

Then open your browser to `http://localhost:7891` (NiceGUI)

## CLI Commands

### `codetective info`
Check system compatibility and tool availability.

### `codetective scan [paths]`
Execute multi-agent code scanning.

**Options:**
- `-a, --agents`: Comma-separated agents (semgrep,trivy,ai_review)
- `-t, --timeout`: Timeout in seconds (default: 900)
- `-o, --output`: Output JSON file (default: codetective_scan_results.json)

**Examples:**
```bash
codetective scan .
codetective scan src/ tests/ --agents semgrep,trivy --timeout 600
codetective scan . --output security_scan.json
# Test with included vulnerable samples
codetective scan vulnerable_code_samples.py --agents semgrep,trivy
```

### `codetective fix <json_file>`
Apply automated fixes to identified issues.

**Options:**
- `-a, --agents`: Fix agents (comment,edit) (default: edit)
- `--keep-backup`: Keep backup files after fix completion
- `--selected-issues`: Comma-separated list of issue IDs to fix

**Examples:**
```bash
codetective fix scan_results.json
codetective fix scan_results.json --agents comment
codetective fix scan_results.json --keep-backup --selected-issues issue-1,issue-2
```

### `codetective gui`
Launch web interface.

**Options:**
- `--host`: Host to run on (default: localhost)
- `--port`: Port to run on (default: 7891 for NiceGUI)



## Web GUI Usage

Codetective offers a modern web interface:

### NiceGUI Interface (Default)
A modern, responsive web interface with better state management and real-time updates.

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
- Configure backup options and keep-backup settings
- Select specific issues to fix or use "Select All"
- Apply fixes with progress tracking and button state management
- View fix results and modified files
- Fixed issues are automatically removed from the GUI
- Real-time progress updates with disabled button during operations

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

- **Comment Agent**: Generates concise TODO comments (under 100 words) for issues
  - Handles None/empty line numbers by adding comments at file beginning
  - Processes multiple issues in same file with proper line number tracking
  - Ignores existing comments when generating new explanations
- **Edit Agent**: Automatically applies code fixes
  - Focuses only on actual security vulnerabilities, not influenced by existing comments
  - Maintains original code structure and functionality

## Testing Codetective

### Vulnerable Code Samples

The repository includes `vulnerable_code_samples.py` - a comprehensive test file containing intentionally vulnerable code patterns that demonstrate Codetective's detection capabilities:

- **Hardcoded Secrets**: AWS keys, GitHub tokens, API keys, private keys
- **Injection Vulnerabilities**: SQL injection, command injection
- **Cryptographic Issues**: Weak hashing (MD5), unverified JWT tokens
- **Network Security**: SSL verification bypass, unencrypted connections
- **File Security**: Insecure temp files, overly permissive file permissions
- **Deserialization**: Unsafe pickle and YAML loading

Use this file to:
- Test your Codetective installation
- Verify scanner configurations
- Demonstrate capabilities to stakeholders
- Benchmark detection accuracy

```bash
# Quick test scan
codetective scan vulnerable_code_samples.py

# Test specific agents
codetective scan vulnerable_code_samples.py --agents semgrep
codetective scan vulnerable_code_samples.py --agents trivy
```

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
- [NiceGUI](https://nicegui.io/) for the modern web interface
