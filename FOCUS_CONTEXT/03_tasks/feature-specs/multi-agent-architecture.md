# Multi-Agent Architecture Feature Specification

## Overview
Implement a multi-agent architecture using LangGraph for orchestrating code review agents in the codetective tool.

## Feature Description
The multi-agent architecture serves as the core orchestration layer that coordinates different specialized agents to perform comprehensive code review tasks.

## Technical Requirements

### Core Components

#### BaseAgent Class
```python
@dataclass
class AgentState:
    """Shared state between agents"""
    files_to_analyze: List[Path]
    analysis_results: Dict[str, Any]
    configuration: Dict[str, Any]
    execution_context: Dict[str, Any]

class BaseAgent(ABC):
    """Abstract base class for all codetective agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = self._setup_logging()
    
    @abstractmethod
    async def analyze(self, state: AgentState) -> AnalysisResult:
        """Perform agent-specific analysis"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
```

#### LangGraph Orchestrator
- **State Management**: Centralized state object passed between agents
- **Workflow Definition**: Graph-based workflow with conditional routing
- **Error Handling**: Graceful degradation when agents fail
- **Parallel Execution**: Support for concurrent agent execution where possible

### Agent Specifications

#### 1. SemgrepAgent
- **Purpose**: Static code analysis for bugs, security issues, and code quality
- **Integration**: Semgrep CLI wrapper with custom rule sets
- **Output**: Structured findings with severity levels and fix suggestions

#### 2. TrivyAgent  
- **Purpose**: Security vulnerability scanning for dependencies and containers
- **Integration**: Trivy CLI wrapper with multiple scan types
- **Output**: Vulnerability reports with CVSS scores and remediation advice

#### 3. AIReviewAgent
- **Purpose**: LLM-powered intelligent code analysis and improvement suggestions
- **Integration**: OpenAI/Anthropic API integration
- **Output**: Code quality suggestions, refactoring recommendations, best practices

#### 4. OutputCommentAgent
- **Purpose**: Generate explanatory comments for identified issues
- **Integration**: LLM integration with code context
- **Output**: Formatted comments explaining issues and solutions

#### 5. OutputUpdateAgent
- **Purpose**: Automatically apply fixes and improvements to code
- **Integration**: AST manipulation and code generation
- **Output**: Modified code files with applied fixes

## Workflow Design

### LangGraph State Machine
```python
def create_codetective_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add agent nodes
    workflow.add_node("semgrep", SemgrepAgent)
    workflow.add_node("trivy", TrivyAgent) 
    workflow.add_node("ai_review", AIReviewAgent)
    workflow.add_node("output_comment", OutputCommentAgent)
    workflow.add_node("output_update", OutputUpdateAgent)
    
    # Define workflow edges
    workflow.add_edge(START, "semgrep")
    workflow.add_edge(START, "trivy")
    workflow.add_edge(["semgrep", "trivy"], "ai_review")
    workflow.add_conditional_edges(
        "ai_review",
        route_output_agent,
        {"comment": "output_comment", "update": "output_update"}
    )
    
    return workflow
```

## Acceptance Criteria

### Core Functionality
- [ ] BaseAgent class implemented with required abstract methods
- [ ] All 5 agents inherit from BaseAgent and implement required methods
- [ ] LangGraph workflow orchestrates agent execution correctly
- [ ] State management works across all agents
- [ ] Error handling provides graceful degradation

### Performance Requirements
- [ ] Agent execution completes within reasonable time limits
- [ ] Parallel agent execution where possible
- [ ] Memory usage remains within acceptable bounds
- [ ] Proper cleanup of resources after execution
