# CLI Interface Feature Specification

## Overview
Implement a command-line interface for codetective that supports CI/CD integration and automated code review workflows.

## Feature Description
The CLI provides a scriptable interface for running code analysis in automated environments, with support for configuration files, batch processing, and various output formats.

## Technical Requirements

### Core CLI Architecture

#### Command Structure
```python
class CodetectiveCLI:
    """Main CLI application using Click framework"""
    
    @click.group()
    @click.option('--config', '-c', help='Configuration file path')
    @click.option('--verbose', '-v', is_flag=True, help='Verbose output')
    @click.option('--quiet', '-q', is_flag=True, help='Quiet mode')
    def main(config: str, verbose: bool, quiet: bool):
        """Codetective multi-agent code review tool"""
        pass
    
    @main.command()
    @click.argument('project_path', type=click.Path(exists=True))
    @click.option('--agents', '-a', multiple=True, help='Agents to run')
    @click.option('--output', '-o', help='Output file path')
    @click.option('--format', '-f', type=click.Choice(['json', 'yaml', 'text', 'sarif']))
    def scan(project_path: str, agents: List[str], output: str, format: str):
        """Run code analysis on project"""
        pass
```

### Command Categories

#### 1. Analysis Commands
- **`scan`**: Primary analysis command with agent selection
- **`quick-scan`**: Fast analysis with predefined agent subset
- **`security-scan`**: Security-focused analysis (Trivy + Semgrep security rules)
- **`quality-scan`**: Code quality analysis (Semgrep + AI review)

#### 2. Configuration Commands
- **`config init`**: Initialize configuration file
- **`config validate`**: Validate configuration file
- **`config show`**: Display current configuration
- **`config set`**: Update configuration values

#### 3. Agent Management Commands
- **`agents list`**: List available agents and their status
- **`agents info`**: Show detailed agent information
- **`agents test`**: Test agent connectivity and configuration

#### 4. Output Commands
- **`apply-fixes`**: Apply suggested fixes from previous analysis
- **`generate-comments`**: Generate code comments for issues
- **`export-report`**: Export analysis results in various formats

## Configuration System

### Configuration File Structure
```yaml
# codetective.yaml
project:
  name: "my-project"
  path: "."
  exclude_patterns:
    - "*.test.py"
    - "node_modules/"
    - ".git/"

agents:
  semgrep:
    enabled: true
    rules:
      - "auto"
      - "security"
    custom_rules_path: ".semgrep/"
    
  trivy:
    enabled: true
    scan_types:
      - "fs"
      - "config"
    severity_threshold: "MEDIUM"
    
  ai_review:
    enabled: true
    model: "gpt-4"
    focus_areas:
      - "performance"
      - "maintainability"
      - "security"

output:
  format: "json"
  file: "codetective-results.json"
  include_fixes: true
  include_context: true

execution:
  mode: "auto"  # auto | interactive
  parallel_agents: true
  timeout_seconds: 300
```

### Environment Variables
```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key

# Ollama
OLLAMA_API_URL=your_ollama_url

# LM Studio
LM_STUDIO_API_URL=your_lm_studio_url

# Configuration
CODE_DETECTIVE_CONFIG_PATH=./codetective.yaml
CODE_DETECTIVE_LOG_LEVEL=INFO
```

## Command Examples

### Basic Usage
```bash
# Quick scan of current directory
codetective scan .

# Scan with specific agents
codetective scan . --agents semgrep,trivy

# Security-focused scan
codetective security-scan . --output security-report.json

# Scan with custom configuration
codetective scan . --config custom-config.yaml
```

### CI/CD Integration
```bash
# Exit with non-zero code if critical issues found
codetective scan . --fail-on critical --format sarif

# Generate fixes and apply them
codetective scan . --output results.json
codetective apply-fixes --input results.json --auto-approve

# Export report for integration
codetective scan . --format json | jq '.findings[] | select(.severity == "HIGH")'
```

### Advanced Usage
```bash
# Interactive mode with human approval
codetective scan . --mode interactive

# Parallel execution with timeout
codetective scan . --parallel --timeout 600

# Custom output formatting
codetective scan . --format text --template custom-template.txt
```

## Output Formats

### JSON Format
```json
{
  "metadata": {
    "timestamp": "2025-07-31T12:49:24Z",
    "project_path": "/path/to/project",
    "agents_executed": ["semgrep", "trivy", "ai_review"],
    "execution_time": 45.2
  },
  "findings": [
    {
      "id": "finding-001",
      "agent": "semgrep",
      "severity": "HIGH",
      "category": "security",
      "file": "src/auth.py",
      "line": 42,
      "message": "SQL injection vulnerability detected",
      "description": "User input is directly concatenated into SQL query",
      "fix_suggestion": "Use parameterized queries",
      "code_context": "query = f\"SELECT * FROM users WHERE id = {user_id}\""
    }
  ],
  "summary": {
    "total_findings": 15,
    "by_severity": {"HIGH": 3, "MEDIUM": 7, "LOW": 5},
    "by_agent": {"semgrep": 8, "trivy": 4, "ai_review": 3}
  }
}
```

### SARIF Format
- Standard format for static analysis results
- Compatible with GitHub Security tab
- Supports code scanning integration

## Acceptance Criteria

### Core Functionality
- [ ] All primary commands work correctly
- [ ] Configuration file loading and validation
- [ ] Multiple output format support
- [ ] Proper exit codes for CI/CD integration
- [ ] Error handling with helpful messages

### CI/CD Integration
- [ ] Non-interactive execution mode
- [ ] Configurable failure thresholds
- [ ] Standard output formats (JSON, SARIF)
- [ ] Environment variable configuration
- [ ] Docker container support

### Performance
- [ ] Reasonable execution time for large projects
- [ ] Parallel agent execution when possible
- [ ] Memory efficient processing
- [ ] Proper cleanup of temporary files

### Usability
- [ ] Comprehensive help documentation
- [ ] Clear error messages and suggestions
- [ ] Progress indicators for long operations
- [ ] Consistent command structure and options

## Implementation Notes
- Use Click framework for command structure
- Implement proper logging with configurable levels
- Support for shell completion
- Comprehensive test coverage for all commands
- Docker image for containerized execution
