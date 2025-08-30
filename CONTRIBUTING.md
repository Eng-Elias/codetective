# Contributing to Codetective

Thank you for your interest in contributing to Codetective! This guide will help you get started with contributing to our multi-agent code review tool.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Process](#pull-request-process)
- [Code of Conduct](#code-of-conduct)

## Getting Started

### Prerequisites

- Python 3.10+ (tested up to 3.12)
- Git
- pip (latest version recommended)

### External Tools
- **SemGrep**: For static analysis (`pip install semgrep`)
- **Trivy**: For vulnerability scanning ([installation guide](https://aquasecurity.github.io/trivy/latest/getting-started/installation/))
- **Ollama**: For AI features ([download from ollama.ai](https://ollama.ai))

## Development Setup

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub first
   git clone https://github.com/YOUR_USERNAME/codetective.git
   cd codetective
   ```

2. **Set Up Development Environment**
   ```bash
   # Install in development mode with all dependencies
   make install-dev
   make install
   
   # Install external tools
   make setup-tools
   ```

3. **Set Up Ollama (for AI features)**
   ```bash
   # Install Ollama from https://ollama.ai
   # Pull the recommended model
   ollama pull qwen3:4b
   ```

4. **Verify Setup**
   ```bash
   # Check version
   make version
   
   # Run basic functionality test
   codetective info
   ```

## Development Workflow

### Before Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/issue#<issue-number>-your-feature-name
   # or
   git checkout -b fix/issue#<issue-number>-your-fix-name
   ```

2. **Update Dependencies** (if needed)
   ```bash
   make update-dev-deps
   ```

### During Development

1. **Format Code Regularly**
   ```bash
   make format
   ```

2. **Run Linting**
   ```bash
   make lint
   ```

3. **Run Security Checks**
   ```bash
   make security-check
   ```

4. **Self-Test with Codetective**
   ```bash
   # Scan the codebase with itself
   codetective scan codetective/
   ```

5. **FOCUS Context**
   While using AI IDEs (Windsurf, Cursor, etc.), try to follow the FOCUS context engineering framework as much as possible. (https://github.com/Eng-Elias/FOCUS--Context_Engineering)

### Before Committing

1. **Final Code Quality Check**
   ```bash
   # Run all checks and fix the issues
   make lint
   make security-check
   make format
   ```

2. **Test Your Changes**
   ```bash
   # Test basic functionality
   codetective info
   codetective scan --help
   codetective fix --help
   codetective gui --help
   ```

## Code Standards

### Python Code Style

- **PEP 8** compliance (enforced by flake8)
- **Type hints** throughout the codebase
- **Line length**: Maximum 130 characters
- **Formatting**: Black with line length 130
- **Import sorting**: isort with black profile

### Code Organization

- Follow the existing package structure
- Use proper `__init__.py` files
- Implement proper error handling
- Add docstrings to all public functions and classes

### Naming Conventions

- **Classes**: PascalCase (`CodeDetectiveOrchestrator`)
- **Functions/Methods**: snake_case (`scan_files`)
- **Constants**: UPPER_SNAKE_CASE (`AGENT_TIMEOUT`)
- **Private methods**: Leading underscore (`_parse_results`)

### Type Hints

```python
from typing import Any, Dict, List, Optional

def process_issues(self, issues: List[Issue], **kwargs: Any) -> List[Issue]:
    """Process issues with proper type hints."""
    pass
```

## Testing

### Manual Testing

1. **Basic Functionality**
   ```bash
   # Test CLI commands
   codetective info
   codetective scan codetective/ --agents semgrep,trivy,ai_review
   codetective gui
   ```

2. **Agent Testing**
   ```bash
   # Test individual agents
   codetective scan . --agents semgrep
   codetective scan . --agents trivy
   codetective scan . --agents ai_review
   ```

3. **Fix Testing**
   ```bash
   # Test fix functionality
   codetective scan . -o test_results.json
   
   codetective fix test_results.json
   # OR
   codetective fix test_results.json --agent comment
   ```

### Self-Testing

Always run Codetective on its own codebase:
```bash
codetective scan codetective/ --agents semgrep,trivy,ai_review
```

## Submitting Changes

### DoD (Definition of Done) Checklist

- [ ] Code follows style guidelines (`make format`, `make lint`)
- [ ] Security checks pass (`make security-check`)
- [ ] Self-scan with Codetective passes
- [ ] All new code has type hints
- [ ] Documentation updated if needed
- [ ] Commit messages follow guidelines
- [ ] Branch is up to date with main

## Issue Guidelines

### Reporting Bugs

1. **Search existing issues** first
2. **Include system information**:
   - OS and version
   - Python version
   - Codetective version
   - External tool versions (SemGrep, Trivy, Ollama)
3. **Provide reproduction steps**
4. **Include error messages and logs**

### Feature Requests

1. **Search existing issues** first
2. **Describe the problem** you're trying to solve
3. **Propose a solution** if you have one
4. **Consider implementation complexity**

### Security Issues

For security vulnerabilities, please email the maintainers directly instead of opening a public issue.

## Pull Request Process

### Before Submitting

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Update documentation** if needed

### PR Requirements

1. **Clear description** of changes
2. **Link to related issues**
3. **Screenshots** for UI changes
4. **Breaking changes** clearly marked
5. **All checks passing**

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Manual testing completed
- [ ] Self-scan with Codetective passes
- [ ] All linting and security checks pass

## Related Issues
Fixes #issue-number

## Screenshots (if applicable)
```

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** by reviewers
4. **Approval** required before merge
5. **Squash and merge** preferred

## Development Tips

### Useful Commands

```bash
# Show all available make targets
make help

# Quick development cycle
make format lint security-check

# Version information
make version

# Clean build artifacts
make clean        # Unix/Linux
make clean-win    # Windows
```

## Architecture Overview

### Core Components

- **CLI Interface** (`cli/`): Command-line interface using Click
- **Core Orchestrator** (`core/`): LangGraph-based workflow management
- **Scanning Agents** (`agents/scan/`): SemGrep, Trivy, AI Review
- **Output Agents** (`agents/output/`): Comment, Edit agents
- **GUI Interface** (`gui/`): NiceGUI-based web interface
- **Models** (`models/`): Pydantic data models
- **Utilities** (`utils/`): Helper functions and utilities

### Agent Architecture

All agents inherit from base classes:
- `ScanAgent`: For scanning operations
- `OutputAgent`: For fix/comment operations
- `AIAgent`: For AI-powered agents

## Getting Help

### Documentation
- [README.md](README.md) - Basic usage and installation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment and release process
- [FOCUS_CONTEXT/](FOCUS_CONTEXT/) - Detailed technical documentation, (https://github.com/Eng-Elias/FOCUS--Context_Engineering)

## License

By contributing to Codetective, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Codetective! Your help makes this project better for everyone.
