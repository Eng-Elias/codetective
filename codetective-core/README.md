# 🔍 Codetective Core

**The multi-agent code analysis engine. Designed to run in Docker.**

Welcome to Codetective Core, the heart of the Codetective analysis suite. This package contains all the logic for running multi-agent code reviews, including the Semgrep, Trivy, and AI agents, as well as the CLI and Streamlit-based GUI.

## 🚀 Recommended Usage: `codetective-launcher`

For the best and simplest experience, we strongly recommend using the [`codetective-launcher`](https://github.com/your-repo/codetective-launcher) (link to be updated). The launcher handles all Docker commands for you, providing a seamless way to run analyses.

## Manual Docker Usage

For advanced users or developers who wish to build and run the Docker image manually, follow the instructions below.

### 1. Build the Docker Image

From the `codetective-core` directory (where this `README.md` and the `Dockerfile` are located), run the following command to build the image:

```bash
docker build -t codetective/codetective-core:latest .
```

### 2. Running the GUI

To run the interactive Streamlit GUI, use the following command. This will start the container and map the required port (8501) to your local machine.

```bash
docker run -p 8501:8501 codetective/codetective-core:latest gui
```

Once the container is running, you can access the GUI at [http://localhost:8501](http://localhost:8501).

### 3. Running a CLI Analysis

To run a headless analysis from your command line, you need to mount your project directory into the container. The container expects the project to be mounted at the `/project` path.

```bash
docker run -v /path/to/your/project:/project codetective/codetective-core:latest analyze /project [OPTIONS]
```

**Example:**

Run Semgrep and Trivy on `~/my-app` and save the results to `~/my-app/results.json`:

```bash
docker run -v ~/my-app:/project codetective/codetective-core:latest analyze /project --agents semgrep --agents trivy --output /project/results.json
```

**Note:** Any output paths specified should be relative to the `/project` directory inside the container so that the results are written back to your mounted host directory.


**Multi-Agent Code Review Tool**

Codetective is a powerful, multi-agent code review tool that combines static analysis, security scanning, and AI-powered review to provide comprehensive code quality assessment. Built with Python, LangGraph, and Streamlit, it offers both GUI and CLI interfaces for flexible integration into your development workflow.

## ✨ Features

### 🤖 Multi-Agent Architecture
- **Semgrep Agent**: Static analysis for security and code quality
- **Trivy Agent**: Vulnerability scanning for dependencies and containers
- **AI Review Agent**: Intelligent code analysis using LLMs (OpenAI, Anthropic, Gemini, Ollama, LM Studio)
- **Output Agents**: Generate comments or apply automatic fixes

### 🖥️ Multiple Interfaces
- **GUI**: Beautiful Streamlit web interface
- **CLI**: Powerful command-line interface
- **MCP**: Model Context Protocol support (planned)

### 🔧 Key Capabilities
- Git repository integration
- Intelligent file discovery and filtering
- Parallel agent execution
- Result aggregation and analysis
- Automatic backup creation before code modifications
- Comprehensive logging and error handling
- Configurable analysis workflows

## 🐳 Docker-Based Execution (Recommended)

For the most reliable and portable experience, we recommend running Codetective using its Docker-based workflow. This approach encapsulates all dependencies, including Python, Semgrep, and Trivy, into a single container, eliminating the need for local installations and avoiding version conflicts.

### Prerequisites

- **Docker**: Ensure Docker is installed and the Docker daemon is running.

### Usage

Codetective will automatically build the required Docker image and run the analysis inside a container.

#### GUI Interface

Simply run the `gui` command as usual. Codetective handles the rest.

```bash
codetective gui
```

The Streamlit interface will launch, and when you click "Run Analysis," the entire workflow will execute inside a Docker container.

#### CLI Interface

The CLI workflow is also streamlined. Just run the `analyze` command, and Codetective will manage the Docker execution in the background.

```bash
# Analyze a project using the Docker workflow
codetective cli analyze /path/to/project --agents semgrep trivy
```

The project directory (`/path/to/project`) will be automatically mounted into the container for analysis.

## 🚀 Quick Start (Manual Setup)


### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/codetective.git
cd codetective

# Install dependencies
pip install -e .

# Or install from PyPI (when available)
pip install codetective
```

### Prerequisites

> **Note:** The prerequisites below are for running Codetective directly on your host machine. For a simpler, more portable setup, please see the **[Docker-Based Execution](#-docker-based-execution-recommended)** section.

1. **Python 3.8+**
2. **Semgrep** (for static analysis)
   ```bash
   pip install semgrep
   ```
3. **Trivy** (for security scanning)
   ```bash
   # Install Trivy following official instructions
   # https://aquasecurity.github.io/trivy/latest/getting-started/installation/
   ```
4. **AI Provider API Keys** (optional, for AI review)
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export GEMINI_API_KEY="your-gemini-key"
   ```

### GUI Interface

Launch the Streamlit web interface:

```bash
codetective gui
```

Then navigate through the workflow:
1. 🏠 **Project Setup**: Select your project directory
2. 📁 **File Selection**: Choose files to analyze
3. ⚙️ **Agent Configuration**: Configure analysis agents
4. 🚀 **Execution**: Run the analysis
5. 📊 **Results**: Review findings and export results

### CLI Interface

Analyze a project using the command line:

```bash
# Basic analysis with Semgrep and Trivy
codetective cli analyze /path/to/project --agents semgrep trivy

# Include AI review with specific provider
codetective cli analyze /path/to/project \
  --agents semgrep trivy ai_review \
  --ai-provider openai \
  --ai-model gpt-4

# Custom file patterns and output
codetective cli analyze /path/to/project \
  --agents semgrep trivy \
  --include "*.py" "*.js" \
  --exclude "**/tests/**" \
  --output results.json \
  --format json

# Discover files in a project
codetective cli discover /path/to/project --include "*.py"

# List available agents
codetective cli agents

# Initialize configuration file
codetective cli init-config codetective.json

# Validate configuration
codetective cli validate-config codetective.json
```

## 📋 Configuration

### Configuration File Example

```json
{
  "agents": {
    "semgrep": {
      "enabled": true,
      "timeout": 300,
      "config_type": "auto",
      "severity_filter": ["ERROR", "WARNING"],
      "output_format": "json"
    },
    "trivy": {
      "enabled": true,
      "timeout": 300,
      "scan_types": ["vuln", "secret"],
      "severity_filter": ["CRITICAL", "HIGH"],
      "ignore_unfixed": false
    },
    "ai_review": {
      "enabled": true,
      "provider": "openai",
      "model": "gpt-4",
      "max_tokens": 4000,
      "temperature": 0.1,
      "focus_areas": ["security", "maintainability", "performance"]
    }
  },
  "file_discovery": {
    "include_patterns": ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx"],
    "exclude_patterns": ["**/node_modules/**", "**/venv/**", "**/__pycache__/**"],
    "max_file_size_mb": 10
  }
}
```

### Environment Variables

```bash
# AI Provider API Keys
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key" 
export GEMINI_API_KEY="your-gemini-api-key"

# Logging Configuration
export CODETECTIVE_LOG_LEVEL="INFO"
export CODETECTIVE_LOG_FILE="/path/to/logfile.log"
```

## 🏗️ Architecture

### Multi-Agent Workflow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   File Input    │───▶│  LangGraph       │───▶│   Results       │
│   Selection     │    │  Orchestrator    │    │   Dashboard     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │     Agents       │
                    ├──────────────────┤
                    │ • Semgrep        │
                    │ • Trivy          │
                    │ • AI Review      │
                    │ • Output Comment │
                    │ • Output Update  │
                    └──────────────────┘
```

### Project Structure

```
codetective/
├── src/codetective/
│   ├── agents/              # Analysis agents
│   │   ├── base.py         # Base agent class
│   │   ├── semgrep_agent.py
│   │   ├── trivy_agent.py
│   │   ├── ai_review_agent.py
│   │   ├── output_comment_agent.py
│   │   └── output_update_agent.py
│   ├── models/             # Data models
│   │   ├── workflow_state.py
│   │   ├── agent_results.py
│   │   ├── configuration.py
│   │   └── interface_models.py
│   ├── utils/              # Utility classes
│   │   ├── file_processor.py
│   │   ├── git_repository_manager.py
│   │   ├── configuration_manager.py
│   │   ├── result_aggregator.py
│   │   └── logger.py
│   ├── workflow/           # LangGraph orchestration
│   │   ├── orchestrator.py
│   │   └── graph_builder.py
│   ├── interfaces/         # User interfaces
│   │   ├── gui.py          # Streamlit GUI
│   │   └── cli.py          # Click CLI
│   └── main.py            # Main entry point
├── FOCUS_CONTEXT/         # Project documentation
├── pyproject.toml         # Project configuration
└── README.md             # This file
```

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/codetective.git
cd codetective
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 src/
black src/
mypy src/

# Run GUI in development mode
streamlit run src/codetective/interfaces/gui.py
```

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`
2. Implement the `analyze()` method
3. Add configuration model in `models/configuration.py`
4. Register the agent in the orchestrator
5. Update CLI and GUI interfaces

Example:

```python
from codetective.agents.base import BaseAgent, AnalysisResult
from codetective.models.workflow_state import WorkflowState

class MyCustomAgent(BaseAgent):
    async def analyze(self, state: WorkflowState) -> AnalysisResult:
        # Implement your analysis logic
        return AnalysisResult(success=True, data={})
```

## 📊 Output Formats

### JSON Output
```json
{
  "scan_id": "scan_123",
  "total_findings": 15,
  "semgrep_results": {...},
  "trivy_results": {...},
  "ai_review_results": {...},
  "metadata": {...}
}
```

### Comment Output
- Line-specific comments for code review platforms
- File-level summaries
- Overall analysis summary with recommendations

### Automatic Fixes
- Safe pattern-based fixes from Semgrep
- Import cleanup
- Documentation improvements
- Security warning additions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints throughout
- Implement comprehensive error handling
- Write tests for new features
- Document all public APIs

### Submitting Issues
- Use the issue templates
- Provide minimal reproduction cases
- Include environment details
- Add relevant logs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Semgrep** for powerful static analysis capabilities
- **Trivy** for comprehensive security scanning
- **LangGraph** for workflow orchestration
- **Streamlit** for the beautiful web interface
- **Click** for the CLI framework

## 📞 Support

- 📖 [Documentation](https://codetective.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/yourusername/codetective/issues)
- 💬 [Discussions](https://github.com/yourusername/codetective/discussions)
- 📧 [Email Support](mailto:support@codetective.dev)

---

**Made with ❤️ by the Codetective Team**
