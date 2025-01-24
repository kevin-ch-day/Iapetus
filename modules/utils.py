import os
import subprocess

def validate_output_directory(output_dir):
    """Ensures the output directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] Created output directory: {output_dir}")
    else:
        print(f"[INFO] Output directory exists: {output_dir}")

def validate_nmap_installation():
    """Check if Nmap is installed on the system."""
    try:
        subprocess.run(["nmap", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("[INFO] Nmap is installed and ready to use.")
    except FileNotFoundError:
        print("[ERROR] Nmap is not installed. Please install it to use this script.")
        exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error validating Nmap installation: {e}")
        exit(1)

def check_command_availability(command):
    """Check if a specific command is available on the system."""
    try:
        subprocess.run([command, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"[INFO] {command} is installed and ready to use.")
    except FileNotFoundError:
        print(f"[ERROR] {command} is not installed. Please install it to use this feature.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error validating {command} installation: {e}")

def ensure_dependencies(dependencies):
    """Ensure a list of dependencies are installed."""
    for dependency in dependencies:
        check_command_availability(dependency)

def truncate_large_file(file_path, lines=50):
    """Truncate a large file to display only the first few lines."""
    try:
        with open(file_path, "r") as f:
            data = f.readlines()
        print(f"\n[INFO] Showing the first {lines} lines of {file_path}:")
        for line in data[:lines]:
            print(line.strip())
    except Exception as e:
        print(f"[ERROR] Could not read or truncate file {file_path}: {e}")
