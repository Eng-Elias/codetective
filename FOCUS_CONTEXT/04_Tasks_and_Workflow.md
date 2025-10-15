# Tasks and Workflow

## Current Focus: Documentation Consolidation & Organization

**Status**: Module 3 core requirements COMPLETE - 76% coverage, security integrated, docs written
**Next Step**: Organize documentation structure for professional presentation

### Module 3 Requirements Status
- ✅ **User Interface**: NiceGUI with git-aware file selection, interactive tree selector
- ✅ **Testing Suite**: **76.03% coverage achieved** (exceeds 70% requirement)
- ✅ **Safety & Security Guardrails**: **3 security modules integrated**
- ✅ **Professional Documentation**: **Complete** - ARCHITECTURE, SECURITY, OPERATIONS, TROUBLESHOOTING (36,000+ words)
- 🔄 **Documentation Organization**: Consolidate enhanced versions, move docs to proper folders

## Module 3 Enhancement Tasks

### Phase 1: Testing Infrastructure ✅ COMPLETED!
**Goal**: Achieve 70%+ test coverage for core functionality
**Status**: ✅ COMPLETE - **76.03% Coverage Achieved**

#### Task 1.1: Unit Testing Framework Setup ✅
- ✅ Create `tests/` directory structure with unit, integration, e2e folders
- ✅ Install pytest, pytest-cov, pytest-asyncio, pytest-mock
- ✅ Configure pytest.ini with coverage settings and test markers
- ✅ Create conftest.py with 40+ common fixtures
- ✅ Add Makefile targets for test execution

#### Task 1.2: Agent Unit Tests ✅
- ✅ `tests/unit/test_semgrep_agent.py` - Test pattern matching, rule parsing, result formatting (14 tests)
- ✅ `tests/unit/test_trivy_agent.py` - Test vulnerability detection, JSON parsing, error handling (13 tests)
- [ ] `tests/unit/test_dynamic_ai_review_agent.py` - Mock Ollama, test prompt generation, response parsing
- ✅ `tests/unit/test_output_agents.py` - CommentAgent & EditAgent tests with backup handling (19 tests)
- ✅ `tests/unit/test_ai_base.py` - Test ChatOllama integration, error handling, response cleaning (21 tests)

#### Task 1.3: Core Component Unit Tests ✅
- [ ] `tests/unit/test_orchestrator.py` - Test agent coordination, parallel execution, error aggregation
- ✅ `tests/unit/test_config.py` - Test configuration loading, validation, environment variables (17 tests)
- ✅ `tests/unit/test_schemas.py` - Test Pydantic models, serialization, validation (19 tests)
- ✅ `tests/unit/test_base_agent.py` - Test BaseAgent, ScanAgent, OutputAgent (14 tests)

#### Task 1.4: Utility Unit Tests ✅
- ✅ `tests/unit/test_file_utils.py` - Test file operations, gitignore parsing, path validation (20 tests)
- ✅ `tests/unit/test_git_utils.py` - Mock git commands, test repo detection, file selection (12 tests)
- ✅ `tests/unit/test_process_utils.py` - Test command execution, timeout handling, output capture (14 tests)
- [ ] `tests/unit/test_string_utils.py` - Test string manipulation, sanitization, cleaning
- [ ] `tests/unit/test_system_utils.py` - Test tool availability checks, system compatibility

#### Task 1.4B: Phase 1B Priority Tests (Coverage Push to 70%+) ✅ COMPLETED
**Objective**: Add strategic unit tests to reach 70%+ coverage
**Result**: **72.28% Coverage - Target Exceeded!**

**HIGH-IMPACT TESTS (Big Coverage Gains):**
- ✅ 🔴 **test_orchestrator.py** - COMPLETED
  - ✅ Agent initialization and configuration
  - ✅ LangGraph state management
  - ✅ Parallel vs sequential execution modes
  - ✅ Result aggregation across agents
  - ✅ Error handling and recovery
  - ✅ Agent coordination workflows
  
- [ ] 🟡 **test_dynamic_ai_review_agent.py** - OPTIONAL
  - Code review prompt generation
  - AI response parsing and validation
  - Fallback mode handling
  - Issue extraction from responses
  - Severity mapping and categorization
  - ChatOllama integration mocking

- [ ] 🟡 **Expand test_output_agents.py** - OPTIONAL (58.60% → 75%+, for higher coverage)
  - EditAgent fix validation logic
  - Batch file processing edge cases
  - File write operation error handling
  - Backup restoration scenarios
  - Invalid fix detection

**QUICK WIN TESTS (Small Modules, Easy Coverage):**
- ✅ 🟢 **test_string_utils.py** - COMPLETED (20% → 96%, 30 tests)
  - ✅ String sanitization functions
  - ✅ Code cleaning utilities
  - ✅ Format conversion helpers
  
- ✅ 🟢 **test_system_utils.py** - COMPLETED (38% → 96.63%, 24 tests)
  - ✅ Tool availability detection
  - ✅ Platform-specific checks
  - ✅ Required tools validation
  - ✅ System compatibility checks

**MEDIUM-IMPACT TESTS (Steady Improvements):**
- ✅ 🟢 **Expand test_git_utils.py** - COMPLETED (+17 tests, improved coverage)
  - ✅ Enhanced file selection logic
  - ✅ Tree structure building
  - ✅ Git diff operations
  - ✅ Untracked file handling
  
- ✅ 🟢 **test_prompt_builder.py** - COMPLETED (42% → 100%, 41 tests)
  - ✅ Template rendering
  - ✅ Context variable substitution
  - ✅ Structured prompt generation
  - ✅ Issue formatting


#### Task 1.5: Integration Tests
- [ ] `tests/integration/test_scan_workflow.py` - Test full scan pipeline with real tools
- [ ] `tests/integration/test_fix_workflow.py` - Test complete fix application workflow
- [ ] `tests/integration/test_multi_agent_coordination.py` - Test agent communication and result merging
- [ ] `tests/integration/test_cli_commands.py` - Test CLI command execution and output
- [ ] `tests/integration/test_gui_operations.py` - Test GUI state management and user flows

#### Task 1.6: End-to-End Tests
- [ ] `tests/e2e/test_vulnerable_code_detection.py` - Test detection of real vulnerabilities
- [ ] `tests/e2e/test_automated_fix_application.py` - Test fixing real security issues
- [ ] `tests/e2e/test_git_integration.py` - Test git-aware scanning on real repositories
- [ ] `tests/e2e/test_complete_user_journey.py` - Test scan → review → fix → verify workflow

### Phase 2: Security & Safety Guardrails ✅ COMPLETED!
**Status**: ✅ **COMPLETE** - Production-grade security implemented
**Goal**: Implement comprehensive security for AAIDC Module 3 requirement
**Result**: 3 security modules integrated
**Architecture**: Defense-in-depth with INPUT (PromptGuard), OUTPUT (OutputFilter), and validation layers

#### Task 2.1: Input Validation ✅
- ✅ Created `codetective/security/input_validator.py` (400+ lines)
  - ✅ Path validation (prevent directory traversal)
  - ✅ File size limits (100MB max, prevent memory exhaustion)
  - ✅ File type validation (40+ code extensions whitelist)
  - ✅ JSON schema validation
  - ✅ Command injection prevention
  - ✅ Integrated into FileUtils.validate_paths()
  - ✅ 65 comprehensive tests

#### Task 2.2: Prompt Injection Protection ✅
- ✅ Created `codetective/security/prompt_guard.py` (450+ lines)
  - ✅ 20+ prompt injection patterns detection
  - ✅ Content safety filtering for AI inputs/outputs
  - ✅ Token limit enforcement (32K max, prevent context overflow)
  - ✅ Suspicious code pattern detection
  - ✅ Sensitive data filtering (API keys, passwords, tokens)
  - ✅ Integrated into AIAgent.call_ai()
  - ✅ 50 comprehensive tests

#### Task 2.3: Output Filtering & Safety ✅
- ✅ Created `codetective/security/output_filter.py` (400+ lines)
  - ✅ Filter sensitive information from logs (API keys, tokens, passwords)
  - ✅ Sanitize AI-generated code suggestions
  - ✅ Validate fix outputs (detect malicious patterns)
  - ✅ Content safety checks
  - ✅ Malicious code detection (rm -rf, backdoors, reverse shells)
  - ✅ Dangerous function detection (eval, exec, pickle)
  - ✅ Fix change ratio validation (80% threshold)
  - ✅ 45 comprehensive tests

#### Task 2.4: Rate Limiting & Abuse Prevention ❌ NOT IMPLEMENTED
- ❌ RateLimiter **not implemented** - Not required for local application
  - **Reason**: Codetective is a local desktop app with local Ollama
  - **Decision**: No external APIs = no rate limiting needed
  - **Alternative**: `--max-files` CLI option allows users to limit scan scope
  - **Impact**: Simplified architecture, right-sized security for local app

### Phase 3: Documentation (Priority: HIGH) ✅ COMPLETED!
**Status**: ✅ **COMPLETE** - Production-grade documentation written
**Goal**: Comprehensive documentation for Module 3 requirement
**Result**: 36,000+ words across 10 documentation files

#### Completed Deliverables:
- ✅ `docs/ARCHITECTURE.md` - Complete system design (23,910 bytes)
- ✅ `docs/SECURITY.md` - Comprehensive security documentation (24,198 bytes)
- ✅ `docs/OPERATIONS.md` - Production operations manual (19,918 bytes)
- ✅ `docs/TROUBLESHOOTING.md` - Complete troubleshooting guide (18,021 bytes)
- ✅ `README_ENHANCED.md` - Professional README (TO BE MERGED)
- ✅ `CONTRIBUTING_ENHANCED.md` - Enhanced development guide (TO BE MERGED)
- ✅ Progress summaries and integration documentation

#### Documentation Organization Task (IN PROGRESS):
- 🔄 Consolidate README.md with README_ENHANCED.md
- 🔄 Consolidate CONTRIBUTING.md with CONTRIBUTING_ENHANCED.md
- 🔄 Move progress/summary docs to docs/ folder
- 🔄 Clean up root directory (5 files instead of 15+)

### Phase 4: Multi-LLM Support (Priority: LOW - PLANNED)

#### Task 3.1: LLM Provider Abstraction
- [ ] Create `codetective/llm/` package structure
- [ ] Create `codetective/llm/base_provider.py` - Abstract LLM interface
- [ ] Refactor `ai_base.py` to use provider abstraction
- [ ] Add provider selection to Config

#### Task 3.2: Gemini Integration
- [ ] Create `codetective/llm/gemini_provider.py`
- [ ] Install google-generativeai package
- [ ] Implement authentication and API calls
- [ ] Add configuration options (--gemini-api-key, --gemini-model)
- [ ] Update CLI and GUI for Gemini selection

#### Task 3.3: Grok Integration
- [ ] Create `codetective/llm/grok_provider.py`
- [ ] Integrate xAI API client
- [ ] Implement authentication and API calls
- [ ] Add configuration options (--grok-api-key, --grok-model)
- [ ] Update CLI and GUI for Grok selection

#### Task 3.4: Provider Fallback & Selection
- [ ] Implement automatic provider fallback on failure
- [ ] Add provider availability detection
- [ ] Create provider comparison/benchmarking utility
- [ ] Update documentation with provider setup instructions

### Phase 5: Resilience & Monitoring (Priority: LOW - PLANNED)

#### Task 4.1: Advanced Retry Logic
- [ ] Create `codetective/resilience/retry_policy.py`
  - Exponential backoff with jitter
  - Configurable retry attempts per agent
  - Circuit breaker pattern for failing services
  - Fallback strategies for each agent type

#### Task 4.2: Enhanced Timeout Handling
- [ ] Update `process_utils.py` with progressive timeout warnings
- [ ] Add per-agent timeout configuration
- [ ] Implement timeout monitoring and metrics
- [ ] Create timeout recovery strategies

#### Task 4.3: Loop Prevention & Iteration Limits
- [ ] Add iteration counters to agent execution
- [ ] Implement max iteration limits in orchestrator
- [ ] Detect infinite loop patterns in LangGraph
- [ ] Add circuit breakers for stuck workflows

#### Task 4.4: Comprehensive Logging System
- [ ] Create `codetective/monitoring/logger.py`
  - Structured JSON logging
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Separate log files per component (agents, cli, gui)
  - Log rotation and retention policies
  - Performance metrics logging


### Phase 6: CI/CD & Quality Assurance (Priority: LOW - PLANNED)

#### Task 6.1: GitHub Actions Setup
- [ ] Create `.github/workflows/test.yml` - Run tests on PR
- [ ] Create `.github/workflows/lint.yml` - Code quality checks
- [ ] Create `.github/workflows/security.yml` - Security scanning
- [ ] Create `.github/workflows/release.yml` - Automated releases

#### Task 6.2: Code Quality Tools
- [ ] Add pre-commit hooks configuration
- [ ] Configure bandit for security scanning
- [ ] Add mypy for type checking
- [ ] Configure coverage reporting (Codecov/Coveralls)

## Main Workflows

### CLI Workflow
1. **info** → Check system compatibility and tool availability
2. **scan** → Execute multi-agent code analysis
3. **fix** → Apply automated remediation to identified issues
4. **gui** → Launch NiceGUI web interface
5. **health** → Check system health and component availability (NEW)

### Agent Orchestration Using LangGraph

```
[Start] → [Git-Aware File Selection] → [Agent Configuration]
    ↓
[Parallel/Sequential Execution Mode]
    ↓
[SemGrep Agent] [Trivy Agent] [Dynamic AI Review Agent]
    ↓                ↓                    ↓
[Static Analysis] [Security Scan] [AI-Powered Analysis]
    ↓
[Result Aggregation] → [JSON Output]
    ↓
[Fix Selection] → [Comment Agent] OR [Edit Agent]
    ↓
[Backup Creation] → [Apply Changes] → [Verification] → [End]
```

## File Processing Pipelines

### Scan Pipeline
1. **Git Repository Detection**: Identify git repositories and apply smart file selection
2. **File Selection**: Apply .gitignore patterns and git-tracked file filtering
3. **Input Validation**: Verify file paths and permissions
4. **Ollama Configuration**: Initialize AI agents with custom Ollama settings
5. **Agent Dispatch**: Route files to appropriate scanning agents
6. **Execution Mode**: Run agents in parallel or sequential mode
7. **Result Collection**: Aggregate results from all agents with unified error handling
8. **JSON Serialization**: Format results in standardized JSON structure with metadata

### Fix Pipeline
1. **Result Parsing**: Load and validate scan results JSON
2. **Issue Prioritization**: Sort issues by severity and type
3. **AI-Powered Fix Generation**: Use ChatOllama with structured prompts
4. **Fix Strategy Selection**: Choose between comment or edit agents
5. **Backup Creation**: Create safety backups before modifications
6. **Automated Application**: Apply AI-generated fixes with validation
7. **Status Tracking**: Update issue status (fixed/failed) in results
8. **Verification**: Validate that fixes don't break functionality

## GUI Interaction Flows

### Project Selection Flow
1. Display project path input with validation
2. Detect git repositories and show appropriate file selection
3. Configure scan mode (Full Project, Git Diff Only, Custom File Selection)
4. Configure agents (SemGrep, Trivy, AI Review) with availability indicators
5. Configure Ollama settings (base URL, model) with real-time validation
6. Set advanced options (parallel execution, force AI, max files, timeout)
7. Initiate scanning process with progress tracking

### File Selection Modes
1. **Full Project Scan**: all project files (respecting .gitignore)
2. **Git Diff Only**: Show only modified and new files from git diff
3. **Custom File Selection**: Interactive tree selector with git-aware filtering

### Scan Results Flow
1. Display tabbed interface (SemGrep, Trivy, AI Review)
2. Show results with severity indicators and expandable details
3. Provide issue selection checkboxes for fix application
4. Display scan metrics (duration, file count, agent performance)
5. Enable "Select All" functionality for batch operations

### Fix Application Flow
1. Select fix agent type (comment/edit) with configuration options
2. Configure backup settings (create/keep backups)
3. Display real-time progress during AI-powered fix generation
4. Show fix results with success/failure indicators
5. Display modified files list and fix summary
6. Update scan results to remove successfully fixed issues

## Error Recovery Mechanisms

- **Tool Availability**: Graceful degradation when external tools are missing
- **Ollama Connection**: Intelligent error handling for AI service connectivity
- **Timeout Handling**: Configurable timeouts with user notification
- **Partial Results**: Continue processing even if some agents fail
- **Git Integration**: Fallback to standard file scanning for non-git directories
- **Backup Safety**: Automatic backup creation before applying fixes
- **State Recovery**: Resume operations from intermediate states
- **User Intervention**: Allow manual override of automated decisions
- **AI Error Handling**: Unified error formatting for model-related issues
