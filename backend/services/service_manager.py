import logging
import sys
import docker
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class AbstractDockerComposeManager(ABC):
    def __init__(self, directory, compose_file="docker-compose.yml"):
        self.directory = Path(directory).resolve()  # Ensure absolute path
        self.compose_file = self.directory / compose_file
        self.client = None
        self.setup_logging()
        self.initialize_docker_client()

    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(message)s")

    def log_info(self, message):
        logging.info(message)

    def log_error(self, message):
        logging.error(message)

    def run_subprocess(self, command, check=True, capture=False):
        """Runs a subprocess command inside the service directory."""
        try:
            out = subprocess.run(command, cwd=self.directory, check=check, shell=False, capture_output=capture,)
            return True if not capture else out.stdout
        except subprocess.CalledProcessError as e:
            self.log_error(f"Error executing command in {self.directory}: {e}")
            return False

    def initialize_docker_client(self):
        """Initialize the Docker client and check if Docker is running."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logging.info("Docker is running.")
        except Exception as e:
            logging.error(f"Docker is not installed or not running: {e}")
            sys.exit(1)
    
    def is_container_running(self):
        """Check if the main container for this service is running."""
        self.log_info(f"Checking if {self.NAME} is running...")
        output = self.run_subprocess(["docker", "compose", "ps", "--services", "--filter", "status=running"], capture=True)
        if output:
            self.log_info(output)
            running_services = str(output).split("\n")
            if self.NAME.lower() in [service.lower() for service in running_services]:
                self.log_info(f"{self.NAME} is running.")
                return True
        self.log_info(f"{self.NAME} is not running.")
        return False

    @abstractmethod
    def update_docker_compose(self):
        pass

    @abstractmethod
    def run_docker_compose(self):
        pass

    @abstractmethod
    def down_docker_compose(self):
        pass