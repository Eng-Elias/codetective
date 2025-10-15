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

## Security Architecture

### Security Modules
- **InputValidator**: Path validation, file size/type limits, command injection prevention
- **PromptGuard**: Prompt injection detection (20+ patterns), content sanitization
- **OutputFilter**: Malicious code detection, dangerous function blocking, output validation

### Security Integration Points
- **FileUtils**: Optional strict validation with `validate_paths(base_dir=...)`
- **AIAgent**: Automatic INPUT validation (PromptGuard) and OUTPUT sanitization (OutputFilter) in `call_ai()`
- **EditAgent**: Validates generated code fixes with OutputFilter before applying
- **CLI & Orchestrator**: Sanitizes scan results before saving to files
- **Complete**: All security modules fully integrated and tested

## Production Architecture (Current State)

### Implemented Components

#### Security Layer (`codetective/security/`) ✅ COMPLETE
- ✅ **input_validator.py**: Path validation, file size/type limits, command injection prevention (65 tests)
- ✅ **prompt_guard.py**: INPUT validation - prompt injection detection (20+ patterns), input sanitization (27 tests)
- ✅ **output_filter.py**: OUTPUT validation - malicious code detection, dangerous function blocking (43 tests)
- ✅ **Security Refactoring**: Clear separation between INPUT (PromptGuard) and OUTPUT (OutputFilter) validation
- ✅ **Integration**: Fully integrated into AIAgent, EditAgent, CLI, and Orchestrator
- ✅ **Coverage**: 160+ security tests, 96%+ coverage on security modules

#### Testing Infrastructure (`tests/`) ✅ COMPLETE
- ✅ **unit/**: 25+ test files covering all components
- ✅ **integration/**: Placeholder for future workflow tests
- ✅ **e2e/**: Placeholder for future end-to-end tests
- ✅ **conftest.py**: 40+ shared fixtures for testing
- ✅ **Coverage**: 76.03% total coverage (412 tests passing)
- ✅ **pytest.ini**: Configured with markers and coverage settings
- ✅ **.coveragerc**: Coverage exclusions and reporting configuration

#### Documentation (`docs/`) ✅ COMPLETE
- ✅ **ARCHITECTURE.md**: Complete system design, agent details, data flows
- ✅ **SECURITY.md**: Threat model, security controls, defense-in-depth
- ✅ **OPERATIONS.md**: Production deployment, monitoring, maintenance
- ✅ **TROUBLESHOOTING.md**: Common issues, solutions, debugging guides

### Planned/Future Components (Not Yet Implemented)

#### Multi-LLM Support (`codetective/llm/`) - FUTURE
- **base_provider.py**: Abstract LLM interface
- **ollama_provider.py**: Ollama integration (current implementation in AIAgent)
- **gemini_provider.py**: Google Gemini integration
- **grok_provider.py**: xAI Grok integration

#### Resilience Layer (`codetective/resilience/`) - FUTURE
- **retry_policy.py**: Exponential backoff, circuit breakers
- **timeout_handler.py**: Advanced timeout management (basic timeout exists in process_utils)
- **fallback_strategies.py**: Graceful degradation logic

#### Monitoring & Observability (`codetective/monitoring/`) - FUTURE
- **logger.py**: Structured JSON logging (currently using print statements)
- **metrics.py**: Performance metrics, resource tracking
- **health.py**: System health checks

## Codebase Navigation

codetective/
├── CONTRIBUTING.md                # Development guide (will consolidate with CONTRIBUTING_ENHANCED.md)
├── CONTRIBUTING_ENHANCED.md       # Enhanced dev guide (TO BE MERGED INTO CONTRIBUTING.md)
├── FOCUS_CONTEXT/                 # AI context engineering
│   ├── 01_System_and_Interaction.md
│   ├── 02_Domain_Overview.md
│   ├── 03_Standards_and_Conventions.md
│   ├── 04_Tasks_and_Workflow.md
│   └── 05_Session.md
├── LICENSE
├── Makefile
├── README.md                      # Main documentation (will consolidate with README_ENHANCED.md)
├── README_ENHANCED.md             # Enhanced README (TO BE MERGED INTO README.md)
├── pytest.ini                     # Test configuration
├── .coveragerc                    # Coverage configuration
├── pyproject.toml                 # Package configuration
├── requirements.txt               # Dependencies
├── docs/                          # Technical documentation
│   ├── ARCHITECTURE.md            # ✅ System design, agent details
│   ├── DEPLOYMENT.md              # ✅ PyPI deployment guide (TO BE MOVED HERE)
│   ├── OPERATIONS.md              # ✅ Production operations
│   ├── SECURITY.md                # ✅ Security architecture
│   ├── TROUBLESHOOTING.md         # ✅ Common issues
│   ├── OUTPUT_FILTER_INTEGRATION.md      # ✅ (TO BE MOVED HERE)
│   ├── PHASE_2_SECURITY_SUMMARY.md       # ✅ (TO BE MOVED HERE)
│   ├── PHASE_3_PROGRESS.md               # ✅ (TO BE MOVED HERE)
│   ├── SECURITY_REFACTORING_SUMMARY.md   # ✅ (TO BE MOVED HERE)
│   ├── SESSION_SUMMARY.md                # ✅ (TO BE MOVED HERE)
│   └── NEXT_PHASE_OPTIONS.md             # ✅ (TO BE MOVED HERE)
├── codetective/                   # Source code
│   ├── __init__.py
│   ├── __main__.py
│   ├── agents/                    # Agent implementations
│   │   ├── __init__.py
│   │   ├── ai_base.py             # ✅ Base class for AI-powered agents
│   │   ├── base.py                # ✅ Base classes (ScanAgent, OutputAgent)
│   │   ├── output/
│   │   │   ├── __init__.py
│   │   │   ├── comment_agent.py   # ✅ Generate explanatory comments
│   │   │   └── edit_agent.py      # ✅ Apply automated fixes
│   │   └── scan/
│   │       ├── __init__.py
│   │       ├── dynamic_ai_review_agent.py  # ✅ AI-powered code review
│   │       ├── semgrep_agent.py   # ✅ Static analysis
│   │       └── trivy_agent.py     # ✅ Vulnerability scanning
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py            # ✅ CLI commands (scan, fix, gui, info)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # ✅ Configuration management
│   │   ├── orchestrator.py        # ✅ LangGraph-based workflow
│   │   └── search.py              # ✅ Code search utilities
│   ├── gui/
│   │   ├── __init__.py
│   │   └── nicegui_app.py         # ✅ Web interface
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # ✅ Pydantic data models
│   ├── security/                  # ✅ Security guardrails
│   │   ├── __init__.py
│   │   ├── input_validator.py     # ✅ Path validation, file limits
│   │   ├── prompt_guard.py        # ✅ INPUT validation (prompt injection)
│   │   └── output_filter.py       # ✅ OUTPUT validation (malicious code)
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── file_utils.py          # ✅ File operations, .gitignore
│       ├── git_utils.py           # ✅ Git integration
│       ├── process_utils.py       # ✅ Command execution
│       ├── prompt_builder.py      # ✅ Prompt construction
│       ├── string_utils.py        # ✅ String manipulation
│       └── system_utils.py        # ✅ System checks
├── tests/                         # ✅ Test suite (76%+ coverage)
│   ├── __init__.py
│   ├── conftest.py                # ✅ Shared fixtures (40+)
│   ├── unit/                      # ✅ 25+ test files, 412 tests
│   │   ├── __init__.py
│   │   ├── test_ai_base.py
│   │   ├── test_base_agent.py
│   │   ├── test_config.py
│   │   ├── test_file_utils.py
│   │   ├── test_git_utils.py
│   │   ├── test_input_validator.py
│   │   ├── test_orchestrator.py
│   │   ├── test_output_agents.py
│   │   ├── test_output_filter.py
│   │   ├── test_process_utils.py
│   │   ├── test_prompt_builder.py
│   │   ├── test_prompt_guard.py
│   │   ├── test_schemas.py
│   │   ├── test_semgrep_agent.py
│   │   ├── test_string_utils.py
│   │   ├── test_system_utils.py
│   │   ├── test_trivy_agent.py
│   │   └── ...
│   ├── integration/                # Placeholder for future tests
│   │   └── __init__.py
│   └── e2e/                        # Placeholder for future tests
│       └── __init__.py
└── screenshots/                    # Project screenshots
    ├── Brand/
    ├── CLI/
    └── GUI/
