import docker
import getpass

def generate_authelia_hash(password: str):
    """Generate an Argon2 password hash securely using Authelia in Docker."""
    client = docker.from_env()

    try:
        # Start the container in detached mode (stdin_open=True allows input)
        container = client.containers.run(
            image="authelia/authelia:latest",
            command=["authelia", "crypto", "hash", "generate", "argon2"],
            stdin_open=True,
            stdout=True,
            stderr=True,
            remove=False,  # We will remove it manually
            detach=True
        )

        # Attach to the container and send the password securely via stdin
        exec_result = container.exec_run(
            cmd="sh -c 'authelia crypto hash generate argon2'",
            stdin=True,
            socket=True
        )

        # Send the password securely (avoids exposure in process list)
        exec_result.output.send(password.encode() + b"\n")

        # Read the output
        output = exec_result.output.recv(4096).decode("utf-8").strip()

        # Cleanup: Stop and remove the container
        container.stop()
        container.remove()

        return output

    except docker.errors.ContainerError as e:
        print(f"Error running Authelia hash command: {e}")
        return None

if __name__ == "__main__":
    password = getpass.getpass("Enter password: ")  # Securely prompt for password
    hashed_password = generate_authelia_hash(password)

    if hashed_password:
        print("\nGenerated Hash:")
        print(hashed_password)