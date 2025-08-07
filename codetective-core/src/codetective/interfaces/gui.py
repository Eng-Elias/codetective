"""
Streamlit GUI interface for codetective.
"""

import asyncio
from enum import Enum
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time
import os

from codetective.models.interface_models import GUIState
from codetective.models.configuration import SemgrepConfig, TrivyConfig, AIReviewConfig, AgentConfig
from codetective.utils.configuration_manager import ConfigurationManager
from codetective.utils.git_repository_manager import GitRepositoryManager
from codetective.utils.file_processor import FileProcessor
from codetective.utils.logger import Logger
from codetective.workflow.orchestrator import WorkflowOrchestrator

class PageEnum(Enum):
    SETUP = "setup"
    FILE_SELECTION = "file_selection"
    AGENT_CONFIG = "agent_config"
    EXECUTION = "execution"
    RESULTS = "results"


class StreamlitGUI:
    """
    Streamlit-based GUI for the codetective multi-agent code review tool.
    
    This class provides a web-based interface for configuring and running
    code review workflows with multiple analysis agents.
    """
    
    def __init__(self):
        """Initialize the Streamlit GUI."""
        self.logger = Logger.get_logger("gui.streamlit")
        self.config_manager = None
        self.orchestrator = None
        self.git_manager = None
        self.file_processor = None
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if "gui_state" not in st.session_state:
            st.session_state.gui_state = GUIState()
        
        if "workflow_results" not in st.session_state:
            st.session_state.workflow_results = None
        
        if "execution_logs" not in st.session_state:
            st.session_state.execution_logs = []
    
    def run(self) -> None:
        """Run the Streamlit GUI application."""
        st.set_page_config(
            page_title="Codetective - Multi-Agent Code Review",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Main title and description
        st.title("🔍 Codetective")
        st.markdown("**Multi-Agent Code Review Tool**")
        st.markdown("Analyze your code with Semgrep, Trivy, and AI-powered review agents.")
        
        # Sidebar for configuration
        self._render_sidebar()
        
        # Main content area
        if st.session_state.gui_state.current_page == PageEnum.SETUP.value:
            self._render_setup_page()
        elif st.session_state.gui_state.current_page == PageEnum.FILE_SELECTION.value:
            self._render_file_selection_page()
        elif st.session_state.gui_state.current_page == PageEnum.AGENT_CONFIG.value:
            self._render_agent_config_page()
        elif st.session_state.gui_state.current_page == PageEnum.EXECUTION.value:
            self._render_execution_page()
        elif st.session_state.gui_state.current_page == PageEnum.RESULTS.value:
            self._render_results_page()
    
    def _render_sidebar(self) -> None:
        """Render the sidebar with navigation and status."""
        with st.sidebar:
            st.header("Navigation")
            
            # Page navigation
            pages = {
                PageEnum.SETUP.value: "🏠 Project Setup",
                PageEnum.FILE_SELECTION.value: "📁 File Selection", 
                PageEnum.AGENT_CONFIG.value: "⚙️ Agent Configuration",
                PageEnum.EXECUTION.value: "🚀 Execution",
                PageEnum.RESULTS.value: "📊 Results"
            }
            
            for page_key, page_name in pages.items():
                if st.button(page_name, key=f"nav_{page_key}"):
                    st.session_state.gui_state.current_page = page_key
                    st.rerun()
            
            st.divider()
            
            # Status information
            st.header("Status")
            gui_state = st.session_state.gui_state
            
            # Project status
            if gui_state.project_path:
                st.success(f"✅ Project: {Path(gui_state.project_path).name}")
            else:
                st.warning("⚠️ No project selected")
            
            # File selection status
            if gui_state.selected_files:
                st.success(f"✅ Files: {len(gui_state.selected_files)} selected")
            else:
                st.warning("⚠️ No files selected")
            
            # Agent status
            if gui_state.selected_agents:
                st.success(f"✅ Agents: {len(gui_state.selected_agents)} enabled")
            else:
                st.warning("⚠️ No agents selected")
            
            st.divider()
            
            # Quick actions
            st.header("Quick Actions")
            if st.button("🔄 Reset All", key="reset_all"):
                st.session_state.gui_state = GUIState()
                st.session_state.workflow_results = None
                st.session_state.execution_logs = []
                st.rerun()
    
    def _render_setup_page(self) -> None:
        """Render the project setup page."""
        st.header("🏠 Project Setup")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Select Project Directory")
            
            # Project path input
            project_path = st.text_input(
                "Project Path",
                value=st.session_state.gui_state.project_path or "",
                placeholder="Enter the path to your project directory",
                help="Select the root directory of your project to analyze"
            )
            
            if project_path and Path(project_path).exists():
                st.session_state.gui_state.project_path = project_path
                
                # Initialize managers
                self._initialize_managers(Path(project_path))
                
                # Show project information
                self._show_project_info(Path(project_path))
                
                # Navigation button
                if st.button("📁 Continue to File Selection", key="continue_files"):
                    st.session_state.gui_state.current_page = PageEnum.FILE_SELECTION.value
                    st.rerun()
            
            elif project_path:
                st.error("❌ Directory does not exist. Please enter a valid path.")
        
        with col2:
            st.subheader("Quick Start")
            st.markdown("""
            **Steps to get started:**
            
            1. 📁 Select your project directory
            2. 📋 Choose files to analyze  
            3. ⚙️ Configure analysis agents
            4. 🚀 Run the analysis
            5. 📊 Review results
            
            **Supported project types:**
            - Python projects
            - JavaScript/Node.js
            - Java projects
            - Go projects
            - And more...
            """)
    
    def _initialize_managers(self, project_path: Path) -> None:
        """Initialize manager instances for the project."""
        try:
            # Initialize configuration manager
            self.config_manager = ConfigurationManager()
            
            # Initialize Git repository manager
            self.git_manager = GitRepositoryManager(project_path)
            
            # Initialize file processor
            self.file_processor = FileProcessor(project_path)
            
            # Initialize workflow orchestrator
            self.orchestrator = WorkflowOrchestrator(self.config_manager)
            
            self.logger.info(f"Initialized managers for project: {project_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            st.error(f"❌ Failed to initialize project managers: {e}")
    
    def _show_project_info(self, project_path: Path) -> None:
        """Show information about the selected project."""
        st.success(f"✅ Project loaded: **{project_path.name}**")
        
        # Project statistics
        if self.file_processor:
            stats = self.file_processor.get_file_statistics()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Files", stats.total_files)
            with col2:
                st.metric("Code Files", stats.code_files)
            with col3:
                st.metric("Total Size", f"{stats.total_size_mb:.1f} MB")
            with col4:
                st.metric("Languages", len(stats.file_types))
        
        # Git information
        if self.git_manager and self.git_manager.is_git_repository():
            git_info = self.git_manager.get_repository_info()
            
            with st.expander("📋 Git Repository Information"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Branch:** {git_info.get('current_branch', 'unknown')}")
                st.session_state.gui_state.current_page = PageEnum.FILE_SELECTION.value
                st.rerun()
        elif project_path:
            st.error("❌ Directory does not exist. Please enter a valid path.")
        
        with col2:
            st.subheader("Quick Start")
            st.markdown("""
            **Steps to get started:**
            
            1. 📁 Select your project directory
            2. 📋 Choose files to analyze  
            3. ⚙️ Configure analysis agents
            4. 🚀 Run the analysis
            5. 📊 Review results
            
            **Supported project types:**
            - Python projects
            - JavaScript/Node.js
            - Java projects
            - Go projects
            - And more...
            """)
    
    def _initialize_managers(self, project_path: Path) -> None:
        """Initialize manager instances for the project."""
        try:
            # Initialize configuration manager
            self.config_manager = ConfigurationManager()
            
            # Initialize Git repository manager
            self.git_manager = GitRepositoryManager(project_path)
            
            # Initialize file processor
            self.file_processor = FileProcessor(project_path)
            
            # Initialize workflow orchestrator
            self.orchestrator = WorkflowOrchestrator(self.config_manager)
            
            self.logger.info(f"Initialized managers for project: {project_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            st.error(f"❌ Failed to initialize project managers: {e}")
    
    def _show_project_info(self, project_path: Path) -> None:
        """Show information about the selected project."""
        st.success(f"✅ Project loaded: **{project_path.name}**")
        
        # Project statistics
        if self.file_processor:
            stats = self.file_processor.get_file_statistics()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Files", stats.total_files)
            with col2:
                st.metric("Code Files", stats.code_files)
            with col3:
                st.metric("Total Size", f"{stats.total_size_mb:.1f} MB")
            with col4:
                st.metric("Languages", len(stats.file_types))
        
        # Git information
        if self.git_manager and self.git_manager.is_git_repository():
            git_info = self.git_manager.get_repository_info()
            
            with st.expander("📋 Git Repository Information"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Branch:** {git_info.get('current_branch', 'unknown')}")
                    st.write(f"**Commits:** {git_info.get('commit_count', 0)}")
                with col2:
                    st.write(f"**Modified Files:** {git_info.get('modified_files', 0)}")
                    st.write(f"**Untracked Files:** {git_info.get('untracked_files', 0)}")
    
    def _render_file_selection_page(self) -> None:
        """Render the file selection page."""
        st.header("📁 File Selection")
        
        if not st.session_state.gui_state.project_path:
            st.warning("⚠️ Please select a project directory first.")
            if st.button("🏠 Go to Project Setup"):
                st.session_state.gui_state.current_page = PageEnum.SETUP.value
                st.rerun()
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Select Files to Analyze")
            
            # File discovery options
            with st.expander("🔍 File Discovery Options"):
                include_patterns = st.text_area(
                    "Include Patterns (one per line)",
                    value="*.py\n*.js\n*.jsx\n*.ts\n*.tsx\n*.java\n*.go",
                    help="Glob patterns for files to include"
                )
                
                exclude_patterns = st.text_area(
                    "Exclude Patterns (one per line)", 
                    value="**/node_modules/**\n**/venv/**\n**/__pycache__/**\n**/build/**\n**/dist/**",
                    help="Glob patterns for files to exclude"
                )
                
                max_file_size = st.slider(
                    "Maximum File Size (MB)",
                    min_value=1,
                    max_value=100,
                    value=10,
                    help="Skip files larger than this size"
                )
            
            # Discover files
            if st.button("🔍 Discover Files", key="discover_files"):
                self._discover_files(include_patterns, exclude_patterns, max_file_size)
            
            # Show discovered files
            if hasattr(st.session_state.gui_state, 'discovered_files') and st.session_state.gui_state.discovered_files:
                self._show_file_selection_interface()
        
        with col2:
            st.subheader("Selection Summary")
            
            if st.session_state.gui_state.selected_files:
                st.success(f"✅ {len(st.session_state.gui_state.selected_files)} files selected")
                
                # Show selected files
                with st.expander("📋 Selected Files"):
                    for file_path in st.session_state.gui_state.selected_files:
                        st.write(f"• {file_path}")
                
                # Navigation button
                if st.button("⚙️ Continue to Agent Configuration", key="continue_agents"):
                    st.session_state.gui_state.current_page = PageEnum.AGENT_CONFIG.value
                    st.rerun()
            else:
                st.warning("⚠️ No files selected")
    
    def _discover_files(self, include_patterns: str, exclude_patterns: str, max_file_size: int) -> None:
        """Discover files based on the specified patterns."""
        try:
            include_list = [p.strip() for p in include_patterns.split('\n') if p.strip()]
            exclude_list = [p.strip() for p in exclude_patterns.split('\n') if p.strip()]
            
            # Use file processor to discover files
            discovered_files = self.file_processor.discover_files(
                include_patterns=include_list,
                exclude_patterns=exclude_list,
                max_size_mb=max_file_size
            )
            
            st.session_state.gui_state.discovered_files = [str(f) for f in discovered_files]
            st.success(f"✅ Discovered {len(discovered_files)} files")
        
        except Exception as e:
            st.error(f"❌ File discovery failed: {e}")
    
    def _show_file_selection_interface(self) -> None:
        """Show the file selection interface."""
        discovered_files = st.session_state.gui_state.discovered_files
        
        # Selection options
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Select All", key="select_all"):
                st.session_state.gui_state.selected_files = discovered_files.copy()
                st.rerun()
        
        with col2:
            if st.button("❌ Clear All", key="clear_all"):
                st.session_state.gui_state.selected_files = []
                st.rerun()
        
        with col3:
            if st.button("🔄 Refresh", key="refresh_files"):
                st.rerun()
        
        # File list with checkboxes
        st.subheader(f"Files Found ({len(discovered_files)})")
        
        # Group files by directory for better organization
        files_by_dir = {}
        for file_path in discovered_files:
            dir_path = str(Path(file_path).parent)
            if dir_path not in files_by_dir:
                files_by_dir[dir_path] = []
            files_by_dir[dir_path].append(file_path)
        
        # Show files grouped by directory
        for dir_path, files in sorted(files_by_dir.items()):
            with st.expander(f"📁 {dir_path} ({len(files)} files)"):
                for file_path in sorted(files):
                    file_name = Path(file_path).name
                    is_selected = file_path in st.session_state.gui_state.selected_files
                    
                    if st.checkbox(file_name, value=is_selected, key=f"file_{file_path}"):
                        if file_path not in st.session_state.gui_state.selected_files:
                            st.session_state.gui_state.selected_files.append(file_path)
                    else:
                        if file_path in st.session_state.gui_state.selected_files:
                            st.session_state.gui_state.selected_files.remove(file_path)
    
    def _render_agent_config_page(self) -> None:
        """Render the agent configuration page."""
        st.header("⚙️ Agent Configuration")
        
        if not st.session_state.gui_state.selected_files:
            st.warning("⚠️ Please select files to analyze first.")
            if st.button("📁 Go to File Selection"):
                st.session_state.gui_state.current_page = PageEnum.FILE_SELECTION.value
                st.rerun()
            return
        
        st.subheader("Configure Analysis Agents")
        
        # Agent selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Semgrep Agent
            self._render_semgrep_config()
            
            st.divider()
            
            # Trivy Agent
            self._render_trivy_config()
            
            st.divider()
            
            # AI Review Agent
            self._render_ai_review_config()
            
            st.divider()
            
            # Output Agents
            self._render_output_agent_config()
        
        with col2:
            st.subheader("Configuration Summary")
            
            # Show selected agents
            if st.session_state.gui_state.selected_agents:
                st.success(f"✅ {len(st.session_state.gui_state.selected_agents)} agents enabled")
                
                for agent in st.session_state.gui_state.selected_agents:
                    st.write(f"• {agent}")
                
                # Navigation button
                if st.button("🚀 Continue to Execution", key="continue_execution"):
                    st.session_state.gui_state.current_page = PageEnum.EXECUTION.value
                    st.rerun()
            else:
                st.warning("⚠️ No agents selected")

    def _render_semgrep_config(self) -> None:
        """Render Semgrep agent configuration."""
        with st.expander("🔍 Semgrep - Static Analysis", expanded=True):
            enable_semgrep = st.checkbox("Enable Semgrep", value=True, key="enable_semgrep")
            
            if enable_semgrep:
                if "semgrep" not in st.session_state.gui_state.selected_agents:
                    st.session_state.gui_state.selected_agents.append("semgrep")
            else:
                if "semgrep" in st.session_state.gui_state.selected_agents:
                    st.session_state.gui_state.selected_agents.remove("semgrep")

    def _render_trivy_config(self) -> None:
        """Render Trivy agent configuration."""
        with st.expander("🛡️ Trivy - Security Scanner"):
            enable_trivy = st.checkbox("Enable Trivy", value=True, key="enable_trivy")
            
            if enable_trivy:
                if "trivy" not in st.session_state.gui_state.selected_agents:
                    st.session_state.gui_state.selected_agents.append("trivy")
            else:
                if "trivy" in st.session_state.gui_state.selected_agents:
                    st.session_state.gui_state.selected_agents.remove("trivy")

    def _render_ai_review_config(self) -> None:
        """Render AI review agent configuration."""
        with st.expander("🤖 AI Review - Intelligent Analysis"):
            enable_ai = st.checkbox("Enable AI Review", value=False, key="enable_ai")
            
            if enable_ai:
                if "ai_review" not in st.session_state.gui_state.selected_agents:
                    st.session_state.gui_state.selected_agents.append("ai_review")
            else:
                if "ai_review" in st.session_state.gui_state.selected_agents:
                    st.session_state.gui_state.selected_agents.remove("ai_review")

    def _render_output_agent_config(self) -> None:
        """Render output agent configuration."""
        with st.expander("📤 Output Agents"):
            output_comment = st.checkbox("Generate Comments", value=True, key="output_comment")
            if output_comment and "output_comment" not in st.session_state.gui_state.selected_agents:
                st.session_state.gui_state.selected_agents.append("output_comment")
            elif not output_comment and "output_comment" in st.session_state.gui_state.selected_agents:
                st.session_state.gui_state.selected_agents.remove("output_comment")

    def _render_execution_page(self) -> None:
        """Render the execution page."""
        st.header("🚀 Execution")
        
        gui_state = st.session_state.gui_state
        
        if not gui_state.project_path or not gui_state.selected_files or not gui_state.selected_agents:
            st.warning("⚠️ Please complete project setup, file selection, and agent configuration first.")
            if st.button("🏠 Go to Project Setup"):
                st.session_state.gui_state.current_page = PageEnum.SETUP.value
                st.rerun()
            return
        
        self._show_execution_summary()
        
        if st.button("🚀 Run Analysis", key="run_analysis"):
            st.session_state.execution_logs = []
            st.session_state.workflow_results = None
            self._run_analysis()

    def _show_execution_summary(self) -> None:
        """Show a summary of the planned execution."""
        st.subheader("Execution Summary")
        st.write(f"**Project:** {Path(st.session_state.gui_state.project_path).name}")
        st.write(f"**Files:** {len(st.session_state.gui_state.selected_files)} selected")
        st.write(f"**Agents:** {', '.join(st.session_state.gui_state.selected_agents)}")

    def _run_analysis(self) -> None:
        """Run the analysis workflow directly."""
        gui_state = st.session_state.gui_state

        try:
            with st.spinner("🚀 Starting analysis... This may take a moment."):
                # Create default configurations for selected agents
                self._create_default_config(gui_state)

                # Initialize orchestrator if not already done
                if not self.orchestrator:
                    self.orchestrator = WorkflowOrchestrator(self.config_manager)

                # Run the workflow asynchronously
                workflow_state = asyncio.run(self.orchestrator.execute_workflow(
                    target_files=[Path(f) for f in gui_state.selected_files],
                    selected_agents=gui_state.selected_agents
                ))

                # Process and store results
                st.session_state.workflow_results = self._process_results(workflow_state)
                st.success("✅ Analysis complete! Results loaded.")
                st.session_state.gui_state.current_page = PageEnum.RESULTS.value
                st.rerun()

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            st.error(f"❌ Analysis failed: {e}")

    def _create_default_config(self, gui_state: GUIState) -> None:
        """Create default agent configurations based on GUI state."""
        if "semgrep" in gui_state.selected_agents:
            self.config_manager.set_agent_config("semgrep", SemgrepConfig(enabled=True))
        
        if "trivy" in gui_state.selected_agents:
            self.config_manager.set_agent_config("trivy", TrivyConfig(enabled=True, severity_filter=["CRITICAL", "HIGH"]))

        if "ai_review" in gui_state.selected_agents:
            self.config_manager.set_agent_config("ai_review", AIReviewConfig(enabled=True))

        if "output_comment" in gui_state.selected_agents:
            self.config_manager.set_agent_config("output_comment", AgentConfig(enabled=True))

    def _process_results(self, workflow_state) -> dict:
        """Process workflow state into a dictionary for display."""
        results_data = {
            "scan_id": workflow_state.scan_id,
            "total_findings": workflow_state.get_total_findings_count(),
            "semgrep_findings": len(workflow_state.semgrep_results.findings) if workflow_state.semgrep_results else 0,
            "trivy_findings": sum(len(r.vulnerabilities) for r in workflow_state.trivy_results.results) if workflow_state.trivy_results else 0,
            "ai_review_findings": len(workflow_state.ai_review_results.issues) if workflow_state.ai_review_results else 0,
            "execution_time": round(workflow_state.metadata.get("execution_time", 0), 2),
            "full_results": workflow_state.to_dict()
        }
        return results_data

    def _render_results_page(self) -> None:
        """Render the results page."""
        st.header("📊 Results")
        
        if not st.session_state.workflow_results:
            st.warning("⚠️ No results available. Please run an analysis first.")
            if st.button("🚀 Go to Execution"):
                st.session_state.gui_state.current_page = PageEnum.EXECUTION.value
                st.rerun()
            return
        
        st.json(st.session_state.workflow_results)
        
        results = st.session_state.workflow_results
        
        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Findings", results["total_findings"])
        
        with col2:
            st.metric("Semgrep Issues", results["semgrep_findings"])
        
        with col3:
            st.metric("Security Vulns", results["trivy_findings"])
        
        with col4:
            st.metric("AI Suggestions", results["ai_review_findings"])
        
        # Results visualization
        st.subheader("📈 Findings Overview")
        
        # Create sample data for visualization
        findings_data = {
            "Agent": ["Semgrep", "Trivy", "AI Review"],
            "Findings": [results["semgrep_findings"], results["trivy_findings"], results["ai_review_findings"]]
        }
        
        fig = px.bar(findings_data, x="Agent", y="Findings", title="Findings by Agent")
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed results tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🔍 Semgrep", "🛡️ Trivy", "🤖 AI Review"])
        
        with tab1:
            st.subheader("Analysis Summary")
            st.write(f"**Scan ID:** {results['scan_id']}")
            st.write(f"**Execution Time:** {results['execution_time']} seconds")
            st.write(f"**Total Issues:** {results['total_findings']}")
            
            # Export options
            st.subheader("📤 Export Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Export JSON"):
                    st.download_button(
                        "Download JSON",
                        json.dumps(results, indent=2),
                        "codetective_results.json",
                        "application/json"
                    )
            
            with col2:
                if st.button("📊 Export CSV"):
                    st.write("CSV export would be implemented here")
            
            with col3:
                if st.button("📝 Export Report"):
                    st.write("Report export would be implemented here")
        
        with tab2:
            st.subheader("Semgrep Static Analysis Results")
            st.write("Detailed Semgrep findings would be displayed here")
        
        with tab3:
            st.subheader("Trivy Security Scan Results")
            st.write("Detailed Trivy vulnerability findings would be displayed here")
        
        with tab4:
            st.subheader("AI Review Results")
            st.write("Detailed AI-powered code review suggestions would be displayed here")


def main():
    """Main entry point for the Streamlit GUI."""
    gui = StreamlitGUI()
    gui.run()

if __name__ == "__main__":
    main()

def st_run():
    from streamlit.web import cli as st_cli
    print(__file__)
    st_cli.main_run([__file__])