# Codetective Architecture

**v0.1.0** | **Oct 2025** | **Production-Ready**

## Overview
Multi-agent code security analyzer: static analysis + vulnerability detection + AI-powered review + automated fixing.

**Architecture**: Agent-based (LangGraph) | Local desktop app | Privacy-first (code never leaves machine)

## Principles
1. **Agent Autonomy** - Self-contained, orchestrator-coordinated
2. **Composability** - Add/remove agents independently
3. **Security by Design** - Input validation → Processing protection → Output filtering
4. **Fail-Safe** - Read-only default, explicit confirmations, auto-backups
5. **Local-First** - No cloud dependencies

## Multi-Agent System

**Hierarchy**:
```
BaseAgent
├── ScanAgent: SemGrepAgent, TrivyAgent, DynamicAIReviewAgent
└── OutputAgent + AIAgent: CommentAgent, EditAgent
```

## Security (Defense-in-Depth)

| Layer | Module | Protection |
|-------|--------|------------|
| **1. Input** | InputValidator | Path traversal, file size, command injection |
| **2. Processing** | PromptGuard | Prompt injection, sensitive data, token limits |
| **3. Output** | OutputFilter | Malicious code, dangerous functions |

**Flow**: `User Input → InputValidator → PromptGuard → Ollama → OutputFilter → Output`

## Data Flow

**Scan**: `CLI/GUI → Config → Git-aware Discovery → Scan → Aggregate → JSON`  
**Fix**: `Load JSON → Select → Output Agents → Backup → Apply → Update JSON`

## Tech Stack

| Category | Technology |
|----------|-----------|
| Core | Python 3.12+, pyproject.toml |
| Orchestration | LangGraph, TypedDict |
| AI | LangChain, Ollama |
| Analysis | SemGrep, Trivy, AI Review |
| UI | Click (CLI), NiceGUI (GUI) |
| Git | git ls-files, .gitignore parser |
| Testing | pytest |
| Security | Custom modules |

## Components

**Core**: Config, Orchestrator  
**Agents**: SemGrepAgent, TrivyAgent, DynamicAIReviewAgent, CommentAgent, EditAgent  
**Security**: InputValidator, PromptGuard, OutputFilter (stateless utilities)  
**Utils**: FileUtils, GitUtils, ProcessUtils, PromptBuilder, SystemUtils, StringUtils  
**Models**: Issue, AgentResult  
**CLI**: scan, fix, gui commands  
**GUI**: Real-time config, file selection, progress tracking

## Design Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| LangGraph | State management, parallelism | Extra dependency |
| Local Ollama | Privacy, no costs, no limits | Requires GPU, lower quality |
| No RateLimiter | Local app | None |
| Git-aware | Faster, relevant files only | Git dependency |
| Separate Security | Testability, reusability | More modules |
| Pytest | Less boilerplate, better fixtures | None |

## Performance

**Bottlenecks**: AI Review (Ollama), file I/O, external tools  
**Optimizations**: Parallel execution, git-aware discovery, file size limit, timeout  

## Deployment

**Local**: Codetective (CLI/GUI) + Ollama + SemGrep + Trivy

```bash
pip install codetective
ollama pull qwen3:4b
```

## Future

1. Multi-LLM (Gemini, Grok, Claude)
2. Resilience (retry, circuit breakers)
3. Observability (metrics, profiling)
4. CI/CD (GitHub Actions, pre-commit)
5. Plugins (third-party agents, custom rules)
