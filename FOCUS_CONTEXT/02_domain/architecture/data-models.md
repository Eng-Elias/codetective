# Data Models

## Purpose
Defines the structure, relationships, and constraints of the core data entities used in the codetective multi-agent code review tool.

## Core Data Entities

### Workflow State
```python
@dataclass
class WorkflowState:
    """Central state object passed between agents in LangGraph workflow"""
    scan_id: str
    target_files: List[Path]
    selected_agents: List[str]
    semgrep_results: Optional[SemgrepResults] = None
    trivy_results: Optional[TrivyResults] = None
    ai_review_results: Optional[AIReviewResults] = None
    output_results: Optional[OutputResults] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Agent Results

#### Semgrep Results
```python
@dataclass
class SemgrepFinding:
    """Individual Semgrep finding based on JSON schema"""
    check_id: str
    path: str
    start: Dict[str, int]  # {"line": int, "col": int}
    end: Dict[str, int]    # {"line": int, "col": int}
    message: str
    severity: str  # ERROR, WARNING, INFO
    metadata: Dict[str, Any]
    extra: Dict[str, Any]

@dataclass
class SemgrepResults:
    """Semgrep scan results container"""
    findings: List[SemgrepFinding]
    errors: List[str]
    stats: Dict[str, Any]
    version: str
```

#### Trivy Results
```python
@dataclass
class TrivyVulnerability:
    """Individual Trivy vulnerability based on JSON schema v2"""
    vulnerability_id: str
    pkg_name: str
    installed_version: str
    fixed_version: Optional[str]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN
    title: str
    description: str
    references: List[str]

@dataclass
class TrivyResult:
    """Individual Trivy scan target result"""
    target: str
    class_type: str  # os-pkgs, lang-pkgs
    type: str  # alpine, java, etc.
    vulnerabilities: List[TrivyVulnerability]

@dataclass
class TrivyResults:
    """Trivy scan results container"""
    schema_version: int
    artifact_name: str
    artifact_type: str
    metadata: Dict[str, Any]
    results: List[TrivyResult]
```

#### AI Review Results
```python
@dataclass
class AIReviewIssue:
    """AI-identified code issue"""
    file_path: str
    line_start: int
    line_end: int
    issue_type: str  # security, performance, maintainability, etc.
    severity: str    # critical, high, medium, low
    description: str
    suggestion: str
    confidence: float  # 0.0 to 1.0

@dataclass
class AIReviewResults:
    """AI review results container"""
    issues: List[AIReviewIssue]
    summary: str
    model_used: str
    processing_time: float
```

#### Output Results
```python
@dataclass
class OutputResults:
    """Final output from comment or update agents"""
    output_type: str  # comment, update
    files_modified: List[str]
    comments_added: List[Dict[str, Any]]
    success: bool
    message: str
```

### Configuration Models

#### Agent Configuration
```python
@dataclass
class AgentConfig:
    """Base agent configuration"""
    enabled: bool
    timeout: int
    retry_count: int
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SemgrepConfig(AgentConfig):
    """Semgrep-specific configuration"""
    rules: List[str]  # Rule IDs or paths
    exclude_rules: List[str]
    config_path: Optional[str]
    severity_filter: List[str]

@dataclass
class TrivyConfig(AgentConfig):
    """Trivy-specific configuration"""
    scan_types: List[str]  # vuln, secret, config
    severity_filter: List[str]
    ignore_unfixed: bool

@dataclass
class AIReviewConfig(AgentConfig):
    """AI review agent configuration"""
    provider: str  # openai, anthropic, gemini, ollama, lmstudio
    model: str
    max_tokens: int
    temperature: float
    focus_areas: List[str]
```

### Interface Models

#### GUI State
```python
@dataclass
class GUIState:
    """Streamlit GUI state management"""
    selected_files: List[str]
    selected_agents: List[str]
    agent_configs: Dict[str, AgentConfig]
    scan_in_progress: bool
    results_available: bool
```

#### CLI Arguments
```python
@dataclass
class CLIArgs:
    """CLI command arguments"""
    target_path: str
    agents: List[str]
    output_format: str  # json, text, sarif
    output_file: Optional[str]
    config_file: Optional[str]
    verbose: bool
```

#### MCP Protocol
```python
@dataclass
class MCPRequest:
    """MCP protocol request structure"""
    method: str
    params: Dict[str, Any]
    id: str

@dataclass
class MCPResponse:
    """MCP protocol response structure"""
    result: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
    id: str
```

## Key Relationships

- **WorkflowState → Agent Results**: One-to-Many. Central state contains results from multiple agents.
- **Agent Results → Findings/Issues**: One-to-Many. Each agent produces multiple findings.
- **Configuration → Agents**: One-to-One. Each agent has its specific configuration.
- **Interface State → WorkflowState**: One-to-One. Each interface manages workflow execution.

## Data Flow Patterns

1. **Input**: Files/paths → WorkflowState initialization
2. **Processing**: WorkflowState → Agents → Results accumulation
3. **Output**: Consolidated results → Interface-specific formatting
4. **Persistence**: Results → JSON/SARIF/Database storage

## Validation Rules

- [ ] All dataclasses use proper type hints and default factories
- [ ] Results structures match external tool JSON schemas
- [ ] State transitions maintain data integrity
- [ ] Error handling preserves partial results
- [ ] Configuration validation prevents invalid agent setups

## Schema Evolution

- **Semgrep**: Monitor semgrep/semgrep-interfaces for schema changes
- **Trivy**: Track Trivy JSON schema version updates
- **Backward Compatibility**: Maintain support for previous result formats
- **Migration**: Provide data migration utilities for schema updates
