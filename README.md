# Codetective: AI-Powered Code Review Co-pilot

[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

Codetective is a powerful, multi-agent code analysis and review tool designed to act as an AI co-pilot for developers. It automates code reviews by leveraging static analysis tools, security scanners, and Large Language Models (LLMs) to identify bugs, vulnerabilities, and quality issues in your codebase.

## Key Features

- **Multi-Agent Architecture**: Uses a flexible workflow powered by LangGraph to orchestrate specialized agents for different analysis tasks.
- **Comprehensive Analysis**: Integrates best-in-class tools like **Semgrep** for static analysis and **Trivy** for security scanning.
- **AI-Powered Insights**: An **AI Review Agent** uses LLMs to provide deeper, context-aware code analysis and suggestions.
- **Multiple Interfaces**: Interact with Codetective through a user-friendly **Streamlit GUI** or a powerful **Command-Line Interface (CLI)**.
- **Flexible Output**: Generates review results as code comments or applies changes directly to your files.
- **Dockerized Core**: The core analysis engine is containerized for consistent and portable execution.

## Architecture Overview

Codetective is composed of two main packages:

1.  **`codetective-launcher`**: A lightweight command-line utility responsible for starting and managing the core analysis engine. It handles Docker image builds/pulls and container lifecycle.
2.  **`codetective-core`**: The main application, containerized in Docker. It contains the multi-agent workflow, all analysis tools, and the user interfaces (GUI and CLI).

This separation ensures that the host system only needs the launcher, while the complex dependencies of the core engine are neatly encapsulated in a Docker container.

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Python 3.9+](https://www.python.org/downloads/)
- An environment variable `OPENAI_API_KEY` (or other LLM provider key) set with your API key.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/codetective.git
    cd codetective
    ```

2.  **Install the launcher:**
    The launcher is the main entrypoint for the application.
    ```bash
    pip install ./codetective-launcher
    ```

### Usage

#### GUI Mode

To launch the user-friendly Streamlit interface, run:

```bash
codetective gui
```

This will start the `codetective-core` container and open the GUI in your web browser. From there, you can select a project, choose files to analyze, and configure the agent workflow.

#### CLI Mode

To run an analysis directly from the command line:

```bash
codetective run --path /path/to/your/project --image-source build
```

- `--path`: The absolute path to the code repository you want to analyze.
- `--image-source`: Choose how to get the core engine's Docker image. Use `build` to build it locally or `pull` to fetch it from a container registry.

## Configuration

Codetective can be configured via a `config.yaml` file placed in your project's root directory. You can also set environment variables prefixed with `CODETECTIVE_` to override default settings.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss proposed changes.

## License

This application is open-source and is released under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See the [LICENSE](LICENSE) file for details.

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
