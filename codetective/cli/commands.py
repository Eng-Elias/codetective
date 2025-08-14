"""
CLI commands implementation for Codetective.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..core.config import get_config
from ..core.utils import get_system_info, validate_paths
from ..core.orchestrator import CodeDetectiveOrchestrator
from ..models.schemas import AgentType, Issue, ScanConfig, FixConfig, SeverityLevel


console = Console()


def get_git_diff_files() -> List[str]:
    """Get list of new/modified files from git diff."""
    try:
        all_files = []
        
        # Get staged files (files added to index)
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            staged_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            all_files.extend(staged_files)
            console.print(f"[blue]Found {len(staged_files)} staged files[/blue]")
        
        # Get unstaged files (modified but not staged)
        result = subprocess.run(
            ['git', 'diff', '--name-only'],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            unstaged_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            all_files.extend(unstaged_files)
            console.print(f"[blue]Found {len(unstaged_files)} unstaged files[/blue]")
        
        # Get untracked files (new files not in git)
        result = subprocess.run(
            ['git', 'ls-files', '--others', '--exclude-standard'],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            untracked_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            all_files.extend(untracked_files)
            console.print(f"[blue]Found {len(untracked_files)} untracked files[/blue]")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path in all_files:
            if file_path and file_path not in seen:
                seen.add(file_path)
                unique_files.append(file_path)
        
        # Convert to absolute paths and filter existing files
        diff_files = []
        for file_path in unique_files:
            full_path = Path(file_path).resolve()
            if full_path.exists():
                diff_files.append(str(full_path))
            else:
                console.print(f"[yellow]Warning: File not found: {file_path}[/yellow]")
        
        return diff_files
        
    except Exception as e:
        console.print(f"[red]Error getting git diff: {e}[/red]")
        return []


def _display_scan_results_in_terminal(scan_result, console):
    """Display scan results in terminal format."""
    # Show detailed issues by type
    all_issues = []
    all_issues.extend(scan_result.semgrep_results)
    all_issues.extend(scan_result.trivy_results)
    all_issues.extend(scan_result.ai_review_results)
    
    if all_issues:
        console.print(f"\n[bold red]Issues Found ({len(all_issues)}):[/bold red]")
        
        # Group issues by severity
        severity_groups = {}
        for issue in all_issues:
            severity = getattr(issue, 'severity', 'UNKNOWN')
            if hasattr(severity, 'value'):
                severity = severity.value
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(issue)
        
        # Display issues by severity
        severity_colors = {
            SeverityLevel.CRITICAL.value: 'bright_red',
            SeverityLevel.HIGH.value: 'red',
            SeverityLevel.MEDIUM.value: 'yellow',
            SeverityLevel.LOW.value: 'blue',
            SeverityLevel.INFO.value: 'green'
        }
        
        for severity in [SeverityLevel.CRITICAL.value, SeverityLevel.HIGH.value, SeverityLevel.MEDIUM.value, SeverityLevel.LOW.value, SeverityLevel.INFO.value]:
            if severity in severity_groups:
                color = severity_colors.get(severity, 'white')
                console.print(f"\n[bold {color}]{severity} ({len(severity_groups[severity])} issues):[/bold {color}]")
                
                for issue in severity_groups[severity]:
                    if isinstance(issue, Issue):
                        if hasattr(issue, 'title'):
                            console.print(f"  • {issue.title}")
                        if hasattr(issue, 'file_path'):
                            console.print(f"    File: {issue.file_path} {" : " + str(issue.line_number) if hasattr(issue, 'line_number') and issue.line_number else ''}")
                        if hasattr(issue, 'rule_id'):
                            console.print(f"    Rule ID: {issue.rule_id}")
                        if hasattr(issue, 'description'):
                            console.print(f"    {issue.description}")
                        if hasattr(issue, 'fix_suggestion'):
                            console.print(f"    Fix suggestion: {issue.fix_suggestion}")

@click.group()
@click.version_option()
def cli():
    """Codetective - Multi-Agent Code Review Tool"""
    pass


@cli.command()
def info():
    """Check system compatibility and tool availability."""
    console.print("[bold blue]Codetective System Information[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Checking system compatibility...", total=None)
        system_info = get_system_info()
        progress.update(task, completed=True)
    
    # Create system info table
    table = Table(title="System Compatibility Check")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Version", style="yellow")
    
    # Add rows for each component
    table.add_row(
        "Python",
        "✅ Available" if system_info.python_version else "❌ Not Available",
        system_info.python_version or "Unknown"
    )
    
    table.add_row(
        "Codetective",
        "✅ Available",
        system_info.codetective_version
    )
    
    table.add_row(
        "SemGrep",
        "✅ Available" if system_info.semgrep_available else "❌ Not Available",
        system_info.semgrep_version or "Not installed"
    )
    
    table.add_row(
        "Trivy",
        "✅ Available" if system_info.trivy_available else "❌ Not Available",
        system_info.trivy_version or "Not installed"
    )
    
    table.add_row(
        "Ollama",
        "✅ Available" if system_info.ollama_available else "❌ Not Available",
        system_info.ollama_version or "Not running"
    )
    
    console.print(table)
    
    # Show recommendations if tools are missing
    missing_tools = []
    if not system_info.semgrep_available:
        missing_tools.append("SemGrep: pip install semgrep")
    if not system_info.trivy_available:
        missing_tools.append("Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/")
    if not system_info.ollama_available:
        missing_tools.append("Ollama: https://ollama.ai/download")
    
    if missing_tools:
        console.print("\n[bold yellow]Installation Recommendations:[/bold yellow]")
        for tool in missing_tools:
            console.print(f"  • {tool}")
    else:
        console.print("\n[bold green]✅ All tools are available![/bold green]")


@cli.command()
@click.argument('paths', nargs=-1)
@click.option('-a', '--agents', 
              default='semgrep,trivy',
              help='Comma-separated list of agents to run')
@click.option('-t', '--timeout', 
              default=300, 
              type=int,
              help='Timeout in seconds')
@click.option('-o', '--output', 
              default='codetective_scan_results.json',
              help='Output JSON file')
@click.option('--diff-only', 
              is_flag=True,
              help='Scan only new/modified files (git diff)')
@click.option('--show-output', 
              is_flag=True,
              help='Show agent output in terminal instead of JSON file')
@click.option('--parallel', 
              is_flag=True,
              help='Run agents in parallel for faster execution')
@click.option('--force-ai', 
              is_flag=True,
              help='Force enable AI review even for >10 files')
@click.option('--max-files', 
              default=None,
              type=int,
              help='Maximum number of files to scan')
def scan(paths: tuple, agents: str, timeout: int, output: str, diff_only: bool, 
         show_output: bool, parallel: bool, force_ai: bool, max_files: int):
    """Execute multi-agent code scanning."""
    try:
        # Handle diff-only scanning
        if diff_only:
            console.print("[bold yellow]Scanning only git diff files...[/bold yellow]")
            diff_files = get_git_diff_files()
            if not diff_files:
                console.print("[yellow]No modified files found in git diff[/yellow]")
                return
            validated_paths = diff_files
            console.print(f"Found {len(diff_files)} modified files")
        else:
            # Use current directory if no paths provided
            if not paths:
                paths = ['.']
            # Validate paths
            validated_paths = validate_paths(list(paths))
        
        # Parse agents
        agent_list = []
        for agent_name in agents.split(','):
            agent_name = agent_name.strip().lower()
            if agent_name == 'semgrep':
                agent_list.append(AgentType.SEMGREP)
            elif agent_name == 'trivy':
                agent_list.append(AgentType.TRIVY)
            elif agent_name == 'ai_review':
                agent_list.append(AgentType.AI_REVIEW)
            else:
                console.print(f"[red]Unknown agent: {agent_name}[/red]")
                sys.exit(1)
        
        # Smart AI review handling
        if AgentType.AI_REVIEW in agent_list:
            # Count files to scan
            file_count = 0
            for path in validated_paths:
                if Path(path).is_file():
                    file_count += 1
                else:
                    # Count files in directory
                    for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh']:
                        file_count += len(list(Path(path).rglob(f'*{ext}')))
            
            if file_count > 10 and not force_ai:
                console.print(f"[yellow]Warning: {file_count} files detected. AI Review disabled for performance.[/yellow]")
                console.print("[yellow]Use --force-ai to enable AI Review for large codebases.[/yellow]")
                agent_list.remove(AgentType.AI_REVIEW)
        
        # Create scan configuration
        scan_config = ScanConfig(
            agents=agent_list,
            timeout=timeout,
            paths=validated_paths,
            output_file=output if not show_output else None,
            max_files=max_files,
            parallel_execution=parallel
        )
        
        console.print(f"[bold blue]Starting scan with agents: {', '.join([a.value for a in agent_list])}[/bold blue]")
        if diff_only:
            console.print(f"Scanning {len(validated_paths)} modified files")
        else:
            console.print(f"Scanning paths: {', '.join(validated_paths)}")
        
        # Initialize orchestrator
        config = get_config()
        orchestrator = CodeDetectiveOrchestrator(config)
        
        # Set parallel execution flag if needed
        if parallel:
            orchestrator._parallel_execution = True
        
        # Count total files for progress tracking
        total_files = 0
        for path in validated_paths:
            if Path(path).is_file():
                total_files += 1
            else:
                # Count files in directory
                for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh']:
                    total_files += len(list(Path(path).rglob(f'*{ext}')))
        
        # Apply max_files limit
        if max_files and total_files > max_files:
            console.print(f"[yellow]Limiting scan to {max_files} files (found {total_files})[/yellow]")
            total_files = max_files
        
        # Run scan with enhanced progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("files"),
            console=console,
        ) as progress:
            scan_task = progress.add_task(f"Scanning {total_files} files with {len(agent_list)} agents...", total=len(agent_list))
            
            scan_result = orchestrator.run_scan(scan_config)
            
            progress.update(scan_task, completed=len(agent_list))

        console.print(f"\n[bold green]✅ Scan completed![/bold green]")
        console.print(f"Total issues found: {scan_result.total_issues}")
        console.print(f"Scan duration: {scan_result.scan_duration:.2f} seconds")
        console.print(f"Files scanned: {total_files}")

        if scan_result.agent_results:
                table = Table(title="Agent Results Summary")
                table.add_column("Agent", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Issues", style="yellow")
                table.add_column("Duration", style="blue")
                
                for agent_result in scan_result.agent_results:
                    status = "✅ Success" if agent_result.success else "❌ Failed"
                    table.add_row(
                        agent_result.agent_type.value.title(),
                        status,
                        str(len(agent_result.issues)),
                        f"{agent_result.execution_time:.2f}s"
                    )
                
                console.print(table)
        
        # Handle output based on show_output flag
        if show_output:
            # Show detailed results by agent (includes agent summary table and issues)
            _display_scan_results_in_terminal(scan_result, console)
        else:
            # Save results to JSON file and show basic summary
            output_path = Path(output)
            with open(output_path, 'w') as f:
                json.dump(scan_result.model_dump(), f, indent=2, default=str)

            console.print(f"Results saved to:\n{output_path.absolute()}")
    
    except Exception as e:
        console.print(f"[red]Error during scan: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('json_file')
@click.option('-a', '--agents', 
              default='edit',
              help='Fix agents to use (comment or edit)')
def fix(json_file: str, agents: str):
    """Apply automated fixes to identified issues."""
    try:
        # Load scan results
        json_path = Path(json_file)
        if not json_path.exists():
            console.print(f"[red]JSON file not found: {json_file}[/red]")
            sys.exit(1)
        
        with open(json_path, 'r') as f:
            scan_data = json.load(f)
        
        # Parse agents
        agent_list = []
        for agent_name in agents.split(','):
            agent_name = agent_name.strip().lower()
            if agent_name == 'comment':
                agent_list.append(AgentType.COMMENT)
            elif agent_name == 'edit':
                agent_list.append(AgentType.EDIT)
            else:
                console.print(f"[red]Unknown fix agent: {agent_name}[/red]")
                sys.exit(1)
        
        # Create fix configuration
        fix_config = FixConfig(
            agents=agent_list,
            selected_issues=[],  # Will be populated from scan results
            backup_files=True,
            dry_run=False
        )
        
        console.print(f"[bold blue]Starting fix with agents: {', '.join([a.value for a in agent_list])}[/bold blue]")
        
        # Initialize orchestrator
        config = get_config()
        orchestrator = CodeDetectiveOrchestrator(config)
        
        # Run fix
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Applying fixes...", total=None)
            fix_result = orchestrator.run_fix(scan_data, fix_config)
            progress.update(task, completed=True)
        
        # Display summary
        console.print(f"\n[bold green]✅ Fix completed![/bold green]")
        console.print(f"Fixed issues: {len(fix_result.fixed_issues)}")
        console.print(f"Failed issues: {len(fix_result.failed_issues)}")
        console.print(f"Modified files: {len(fix_result.modified_files)}")
        console.print(f"Fix duration: {fix_result.fix_duration:.2f} seconds")
        
        if fix_result.modified_files:
            console.print("\n[bold yellow]Modified files:[/bold yellow]")
            for file_path in fix_result.modified_files:
                console.print(f"  • {file_path}")
    
    except Exception as e:
        console.print(f"[red]Error during fix: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--host', default='localhost', help='Host to run GUI on')
@click.option('--port', default=8501, type=int, help='Port to run GUI on')
def gui(host: str, port: int):
    """Launch Streamlit GUI."""
    try:
        import subprocess
        import sys
        from pathlib import Path
        
        # Get the path to the streamlit app
        gui_module = Path(__file__).parent.parent / "gui" / "streamlit_app.py"
        
        console.print(f"[bold blue]Starting Codetective GUI...[/bold blue]")
        console.print(f"GUI will be available at: http://{host}:{port}")
        
        # Launch streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(gui_module),
            "--server.address", host,
            "--server.port", str(port),
            "--server.headless", "true"
        ]
        
        subprocess.run(cmd)
    
    except ImportError:
        console.print("[red]Streamlit not installed. Please install with: pip install streamlit[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error launching GUI: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()
