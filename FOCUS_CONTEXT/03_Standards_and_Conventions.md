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
