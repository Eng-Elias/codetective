import click
from .docker_manager import DockerManager

IMAGE_NAME = "codetective/codetective-core:latest"

@click.group()
@click.option('--docker-host', default=None, help='The URL of the Docker daemon API (e.g., http://localhost:2375).')
@click.option('--image-source', type=click.Choice(['pull', 'build']), default='pull', help='Source for the Docker image: pull from Docker Hub or build locally.')
@click.option('--core-project-path', type=click.Path(file_okay=False, resolve_path=True), default=None, help='Path to the local codetective-core project (required for --image-source=build).')
@click.pass_context
def cli(ctx, docker_host, image_source, core_project_path):
    """A launcher for the Codetective Docker-based code analysis tool."""
    # If building, ensure we have a valid path for the core project
    if image_source == 'build':
        if not core_project_path:
            # If no path is provided, assume a default parallel directory structure
            import os
            current_dir = os.path.abspath(os.path.dirname(__file__))
            # Assumes this file is in .../codetective-launcher/src/codetective_launcher/
            # We want to get to .../codetective-core/
            assumed_path = os.path.join(current_dir, '..', '..', '..', 'codetective-core')
            core_project_path = os.path.abspath(assumed_path)

        if not os.path.isdir(core_project_path):
            raise click.UsageError(f'The specified --core-project-path does not exist or is not a directory: {core_project_path}')
    ctx.obj = {
        'DOCKER_HOST': docker_host,
        'IMAGE_SOURCE': image_source,
        'CORE_PROJECT_PATH': core_project_path
    }

@cli.command()
@click.pass_context
def gui(ctx):
    """Launch the Codetective GUI.

    This command pulls the latest 'codetective-core' Docker image and runs the
    Streamlit GUI, forwarding the necessary ports.
    """
    manager = DockerManager(
        base_url=ctx.obj.get('DOCKER_HOST'),
        image_source=ctx.obj.get('IMAGE_SOURCE'),
        core_project_path=ctx.obj.get('CORE_PROJECT_PATH')
    )
    manager.run_gui(IMAGE_NAME)

@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option('--agents', '-a', multiple=True, help='Agents to run (e.g., semgrep, trivy).')
@click.option('--output', '-o', help='Output file path.')
@click.option('--format', '-f', type=click.Choice(['json', 'sarif']), default='json', help='Output format.')
@click.pass_context
def analyze(ctx, path, agents, output, format):
    """Run a headless analysis of a project directory.

    This command runs the 'codetective-core' container, mounts the specified
    project PATH, and executes the analysis using the selected agents.
    """
    manager = DockerManager(
        base_url=ctx.obj.get('DOCKER_HOST'),
        image_source=ctx.obj.get('IMAGE_SOURCE'),
        core_project_path=ctx.obj.get('CORE_PROJECT_PATH')
    )
    
    # Construct the arguments to pass to the container's CLI
    args = []
    if agents:
        for agent in agents:
            args.extend(['--agents', agent])
    if output:
        args.extend(['--output', output])
    if format:
        args.extend(['--format', format])

    manager.run_cli(IMAGE_NAME, path, args)

if __name__ == '__main__':
    cli()
