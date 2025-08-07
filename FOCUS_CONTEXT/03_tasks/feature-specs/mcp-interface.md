# MCP Interface Feature Specification

## Overview
Implement Model Context Protocol (MCP) interface for codetective to enable seamless integration with AI assistants and development environments.

## Feature Description
The MCP interface exposes codetective's capabilities as tools and resources that AI assistants can use to perform code review tasks, providing context-aware code analysis within AI-powered development workflows.

## Technical Requirements

### MCP Server Implementation

#### Core MCP Server
```python
class CodetectiveMCPServer:
    """MCP server exposing codetective capabilities"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.workflow_manager = WorkflowManager()
        self.server = Server("codetective")
    
    async def setup_tools(self):
        """Register codetective tools with MCP server"""
        await self.server.register_tool(
            name="analyze_code",
            description="Run multi-agent code analysis",
            input_schema=AnalyzeCodeSchema
        )
        
        await self.server.register_tool(
            name="get_findings",
            description="Retrieve analysis findings",
            input_schema=GetFindingsSchema
        )
        
        await self.server.register_tool(
            name="apply_fixes",
            description="Apply suggested code fixes",
            input_schema=ApplyFixesSchema
        )
```

### MCP Tools

#### 1. Code Analysis Tool
```python
@tool
async def analyze_code(
    project_path: str,
    files: Optional[List[str]] = None,
    agents: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    Run multi-agent code analysis on specified files or project.
    
    Args:
        project_path: Path to the project directory
        files: Optional list of specific files to analyze
        agents: Optional list of agents to run (semgrep, trivy, ai_review)
        config: Optional configuration overrides
    
    Returns:
        AnalysisResult with findings and recommendations
    """
    pass
```

#### 2. Findings Retrieval Tool
```python
@tool
async def get_findings(
    analysis_id: str,
    filters: Optional[Dict[str, Any]] = None,
    format: str = "structured"
) -> FindingsResult:
    """
    Retrieve analysis findings with optional filtering.
    
    Args:
        analysis_id: ID of the analysis to retrieve
        filters: Optional filters (severity, agent, file_pattern)
        format: Output format (structured, markdown, json)
    
    Returns:
        FindingsResult with filtered findings
    """
    pass
```

#### 3. Fix Application Tool
```python
@tool
async def apply_fixes(
    analysis_id: str,
    finding_ids: List[str],
    mode: str = "preview",
    auto_approve: bool = False
) -> FixResult:
    """
    Apply suggested fixes for specific findings.
    
    Args:
        analysis_id: ID of the analysis containing findings
        finding_ids: List of finding IDs to fix
        mode: preview, apply, or comment
        auto_approve: Whether to apply fixes without confirmation
    
    Returns:
        FixResult with applied changes and status
    """
    pass
```

### MCP Resources

#### 1. Project Context Resource
```python
@resource
async def get_project_context(uri: str) -> ProjectContext:
    """
    Provide project context including structure, dependencies, and metadata.
    
    Args:
        uri: Project URI (file:// or git://)
    
    Returns:
        ProjectContext with project information
    """
    pass
```

#### 2. Analysis History Resource
```python
@resource
async def get_analysis_history(uri: str) -> AnalysisHistory:
    """
    Provide history of previous analyses for the project.
    
    Args:
        uri: Project URI
    
    Returns:
        AnalysisHistory with previous analysis results
    """
    pass
```

#### 3. Agent Capabilities Resource
```python
@resource
async def get_agent_capabilities() -> AgentCapabilities:
    """
    Provide information about available agents and their capabilities.
    
    Returns:
        AgentCapabilities with agent descriptions and configuration options
    """
    pass
```

## AI Assistant Integration

### Context Sharing
```python
class ContextManager:
    """Manages context sharing between codetective and AI assistants"""
    
    def prepare_code_context(self, files: List[Path]) -> CodeContext:
        """Prepare code context for AI assistant"""
        return CodeContext(
            files=self._extract_file_contents(files),
            dependencies=self._analyze_dependencies(files),
            structure=self._analyze_project_structure(files),
            git_info=self._extract_git_context(files)
        )
    
    def format_findings_for_ai(self, findings: List[Finding]) -> str:
        """Format findings for AI assistant consumption"""
        pass
```

### Workflow Integration
- **Proactive Analysis**: AI assistant can trigger analysis on code changes
- **Context-Aware Suggestions**: Findings include full context for AI understanding
- **Interactive Fixes**: AI assistant can preview and apply fixes with user approval
- **Learning Integration**: Analysis results inform AI assistant about code patterns

## Protocol Implementation

### Message Types
```python
# Tool call message
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "analyze_code",
        "arguments": {
            "project_path": "/path/to/project",
            "agents": ["semgrep", "ai_review"],
            "files": ["src/main.py", "src/utils.py"]
        }
    },
    "id": "analysis-001"
}

# Resource request message
{
    "jsonrpc": "2.0",
    "method": "resources/read",
    "params": {
        "uri": "codetective://project-context/current"
    },
    "id": "context-001"
}
```

### Response Formats
```python
# Tool response
{
    "jsonrpc": "2.0",
    "result": {
        "content": [
            {
                "type": "text",
                "text": "Analysis completed with 5 findings"
            },
            {
                "type": "resource",
                "resource": {
                    "uri": "codetective://analysis/analysis-001",
                    "name": "Analysis Results",
                    "mimeType": "application/json"
                }
            }
        ]
    },
    "id": "analysis-001"
}
```

## Use Cases

### 1. AI-Assisted Code Review
```
AI Assistant: "Let me analyze this pull request for security issues"
→ analyze_code(project_path=".", files=["changed_files.py"])
→ AI reviews findings and provides contextual explanations
```

### 2. Proactive Code Quality
```
AI Assistant: "I notice you're working on authentication code"
→ analyze_code(agents=["semgrep", "trivy"], files=["auth.py"])
→ AI suggests security improvements based on findings
```

### 3. Automated Fix Application
```
AI Assistant: "I found some issues that can be automatically fixed"
→ apply_fixes(finding_ids=["fix-001", "fix-002"], mode="preview")
→ AI shows preview and asks for confirmation
→ apply_fixes(finding_ids=["fix-001", "fix-002"], mode="apply")
```

## Acceptance Criteria

### Protocol Compliance
- [ ] Full MCP protocol implementation
- [ ] Proper JSON-RPC message handling
- [ ] Standard tool and resource registration
- [ ] Error handling with appropriate error codes
- [ ] Capability advertisement and discovery

### Tool Functionality
- [ ] All tools work correctly with proper input validation
- [ ] Results are properly formatted for AI consumption
- [ ] Error messages are clear and actionable
- [ ] Performance is suitable for interactive use
- [ ] Proper authentication and authorization

### Integration Quality
- [ ] Seamless integration with AI assistants
- [ ] Context sharing works effectively
- [ ] Real-time analysis capabilities
- [ ] Proper state management across sessions
- [ ] Comprehensive documentation for AI assistants

### Reliability
- [ ] Robust error handling and recovery
- [ ] Proper resource cleanup
- [ ] Memory and performance optimization
- [ ] Comprehensive logging for debugging
- [ ] Security considerations for remote access

## Implementation Notes
- Use official MCP Python SDK
- Implement proper async/await patterns
- Add comprehensive input validation
- Support for multiple concurrent AI assistant connections
- Configurable security and access controls
