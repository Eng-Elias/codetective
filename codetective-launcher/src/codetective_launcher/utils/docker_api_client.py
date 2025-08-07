import json
import socket
import requests
import tarfile
import io
import os

# On Windows, the Docker daemon listens on a named pipe. On Linux/macOS, it's a Unix socket.
# We will use a TCP socket for cross-platform compatibility, which requires the user to
# expose the Docker daemon on tcp://localhost:2375 in their Docker Desktop settings.

DEFAULT_DOCKER_BASE_URL = "http://localhost:2375"

class DockerAPIClient:
    """A lightweight client for the Docker Engine API using HTTP requests."""

    def __init__(self, base_url=None):
        self.base_url = base_url or DEFAULT_DOCKER_BASE_URL

    def _url(self, path):
        return f"{self.base_url}{path}"

    def image_exists(self, image_name: str):
        """Check if a Docker image exists locally."""
        try:
            response = requests.get(self._url(f"/images/{image_name}/json"), timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def build_image(self, image_tag: str, context_path: str, dockerfile_path: str):
        """Build a Docker image from a given context path and Dockerfile."""
        
        # Create an in-memory tarball of the build context
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w:gz') as tar:
            tar.add(context_path, arcname='.')

        tar_stream.seek(0)

        headers = {'Content-Type': 'application/x-tar'}
        params = {
            't': image_tag,
            'dockerfile': dockerfile_path, # Path to Dockerfile within the context
            'q': False, # Not quiet, show logs
            'nocache': False,
        }

        try:
            response = requests.post(
                self._url("/build"),
                params=params,
                data=tar_stream,
                headers=headers,
                stream=True,
                timeout=3600 # Long timeout for build
            )
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            print(f"Connection Error: Could not connect to Docker daemon at {self.base_url}. Please ensure Docker is running and the API is exposed on a TCP socket.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred during build: {e}")
            return None

    def ping(self):
        """Check if the Docker daemon is responsive."""
        try:
            response = requests.get(self._url("/_ping"), timeout=2)
            return response.status_code == 200 and response.text == "OK"
        except requests.exceptions.ConnectionError:
            return False

    def pull_image(self, image_name: str):
        """Pull a Docker image from a registry, streaming the progress."""
        params = {"fromImage": image_name}
        try:
            response = requests.post(self._url("/images/create"), params=params, stream=True, timeout=3600)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            print(f"Connection Error: Could not connect to Docker daemon at {self.base_url}. Please ensure Docker is running and the API is exposed on a TCP socket.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An unexpected error occurred while pulling the image: {e}")
            return None

    def create_container(self, image, command, volumes, ports=None):
        """Create a new container."""
        host_config = {
            "Binds": [f"{vol['host']}:{vol['container']}" for vol in volumes],
            "PortBindings": ports or {}
        }
        container_config = {
            "Image": image,
            "Cmd": command,
            "HostConfig": host_config,
            "Tty": False,
            "AttachStdout": True,
            "AttachStderr": True,
        }
        response = requests.post(self._url("/containers/create"), json=container_config)
        response.raise_for_status()
        return response.json()["Id"]

    def start_container(self, container_id):
        """Start a container by its ID."""
        response = requests.post(self._url(f"/containers/{container_id}/start"))
        response.raise_for_status()

    def stream_logs(self, container_id):
        """Stream logs from a running container."""
        params = {"stdout": True, "stderr": True, "follow": True}
        response = requests.get(self._url(f"/containers/{container_id}/logs"), params=params, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                yield line.decode('utf-8')

    def wait_for_container(self, container_id):
        """Wait for a container to stop and return its exit code."""
        response = requests.post(self._url(f"/containers/{container_id}/wait"))
        response.raise_for_status()
        return response.json()["StatusCode"]

    def remove_container(self, container_id):
        """Remove a container by its ID."""
        response = requests.delete(self._url(f"/containers/{container_id}?v=1")) # v=1 removes volumes
        # Don't raise for status, as we might try to remove a non-existent container
        return response.status_code in [204, 404]
