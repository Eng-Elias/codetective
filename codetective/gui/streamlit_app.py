"""
Streamlit GUI for Codetective - Multi-Agent Code Review Tool.
"""

import streamlit as st
import os
from pathlib import Path
from typing import List, Dict
import time
from streamlit_tree_select import tree_select

try:
    # Try relative imports first (when run as module)
    from codetective.core.config import get_config
    from codetective.core.orchestrator import CodeDetectiveOrchestrator
    from codetective.utils import SystemUtils, FileUtils, GitUtils
    from codetective.models.schemas import ScanConfig, FixConfig, AgentType, Issue
    from codetective.cli.commands import get_git_diff_files
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
    from codetective.utils import SystemUtils, FileUtils, GitUtils
    from codetective.models.schemas import ScanConfig, FixConfig, AgentType, Issue
    from codetective.cli.commands import get_git_diff_files
    from codetective.utils.git_utils import GitUtils


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
if 'selected_files' not in st.session_state:
    st.session_state.selected_files = []
if 'diff_files' not in st.session_state:
    st.session_state.diff_files = []


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
            system_info = SystemUtils.get_system_info()
        
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
                
                # Scan mode selection
                st.subheader("📋 Scan Mode")
                scan_mode = st.radio(
                    "Select scan mode:",
                    ["Full Project Scan", "Git Diff Only", "Custom File Selection"],
                    help="Choose how to select files for scanning"
                )
                
                selected_files = []
                
                if scan_mode == "Git Diff Only":
                    # Git diff mode
                    if st.button("🔍 Load Git Diff Files"):
                        try:
                            os.chdir(project_path)
                            diff_files = get_git_diff_files()
                            st.session_state.diff_files = diff_files
                            if diff_files:
                                st.success(f"Found {len(diff_files)} modified files")
                                for file in diff_files[:10]:  # Show first 10
                                    st.write(f"📄 {Path(file).name}")
                                if len(diff_files) > 10:
                                    st.write(f"... and {len(diff_files) - 10} more files")
                            else:
                                st.warning("No modified files found in git diff")
                        except Exception as e:
                            st.error(f"Error getting git diff: {e}")
                    
                    selected_files = st.session_state.diff_files
                
                elif scan_mode == "Custom File Selection":
                    # File tree selection with checkboxes
                    st.write("**Select Files to Scan:**")
                    
                    # Check if it's a git repository
                    if GitUtils.is_git_repo(project_path):
                        st.info("🔍 Git repository detected - showing git-tracked files only")
                        selected_files = show_git_file_tree_selector(project_path)
                    else:
                        st.info("📁 Non-git directory - showing all files (respecting .gitignore)")
                        selected_files = show_file_tree_selector(project_path)
                
                else:
                    # Full project scan - check if git repo
                    if GitUtils.is_git_repo(project_path):
                        st.info("🔍 Git repository detected - scanning git-tracked files only")
                        selected_files = GitUtils.get_code_files(project_path)
                        if not selected_files:
                            st.warning("No git-tracked code files found")
                    else:
                        selected_files = [project_path]
                
                # Scan configuration
                st.subheader("🔧 Scan Configuration")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Select Agents:**")
                    use_semgrep = st.checkbox("SemGrep (Static Analysis)", value=True)
                    use_trivy = st.checkbox("Trivy (Security Scanning)", value=True)
                    use_ai_review = st.checkbox("AI Review (Intelligent Analysis)", value=False)
                    
                    # Advanced options
                    st.write("**Advanced Options:**")
                    use_parallel = st.checkbox("Parallel Execution", value=False, help="Run agents in parallel for faster scanning")
                    force_ai = st.checkbox("Force AI Review", value=False, help="Enable AI Review even for large file sets (>10 files)")
                
                with col2:
                    timeout = st.number_input(
                        "Timeout (seconds)",
                        min_value=30,
                        max_value=1800,
                        value=300,
                        step=30
                    )
                    
                    max_files = st.number_input(
                        "Max Files (0 = unlimited)",
                        min_value=0,
                        max_value=1000,
                        value=0,
                        step=10,
                        help="Limit the maximum number of files to scan"
                    )
                
                # Smart AI Review handling
                if use_ai_review and scan_mode != "Git Diff Only":
                    if scan_mode == "Full Project Scan":
                        if GitUtils.is_git_repo(project_path):
                            file_count = GitUtils.get_file_count(project_path)
                        else:
                            file_count = count_files_in_path(project_path)
                    else:
                        file_count = len(selected_files)
                    
                    if file_count > 10 and not force_ai:
                        st.warning(f"⚠️ {file_count} files detected. AI Review will be disabled for performance. Enable 'Force AI Review' to override.")
                        use_ai_review = False
                
                # Start scan button
                scan_enabled = (scan_mode == "Full Project Scan" or 
                              (scan_mode == "Git Diff Only" and st.session_state.diff_files) or 
                              (scan_mode == "Custom File Selection" and selected_files))
                
                if st.button("🚀 Start Scan", type="primary", use_container_width=True, disabled=not scan_enabled):
                    start_scan(selected_files, use_semgrep, use_trivy, use_ai_review, timeout, use_parallel, force_ai, max_files, scan_mode)
            
            else:
                st.error(f"❌ Path does not exist: {project_path}")
        
        except Exception as e:
            st.error(f"❌ Error validating path: {e}")


def show_file_tree_selector(project_path: str) -> List[str]:
    """Show an interactive file tree with checkboxes for file selection."""
    try:
        path = Path(project_path)
        
        # Build tree structure for streamlit_tree_select
        nodes = build_tree_nodes(path)
        
        if nodes:
            # Use tree_select component
            return_select = tree_select(
                nodes,
                check_model="all",  # Allow both files and folders to be checked
                expanded=[],  # Start with collapsed tree
                only_leaf_checkboxes=False,  # Allow checkboxes on both files and folders
                show_expand_all=True  # Show expand/collapse all buttons
            )
            
            # Extract selected file paths
            selected_files = []
            if return_select and 'checked' in return_select:
                selected_dirs = []
                selected_individual_files = []
                
                # Separate directories and individual files
                for item_value in return_select['checked']:
                    if item_value.startswith('dir_'):
                        dir_path = item_value.replace('dir_', '')
                        selected_dirs.append(str(Path(project_path) / dir_path))
                    elif item_value.startswith('file_'):
                        file_path = item_value.replace('file_', '')
                        selected_individual_files.append(str(Path(project_path) / file_path))
                
                # Get all files from selected directories (respecting .gitignore)
                for dir_path in selected_dirs:
                    dir_files = FileUtils.get_file_list([dir_path], 
                                            include_patterns=['*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.java', '*.c', '*.cpp', '*.h', '*.hpp', '*.cs', '*.php', '*.rb', '*.go', '*.rs', '*.swift', '*.kt', '*.scala', '*.sh', '*.yaml', '*.yml', '*.json', '*.xml', '*.html', '*.css', '*.scss', '*.less', '*.md', '*.txt'],
                                            respect_gitignore=True)
                    selected_files.extend(dir_files)
                
                # Add individual files
                selected_files.extend(selected_individual_files)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_files = []
                for f in selected_files:
                    if f not in seen:
                        seen.add(f)
                        unique_files.append(f)
                selected_files = unique_files
            
            st.session_state.selected_files = selected_files
            
            if selected_files:
                st.info(f"Selected {len(selected_files)} files for scanning")
            
            return selected_files
        else:
            st.warning("No files found in the specified path")
            return []
    
    except Exception as e:
        st.error(f"Error building file tree: {e}")
        return []


def show_git_file_tree_selector(project_path: str) -> List[str]:
    """Show an interactive git-tracked file tree with checkboxes for file selection."""
    try:
        # Build git-aware tree structure
        nodes = GitUtils.build_git_tree_structure(project_path)
        
        if nodes:
            # Use tree_select component
            return_select = tree_select(
                nodes,
                check_model="all",  # Allow both files and folders to be checked
                expanded=[],  # Start with collapsed tree
                only_leaf_checkboxes=False,  # Allow checkboxes on both files and folders
                show_expand_all=True  # Show expand/collapse all buttons
            )
            
            # Extract selected file paths
            selected_files = []
            if return_select and 'checked' in return_select:
                git_root = GitUtils.get_git_root(project_path)
                if not git_root:
                    return []
                
                selected_dirs = []
                selected_individual_files = []
                
                # Separate directories and individual files
                for item_value in return_select['checked']:
                    if item_value.startswith('dir_'):
                        dir_path = item_value.replace('dir_', '')
                        selected_dirs.append(dir_path)
                    elif item_value.startswith('file_'):
                        file_path = item_value.replace('file_', '')
                        selected_individual_files.append(str(Path(git_root) / file_path))
                
                # Get all git-tracked files from selected directories
                all_git_files = GitUtils.get_code_files(git_root)
                for dir_path in selected_dirs:
                    dir_prefix = f"{dir_path}/"
                    for git_file in all_git_files:
                        try:
                            rel_path = str(Path(git_file).relative_to(Path(git_root)))
                            if rel_path.startswith(dir_prefix) or rel_path.startswith(dir_path.replace('/', os.sep)):
                                selected_files.append(git_file)
                        except ValueError:
                            continue
                
                # Add individual files
                selected_files.extend(selected_individual_files)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_files = []
                for f in selected_files:
                    if f not in seen:
                        seen.add(f)
                        unique_files.append(f)
                selected_files = unique_files
            
            st.session_state.selected_files = selected_files
            
            if selected_files:
                st.info(f"Selected {len(selected_files)} git-tracked files for scanning")
            
            return selected_files
        else:
            st.warning("No git-tracked files found in the repository")
            return []
    
    except Exception as e:
        st.error(f"Error building git file tree: {e}")
        return []


def build_tree_nodes(path: Path, max_depth: int = 3, current_depth: int = 0, project_root: Path = None) -> List[Dict]:
    """Build tree nodes for streamlit_tree_select component."""
    nodes = []
    
    if current_depth >= max_depth:
        return nodes
    
    if project_root is None:
        project_root = path
    
    # Load .gitignore patterns for filtering
    gitignore_patterns = FileUtils.load_gitignore_patterns(str(project_root))
    
    try:
        # Get directories and files separately
        items = list(path.iterdir())
        dirs = [item for item in items if item.is_dir() and not item.name.startswith('.')]
        files = [item for item in items if item.is_file() and not item.name.startswith('.')]
        
        # Filter out ignored directories and files
        dirs = [d for d in dirs if not FileUtils.is_ignored_by_git(d, project_root, gitignore_patterns)]
        files = [f for f in files if not FileUtils.is_ignored_by_git(f, project_root, gitignore_patterns)]
        
        # Add directories first
        for dir_path in sorted(dirs):
            try:
                children = build_tree_nodes(dir_path, max_depth, current_depth + 1, project_root)
                # Add directory even if no children (user can select empty dirs)
                node = {
                    "label": f"📁 {dir_path.name}",
                    "value": f"dir_{dir_path.relative_to(project_root)}",
                }
                if children:
                    node["children"] = children
                nodes.append(node)
            except (PermissionError, OSError):
                continue
        
        # Add files
        for file_path in sorted(files):
            # Filter for code files
            if file_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh', '.yaml', '.yml', '.json', '.xml', '.html', '.css', '.scss', '.less', '.md', '.txt']:
                node = {
                    "label": f"📄 {file_path.name}",
                    "value": f"file_{file_path.relative_to(project_root)}"
                }
                nodes.append(node)
    
    except (PermissionError, OSError):
        pass
    
    return nodes


def count_files_in_path(project_path: str) -> int:
    """Count the number of scannable files in a project path (respecting .gitignore)."""
    try:
        files = FileUtils.get_file_list([project_path], 
                            include_patterns=['*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.java', '*.c', '*.cpp', '*.h', '*.hpp', '*.cs', '.php', '*.rb', '*.go', '*.rs', '*.swift', '*.kt', '*.scala', '*.sh'],
                            respect_gitignore=True)
        return len(files)
    except Exception:
        return 0


def start_scan(selected_files: List[str], use_semgrep: bool, use_trivy: bool, 
               use_ai_review: bool, timeout: int, use_parallel: bool, force_ai: bool, 
               max_files: int, scan_mode: str):
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
    
    if not selected_files:
        st.error("No files selected for scanning")
        return
    
    # Create scan configuration
    scan_config = ScanConfig(
        agents=agents,
        timeout=timeout,
        paths=selected_files,
        max_files=max_files if max_files > 0 else None,
        parallel_execution=use_parallel
    )
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize orchestrator
        config = get_config()
        orchestrator = CodeDetectiveOrchestrator(config)
        
        # Set parallel execution flag if needed
        if use_parallel:
            orchestrator._parallel_execution = True
        
        # Run scan
        scan_info = f"🔍 Running {scan_mode.lower()} scan..."
        if use_parallel:
            scan_info += " (parallel mode)"
        status_text.text(scan_info)
        progress_bar.progress(25)
        
        scan_result = orchestrator.run_scan(scan_config)
        
        progress_bar.progress(100)
        status_text.text("✅ Scan completed!")
        
        # Store results in session state
        st.session_state.scan_results = scan_result
        
        # Show summary with enhanced info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Issues Found", scan_result.total_issues)
        with col2:
            st.metric("Scan Duration", f"{scan_result.scan_duration:.2f}s")
        with col3:
            st.metric("Files Scanned", len(selected_files))
        
        # Show agent performance if available
        if hasattr(scan_result, 'agent_results') and scan_result.agent_results:
            st.subheader("Agent Performance")
            for agent_result in scan_result.agent_results:
                status_icon = "✅" if agent_result.success else "❌"
                st.write(f"{status_icon} {agent_result.agent_type.value.title()}: {len(agent_result.issues)} issues in {agent_result.execution_time:.2f}s")
        
        st.success(f"Scan completed! Found {scan_result.total_issues} issues")
        
        # Auto-navigate to results
        time.sleep(1)
        st.session_state.current_page = "scan_results"
        st.rerun()
    
    except Exception as e:
        progress_bar.progress(0)
        status_text.text("")
        st.error(f"Scan failed: {e}")
        st.exception(e)  # Show full traceback for debugging


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
