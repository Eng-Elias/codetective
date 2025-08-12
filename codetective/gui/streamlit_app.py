"""
Streamlit GUI for Codetective - Multi-Agent Code Review Tool.
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import time

try:
    # Try relative imports first (when run as module)
    from ..core.config import get_config
    from ..core.orchestrator import CodeDetectiveOrchestrator
    from ..core.utils import get_system_info, validate_paths
    from ..models.schemas import ScanConfig, FixConfig, AgentType, Issue
except ImportError:
    # Fall back to absolute imports (when run as script)
    import sys
    from pathlib import Path
    
    # Add the parent directory to the path
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from codetective.core.config import get_config
    from codetective.core.orchestrator import CodeDetectiveOrchestrator
    from codetective.core.utils import get_system_info, validate_paths
    from codetective.models.schemas import ScanConfig, FixConfig, AgentType, Issue


# Page configuration
st.set_page_config(
    page_title="Codetective - Multi-Agent Code Review",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "project_selection"
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'selected_issues' not in st.session_state:
    st.session_state.selected_issues = []
if 'project_path' not in st.session_state:
    st.session_state.project_path = ""


def main():
    """Main Streamlit application."""
    st.title("🔍 Codetective - Multi-Agent Code Review Tool")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        
        if st.button("📁 Project Selection", use_container_width=True):
            st.session_state.current_page = "project_selection"
        
        if st.button("🔍 Scan Results", use_container_width=True, 
                    disabled=st.session_state.scan_results is None):
            st.session_state.current_page = "scan_results"
        
        if st.button("🔧 Fix Application", use_container_width=True,
                    disabled=not st.session_state.selected_issues):
            st.session_state.current_page = "fix_application"
        
        st.divider()
        
        # System status
        st.subheader("System Status")
        with st.spinner("Checking system..."):
            system_info = get_system_info()
        
        st.write("**Tool Availability:**")
        st.write(f"✅ SemGrep" if system_info.semgrep_available else "❌ SemGrep")
        st.write(f"✅ Trivy" if system_info.trivy_available else "❌ Trivy")
        st.write(f"✅ Ollama" if system_info.ollama_available else "❌ Ollama")
    
    # Main content area
    if st.session_state.current_page == "project_selection":
        show_project_selection_page()
    elif st.session_state.current_page == "scan_results":
        show_scan_results_page()
    elif st.session_state.current_page == "fix_application":
        show_fix_application_page()


def show_project_selection_page():
    """Show the project selection page."""
    st.header("📁 Project Selection")
    
    # Project path input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        project_path = st.text_input(
            "Project Path",
            value=st.session_state.project_path,
            placeholder="Enter the path to your project (e.g., /path/to/project or .)"
        )
    
    with col2:
        if st.button("Browse", help="Browse for project directory"):
            # Note: Streamlit doesn't have native file browser, so we'll use text input
            st.info("Please enter the project path manually")
    
    if project_path:
        st.session_state.project_path = project_path
        
        # Validate path
        try:
            if Path(project_path).exists():
                st.success(f"✅ Valid path: {Path(project_path).absolute()}")
                
                # Show file tree (limited depth)
                show_file_tree(project_path)
                
                # Scan configuration
                st.subheader("🔧 Scan Configuration")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Select Agents:**")
                    use_semgrep = st.checkbox("SemGrep (Static Analysis)", value=True)
                    use_trivy = st.checkbox("Trivy (Security Scanning)", value=True)
                    use_ai_review = st.checkbox("AI Review (Intelligent Analysis)", value=True)
                
                with col2:
                    timeout = st.number_input(
                        "Timeout (seconds)",
                        min_value=30,
                        max_value=1800,
                        value=300,
                        step=30
                    )
                
                # Start scan button
                if st.button("🚀 Start Scan", type="primary", use_container_width=True):
                    start_scan(project_path, use_semgrep, use_trivy, use_ai_review, timeout)
            
            else:
                st.error(f"❌ Path does not exist: {project_path}")
        
        except Exception as e:
            st.error(f"❌ Error validating path: {e}")


def show_file_tree(project_path: str, max_files: int = 50):
    """Show a simple file tree for the project."""
    st.write("**Project Files:**")
    
    try:
        path = Path(project_path)
        files = []
        
        # Get files (limited to prevent overwhelming display)
        for file_path in path.rglob("*"):
            if file_path.is_file() and len(files) < max_files:
                rel_path = file_path.relative_to(path)
                files.append(str(rel_path))
        
        if files:
            # Show first few files
            display_files = files[:20]
            for file in display_files:
                st.write(f"📄 {file}")
            
            if len(files) > 20:
                st.write(f"... and {len(files) - 20} more files")
            
            st.info(f"Total files found: {len(files)}")
        else:
            st.warning("No files found in the specified path")
    
    except Exception as e:
        st.error(f"Error reading project files: {e}")


def start_scan(project_path: str, use_semgrep: bool, use_trivy: bool, 
               use_ai_review: bool, timeout: int):
    """Start the scanning process."""
    # Prepare agent list
    agents = []
    if use_semgrep:
        agents.append(AgentType.SEMGREP)
    if use_trivy:
        agents.append(AgentType.TRIVY)
    if use_ai_review:
        agents.append(AgentType.AI_REVIEW)
    
    if not agents:
        st.error("Please select at least one agent")
        return
    
    # Create scan configuration
    scan_config = ScanConfig(
        agents=agents,
        timeout=timeout,
        paths=[project_path]
    )
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize orchestrator
        config = get_config()
        orchestrator = CodeDetectiveOrchestrator(config)
        
        # Run scan
        status_text.text("🔍 Running scan...")
        progress_bar.progress(25)
        
        scan_result = orchestrator.run_scan(scan_config)
        
        progress_bar.progress(100)
        status_text.text("✅ Scan completed!")
        
        # Store results in session state
        st.session_state.scan_results = scan_result
        
        # Show summary
        st.success(f"Scan completed! Found {scan_result.total_issues} issues in {scan_result.scan_duration:.2f} seconds")
        
        # Auto-navigate to results
        time.sleep(1)
        st.session_state.current_page = "scan_results"
        st.rerun()
    
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        st.error(f"Scan failed: {e}")


def show_scan_results_page():
    """Show the scan results page."""
    st.header("🔍 Scan Results")
    
    if st.session_state.scan_results is None:
        st.warning("No scan results available. Please run a scan first.")
        return
    
    scan_result = st.session_state.scan_results
    
    # Results summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Issues", scan_result.total_issues)
    
    with col2:
        st.metric("Scan Duration", f"{scan_result.scan_duration:.2f}s")
    
    with col3:
        st.metric("SemGrep Issues", len(scan_result.semgrep_results))
    
    with col4:
        st.metric("Trivy Issues", len(scan_result.trivy_results))
    
    # Tabbed interface for results
    tab1, tab2, tab3 = st.tabs(["🔒 SemGrep Results", "🛡️ Trivy Results", "🤖 AI Review Results"])
    
    with tab1:
        show_issues_tab("SemGrep", scan_result.semgrep_results)
    
    with tab2:
        show_issues_tab("Trivy", scan_result.trivy_results)
    
    with tab3:
        show_issues_tab("AI Review", scan_result.ai_review_results)
    
    # Fix selection
    if scan_result.total_issues > 0:
        st.subheader("🔧 Fix Selection")
        
        if st.button("Select All Issues for Fixing", use_container_width=True):
            all_issues = (scan_result.semgrep_results + 
                         scan_result.trivy_results + 
                         scan_result.ai_review_results)
            st.session_state.selected_issues = all_issues
            st.success(f"Selected {len(all_issues)} issues for fixing")
        
        if st.session_state.selected_issues:
            st.info(f"Selected {len(st.session_state.selected_issues)} issues for fixing")
            
            if st.button("Proceed to Fix Application", type="primary"):
                st.session_state.current_page = "fix_application"
                st.rerun()


def show_issues_tab(agent_name: str, issues: List[Issue]):
    """Show issues for a specific agent in a tab."""
    if not issues:
        st.info(f"No issues found by {agent_name}")
        return
    
    st.write(f"**{agent_name} found {len(issues)} issues:**")
    
    # Issues table
    for i, issue in enumerate(issues):
        with st.expander(f"{issue.severity.value.upper()}: {issue.title}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**File:** {issue.file_path}")
                if issue.line_number:
                    st.write(f"**Line:** {issue.line_number}")
                st.write(f"**Description:** {issue.description}")
                if issue.fix_suggestion:
                    st.write(f"**Suggested Fix:** {issue.fix_suggestion}")
            
            with col2:
                severity_color = {
                    "low": "🟢",
                    "medium": "🟡", 
                    "high": "🟠",
                    "critical": "🔴"
                }
                st.write(f"**Severity:** {severity_color.get(issue.severity.value, '⚪')} {issue.severity.value.title()}")
                
                if st.checkbox(f"Include in fix", key=f"issue_{agent_name}_{i}"):
                    if issue not in st.session_state.selected_issues:
                        st.session_state.selected_issues.append(issue)
                else:
                    if issue in st.session_state.selected_issues:
                        st.session_state.selected_issues.remove(issue)


def show_fix_application_page():
    """Show the fix application page."""
    st.header("🔧 Fix Application")
    
    if not st.session_state.selected_issues:
        st.warning("No issues selected for fixing. Please select issues from the scan results.")
        return
    
    st.info(f"Ready to fix {len(st.session_state.selected_issues)} selected issues")
    
    # Fix configuration
    st.subheader("Fix Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fix_agent = st.selectbox(
            "Fix Agent",
            options=["edit", "comment"],
            index=0,
            help="Edit: Apply automatic code fixes | Comment: Add explanatory comments"
        )
    
    with col2:
        backup_files = st.checkbox("Create backup files", value=True)
    
    # Show selected issues summary
    st.subheader("Selected Issues Summary")
    
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for issue in st.session_state.selected_issues:
        severity_counts[issue.severity.value] += 1
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🟢 Low", severity_counts["low"])
    with col2:
        st.metric("🟡 Medium", severity_counts["medium"])
    with col3:
        st.metric("🟠 High", severity_counts["high"])
    with col4:
        st.metric("🔴 Critical", severity_counts["critical"])
    
    # Apply fixes button
    if st.button("🚀 Apply Fixes", type="primary", use_container_width=True):
        apply_fixes(fix_agent, backup_files)


def apply_fixes(fix_agent: str, backup_files: bool):
    """Apply fixes to selected issues."""
    # Create fix configuration
    agent_type = AgentType.EDIT if fix_agent == "edit" else AgentType.COMMENT
    
    fix_config = FixConfig(
        agents=[agent_type],
        selected_issues=[issue.id for issue in st.session_state.selected_issues],
        backup_files=backup_files,
        dry_run=False
    )
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize orchestrator
        config = get_config()
        orchestrator = CodeDetectiveOrchestrator(config)
        
        # Prepare scan data for fix operation
        scan_data = {
            "semgrep_results": [issue.model_dump() for issue in st.session_state.selected_issues if "semgrep" in issue.id],
            "trivy_results": [issue.model_dump() for issue in st.session_state.selected_issues if "trivy" in issue.id],
            "ai_review_results": [issue.model_dump() for issue in st.session_state.selected_issues if "ai-review" in issue.id]
        }
        
        # Run fix
        status_text.text("🔧 Applying fixes...")
        progress_bar.progress(50)
        
        fix_result = orchestrator.run_fix(scan_data, fix_config)
        
        progress_bar.progress(100)
        status_text.text("✅ Fixes applied!")
        
        # Show results
        st.success(f"Fix operation completed in {fix_result.fix_duration:.2f} seconds")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fixed Issues", len(fix_result.fixed_issues))
        with col2:
            st.metric("Failed Issues", len(fix_result.failed_issues))
        with col3:
            st.metric("Modified Files", len(fix_result.modified_files))
        
        if fix_result.modified_files:
            st.subheader("Modified Files")
            for file_path in fix_result.modified_files:
                st.write(f"📝 {file_path}")
        
        # Clear selected issues
        st.session_state.selected_issues = []
    
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        st.error(f"Fix operation failed: {e}")


if __name__ == "__main__":
    main()
