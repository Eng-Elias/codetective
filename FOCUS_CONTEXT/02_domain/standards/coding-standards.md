# Coding Standards

## Purpose
Defines the coding style, formatting, and patterns for the codetective Python codebase, emphasizing clean code principles and multi-agent architecture patterns.

## Python Standards

### Formatting
- **Style Guide**: PEP 8 for Python with Black formatter
- **Linter Configuration**: `pyproject.toml` with ruff, black, mypy, and isort
- **Max Line Length**: 100 characters (Black default)
- **Import Organization**: isort with profile "black"

### Naming Conventions
- **Variables**: `snake_case` for all variables and functions
- **Functions**: `snake_case` with descriptive verbs
- **Classes**: `PascalCase` with descriptive nouns
- **Constants**: `UPPER_SNAKE_CASE`
- **Private Members**: Leading underscore `_private_method`
- **Agent Classes**: Suffix with "Agent" (e.g., `SemgrepAgent`)
- **Interface Classes**: Suffix with "Interface" (e.g., `CLIInterface`)

### Clean Code Architecture Patterns

#### Class-Based Utilities (Required)
- **NO standalone functions in utility modules**
- **ALL utilities must be implemented as classes with properties and methods**
- **Follow SOLID Principles**

```python
# ✅ CORRECT: Class-based utility
class GitRepositoryManager:
    def __init__(self, repo_path: Path):
        self._repo_path = repo_path
        self._repo = None
    
    @property
    def current_branch(self) -> str:
        return self._repo.active_branch.name
    
    def get_modified_files(self) -> List[Path]:
        return [Path(item.a_path) for item in self._repo.index.diff(None)]

# ❌ INCORRECT: Standalone functions
def get_git_files(repo_path):
    pass
```

#### Agent Design Patterns
- **Base Agent Class**: All agents inherit from `BaseAgent`
- **State Management**: Use dataclasses for agent state
- **Result Objects**: Structured results with typing
- **Error Handling**: Custom exceptions with context

```python
@dataclass
class AnalysisResult:
    agent_name: str
    findings: List[Finding]
    execution_time: float
    status: AnalysisStatus
```

### Multi-Agent Patterns
- **LangGraph Integration**: Agents as graph nodes with typed state
- **Async/Await**: All agent operations are async
- **Context Passing**: Structured context objects between agents
- **Result Aggregation**: Typed result collectors

### Error Handling
- **Custom Exceptions**: Domain-specific exception hierarchy
- **Logging**: Structured logging with context
- **Graceful Degradation**: Partial results on agent failures
- **Retry Logic**: Exponential backoff for external services
