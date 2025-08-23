# User and Session

## CLI User Profile

**Command-line Interface Users**
- Developers who prefer terminal-based workflows
- DevOps engineers integrating into CI/CD pipelines
- Power users requiring scriptable automation
- Batch processing of multiple projects

### CLI User Preferences
- Minimal output for successful operations
- Detailed error messages with actionable guidance
- Progress indicators for long-running operations
- Configurable output formats (JSON, text, etc.)

## GUI User Profile

**Web Interface Users via NiceGUI**
- Developers new to code analysis tools
- Team leads conducting code reviews
- Security analysts performing assessments
- Users preferring visual interfaces

### GUI User Preferences
- Intuitive navigation with clear visual feedback
- Interactive result exploration and filtering
- Visual progress indicators and status updates
- Easy issue selection and batch operations

## Session Management

### Temporary Files and State
- **Scan Results**: Stored in temporary JSON files during processing
- **Progress Tracking**: Maintain state across multi-step operations
- **Agent Communication**: Temporary files for inter-agent data exchange
- **User Selections**: Cache user choices during GUI sessions

### Configuration Persistence
- **Agent Configuration**: Default settings for each agent type
- **GUI State**: Remember last used settings and preferences

## Multi-Project Support

### Project Context Management
- **Project Detection**: Automatic detection of project type and structure
- **Configuration Inheritance**: Global → Project → Command-line precedence
- **Result Organization**: Separate results by project and timestamp
- **History Tracking**: Maintain scan history for trend analysis

### Session Isolation
- **Concurrent Operations**: Support multiple simultaneous scans
- **Resource Management**: Prevent conflicts between parallel sessions
- **Clean Shutdown**: Proper cleanup of temporary files and processes
- **Error Isolation**: Failures in one session don't affect others
