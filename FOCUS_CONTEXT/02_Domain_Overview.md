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

## Codebase Navigation

codetective/
├── DEPLOYMENT.md
├── FOCUS_CONTEXT
│   ├── 01_System_and_Interaction.md
│   ├── 02_Domain_Overview.md
│   ├── 03_Standards_and_Conventions.md
│   ├── 04_Tasks_and_Workflow.md
│   └── 05_Session.md
├── Makefile
├── README.md
├── codetective
│   ├── __init__.py
│   ├── __main__.py
│   ├── agents
│   │   ├── __init__.py
│   │   ├── ai_base.py
│   │   ├── base.py
│   │   ├── output
│   │   │   ├── __init__.py
│   │   │   ├── comment_agent.py
│   │   │   └── edit_agent.py
│   │   └── scan
│   │       ├── __init__.py
│   │       ├── dynamic_ai_review_agent.py
│   │       ├── semgrep_agent.py
│   │       └── trivy_agent.py
│   ├── cli
│   │   ├── __init__.py
│   │   └── commands.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── orchestrator.py
│   │   └── search.py
│   ├── gui
│   │   ├── __init__.py
│   │   └── nicegui_app.py
│   ├── models
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── utils
│       ├── __init__.py
│       ├── file_utils.py
│       ├── git_utils.py
│       ├── process_utils.py
│       ├── prompt_builder.py
│       ├── string_utils.py
│       └── system_utils.py
├── pyproject.toml
└── requirements.txt
