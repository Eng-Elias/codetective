# Tasks and Workflow

## Main Workflows

### CLI Workflow
1. **info** → Check system compatibility and tool availability
2. **scan** → Execute multi-agent code analysis
3. **fix** → Apply automated remediation to identified issues
4. **gui** → Launch NiceGUI web interface

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
