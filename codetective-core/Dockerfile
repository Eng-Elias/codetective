# Use a specific, stable Python version
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for Trivy and other tools
RUN apt-get update && apt-get install -y \
    wget \
    apt-transport-https \
    gnupg \
    lsb-release \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Trivy
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add - && \
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | tee -a /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y trivy

# Set up the working directory
WORKDIR /app

# Copy the application source code
COPY ./src /app/src
COPY pyproject.toml README.md /app/

# Install Python dependencies, including Semgrep
# Pinning versions for reproducibility
RUN pip install --no-cache-dir \
    "langgraph==0.6.3" \
    "streamlit==1.48.0" \
    "click==8.1.8" \
    "typer==0.16.0" \
    "semgrep==1.131.0" \
    "openai==1.99.1" \
    "anthropic==0.61.0" \
    "google-genai==1.28.0" \
    "requests==2.32.4" \
    "pydantic==2.11.7" \
    "dataclasses-json==0.6.7" \
    "pyyaml==6.0.2" \
    "jsonschema==4.25.0" \
    "rich==13.5.3" \
    "loguru==0.7.3" \
    "typing-extensions==4.14.1" \
    "pathlib2==2.3.7.post1"

# Install the codetective package itself in editable mode
RUN pip install -e .

# Create a directory for the project to be analyzed
RUN mkdir /project

# Expose the Streamlit port
EXPOSE 8501

# Set the entrypoint
ENTRYPOINT ["codetective"]
