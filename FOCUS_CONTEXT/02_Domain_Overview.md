# Domain Overview

## Project Domain

**Automated Code Security and Quality Analysis**

Codetective operates in the domain of automated code review, combining static analysis, vulnerability detection, and AI-powered code assessment to provide comprehensive code quality assurance.

## Key Concepts

### Static Code Analysis
- **Pattern Matching**: Identifying code patterns that may indicate security vulnerabilities or quality issues
- **Rule-Based Scanning**: Using predefined rulesets to detect common programming mistakes
- **Security Vulnerability Detection**: Finding potential security flaws in source code

### AI-Powered Code Review
- **Intelligent Analysis**: Using large language models to understand code context and semantics
- **Automated Suggestions**: Generating human-readable explanations and fix recommendations
- **Context-Aware Fixes**: Applying fixes that consider the broader codebase context

## Agent Types

### Scan Agents
- **SemGrep Agent**: Executes SemGrep static analysis rules
- **Trivy Agent**: Performs security vulnerability scanning
- **AI Review Agent**: Conducts intelligent code review using Ollama

### Output Agents
- **Comment Agent**: Generates explanatory comments for identified issues
- **Edit Agent**: Automatically applies code fixes and improvements

## Workflow

```
Scan Phase: Multiple agents analyze code simultaneously
    ↓
Analyze Phase: Results are aggregated and prioritized
    ↓
Fix Phase: Automated remediation is applied based on user selection
```

## Target Users

- **Developers**: Individual developers seeking code quality improvements
- **DevOps Engineers**: Teams integrating automated code review into CI/CD pipelines
- **Security Teams**: Security professionals conducting code security assessments
- **Code Reviewers**: Team leads and senior developers performing code reviews

## Production Architecture (Module 3 Enhancement)

### New Components for Production Readiness

#### Security Layer (`codetective/security/`)
- **input_validator.py**: Path validation, file size limits, type validation
- **prompt_guard.py**: Prompt injection detection and sanitization
- **output_filter.py**: Sensitive data filtering, output validation
- **rate_limiter.py**: API rate limiting, resource usage controls

#### Multi-LLM Support (`codetective/llm/`)
- **base_provider.py**: Abstract LLM interface
- **ollama_provider.py**: Ollama integration (existing, refactored)
- **gemini_provider.py**: Google Gemini integration
- **grok_provider.py**: xAI Grok integration

#### Resilience Layer (`codetective/resilience/`)
- **retry_policy.py**: Exponential backoff, circuit breakers
- **timeout_handler.py**: Advanced timeout management
- **fallback_strategies.py**: Graceful degradation logic

#### Monitoring & Observability (`codetective/monitoring/`)
- **logger.py**: Structured JSON logging with rotation
- **metrics.py**: Performance metrics, resource tracking
- **health.py**: System health checks

#### Testing Infrastructure (`tests/`)
- **unit/**: Unit tests for all components (70%+ coverage)
- **integration/**: Integration tests for workflows
- **e2e/**: End-to-end user journey tests
- **fixtures/**: Test data and mock objects
- **conftest.py**: Shared test configuration

## Codebase Navigation

codetective/
├── DEPLOYMENT.md
├── FOCUS_CONTEXT/
│   ├── 01_System_and_Interaction.md
│   ├── 02_Domain_Overview.md
│   ├── 03_Standards_and_Conventions.md
│   ├── 04_Tasks_and_Workflow.md
│   └── 05_Session.md
├── Makefile
├── README.md
├── pytest.ini (NEW)
├── .coveragerc (NEW)
├── docs/ (NEW)
│   ├── ARCHITECTURE.md
│   ├── TROUBLESHOOTING.md
│   ├── OPERATIONS.md
│   └── api/
├── codetective/
│   ├── __init__.py
│   ├── __main__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ai_base.py
│   │   ├── base.py
│   │   ├── output/
│   │   │   ├── __init__.py
│   │   │   ├── comment_agent.py
│   │   │   └── edit_agent.py
│   │   └── scan/
│   │       ├── __init__.py
│   │       ├── dynamic_ai_review_agent.py
│   │       ├── semgrep_agent.py
│   │       └── trivy_agent.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── orchestrator.py
│   │   └── search.py
│   ├── gui/
│   │   ├── __init__.py
│   │   └── nicegui_app.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── llm/ (NEW - Multi-LLM Support)
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── ollama_provider.py
│   │   ├── gemini_provider.py
│   │   └── grok_provider.py
│   ├── security/ (NEW - Safety Guardrails)
│   │   ├── __init__.py
│   │   ├── input_validator.py
│   │   ├── prompt_guard.py
│   │   ├── output_filter.py
│   │   └── rate_limiter.py
│   ├── resilience/ (NEW - Reliability)
│   │   ├── __init__.py
│   │   ├── retry_policy.py
│   │   ├── timeout_handler.py
│   │   └── fallback_strategies.py
│   ├── monitoring/ (NEW - Observability)
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   └── health.py
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       ├── git_utils.py
│       ├── process_utils.py
│       ├── prompt_builder.py
│       ├── string_utils.py
│       └── system_utils.py
├── tests/ (NEW - Comprehensive Testing)
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_agents.py
│   │   ├── test_orchestrator.py
│   │   ├── test_security.py
│   │   └── test_utils.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_scan_workflow.py
│   │   └── test_fix_workflow.py
│   └── e2e/
│       ├── __init__.py
│       └── test_complete_journey.py
├── pyproject.toml
└── requirements.txt
