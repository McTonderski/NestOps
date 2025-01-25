#!/bin/bash

# Function to check if Docker is installed
check_docker_installed() {
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed. Installing Docker..."

        # Install Docker
        if [ -x "$(command -v apt)" ]; then
            sudo apt update && sudo apt install -y docker.io
        elif [ -x "$(command -v yum)" ]; then
            sudo yum install -y docker
        elif [ "$(uname)" == "Darwin" ]; then
            if ! command -v brew &> /dev/null; then
                echo "Homebrew is not installed. Please install Homebrew first."
                exit 1
            fi
            brew install --cask docker
        else
            echo "Unsupported package manager. Please install Docker manually."
            exit 1
        fi

        if [ "$(uname)" != "Darwin" ]; then
            sudo systemctl enable docker
            sudo systemctl start docker
        else
            echo "Please ensure Docker Desktop is running on macOS."
        fi
    else
        echo "Docker is already installed."
    fi
}

check_platform_architecture() {
    ARCH=$(uname -m)
    case "$ARCH" in
        "x86_64")
            echo "Platform detected: amd64"
            ;;
        "armv7l" | "aarch64")
            echo "Platform detected: arm"
            ;;
        "arm64")
            echo "Platform detected: mac M1/M2 (arm64)"
            ;;
        *)
            echo "Unsupported platform: $ARCH"
            exit 1
            ;;
    esac
}

main() {
    echo "Starting installation..."

    check_docker_installed

    check_platform_architecture

    echo "Installation completed successfully. You can now proceed with NestOps setup."
}

main
