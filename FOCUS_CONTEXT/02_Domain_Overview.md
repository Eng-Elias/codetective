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
