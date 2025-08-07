# Codetective Context-Driven Development Workflow

## Core Workflow: Context Understanding and Task Implementation

### Prerequisites
1. **Context Understanding**
   - Load and understand FOCUS_CONTEXT system files (assistant persona, interaction guidelines, safety constraints)
   - Review FOCUS_CONTEXT domain files (project overview, architecture, coding standards, data models)
   - Understand current task objectives and acceptance criteria
   - Verify project structure and dependencies

### Main Workflow Steps

#### Step 1: Context Analysis
**Deep understanding of the current state:**

##### 1a. System Context Review
- **Assistant Persona**: Understand role as codetective multi-agent expert
- **Safety Constraints**: Review security-first approach and backup requirements
- **Interaction Guidelines**: Apply structured communication and clear rationales

##### 1b. Domain Context Review
- **Project Architecture**: Multi-agent code review tool with LangGraph orchestration
- **Technology Stack**: Python, LangGraph, Streamlit, Click, Semgrep, Trivy, LLM providers
- **Design Principles**: Class-based utilities, SOLID principles, type safety, error handling
- **Current State**: Assess existing codebase and implementation progress

##### 1c. Task Context Understanding
- **Current Objectives**: Review from FOCUS_CONTEXT current-objectives.md
- **Acceptance Criteria**: Reference multi-agent workflow requirements
- **Priority Assessment**: Understand what needs immediate attention

#### Step 2: Task Implementation
**Focus on the specific task at hand:**

##### 2a. Task Analysis
- **Requirements Clarification**: Ensure complete understanding of what needs to be done
- **Architecture Alignment**: Verify task aligns with codetective principles
- **Impact Assessment**: Understand how changes affect the broader system

##### 2b. Implementation Planning
- **Approach Design**: Plan the specific implementation strategy
- **Quality Standards**: Ensure compliance with coding standards
- **Risk Mitigation**: Identify potential issues and mitigation strategies

##### 2c. Implementation Execution
- **Code Development**: Implement the required functionality
- **Architecture Compliance**: Ensure adherence to:
  - Multi-agent architecture principles
  - Class-based utility requirements (no standalone functions)
  - SOLID design principles
  - Type safety and error handling standards
- **Quality Validation**: Run linting, type checking, and testing

#### Step 3: Session Management
**Throughout the implementation process:**

##### 3a. Progress Tracking
- **Session Updates**: Document progress and completed work
- **Context Maintenance**: Keep track of how work contributes to objectives
- **Issue Documentation**: Record any blockers or challenges encountered

##### 3b. Quality Assurance
- **Standards Compliance**: Ensure all work meets codetective quality standards
- **Architecture Validation**: Verify no violations of design principles
- **Testing**: Validate functionality where possible

#### Step 4: Completion and Handoff
**After task completion:**

##### 4a. Implementation Summary
- **Work Completed**: Detail all changes and implementations
- **Files Modified**: List specific files and modifications made
- **Architecture Impact**: Highlight any architectural improvements or considerations

##### 4b. Next Steps
- **Follow-up Actions**: Recommend any additional work needed
- **Testing Requirements**: Suggest testing approaches for implemented features
- **Documentation Updates**: Note any documentation that should be updated

## Quality Gates

### Before Making Changes
- [ ] Comment is clearly understood
- [ ] Change aligns with codetective architecture
- [ ] No violation of class-based utility rule
- [ ] Change maintains type safety
- [ ] Impact on other components assessed

### After Making Changes
- [ ] Code passes linting checks
- [ ] Type checking passes
- [ ] No breaking changes introduced
- [ ] Documentation updated if needed
- [ ] Change tested where possible

### Session Completion
- [ ] All processable comments addressed
- [ ] Summary provided with clear next steps
- [ ] User attention items clearly identified
- [ ] Session progress documented

## Success Metrics

- **Completion Rate**: Percentage of comments successfully processed
- **Quality Compliance**: All changes meet codetective standards
- **Context Preservation**: Project architecture and principles maintained
- **User Satisfaction**: Clear communication and appropriate escalation of complex issues
