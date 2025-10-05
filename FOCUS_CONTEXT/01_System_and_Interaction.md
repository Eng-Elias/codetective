# System and Interaction

## System Overview

**Codetective** is a multi-agent code review tool that combines multiple code analysis engines with automated fixing capabilities.

### Core Components
- **LangGraph Orchestration**: Manages agent workflow and coordination
- **Multiple Scanning Agents**: SemGrep, Trivy, AI Review agents
- **Fixing Agents**: Comment and Edit agents for automated remediation
- **CLI Interface**: Command-line interface using Click framework
- **GUI Interface**: NiceGUI-based web interface
- **Git Integration**: Smart file selection respecting .gitignore and git-tracked files
- **Unified AI Integration**: All AI agents use consistent ChatOllama integration via AIAgent base class

### Production Components (Module 3 Enhancements)
- **Multi-LLM Support**: Abstract provider interface supporting Ollama, Gemini, Grok
- **Security Layer**: Input validation, prompt injection protection, output filtering, rate limiting
- **Resilience Layer**: Retry policies, circuit breakers, timeout handling, fallback strategies
- **Monitoring & Observability**: Structured logging, performance metrics, health checks
- **Testing Infrastructure**: Comprehensive unit, integration, and e2e test suites (70%+ coverage)

### External Dependencies
- **SemGrep**: Static analysis security scanner
- **Trivy**: Vulnerability scanner for containers and code
- **Ollama**: Local AI model server for intelligent code review

## Interactions

### CLI Commands
- `codetective --version`: Show version information
- `codetective --help`: Show help message
- `codetective info`: System compatibility and tool availability check
- `codetective health` **(NEW - Module 3)**: Comprehensive health check with metrics
  - Check tool availability (SemGrep, Trivy, LLM services)
  - Monitor system resources (CPU, memory, disk)
  - Verify LLM provider connectivity
  - Report component status and health metrics
- `codetective scan [paths]`: Execute multi-agent code scanning
  - `-a or --agents`: Select agents to run as comma-separated list (default: semgrep,trivy)
  - `-t or --timeout`: Timeout in seconds (default: 900)
  - `-o or --output`: Output JSON file (default: codetective_scan_results.json)
  - `--llm-provider` **(NEW)**: LLM provider selection (ollama, gemini, grok)
  - `--ollama-url`: Custom Ollama server URL (default: http://localhost:11434)
  - `--ollama-model`: Custom AI model (default: qwen3:4b)
  - `--gemini-api-key` **(NEW)**: Google Gemini API key
  - `--gemini-model` **(NEW)**: Gemini model name
  - `--grok-api-key` **(NEW)**: xAI Grok API key
  - `--grok-model` **(NEW)**: Grok model name
  - `--parallel`: Enable parallel agent execution
  - `--diff-only`: Scan only git diff files
  - `--force-ai`: Force AI review for large codebases
  - `--show-output`: Show agent output in terminal instead of JSON file
  - `--max-files`: Maximum number of files to scan
  - `--log-level` **(NEW)**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `--metrics` **(NEW)**: Export metrics to file
- `codetective fix <json_file>`: Apply automated fixes to identified issues
  - `-a or --agent`: Select agent to run (default: edit)
  - `--keep-backup`: Keep backup files after fix completion
  - `--llm-provider` **(NEW)**: LLM provider selection
  - `--ollama-url`: Custom Ollama server URL
  - `--ollama-model`: Custom AI model
  - `--log-level` **(NEW)**: Logging level
- `codetective gui`: Launch NiceGUI web interface
  - Multi-LLM provider selection in UI **(NEW)**
  - Real-time health monitoring dashboard **(NEW)**
  - Enhanced error reporting with troubleshooting links **(NEW)**

### PyPI Distribution
- **Package Name**: `codetective`
- **Installation**: `pip install codetective`
- **Python Support**: 3.10-3.12

### File System Operations
- **Input**: Source code files and directories
- **Output**: JSON results files with standardized format
- **Processing**: Temporary files for agent communication
- **Git Integration**: Respects .gitignore patterns and tracks git-managed files

### Input/Output Flow
```
Source Code Files → Git-Aware Selection → Multi-Agent Scanning (Sequential or Parallel) → JSON Results → AI-Powered Fix Generation (Comment or Edit) → Updated Code Files
```

### Configuration Management
- **Ollama Integration**: Configurable base URL and model selection
- **Agent Selection**: Flexible agent combination (SemGrep, Trivy, AI Review)
- **Execution Modes**: Sequential or parallel agent execution
- **File Filtering**: Git-aware file selection with .gitignore support
