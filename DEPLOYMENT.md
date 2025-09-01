# Codetective Deployment Guide

This guide covers how to deploy Codetective to PyPI and set up the development environment.

## Prerequisites

### Required Tools
- Python 3.10+ (tested up to 3.12)
- pip (latest version recommended)
- build (`pip install build`)
- twine (`pip install twine`)

### External Dependencies
- **Ollama** (for AI features): Download from [ollama.ai](https://ollama.ai)
- **SemGrep** (optional): `pip install semgrep`
- **Trivy** (optional): Install from [aquasecurity.github.io/trivy](https://aquasecurity.github.io/trivy)

## Development Setup

### 1. Clone and Install Development
```bash
git clone https://github.com/Eng-Elias/codetective.git
cd codetective
make install-dev
make install
```

### 2. Install External Tools
```bash
# Install external tools automatically
make setup-tools

# This will:
# - Install SemGrep via pip
# - Provide instructions for Trivy installation
# - Provide instructions for Ollama setup
```

### 3. Manual Tool Setup
```bash
# Install Ollama (visit https://ollama.ai)
# Pull recommended AI model
ollama pull qwen3:4b
ollama start

# Install Trivy (follow official docs at https://aquasecurity.github.io/trivy/latest/getting-started/installation/)
```

## Development Workflow

### Contribution Guide

Follow the [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

### Pre-Release Process

1. **Run Linting**: `make lint` and fix any issues
2. **Security Check**: `make security-check` and fix any issues
3. **Self-Scan**: Run `codetective scan codetective/` to scan the tool with itself and fix any issues (some issues are accepted like AI use warning, sleep and subprocess)
4. **Format Code**: `make format`
5. **Update Dependencies**: `make update-dev-deps` if needed

## PyPI Deployment

### Beta Release Process

#### Unix/Linux
```bash
# Complete beta release workflow
make beta-release

# Or step by step:
make prepare-release  # format, lint, clean
make build           # build package
make upload-test     # upload to TestPyPI
```

#### Windows
```bash
# Complete beta release workflow
make beta-release-win

# Or step by step:
make prepare-release-win  # format, lint, clean
make build-win           # build package
make upload-test-win     # upload to TestPyPI
```

### Production Release Process

#### Unix/Linux
```bash
# Complete production release workflow
make production-release

# Or step by step:
make prepare-release  # format, lint, clean
make build           # build package
make upload          # upload to PyPI
```

#### Windows
```bash
# Complete production release workflow
make production-release-win

# Or step by step:
make prepare-release-win  # format, lint, clean
make build-win           # build package
make upload-win          # upload to PyPI
```

### Manual Build Steps

1. **Update Version**
   ```bash
   # Version is managed in pyproject.toml
   # Format: X.Y.ZbN (e.g., 0.1.0b1, 0.1.0b2)
   ```

2. **Build Package**
   ```bash
   # Unix/Linux
   make build
   
   # Windows
   make build-win
   ```

3. **Check Package**
   ```bash
   # Unix/Linux
   make check
   
   # Windows
   make check-win
   ```

4. **Upload to TestPyPI**
   ```bash
   # Unix/Linux
   make upload-test
   
   # Windows
   make upload-test-win
   ```

5. **Upload to PyPI (Production)**
   ```bash
   # Unix/Linux
   make upload
   
   # Windows
   make upload-win
   ```

## Git Workflow

### Tagging Releases
```bash
# Create git tag for current version
make git-tag-version

# Push tags to remote
make git-push-tags
```

## Configuration

### PyPI Credentials
Set up your PyPI credentials using one of these methods:

#### Option 1: API Token (Recommended)
```bash
# Create ~/.pypirc
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
```

#### Option 2: Environment Variables
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
```

## Versioning Strategy

### Beta Versions
- Format: `X.Y.ZbN` (e.g., `0.1.0b1`)
- Used for testing and feedback
- May have breaking changes

### Stable Versions
- Format: `X.Y.Z` (e.g., `0.1.0`)
- Production-ready
- Follows semantic versioning

### Version Bumping
```bash
# Beta releases
0.1.0b1 → 0.1.0b2 → 0.1.0b3 → 0.1.0

# Minor releases
0.1.0 → 0.1.1 → 0.1.2

# Major releases
0.1.0 → 0.2.0 → 1.0.0
```

### Getting Help
- GitHub Issues: https://github.com/Eng-Elias/codetective/issues
- Documentation: https://github.com/Eng-Elias/codetective/blob/main/README.md
