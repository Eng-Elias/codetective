# Codetective - Multi-Agent Code Review Tool
# Makefile for development, testing, and deployment

.PHONY: help install install-dev version setup-tools format lint security-check update-dev-deps clean clean-win build build-win check check-win upload-test upload-test-win upload upload-win prepare-release prepare-release-win beta-release beta-release-win production-release production-release-win git-tag-version git-push-tags

# Default target
help:
	@echo "Codetective - Multi-Agent Code Review Tool"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install         - Install package in production mode"
	@echo "  install-dev     - Install package in development mode with dev dependencies"
	@echo "  setup-tools     - Install external tools (SemGrep, instructions for Trivy/Ollama)"
	@echo ""
	@echo "Development:"
	@echo "  format          - Format code (black, isort)"
	@echo "  lint            - Run linting (flake8, mypy)"
	@echo "  security-check  - Run security checks (bandit)"
	@echo "  update-dev-deps - Update development dependencies"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  clean           - Clean build artifacts (Unix/Linux)"
	@echo "  clean-win       - Clean build artifacts (Windows)"
	@echo "  build           - Build package for distribution (Unix/Linux)"
	@echo "  build-win       - Build package for distribution (Windows)"
	@echo "  check           - Check package before upload (Unix/Linux)"
	@echo "  check-win       - Check package before upload (Windows)"
	@echo "  upload-test     - Upload to TestPyPI (Unix/Linux)"
	@echo "  upload-test-win - Upload to TestPyPI (Windows)"
	@echo "  upload          - Upload to PyPI production (Unix/Linux)"
	@echo "  upload-win      - Upload to PyPI production (Windows)"
	@echo ""
	@echo "Release Workflows:"
	@echo "  prepare-release     - Prepare release (format, lint, clean) (Unix/Linux)"
	@echo "  prepare-release-win - Prepare release (format, lint, clean) (Windows)"
	@echo "  beta-release        - Complete beta release workflow (Unix/Linux)"
	@echo "  beta-release-win    - Complete beta release workflow (Windows)"
	@echo "  production-release     - Complete production release workflow (Unix/Linux)"
	@echo "  production-release-win - Complete production release workflow (Windows)"
	@echo ""
	@echo "Git Helpers:"
	@echo "  git-tag-version - Create git tag for current version"
	@echo "  git-push-tags   - Push tags to remote repository"
	@echo ""
	@echo "Utilities:"
	@echo "  version         - Show current version"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install build twine

# Utility targets
version:
	@python -c "import tomllib; print('Version:', tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"

# Setup targets
setup-tools:
	@echo "Installing external tools..."
	pip install semgrep
	@echo ""
	@echo "Install Trivy for security scanning"
	@echo "  Visit: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
	@echo ""
	@echo "Please install Ollama manually:"
	@echo "  1. Visit https://ollama.ai"
	@echo "  2. Download and install for your OS"
	@echo "  3. Run: ollama pull qwen3:4b"
	@echo ""

# Development targets
format:
	black codetective/ --line-length=130
	isort codetective/ --profile=black --line-length=130

lint:
	flake8 codetective/ --max-line-length=130 --ignore=E203,W503
	mypy codetective/

security-check:
	pip install bandit
	bandit -r codetective/ --skip B404,B603,B607

update-dev-deps:
	python -m pip install --upgrade pip setuptools wheel
	pip install --upgrade -e ".[dev]"

# Build and deployment targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .mypy_cache/

clean-win:
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	if exist codetective.egg-info rmdir /s /q codetective.egg-info
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist htmlcov rmdir /s /q htmlcov
	if exist .mypy_cache rmdir /s /q .mypy_cache

build: clean
	python -m build

build-win: clean-win
	python -m build

check: build
	twine check dist/*

check-win: build-win
	twine check dist/*

upload-test: check
	twine upload --repository testpypi dist/*

upload-test-win: check-win
	twine upload --repository testpypi dist/*

upload: check
	twine upload dist/*

upload-win: check-win
	twine upload dist/*

# Release workflow
prepare-release: format lint clean
	@echo "Release preparation complete!"
	@echo "Ready to build and upload"

prepare-release-win: format lint clean-win
	@echo "Release preparation complete!"
	@echo "Ready to build and upload"

beta-release: prepare-release build upload-test
	@echo "Beta release uploaded to TestPyPI"
	@echo "Test with: pip install -i https://test.pypi.org/simple/ codetective"

beta-release-win: prepare-release-win build upload-test-win
	@echo "Beta release uploaded to TestPyPI"
	@echo "Test with: pip install -i https://test.pypi.org/simple/ codetective"

production-release: prepare-release build upload
	@echo "Production release uploaded to PyPI"
	@echo "Install with: pip install codetective"

production-release-win: prepare-release-win build upload-win
	@echo "Production release uploaded to PyPI"
	@echo "Install with: pip install codetective"

# Git workflow helpers
git-tag-version:
	@VERSION=$$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"); \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	echo "Tagged version v$$VERSION"

git-push-tags:
	git push origin --tags
