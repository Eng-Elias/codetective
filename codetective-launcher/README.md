# Codetective Launcher

**A lightweight CLI to launch and manage the `codetective-core` Docker container.**

This tool provides a simple and convenient way to run the Codetective multi-agent code analysis tool without needing to manage Docker commands manually. It ensures that the analysis environment is consistent and portable.

## Prerequisites

Before using the launcher, you must have **Docker** installed and running on your system.

- [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)

## Installation

You can install the Codetective Launcher from PyPI:

```bash
pip install codetective
```

## Usage

The launcher provides two main commands: `gui` to launch the interactive web interface and `analyze` to run a headless scan from your terminal.

### Global Options

These options can be used with both the `gui` and `analyze` commands:

- `--image-source [pull|build]`: Choose whether to `pull` the official image from Docker Hub (default) or `build` it from a local source.
- `--core-project-path <PATH>`: If building from a local source (`--image-source=build`), specifies the path to your `codetective-core` project directory. If not provided, it assumes a parallel directory structure (e.g., `../codetective-core`).
- `--docker-host <URL>`: Specify the URL of the Docker daemon API (e.g., `http://localhost:2375`).

### Launching the GUI

To start the Streamlit-based graphical user interface, simply run:

```bash
codetective gui
```

This will pull the latest `codetective/codetective-core` image from Docker Hub and start the container. You can access the GUI at [http://localhost:8501](http://localhost:8501).

To build the GUI from a local source instead:

```bash
codetective --image-source=build --core-project-path /path/to/your/codetective-core gui
```

Press `Ctrl+C` in your terminal to stop the GUI container.

### Running a CLI Analysis

To run a headless analysis on a project directory, use the `analyze` command. You must provide the path to the project you want to scan.

```bash
codetective analyze /path/to/your/project
```

**Analysis Options:**

- `--agents` or `-a`: Specify which analysis agents to run. Can be used multiple times. (e.g., `semgrep`, `trivy`, `ai_review`)
- `--output` or `-o`: Specify a file to save the analysis results.
- `--format` or `-f`: The output format for the results file (`json` or `sarif`).

**Example:**

Run Semgrep and Trivy on a project, building the image from a local source, and saving the results to a JSON file:

```bash
codetective --image-source=build analyze /path/to/your/project --agents semgrep --agents trivy --output results.json --format json
```
