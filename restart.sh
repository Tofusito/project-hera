#!/bin/bash

# Function to print colored output
print_colored() {
    local color=$1
    local message=$2
    printf "\033[0;${color}m%s\033[0m\n" "$message"
}

# Function to execute commands and handle errors
execute_command() {
    local command=$1
    local error_message=$2
    
    if ! $command; then
        print_colored "31" "Error: $error_message"
    fi
}

# Main script
main() {
    print_colored "34" "Starting cleanup process..."

    # Add docker compose down at the beginning
    print_colored "33" "Stopping and removing Docker containers..."
    execute_command "docker compose down" "Failed to stop and remove Docker containers"

    # Remove and recreate documents directory
    print_colored "33" "Removing and recreating documents directory..."
    execute_command "sudo rm -rf documentos" "Failed to remove documentos directory"
    execute_command "mkdir -p documentos/input" "Failed to create documentos/input directory"

    # Remove Docker volumes
    print_colored "33" "Removing Docker volumes..."
    execute_command "docker volume rm project-hera_anythingllm_storage" "Failed to remove project-hera_anythingllm_storage volume"
    execute_command "docker volume rm project-hera_chroma_data" "Failed to remove project-hera_chroma_data volume"

    # Remove API key
    print_colored "33" "Removing API key..."
    execute_command "sudo rm -rf hera/session/api_key" "Failed to remove API key"

    print_colored "32" "Cleanup process completed!"
}

# Run the main function
main
