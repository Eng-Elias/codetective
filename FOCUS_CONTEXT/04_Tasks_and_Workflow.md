# Tasks and Workflow

## Main Workflows

### CLI Workflow
1. **info** → Check system compatibility and tool availability
2. **scan** → Execute multi-agent code analysis
3. **fix** → Apply automated remediation to identified issues
4. **gui** → Launch Streamlit web interface

### Agent Orchestration Using LangGraph

```
[Start] → [Agent Selection] → [Parallel Scanning]
    ↓
[SemGrep Agent] [Trivy Agent] [AI Review Agent]
    ↓
[Result Aggregation] → [JSON Output]
    ↓
[Fix Selection] → [Comment Agent] OR [Edit Agent]
    ↓
[Apply Changes] → [End]
```

## File Processing Pipelines

### Scan Pipeline
1. **Input Validation**: Verify file paths and permissions
2. **Agent Dispatch**: Route files to appropriate scanning agents
3. **Parallel Execution**: Run multiple agents simultaneously
4. **Result Collection**: Aggregate results from all agents
5. **JSON Serialization**: Format results in standardized JSON structure

### Fix Pipeline
1. **Result Parsing**: Load and validate scan results JSON
2. **Issue Prioritization**: Sort issues by severity and type
3. **Fix Strategy Selection**: Choose between comment or edit agents
4. **Automated Application**: Apply fixes with user confirmation
5. **Verification**: Validate that fixes don't break functionality

## GUI Interaction Flows

### Project Selection Flow
1. Display file browser for project path selection
2. Show repository files with checkboxes (all selected by default)
3. Configure scan options (agent selection, timeout)
4. Initiate scanning process

### Scan Results Flow
1. Display tabbed interface (one tab per agent)
2. Show results as selectable list with checkboxes
3. All issues selected by default for fixing
4. Allow user to deselect specific issues

### Fix Application Flow
1. Select fix agent type (comment/edit)
2. Display progress bar during fixing process
3. Mark completed issues as resolved
4. Show summary of applied changes

## Error Recovery Mechanisms

- **Tool Availability**: Graceful degradation when external tools are missing
- **Timeout Handling**: Configurable timeouts with user notification
- **Partial Results**: Continue processing even if some agents fail
- **State Recovery**: Resume operations from intermediate states
- **User Intervention**: Allow manual override of automated decisions
