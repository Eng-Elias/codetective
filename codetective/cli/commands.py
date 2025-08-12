"""
CLI commands implementation for Codetective.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import get_config
from ..core.utils import get_system_info, validate_paths
from ..core.orchestrator import CodeDetectiveOrchestrator
from ..models.schemas import AgentType, ScanConfig, FixConfig


console = Console()


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
              default='semgrep,trivy,ai_review',
              help='Comma-separated list of agents to run')
@click.option('-t', '--timeout', 
              default=300, 
              type=int,
              help='Timeout in seconds')
@click.option('-o', '--output', 
              default='codetective_scan_results.json',
              help='Output JSON file')
def scan(paths: tuple, agents: str, timeout: int, output: str):
    """Execute multi-agent code scanning."""
    try:
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
        
        # Create scan configuration
        scan_config = ScanConfig(
            agents=agent_list,
            timeout=timeout,
            paths=validated_paths,
            output_file=output
        )
        
        console.print(f"[bold blue]Starting scan with agents: {', '.join([a.value for a in agent_list])}[/bold blue]")
        console.print(f"Scanning paths: {', '.join(validated_paths)}")
        
        # Initialize orchestrator
        config = get_config()
        orchestrator = CodeDetectiveOrchestrator(config)
        
        # Run scan
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running scan...", total=None)
            scan_result = orchestrator.run_scan(scan_config)
            progress.update(task, completed=True)
        
        # Save results
        output_path = Path(output)
        with open(output_path, 'w') as f:
            json.dump(scan_result.model_dump(), f, indent=2, default=str)
        
        # Display summary
        console.print(f"\n[bold green]✅ Scan completed![/bold green]")
        console.print(f"Total issues found: {scan_result.total_issues}")
        console.print(f"Scan duration: {scan_result.scan_duration:.2f} seconds")
        console.print(f"Results saved to: {output_path.absolute()}")
        
        # Show breakdown by agent
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
