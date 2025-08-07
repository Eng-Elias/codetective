# Current Objectives

## Purpose
Defines the immediate goals for codetective multi-agent code review tool development to keep progress focused and measurable.

## Sprint Goal
- **Goal**: "Build MVP of codetective multi-agent code review tool with GUI, CLI, and MCP interfaces"
- **Sprint Dates**: 2025-07-31 - 2025-08-07
- **Key Performance Indicators (KPIs)**:
  - All 5 agents (Semgrep, Trivy, AI Review, Output Comment, Output Update) functional
  - GUI workflow complete from project selection to issue resolution
  - CLI interface supports basic scanning operations
  - MCP interface provides basic code review capabilities
  - Clean code architecture with class-based utilities

## Primary Objectives

### Phase 1: Core Architecture (Priority: High)
- **[Objective 1: Multi-Agent Framework Setup](#core-framework)**
  - **Status**: To Do
  - **Tasks**: 
    - Implement BaseAgent class with LangGraph integration
    - Create agent state management with dataclasses
    - Setup LangGraph orchestrator for workflow coordination
    - Implement structured result objects and error handling

- **[Objective 2: Agent Implementation](#agents)**
  - **Status**: To Do
  - **Tasks**:
    - SemgrepAgent: Static code analysis integration
    - TrivyAgent: Security vulnerability scanning
    - AIReviewAgent: LLM-powered code analysis
    - OutputCommentAgent: Generate explanatory comments
    - OutputUpdateAgent: Apply automatic code fixes

### Phase 2: Interface Development (Priority: High)
- **[Objective 3: Streamlit GUI](#gui-interface)**
  - **Status**: To Do
  - **Tasks**:
    - Project path selection and git repository browsing
    - File selection interface with tree view
    - Agent configuration and selection
    - Results display and issue resolution interface

- **[Objective 4: CLI Interface](#cli-interface)**
  - **Status**: To Do
  - **Tasks**:
    - Command structure design
    - Configuration file support
    - Batch processing capabilities
    - Output formatting options

- **[Objective 5: MCP Interface](#mcp-interface)**
  - **Status**: To Do
  - **Tasks**:
    - MCP protocol implementation
    - Context sharing with AI assistants
    - Tool registration and capability exposure

### Phase 3: Integration & Testing (Priority: Medium)
- **[Objective 6: Git Integration](#git-integration)**
  - **Status**: To Do
  - **Tasks**:
    - GitRepositoryManager class implementation
    - File selection and diff analysis
    - Branch and commit context

- **[Objective 7: Configuration System](#configuration)**
  - **Status**: To Do
  - **Tasks**:
    - User preferences management
    - Agent configuration profiles
    - Auto/human-in-the-loop mode settings

## Task Context
- **Relevant Files**: 
  - `/src/agents/` - Agent implementations
  - `/src/interfaces/` - GUI, CLI, MCP interfaces
  - `/src/core/` - Core orchestration and utilities
  - `/src/utils/` - Class-based utility modules
  - `/tests/` - Comprehensive test suite
- **Relevant Architecture**: `02_domain/architecture/system-architecture.md`
- **Coding Standards**: `02_domain/standards/coding-standards.md`
