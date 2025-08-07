import sys
import time
import os
import json
import tempfile
import subprocess
import shutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from .utils.docker_api_client import DockerAPIClient

class DockerManager:
    """A manager for Codetective's Docker operations using the Docker Engine API."""

    def __init__(self, base_url=None, image_source='pull', core_project_path=None):
        self.console = Console()
        self.client = DockerAPIClient(base_url=base_url)
        self.image_source = image_source
        self.core_project_path = core_project_path

    def check_docker(self):
        """Check if the Docker daemon is responsive."""
        if not self.client.ping():
            self.console.print("[bold red]Error:[/bold red] Cannot connect to the Docker daemon.")
            self.console.print("Please ensure Docker is running and that you have exposed the daemon on [bold]tcp://localhost:2375[/bold] in your Docker settings.")
            sys.exit(1)
        return True

    def ensure_image_exists(self, image_name: str):
        """Ensure the Docker image exists, pulling or building it if necessary."""
        if self.client.image_exists(image_name):
            self.console.print(f"Image [bold cyan]{image_name}[/bold cyan] found locally.")
            return True

        if self.image_source == 'pull':
            self.console.print(f"Image [bold cyan]{image_name}[/bold cyan] not found. Pulling from Docker Hub...")
            self.console.print("This may take a few minutes.")
            # NOTE: self.client.pull_image() needs to be implemented in the DockerAPIClient
            response = self.client.pull_image(image_name)

            if not response:
                self.console.print("[bold red]Pull failed:[/bold red] Could not start pull process.")
                return False

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                task = progress.add_task(description=f"Pulling {image_name}...", total=None)
                for line in response.iter_lines():
                    if line:
                        try:
                            log_entry = json.loads(line)
                            if 'status' in log_entry:
                                progress.update(task, description=log_entry['status'])
                            if 'error' in log_entry:
                                self.console.print(f"[bold red]Pull Error:[/bold red] {log_entry['error']}")
                                return False
                        except json.JSONDecodeError:
                            self.console.print(line.decode('utf-8').strip(), highlight=False)

        elif self.image_source == 'build':
            self.console.print(f"Image [bold cyan]{image_name}[/bold cyan] not found. Building from local path...")
            self.console.print(f"[dim]Source: {self.core_project_path}[/dim]")
            
            response = self.client.build_image(image_name, self.core_project_path, 'Dockerfile')

            if not response:
                self.console.print("[bold red]Build failed:[/bold red] Could not start build process.")
                return False

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="Building image...", total=None)
                for line in response.iter_lines():
                    if line:
                        try:
                            log_entry = json.loads(line)
                            if 'stream' in log_entry:
                                self.console.print(log_entry['stream'].strip(), highlight=False)
                            elif 'error' in log_entry:
                                self.console.print(f"[bold red]Build Error:[/bold red] {log_entry['error']}")
                                return False
                        except json.JSONDecodeError:
                            self.console.print(line.decode('utf-8').strip(), highlight=False)

        # Final check
        if self.client.image_exists(image_name):
            self.console.print(f"[bold green]Successfully acquired image [bold cyan]{image_name}[/bold cyan][/bold green]")
            return True
        else:
            self.console.print(f"[bold red]Failed to acquire image [bold cyan]{image_name}[/bold cyan].")
            return False

    def run_gui(self, image_name: str):
        """Run the Streamlit GUI in a Docker container."""
        if not self.check_docker() or not self.ensure_image_exists(image_name):
            sys.exit(1)

        ports = {"8501/tcp": [{"HostPort": "8501"}]}
        container_id = None

        self.console.print(f"Starting GUI container from image [cyan]{image_name}[/cyan]...")
        try:
            container_id = self.client.create_container(image_name, command=["gui"], volumes=[], ports=ports)
            self.client.start_container(container_id)

            self.console.print(f"GUI is running at [bold blue]http://localhost:8501[/bold blue]")
            self.console.print("Press [bold]Ctrl+C[/bold] to stop the container.")

            # Stream logs until user interrupts
            for log_line in self.client.stream_logs(container_id):
                self.console.print(log_line, highlight=False)

        except KeyboardInterrupt:
            self.console.print("\nStopping container...")
        finally:
            if container_id:
                self.client.remove_container(container_id)
                self.console.print("[green]Container stopped and removed.[/green]")

    def run_cli(self, image_name: str, project_path: str, cli_args: list):
        """Run a headless analysis in a Docker container."""
        if not self.check_docker() or not self.ensure_image_exists(image_name):
            sys.exit(1)

        volumes = [{'host': project_path, 'container': '/project'}]
        command = ["analyze", "/project"] + cli_args
        container_id = None

        self.console.print(f"Running analysis in container on path [cyan]{project_path}[/cyan]...")
        try:
            container_id = self.client.create_container(image_name, command=command, volumes=volumes)
            self.client.start_container(container_id)

            # Stream logs and wait for completion
            for log_line in self.client.stream_logs(container_id):
                self.console.print(log_line, highlight=False)

            self.client.wait_for_container(container_id)
            self.console.print("[green]Analysis complete.[/green]")

        finally:
            if container_id:
                self.client.remove_container(container_id)
                self.console.print("Container removed.")
