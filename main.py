import os
from modules.banner import display_banner
from modules.targeting import get_target
from modules.scanning import scan_menu
from modules.utils import validate_nmap_installation
from config import app_config

# Ensure OUTPUT_DIR exists
def setup_output_directory(output_dir):
    """Ensure the output directory exists or create it."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] Created output directory: {output_dir}")
    else:
        print(f"[INFO] Output directory already exists: {output_dir}")

# Main application flow
def main():
    # Display the application banner
    display_banner()

    # Ensure Nmap is installed
    validate_nmap_installation()

    # Setup results directory
    setup_output_directory(app_config.OUTPUT_DIR)

    # Get target or target list from user
    target = get_target()
    if not target:
        print("[ERROR] No target specified. Exiting.")
        return

    # Launch scan menu
    try:
        scan_menu(target, app_config.OUTPUT_DIR)
        print("\n[INFO] Scanning completed successfully. Check the output directory for results.")
    except Exception as e:
        print(f"[ERROR] An error occurred during scanning: {e}")

if __name__ == "__main__":
    main()
