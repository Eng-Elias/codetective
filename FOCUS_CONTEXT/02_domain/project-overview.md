# Project Overview

## Business Context
- **Project Name**: `codetective`
- **Project Mission**: Multi-agent code review tool that automates static analysis, security scanning, and AI-powered code improvements with multiple interfaces (GUI/CLI/MCP).
- **Business Goals**: 
  - Automate code quality and security analysis workflows
  - Provide intelligent code improvement suggestions
  - Support multiple interaction modes for different user preferences
  - Integrate seamlessly with existing development workflows
- **Target Audience**: Software developers, DevOps teams, security engineers, and development teams seeking automated code review capabilities.

## Core Functionality
- **Multi-Agent Architecture**:
  - **Semgrep Agent**: Static code analysis for bugs, security issues, and code quality
  - **Trivy Agent**: Security vulnerability scanning and dependency analysis
  - **AI Review Agent**: Intelligent code review with enhancement suggestions
  - **Output Agent (Comments)**: Generates AI-powered comments explaining issues and solutions
  - **Output Agent (Code Updates)**: Automatically applies fixes and improvements to code

- **Key Features**:
  - **GUI Interface**: Streamlit-based web interface for interactive code review
  - **CLI Interface**: Command-line tool for CI/CD integration
  - **MCP Interface**: Model Context Protocol support for AI assistant integration
  - **Git Repository Integration**: Browse and select files from git repositories
  - **Configurable Workflows**: Auto-mode and human-in-the-loop options
  - **Issue Resolution**: Select and apply fixes with different output modes

## Technology Stack
- **Core Framework**: Python 3.8+
- **Agent Orchestration**: LangGraph for multi-agent workflow management
- **GUI Framework**: Streamlit for web-based user interface
- **Static Analysis**: Semgrep for code quality and security analysis
- **Security Scanning**: Trivy for vulnerability detection
- **AI Integration**: OpenAI/Anthropic/Gemini/Ollama/LM_Studio APIs for intelligent code review
- **Version Control**: Git integration for repository management
- **CLI Framework**: Click or Typer for command-line interface
- **MCP Support**: Model Context Protocol for AI assistant integration
