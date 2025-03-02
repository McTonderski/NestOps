import subprocess
import sys

from services.service_manager import AbstractDockerComposeManager

class MealieManager(AbstractDockerComposeManager):
    NAME = "Mealie"

    def update_docker_compose(self):
        """Pull the latest Mealie images."""
        self.log_info(f"Pulling latest images for {self.NAME}...")
        if not self.run_subprocess(["docker", "compose", "pull"]):
            self.log_error(f"Error pulling {self.NAME}")

    def run_docker_compose(self):
        """Start Mealie using Docker Compose."""
        self.log_info(f"Starting {self.NAME} containers...")
        if not self.run_subprocess(["docker", "compose", "up", "-d"]):
            self.log_error(f"Error starting {self.NAME}")
            return
        self.log_info(f"{self.NAME} setup complete.")

    def down_docker_compose(self):
        """Stop Mealie using Docker Compose."""
        self.log_info(f"Stopping {self.NAME} containers...")
        if not self.run_subprocess(["docker", "compose", "down"]):
            self.log_error(f"Error stopping {self.NAME}")
            return
        self.log_info(f"{self.NAME} stopped successfully.")

def main():
    manager = MealieManager()
    manager.update_docker_compose()
    manager.run_docker_compose()

if __name__ == "__main__":
    main()