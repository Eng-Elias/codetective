"""
NiceGUI application for Codetective - Multi-Agent Code Review Tool.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from nicegui import ui
from nicegui.elements.button import Button
from nicegui.elements.column import Column
from nicegui.elements.drawer import LeftDrawer
from nicegui.elements.label import Label
from nicegui.events import ValueChangeEventArguments

from codetective.models.schemas import ScanResult

try:
    # Try relative imports first (when run as module)
    from codetective.core.config import get_config
    from codetective.core.orchestrator import CodeDetectiveOrchestrator
    from codetective.models.schemas import AgentType, FixConfig, Issue, ScanConfig
    from codetective.utils import FileUtils, GitUtils, SystemUtils
except ImportError:
    # Fall back to absolute imports (when run as script)
    import sys

    # Add the parent directory to the path
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    from codetective.core.config import get_config
    from codetective.core.orchestrator import CodeDetectiveOrchestrator
    from codetective.models.schemas import AgentType, FixConfig, Issue, ScanConfig
    from codetective.utils import FileUtils, GitUtils, SystemUtils


class CodeDetectiveApp:
    """Main NiceGUI application class for Codetective."""

    def __init__(self) -> None:
        self.current_page: str = "project_selection"
        self.scan_results: ScanResult = ScanResult()
        self.selected_issues: list[Issue] = []
        self.project_path: str = ""
        self.selected_files: list[str] = []
        self.scanning_in_progress: bool = False
        self.selected_issue_checkboxes: dict[str, bool] = {}
        self.scan_mode: str = "Full Project Scan"

        # UI components
        self.main_content: Column
        self.sidebar: LeftDrawer
        self.progress_container: Column
        self.file_selection_container: Column
        self.selected_issues_label: Label
        self.proceed_button: Button

        # System info
        self.system_info = SystemUtils.get_system_info()

    def setup_ui(self) -> None:
        """Setup the main UI layout."""
        ui.page_title("Codetective - Multi-Agent Code Review Tool")

        with ui.header().classes("items-center justify-between"):
            ui.label("🔍 Codetective - Multi-Agent Code Review Tool").classes("text-h4")

        with ui.left_drawer().classes("bg-blue-100") as self.sidebar:
            self.setup_sidebar()

        with ui.page_sticky(position="bottom-right", x_offset=20, y_offset=20):
            ui.button("🔄", on_click=self.refresh_page).props("fab color=primary")

        # Main content area
        self.main_content = ui.column().classes("w-full p-4")

        # Show initial page
        self.show_current_page()

    def setup_sidebar(self) -> None:
        """Setup the sidebar navigation."""
        ui.label("Navigation").classes("text-h6 q-mb-md")

        ui.button("📁 Project Selection", on_click=lambda: self.navigate_to("project_selection")).classes("w-full q-mb-sm")

        ui.button("🔍 Scan Results", on_click=lambda: self.navigate_to("scan_results")).classes(
            "w-full q-mb-sm"
        ).bind_enabled_from(self, "scan_results", lambda x: x is not None)

        ui.button("🔧 Fix Application", on_click=lambda: self.navigate_to("fix_application")).classes(
            "w-full q-mb-sm"
        ).bind_enabled_from(self, "selected_issues", lambda x: len(x) > 0)

        ui.separator()

        # System status
        ui.label("System Status").classes("text-h6 q-mt-md q-mb-md")
        ui.label("Tool Availability:").classes("text-subtitle2")

        semgrep_icon = "✅" if self.system_info.semgrep_available else "❌"
        trivy_icon = "✅" if self.system_info.trivy_available else "❌"
        ollama_icon = "✅" if self.system_info.ollama_available else "❌"

        ui.label(f"{semgrep_icon} SemGrep").classes("q-ml-sm")
        ui.label(f"{trivy_icon} Trivy").classes("q-ml-sm")
        ui.label(f"{ollama_icon} Ollama").classes("q-ml-sm")

    def navigate_to(self, page: str) -> None:
        """Navigate to a specific page."""
        self.current_page = page
        self.show_current_page()

    def show_current_page(self) -> None:
        """Show the current page content."""
        self.main_content.clear()

        with self.main_content:
            if self.current_page == "project_selection":
                self.show_project_selection_page()
            elif self.current_page == "scan_results":
                self.show_scan_results_page()
            elif self.current_page == "fix_application":
                self.show_fix_application_page()

    def show_project_selection_page(self) -> None:
        """Show the project selection page."""
        ui.label("📁 Project Selection").classes("text-h4 q-mb-md")

        # Project path input
        with ui.row().classes("w-full items-center q-mb-md"):
            self.project_input = ui.input(
                "Project Path",
                placeholder="Enter the path to your project (e.g., /path/to/project or .)",
                value=self.project_path,
                on_change=self.on_project_path_change,
            ).classes("flex-grow")

            ui.button("Start Detection", on_click=self.validate_project_path).props("color=primary")

        # Project validation and configuration
        self.project_config_container = ui.column().classes("w-full")

        if self.project_path:
            self.show_project_configuration()

    def on_project_path_change(self, e: ValueChangeEventArguments) -> None:
        """Handle project path input change."""
        self.project_path = e.value
        if getattr(self, "file_selection_container", None):
            self.update_file_selection_info()

    def validate_project_path(self) -> None:
        """Validate the project path and show configuration."""
        if not self.project_path:
            ui.notify("Please enter a project path", type="warning")
            return

        try:
            if Path(self.project_path).exists():
                ui.notify(f"✅ Valid path: {Path(self.project_path).absolute()}", type="positive")
                self.show_project_configuration()
            else:
                ui.notify(f"❌ Path does not exist: {self.project_path}", type="negative")
        except Exception as e:
            ui.notify(f"❌ Error validating path: {e}", type="negative")

    def show_project_configuration(self) -> None:
        """Show project configuration options."""
        self.project_config_container.clear()

        with self.project_config_container:
            # Scan mode selection
            ui.label("📋 Scan Mode").classes("text-h5 q-mt-md q-mb-sm")

            self.scan_mode_radio = ui.radio(
                ["Full Project Scan", "Git Diff Only", "Custom File Selection"],
                value="Full Project Scan",
                on_change=self.on_scan_mode_change,
            )

            # File selection container
            self.file_selection_container = ui.column().classes("w-full q-mt-md")
            self.update_file_selection_info()

            # Scan configuration
            ui.label("🔧 Scan Configuration").classes("text-h5 q-mt-md q-mb-sm")

            with ui.row().classes("w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("Select Agents:").classes("text-subtitle1 q-mb-sm")
                    self.use_semgrep = ui.checkbox("SemGrep (Static Analysis)", value=True)
                    self.use_trivy = ui.checkbox("Trivy (Security Scanning)", value=True)
                    self.use_ai_review = ui.checkbox("AI Review (Intelligent Analysis)", value=False)

                    ui.label("Advanced Options:").classes("text-subtitle1 q-mt-md q-mb-sm")
                    self.use_parallel = ui.checkbox("Parallel Execution", value=False)
                    self.force_ai = ui.checkbox("Force AI Review", value=False)

                with ui.column().classes("flex-1"):
                    self.timeout_input = ui.number("Timeout (seconds)", value=900, min=30, max=1800, step=30)

                    self.max_files_input = ui.number("Max Files (0 = unlimited)", value=0, min=0, max=1000, step=10)

            # Ollama Configuration
            ui.label("🤖 Ollama Configuration").classes("text-h5 q-mt-md q-mb-sm")

            with ui.row().classes("w-full"):
                with ui.column().classes("flex-1"):
                    self.ollama_url_input = ui.input(
                        "Ollama Base URL", value="http://localhost:11434", placeholder="http://localhost:11434"
                    ).classes("w-full")

                with ui.column().classes("flex-1"):
                    self.ollama_model_input = ui.input("Ollama Model", value="qwen3:4b", placeholder="qwen3:4b").classes("w-full")

            # Start scan button
            self.start_scan_button = (
                ui.button("🚀 Start Scan", on_click=self.start_scan).classes("w-full q-mt-md").props("size=lg color=primary")
            )

            self.start_scan_button.bind_enabled_from(self, "scanning_in_progress", lambda x: not x)

            # Progress container (hidden by default)
            self.progress_container = ui.column().classes("w-full q-mt-md").style("display: none")
            with self.progress_container:
                self.progress_bar = ui.linear_progress(value=0).classes("w-full")
                self.progress_label = ui.label("").classes("text-center q-mt-sm")

    def on_scan_mode_change(self, e: ValueChangeEventArguments) -> None:
        """Handle scan mode change."""
        self.scan_mode = e.value
        self.update_file_selection_info()

    def update_file_selection_info(self) -> None:
        """Update file selection information based on scan mode."""
        if not self.file_selection_container or not self.project_path:
            return

        self.file_selection_container.clear()

        with self.file_selection_container:
            if self.scan_mode == "Git Diff Only":
                try:
                    diff_files = GitUtils.get_diff_files()
                    if diff_files:
                        self.selected_files = diff_files
                        ui.label(f"🔄 Found {len(diff_files)} modified files in git diff").classes("text-positive")
                        with ui.expansion("View modified files", icon="visibility").classes("w-full q-mt-sm"):
                            for file in diff_files[:10]:  # Show first 10 files
                                ui.label(f"📄 {file}").classes("q-ml-md text-caption")
                            if len(diff_files) > 10:
                                ui.label(f"... and {len(diff_files) - 10} more files").classes("q-ml-md text-caption")
                    else:
                        ui.label("⚠️ No modified files found in git diff").classes("text-warning")
                        self.selected_files = []
                except Exception as e:
                    ui.label(f"❌ Error getting git diff files: {e}").classes("text-negative")
                    self.selected_files = []

            elif self.scan_mode == "Custom File Selection":
                ui.label("📁 Select files and directories to scan:").classes("text-subtitle1 q-mb-sm")
                self.show_file_tree_selector()

            else:  # Full Project Scan
                if GitUtils.is_git_repo(self.project_path):
                    ui.label("🔍 Git repository detected - scanning git-tracked + new untracked files").classes("text-info")
                    try:
                        all_files = GitUtils.get_git_tracked_and_new_files(self.project_path)
                        self.selected_files = all_files
                        ui.label(f"Found {len(all_files)} selectable code files (tracked + new untracked)").classes(
                            "text-positive"
                        )
                    except Exception as e:
                        ui.label(f"Error getting git files: {e}").classes("text-negative")
                        self.selected_files = [self.project_path]
                else:
                    self.selected_files = [self.project_path]
                    ui.label("📁 Non-git directory - scanning all files (respecting .gitignore)").classes("text-info")

    def show_file_tree_selector(self) -> None:
        """Show file tree selector for custom file selection."""
        try:
            if GitUtils.is_git_repo(self.project_path):
                files = GitUtils.get_git_tracked_and_new_files(self.project_path)
                ui.label("🔍 Showing git-tracked files + new untracked files (respecting .gitignore):").classes(
                    "text-caption q-mb-sm"
                )
            else:
                files = FileUtils.get_file_list(
                    [self.project_path],
                    include_patterns=[
                        "*.py",
                        "*.js",
                        "*.ts",
                        "*.jsx",
                        "*.tsx",
                        "*.java",
                        "*.c",
                        "*.cpp",
                        "*.h",
                        "*.hpp",
                        "*.cs",
                        "*.php",
                        "*.rb",
                        "*.go",
                        "*.rs",
                        "*.swift",
                        "*.kt",
                        "*.scala",
                        "*.sh",
                    ],
                    respect_gitignore=True,
                )
                ui.label("📁 Showing all code files (respecting .gitignore):").classes("text-caption q-mb-sm")

            # Build tree structure for ui.tree
            tree_nodes = self.build_tree_structure(files)

            self.selected_files = []

            # Show file tree with NiceGUI tree component
            with ui.scroll_area().classes("h-64 w-full max-w-full border"):
                self.file_tree = ui.tree(
                    tree_nodes, label_key="label", tick_strategy="leaf-filtered", on_tick=self.on_tree_tick
                ).classes("w-full")

            self.selected_files_label = ui.label(f"Selected: {len(self.selected_files)} files").classes("text-info q-mt-sm")

        except Exception as e:
            ui.label(f"❌ Error loading files: {e}").classes("text-negative")

    def build_tree_structure(self, files: List[str]) -> List[Dict]:
        """Build hierarchical tree structure from file list."""
        tree: Dict[str, Any] = {}

        for file_path in files:
            try:
                rel_path = Path(file_path).relative_to(Path(self.project_path))
                parts = rel_path.parts

                current_level = tree
                path_so_far = []

                # Build nested directory structure
                for i, part in enumerate(parts):
                    path_so_far.append(part)

                    if i == len(parts) - 1:  # This is a file
                        current_level[part] = {"type": "file", "path": str(rel_path), "full_path": file_path}
                    else:  # This is a directory
                        if part not in current_level:
                            current_level[part] = {"type": "directory", "children": {}, "path": str(Path(*path_so_far))}
                        current_level = current_level[part]["children"]

            except ValueError:
                continue

        return self.convert_to_tree_nodes(tree)

    def convert_to_tree_nodes(self, tree_dict: Dict, parent_path: str = "") -> List[Dict]:
        """Convert nested dictionary to NiceGUI tree node format."""
        nodes = []

        for name, node_data in sorted(tree_dict.items()):
            if node_data["type"] == "file":
                nodes.append(
                    {
                        "id": node_data["full_path"],
                        "label": f"📄 {name}",
                        "path": node_data["path"],
                        "full_path": node_data["full_path"],
                        "type": "file",
                    }
                )
            else:  # directory
                children = self.convert_to_tree_nodes(node_data["children"], node_data["path"])
                nodes.append(
                    {
                        "id": node_data["path"],
                        "label": f"📁 {name}",
                        "path": node_data["path"],
                        "type": "directory",
                        "children": children,
                    }
                )

        return nodes

    def on_tree_tick(self, e: ValueChangeEventArguments) -> None:
        """Handle tree node selection."""
        # e.value contains the list of selected node IDs
        selected_node_ids = e.value if e.value else []

        # Filter to get only file paths (not directory paths)
        self.selected_files = []
        for node_id in selected_node_ids:
            # Check if this is a file path (files have full absolute paths as IDs)
            if Path(node_id).is_absolute() or "/" in node_id or "\\" in node_id:
                self.selected_files.append(node_id)

        # Update the selected files label
        if hasattr(self, "selected_files_label"):
            self.selected_files_label.text = f"Selected: {len(self.selected_files)} files"

        ui.notify(f"Selected {len(self.selected_files)} files", type="info")

    async def start_scan(self) -> None:
        """Start the scanning process."""
        if self.scanning_in_progress:
            return

        # Validate inputs
        agents = []
        if self.use_semgrep.value:
            agents.append(AgentType.SEMGREP)
        if self.use_trivy.value:
            agents.append(AgentType.TRIVY)
        if self.use_ai_review.value:
            agents.append(AgentType.AI_REVIEW)

        if not agents:
            ui.notify("Please select at least one agent", type="warning")
            return

        if not self.selected_files:
            ui.notify("No files selected for scanning", type="warning")
            return

        self.scanning_in_progress = True
        self.start_scan_button.text = "⏳ Scanning..."

        # Show progress
        self.progress_container.style("display: block")
        self.progress_bar.value = 0
        self.progress_label.text = "Initializing scan..."

        try:
            # Create scan configuration
            scan_config = ScanConfig(
                agents=agents,
                parallel_execution=self.use_parallel.value,
                paths=self.selected_files,
                max_files=int(self.max_files_input.value) if self.max_files_input.value > 0 else None,
            )

            # Initialize orchestrator with Ollama configuration
            config = get_config(
                scan_config=scan_config,
                agent_timeout=self.timeout_input.value,
                ollama_base_url=self.ollama_url_input.value,
                ollama_model=self.ollama_model_input.value,
            )
            orchestrator = CodeDetectiveOrchestrator(config)

            # Update progress
            self.progress_bar.value = 0.25
            self.progress_label.text = f"🔍 Running {self.scan_mode.lower()} scan..."
            await asyncio.sleep(0.1)  # Allow UI to update

            # Run scan in executor to avoid blocking UI
            scan_result = await asyncio.get_event_loop().run_in_executor(None, orchestrator.run_scan, scan_config)

            self.progress_bar.value = 1.0
            self.progress_label.text = "✅ Scan completed!"
            await asyncio.sleep(1)

            # Store results
            self.scan_results = scan_result
            self.selected_issues = []
            self.selected_issue_checkboxes = {}

            # Hide progress
            self.progress_container.style("display: none")

            # Show results summary
            ui.notify(f"Scan completed! Found {scan_result.total_issues} issues", type="positive")

            # Navigate to results
            self.navigate_to("scan_results")

        except Exception as e:
            self.progress_bar.value = 0
            self.progress_label.text = f"❌ Scan failed: {e}"
            await asyncio.sleep(2)
            self.progress_container.style("display: none")
            ui.notify(f"Scan failed: {e}", type="negative")

        finally:
            self.scanning_in_progress = False
            self.start_scan_button.text = "🚀 Start Scan"

    def show_scan_results_page(self) -> None:
        """Show the scan results page."""
        ui.label("🔍 Scan Results").classes("text-h4 q-mb-md")

        if self.scan_results is None:
            ui.label("No scan results available. Please run a scan first.").classes("text-warning")
            return

        scan_result = self.scan_results

        # Results summary
        with ui.row().classes("w-full q-mb-md"):
            with ui.card().classes("flex-1"):
                ui.label("Total Issues").classes("text-subtitle2")
                ui.label(str(scan_result.total_issues)).classes("text-h4 text-primary")

            with ui.card().classes("flex-1"):
                ui.label("Scan Duration").classes("text-subtitle2")
                ui.label(f"{scan_result.scan_duration:.2f}s").classes("text-h4 text-positive")

            with ui.card().classes("flex-1"):
                ui.label("SemGrep Issues").classes("text-subtitle2")
                ui.label(str(len(scan_result.semgrep_results))).classes("text-h4 text-orange")

            with ui.card().classes("flex-1"):
                ui.label("Trivy Issues").classes("text-subtitle2")
                ui.label(str(len(scan_result.trivy_results))).classes("text-h4 text-red")

        # Tabbed interface for results
        with ui.tabs().classes("w-full") as tabs:
            semgrep_tab = ui.tab("🔒 SemGrep Results")
            trivy_tab = ui.tab("🛡️ Trivy Results")
            ai_review_tab = ui.tab("🤖 AI Review Results")

        with ui.tab_panels(tabs, value=semgrep_tab).classes("w-full"):
            with ui.tab_panel(semgrep_tab):
                self.show_issues_tab("SemGrep", scan_result.semgrep_results)

            with ui.tab_panel(trivy_tab):
                self.show_issues_tab("Trivy", scan_result.trivy_results)

            with ui.tab_panel(ai_review_tab):
                self.show_issues_tab("AI Review", scan_result.ai_review_results)

        # Fix selection
        if scan_result.total_issues > 0:
            ui.label("🔧 Fix Selection").classes("text-h5 q-mt-md q-mb-sm")

            ui.button("Select All Issues for Fixing", on_click=self.select_all_issues).classes("w-full q-mb-md")

            # Selected issues info and proceed button
            self.selected_issues_label = ui.label("").classes("text-info q-mb-md")
            self.proceed_button = (
                ui.button("Proceed to Fix Application", on_click=lambda: self.navigate_to("fix_application"))
                .classes("w-full")
                .props("color=primary size=lg")
            )

            self.update_selected_issues_display()

    def show_issues_tab(self, agent_name: str, issues: List[Issue]) -> None:
        """Show issues for a specific agent in a tab."""
        if not issues:
            ui.label(f"No issues found by {agent_name}").classes("text-info")
            return

        ui.label(f"{agent_name} found {len(issues)} issues:").classes("text-subtitle1 q-mb-md")

        # Issues list
        for i, issue in enumerate(issues):
            severity_icons = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}

            severity = getattr(issue.severity, "value", str(issue.severity))
            icon = severity_icons.get(severity, "⚪")

            with ui.expansion(f"{icon} {severity.upper()}: {issue.title}").classes("w-full q-mb-sm"):
                with ui.row().classes("w-full"):
                    with ui.column().classes("flex-1"):
                        ui.label(f"File: {issue.file_path}").classes("text-body2")
                        if issue.line_number:
                            ui.label(f"Line: {issue.line_number}").classes("text-body2")
                        ui.label(f"Description: {issue.description}").classes("text-body2 q-mt-sm")
                        if issue.fix_suggestion:
                            ui.label(f"Suggested Fix: {issue.fix_suggestion}").classes("text-body2 q-mt-sm")

                    with ui.column().classes("flex-none"):
                        ui.label(f"Severity: {icon} {severity.title()}").classes("text-body2")

                        checkbox_key = f"issue_{agent_name}_{i}"
                        ui.checkbox(
                            "Include in fix",
                            value=self.selected_issue_checkboxes.get(checkbox_key, False),
                            on_change=lambda e, issue=issue, key=checkbox_key: self.on_issue_checkbox_change(e, issue, key),
                        )

    def on_issue_checkbox_change(self, e: ValueChangeEventArguments, issue: Issue, checkbox_key: str) -> None:
        """Handle issue checkbox change."""
        self.selected_issue_checkboxes[checkbox_key] = e.value

        if e.value:
            if issue not in self.selected_issues:
                self.selected_issues.append(issue)
        else:
            if issue in self.selected_issues:
                self.selected_issues.remove(issue)

        # Update the display without full page refresh
        self.update_selected_issues_display()

    def update_selected_issues_display(self) -> None:
        """Update the selected issues count and button visibility."""
        if hasattr(self, "selected_issues_label") and self.selected_issues_label:
            if self.selected_issues:
                self.selected_issues_label.text = f"Selected {len(self.selected_issues)} issues for fixing"
                self.selected_issues_label.style("display: block")
                self.proceed_button.style("display: block")
            else:
                self.selected_issues_label.style("display: none")
                self.proceed_button.style("display: none")

    def select_all_issues(self) -> None:
        """Select all issues for fixing."""
        if not self.scan_results:
            return

        all_issues = self.scan_results.semgrep_results + self.scan_results.trivy_results + self.scan_results.ai_review_results

        self.selected_issues = all_issues

        # Update checkbox states
        self.selected_issue_checkboxes = {}
        for i, issue in enumerate(self.scan_results.semgrep_results):
            self.selected_issue_checkboxes[f"issue_SemGrep_{i}"] = True
        for i, issue in enumerate(self.scan_results.trivy_results):
            self.selected_issue_checkboxes[f"issue_Trivy_{i}"] = True
        for i, issue in enumerate(self.scan_results.ai_review_results):
            self.selected_issue_checkboxes[f"issue_AI Review_{i}"] = True

        ui.notify(f"Selected {len(all_issues)} issues for fixing", type="positive")
        self.update_selected_issues_display()

        # Force refresh the current page to update checkbox states
        self.show_current_page()

    def show_fix_application_page(self) -> None:
        """Show the fix application page."""
        ui.label("🔧 Fix Application").classes("text-h4 q-mb-md")

        if not self.selected_issues:
            ui.label("No issues selected for fixing. Please select issues from the scan results.").classes("text-warning")
            return

        ui.label(f"Ready to fix {len(self.selected_issues)} selected issues").classes("text-info q-mb-md")

        # Fix configuration
        ui.label("Fix Configuration").classes("text-h5 q-mb-sm")

        with ui.row().classes("w-full q-mb-md"):
            with ui.column().classes("flex-1"):
                self.fix_agent = (
                    ui.select(["edit", "comment"], label="Fix Agent", value="edit").classes("w-full").style("min-width: 200px")
                )

            with ui.column().classes("flex-1"):
                self.backup_files = ui.checkbox("Create backup files", value=True)
                self.keep_backup = ui.checkbox("Keep backup files after fix completion", value=False)

        # Show selected issues summary
        ui.label("Selected Issues Summary").classes("text-h5 q-mb-sm")

        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for issue in self.selected_issues:
            severity = getattr(issue.severity, "value", str(issue.severity))
            if severity in severity_counts:
                severity_counts[severity] += 1

        with ui.row().classes("w-full q-mb-md"):
            with ui.card().classes("flex-1"):
                ui.label("🟢 Low").classes("text-subtitle2")
                ui.label(str(severity_counts["low"])).classes("text-h4 text-blue")

            with ui.card().classes("flex-1"):
                ui.label("🟡 Medium").classes("text-subtitle2")
                ui.label(str(severity_counts["medium"])).classes("text-h4 text-orange")

            with ui.card().classes("flex-1"):
                ui.label("🟠 High").classes("text-subtitle2")
                ui.label(str(severity_counts["high"])).classes("text-h4 text-red")

            with ui.card().classes("flex-1"):
                ui.label("🔴 Critical").classes("text-subtitle2")
                ui.label(str(severity_counts["critical"])).classes("text-h4 text-red")

        # Apply fixes button
        self.apply_fixes_button = (
            ui.button("🚀 Apply Fixes", on_click=self.apply_fixes).classes("w-full").props("size=lg color=primary")
        )

    async def apply_fixes(self) -> None:
        """Apply fixes to selected issues."""
        # Disable the apply fixes button
        self.apply_fixes_button.props("disable")
        self.apply_fixes_button.text = "⏳ Applying Fixes..."

        # Create fix configuration
        agent_type = AgentType.EDIT if self.fix_agent.value == "edit" else AgentType.COMMENT

        fix_config = FixConfig(
            agents=[agent_type],
        )

        # Show progress inline
        progress_container = ui.column().classes("w-full q-mt-md")
        with progress_container:
            ui.label("Applying Fixes").classes("text-h6")
            progress = ui.linear_progress(value=0).classes("w-full q-mt-md")
            status_label = ui.label("Preparing fixes...").classes("q-mt-sm")

        try:
            # Initialize orchestrator with Ollama configuration
            config = get_config(
                fix_config=fix_config,
                keep_backup=self.keep_backup.value,
                ollama_base_url=self.ollama_url_input.value,
                ollama_model=self.ollama_model_input.value,
            )
            orchestrator = CodeDetectiveOrchestrator(config)

            # Prepare scan data for fix operation
            scan_data = {
                "semgrep_results": [issue.model_dump() for issue in self.selected_issues if "semgrep" in issue.id],
                "trivy_results": [issue.model_dump() for issue in self.selected_issues if "trivy" in issue.id],
                "ai_review_results": [issue.model_dump() for issue in self.selected_issues if "ai-review" in issue.id],
            }

            progress.value = 0.5
            status_label.text = "🔧 Applying fixes..."
            await asyncio.sleep(0.1)

            # Run fix in executor
            fix_result = await asyncio.get_event_loop().run_in_executor(None, orchestrator.run_fix, scan_data, fix_config)

            progress.value = 1.0
            status_label.text = "✅ Fixes applied!"
            await asyncio.sleep(1)

            progress_container.delete()

            # Show results
            ui.notify(f"Fix operation completed in {fix_result.fix_duration:.2f} seconds", type="positive")

            with ui.dialog() as results_dialog, ui.card():
                ui.label("Fix Results").classes("text-h6")

                with ui.row().classes("w-full q-mt-md"):
                    with ui.card().classes("flex-1"):
                        ui.label("Fixed Issues").classes("text-subtitle2")
                        ui.label(str(len(fix_result.fixed_issues))).classes("text-h4 text-positive")

                    with ui.card().classes("flex-1"):
                        ui.label("Failed Issues").classes("text-subtitle2")
                        ui.label(str(len(fix_result.failed_issues))).classes("text-h4 text-negative")

                    with ui.card().classes("flex-1"):
                        ui.label("Modified Files").classes("text-subtitle2")
                        ui.label(str(len(fix_result.modified_files))).classes("text-h4 text-info")

                if fix_result.modified_files:
                    ui.label("Modified Files:").classes("text-subtitle1 q-mt-md")
                    for file_path in fix_result.modified_files:
                        ui.label(f"📝 {file_path}").classes("q-ml-md")

                ui.button("Close", on_click=results_dialog.close).classes("q-mt-md")

            results_dialog.open()

            # Remove fixed issues from the scan results and GUI
            fixed_issue_ids = {issue.id for issue in fix_result.fixed_issues}

            # Filter out fixed issues from scan results
            self.scan_results.semgrep_results = [
                issue for issue in self.scan_results.semgrep_results if issue.id not in fixed_issue_ids
            ]
            self.scan_results.trivy_results = [
                issue for issue in self.scan_results.trivy_results if issue.id not in fixed_issue_ids
            ]
            self.scan_results.ai_review_results = [
                issue for issue in self.scan_results.ai_review_results if issue.id not in fixed_issue_ids
            ]

            # Update total issues count
            self.scan_results.total_issues = (
                len(self.scan_results.semgrep_results)
                + len(self.scan_results.trivy_results)
                + len(self.scan_results.ai_review_results)
            )

            # Clear selected issues
            self.selected_issues = []
            self.selected_issue_checkboxes = {}

            # Refresh the scan results page to show updated issues
            if len(fixed_issue_ids) > 0:
                ui.notify(f"Removed {len(fixed_issue_ids)} fixed issues from the list", type="positive")
                # Navigate back to scan results to show updated list
                self.navigate_to("scan_results")

        except Exception as e:
            progress.value = 0
            status_label.text = f"❌ Fix failed: {e}"
            await asyncio.sleep(2)
            progress_container.delete()
            ui.notify(f"Fix operation failed: {e}", type="negative")

        finally:
            # Re-enable the apply fixes button
            self.apply_fixes_button.props("enable")
            self.apply_fixes_button.text = "🚀 Apply Fixes"

    def refresh_page(self) -> None:
        """Refresh the current page."""
        self.show_current_page()


def create_app() -> CodeDetectiveApp:
    """Create and configure the NiceGUI app."""
    app_instance = CodeDetectiveApp()
    app_instance.setup_ui()
    return app_instance


def main() -> None:
    """Main entry point for the NiceGUI application."""
    create_app()
    ui.run(title="Codetective - Multi-Agent Code Review Tool", port=7891, show=True, reload=False)


if __name__ == "__main__":
    main()
