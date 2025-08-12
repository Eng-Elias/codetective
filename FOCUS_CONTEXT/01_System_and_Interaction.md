# System and Interaction

## System Overview

**Codetective** is a multi-agent code review tool that combines multiple code analysis engines with automated fixing capabilities.

### Core Components
- **LangGraph Orchestration**: Manages agent workflow and coordination
- **Multiple Scanning Agents**: SemGrep, Trivy, AI Review agents
- **Fixing Agents**: Comment and Edit agents for automated remediation
- **CLI Interface**: Command-line interface using Click framework
- **GUI Interface**: Streamlit-based web interface

### External Dependencies
- **SemGrep**: Static analysis security scanner
- **Trivy**: Vulnerability scanner for containers and code
- **Ollama**: Local AI model server for intelligent code review

## Interactions

### CLI Commands
- `codetective info`: System compatibility and tool availability check
- `codetective scan [paths]`: Execute multi-agent code scanning
- `codetective fix <json_file>`: Apply automated fixes to identified issues
- `codetective gui`: Launch Streamlit web interface

### File System Operations
- **Input**: Source code files and directories
- **Output**: JSON results files with standardized format
- **Processing**: Temporary files for agent communication

### Input/Output Flow
```
Source Code Files → Multi-Agent Scanning → JSON Results → Automated Fixes → Updated Code Files
```
