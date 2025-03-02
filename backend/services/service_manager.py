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

    def run_subprocess(self, command, check=True):
        """Runs a subprocess command inside the service directory."""
        try:
            subprocess.run(command, cwd=self.directory, check=check, shell=False)
            return True
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

    @abstractmethod
    def update_docker_compose(self):
        pass

    @abstractmethod
    def run_docker_compose(self):
        pass

    @abstractmethod
    def down_docker_compose(self):
        pass