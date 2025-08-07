"""
CLI interface for codetective.
"""

import asyncio
import click
import json
import os
import time
from typing import List, Optional
from pathlib import Path
import sys

from codetective.models.interface_models import CLIArgs
from codetective.models.configuration import SemgrepConfig, TrivyConfig, AIReviewConfig, AgentConfig
from codetective.utils.configuration_manager import ConfigurationManager
from codetective.utils.file_processor import FileProcessor
from codetective.utils.logger import Logger
from codetective.workflow.orchestrator import WorkflowOrchestrator
from codetective.interfaces.gui import StreamlitGUI, st_run



class CodedetectiveCLI:
    """
    Command-line interface for the codetective multi-agent code review tool.
    
    This class provides a CLI for running code review workflows with
    multiple analysis agents from the command line.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.logger = Logger.get_logger("cli.codetective")
        self.config_manager = None
        self.orchestrator = None
    
    def create_cli(self) -> click.Group:
        """Create the Click CLI group."""
        @click.group()
        @click.version_option(version="1.0.0", prog_name="codetective")
        @click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
        @click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
        @click.pass_context
        def cli(ctx, verbose, config):
            """Codetective - Multi-Agent Code Review Tool"""
            ctx.ensure_object(dict)
            ctx.obj["verbose"] = verbose
            ctx.obj["config"] = config
        
        @cli.command()
        @click.argument("project_path", type=click.Path(exists=True, file_okay=False))
        @click.option("--agents", "-a", multiple=True, 
                     type=click.Choice(["semgrep", "trivy", "ai_review", "output_comment", "output_update"]),
                     help="Agents to run (can be specified multiple times)")
        @click.option("--include", "-i", multiple=True, help="Include patterns (can be specified multiple times)")
        @click.option("--exclude", "-e", multiple=True, help="Exclude patterns (can be specified multiple times)")
        @click.option("--output", "-o", type=click.Path(), help="Output file path")
        @click.option("--format", "-f", type=click.Choice(["json", "yaml", "text"]), default="json", help="Output format")
        @click.option("--semgrep-config", help="Semgrep configuration")
        @click.option("--trivy-severity", multiple=True, help="Trivy severity filter")
        @click.option("--ai-provider", type=click.Choice(["openai", "anthropic", "gemini", "ollama", "lmstudio"]), help="AI provider")
        @click.option("--ai-model", help="AI model name")
        @click.option("--timeout", type=int, default=300, help="Analysis timeout in seconds")
        @click.option("--parallel", is_flag=True, help="Run agents in parallel where possible")
        @click.pass_context
        def analyze(ctx, project_path, agents, include, exclude, output, format, 
                   semgrep_config, trivy_severity, ai_provider, ai_model, timeout, parallel):
            """Analyze a project with selected agents."""
            
            # Create CLI args
            cli_args = CLIArgs(
                project_path=project_path,
                agents=list(agents) if agents else ["semgrep", "trivy"],
                include_patterns=list(include) if include else ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx"],
                exclude_patterns=list(exclude) if exclude else ["**/node_modules/**", "**/venv/**", "**/__pycache__/**"],
                output_file=output,
                output_format=format,
                semgrep_config=semgrep_config,
                trivy_severity=list(trivy_severity) if trivy_severity else ["CRITICAL", "HIGH"],
                ai_provider=ai_provider,
                ai_model=ai_model,
                timeout=timeout,
                parallel=parallel,
                verbose=ctx.obj["verbose"],
                config_file=ctx.obj["config"]
            )
            
            # This tool is designed to run inside a container, so we execute the analysis directly.
            click.echo("Running analysis...")
            asyncio.run(self._run_analysis(cli_args))
        
        @cli.command()
        @click.argument("project_path", type=click.Path(exists=True, file_okay=False))
        @click.option("--include", "-i", multiple=True, help="Include patterns")
        @click.option("--exclude", "-e", multiple=True, help="Exclude patterns")
        @click.option("--max-size", type=int, default=10, help="Maximum file size in MB")
        def discover(project_path, include, exclude, max_size):
            """Discover files in a project."""
            asyncio.run(self._discover_files(project_path, include, exclude, max_size))
        
        @cli.command()
        def agents():
            """List available agents and their capabilities."""
            self._list_agents()
        
        @cli.command()
        @click.argument("config_file", type=click.Path())
        def init_config(config_file):
            """Initialize a configuration file."""
            self._init_config(config_file)
        
        @cli.command()
        @click.argument("config_file", type=click.Path(exists=True))
        def validate_config(config_file):
            """Validate a configuration file."""
            self._validate_config(config_file)
        
        @cli.command()
        def gui():
            """Launch the Codetective GUI."""
            click.echo("Launching Codetective GUI...")
            # gui = StreamlitGUI()
            # gui.run()
            st_run()
            
        return cli


def main():
    """Main entry point for the codetective CLI."""
    cli_app = CodedetectiveCLI()
    cli = cli_app.create_cli()
    cli()


if __name__ == "__main__":
    main()



    
    async def _run_analysis(self, cli_args: CLIArgs) -> None:
        """Run the analysis workflow."""
        try:
            click.echo(f"🔍 Starting analysis of {cli_args.project_path}")
            click.echo(f"📋 Selected agents: {', '.join(cli_args.agents)}")
            
            # Initialize configuration manager
            self.config_manager = ConfigurationManager()
            if cli_args.config_file:
                self.config_manager.load_from_file(Path(cli_args.config_file))
            else:
                self._create_default_config(cli_args)
            
            # Initialize file processor
            project_path = Path(cli_args.project_path)
            file_processor = FileProcessor(project_path)
            
            # Discover files
            click.echo("🔍 Discovering files...")
            target_files = file_processor.discover_files(
                include_patterns=cli_args.include_patterns,
                exclude_patterns=cli_args.exclude_patterns,
                max_size_mb=10
            )
            
            if not target_files:
                click.echo("❌ No files found matching the criteria")
                return
            
            click.echo(f"📁 Found {len(target_files)} files to analyze")
            
            # Initialize orchestrator
            self.orchestrator = WorkflowOrchestrator(self.config_manager)
            
            # Execute workflow
            click.echo("🚀 Starting workflow execution...")
            
            with click.progressbar(length=100, label="Analyzing") as bar:
                # Simulate progress updates
                bar.update(20)
                
                # Run the workflow
                workflow_state = await self.orchestrator.execute_workflow(
                    target_files=target_files,
                    selected_agents=cli_args.agents
                )
                
                bar.update(80)
                bar.finish()
            
            # Process results
            self._process_results(workflow_state, cli_args)
            
            click.echo("✅ Analysis completed successfully!")
        
        except Exception as e:
            click.echo(f"❌ Analysis failed: {e}", err=True)
            if cli_args.verbose:
                import traceback
                click.echo(traceback.format_exc(), err=True)
            sys.exit(1)
    
    def _create_default_config(self, cli_args: CLIArgs) -> None:
        """Create default configuration from CLI arguments."""
        # Semgrep configuration
        if "semgrep" in cli_args.agents:
            semgrep_config = SemgrepConfig(
                enabled=True,
                timeout=cli_args.timeout,
                config_type=cli_args.semgrep_config or "auto",
                severity_filter=["ERROR", "WARNING"],
                output_format="json"
            )
            self.config_manager.set_agent_config("semgrep", semgrep_config)
        
        # Trivy configuration
        if "trivy" in cli_args.agents:
            trivy_config = TrivyConfig(
                enabled=True,
                timeout=cli_args.timeout,
                scan_types=["vuln"],
                severity_filter=cli_args.trivy_severity,
                ignore_unfixed=False,
                output_format="json"
            )
            self.config_manager.set_agent_config("trivy", trivy_config)
        
        # AI Review configuration
        if "ai_review" in cli_args.agents:
            ai_config = AIReviewConfig(
                enabled=True,
                timeout=cli_args.timeout,
                provider=cli_args.ai_provider or "openai",
                model=cli_args.ai_model or "gpt-4",
                max_tokens=4000,
                temperature=0.1,
                focus_areas=["security", "maintainability"]
            )
            self.config_manager.set_agent_config("ai_review", ai_config)
        
        # Output agents
        if "output_comment" in cli_args.agents:
            self.config_manager.set_agent_config("output_comment", AgentConfig(enabled=True, timeout=60))
        
        if "output_update" in cli_args.agents:
            self.config_manager.set_agent_config("output_update", AgentConfig(enabled=True, timeout=60))
    
    def _process_results(self, workflow_state, cli_args: CLIArgs) -> None:
        """Process and output the workflow results."""
        # Prepare results data
        results_data = {
            "scan_id": workflow_state.scan_id,
            "target_files": [str(f) for f in workflow_state.target_files],
            "selected_agents": workflow_state.selected_agents,
            "total_findings": workflow_state.get_total_findings_count(),
            "errors": workflow_state.errors,
            "metadata": workflow_state.metadata
        }
        
        # Add agent-specific results
        if workflow_state.semgrep_results:
            results_data["semgrep_results"] = workflow_state.semgrep_results.to_dict()
        
        if workflow_state.trivy_results:
            results_data["trivy_results"] = workflow_state.trivy_results.to_dict()
        
        if workflow_state.ai_review_results:
            results_data["ai_review_results"] = workflow_state.ai_review_results.to_dict()
        
        if workflow_state.output_results:
            results_data["output_results"] = workflow_state.output_results.to_dict()
        
        # Output results
        if cli_args.output_file:
            self._write_results_to_file(results_data, cli_args.output_file, cli_args.output_format)
        else:
            self._print_results_summary(results_data)
    
    def _write_results_to_file(self, results_data: dict, output_file: str, format: str) -> None:
        """Write results to a file."""
        output_path = Path(output_file)
        
        try:
            if format == "json":
                with open(output_path, 'w') as f:
                    json.dump(results_data, f, indent=2, default=str)
            
            elif format == "yaml":
                import yaml
                with open(output_path, 'w') as f:
                    yaml.dump(results_data, f, default_flow_style=False)
            
            elif format == "text":
                with open(output_path, 'w') as f:
                    f.write(self._format_text_results(results_data))
            
            click.echo(f"📄 Results written to {output_path}")
        
        except Exception as e:
            click.echo(f"❌ Failed to write results: {e}", err=True)
    
    def _print_results_summary(self, results_data: dict) -> None:
        """Print a summary of results to the console."""
        click.echo("\n" + "="*50)
        click.echo("📊 ANALYSIS RESULTS SUMMARY")
        click.echo("="*50)
        
        click.echo(f"Scan ID: {results_data['scan_id']}")
        click.echo(f"Total Findings: {results_data['total_findings']}")
        click.echo(f"Files Analyzed: {len(results_data['target_files'])}")
        click.echo(f"Agents Used: {', '.join(results_data['selected_agents'])}")
        
        if results_data.get('errors'):
            click.echo(f"\n⚠️  Errors: {len(results_data['errors'])}")
            for error in results_data['errors']:
                click.echo(f"  • {error}")
        
        # Agent-specific summaries
        if "semgrep_results" in results_data:
            semgrep_count = len(results_data["semgrep_results"].get("findings", []))
            click.echo(f"\n🔍 Semgrep: {semgrep_count} issues found")
        
        if "trivy_results" in results_data:
            trivy_vulns = sum(len(r.get("vulnerabilities", [])) for r in results_data["trivy_results"].get("results", []))
            click.echo(f"🛡️  Trivy: {trivy_vulns} vulnerabilities found")
        
        if "ai_review_results" in results_data:
            ai_issues = len(results_data["ai_review_results"].get("issues", []))
            click.echo(f"🤖 AI Review: {ai_issues} suggestions")
        
        click.echo("\n" + "="*50)
    
    def _format_text_results(self, results_data: dict) -> str:
        """Format results as plain text."""
        lines = [
            "CODETECTIVE ANALYSIS RESULTS",
            "=" * 30,
            f"Scan ID: {results_data['scan_id']}",
            f"Total Findings: {results_data['total_findings']}",
            f"Files Analyzed: {len(results_data['target_files'])}",
            f"Agents Used: {', '.join(results_data['selected_agents'])}",
            ""
        ]
        
        # Add detailed results here if needed
        
        return "\n".join(lines)
    
    async def _discover_files(self, project_path: str, include: tuple, exclude: tuple, max_size: int) -> None:
        """Discover files in a project."""
        try:
            file_processor = FileProcessor(Path(project_path))
            
            include_patterns = list(include) if include else ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx"]
            exclude_patterns = list(exclude) if exclude else ["**/node_modules/**", "**/venv/**"]
            
            files = file_processor.discover_files(
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                max_size_mb=max_size
            )
            
            click.echo(f"📁 Found {len(files)} files:")
            for file_path in sorted(files):
                click.echo(f"  • {file_path}")
        
        except Exception as e:
            click.echo(f"❌ File discovery failed: {e}", err=True)
    
    def _list_agents(self) -> None:
        """List available agents and their capabilities."""
        agents_info = {
            "semgrep": {
                "name": "Semgrep Static Analysis",
                "description": "Static analysis for security and code quality",
                "capabilities": ["pattern_matching", "security_rules", "custom_rules"]
            },
            "trivy": {
                "name": "Trivy Security Scanner", 
                "description": "Vulnerability scanning for dependencies and containers",
                "capabilities": ["vulnerability_scanning", "dependency_analysis", "secret_detection"]
            },
            "ai_review": {
                "name": "AI Code Review",
                "description": "Intelligent code analysis using LLMs",
                "capabilities": ["intelligent_analysis", "security_review", "best_practices"]
            },
            "output_comment": {
                "name": "Comment Generator",
                "description": "Generate structured review comments",
                "capabilities": ["comment_generation", "result_aggregation"]
            },
            "output_update": {
                "name": "Code Updater",
                "description": "Apply automatic fixes to code",
                "capabilities": ["automatic_fixes", "backup_creation"]
            }
        }
        
        click.echo("🤖 Available Agents:")
        click.echo("=" * 20)
        
        for agent_id, info in agents_info.items():
            click.echo(f"\n{info['name']} ({agent_id})")
            click.echo(f"  Description: {info['description']}")
            click.echo(f"  Capabilities: {', '.join(info['capabilities'])}")
    
    def _init_config(self, config_file: str) -> None:
        """Initialize a configuration file."""
        config_path = Path(config_file)
        
        # Create default configuration
        default_config = {
            "agents": {
                "semgrep": {
                    "enabled": True,
                    "timeout": 300,
                    "config_type": "auto",
                    "severity_filter": ["ERROR", "WARNING"]
                },
                "trivy": {
                    "enabled": True,
                    "timeout": 300,
                    "scan_types": ["vuln"],
                    "severity_filter": ["CRITICAL", "HIGH"]
                },
                "ai_review": {
                    "enabled": False,
                    "provider": "openai",
                    "model": "gpt-4",
                    "focus_areas": ["security", "maintainability"]
                }
            },
            "file_discovery": {
                "include_patterns": ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx"],
                "exclude_patterns": ["**/node_modules/**", "**/venv/**", "**/__pycache__/**"],
                "max_file_size_mb": 10
            }
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            click.echo(f"✅ Configuration file created: {config_path}")
        
        except Exception as e:
            click.echo(f"❌ Failed to create configuration file: {e}", err=True)
    
    def _validate_config(self, config_file: str) -> None:
        """Validate a configuration file."""
        try:
            config_manager = ConfigurationManager()
            config_manager.load_from_file(Path(config_file))
            
            errors = config_manager.validate_configuration()
            
            if not errors:
                click.echo("✅ Configuration file is valid")
            else:
                click.echo("❌ Configuration validation failed:")
                for error in errors:
                    click.echo(f"  • {error}")
        
        except Exception as e:
            click.echo(f"❌ Failed to validate configuration: {e}", err=True)


def main():
    """Main entry point for the CLI."""
    cli_instance = CodedetectiveCLI()
    cli = cli_instance.create_cli()
    cli()


if __name__ == "__main__":
    main()
