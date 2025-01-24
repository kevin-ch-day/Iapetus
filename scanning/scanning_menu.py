from . import scanning_operations
from modules import utils
from config import app_config


def display_menu():
    """Displays the scan menu options dynamically."""
    print("\n======================================")
    print(f"      {app_config.APP_NAME} - Scan Menu")
    print("======================================")
    for key, desc in app_config.SCAN_OPTIONS.items():
        print(f"  [{key}] {desc}")
    print("  [0] Exit")
    print("======================================")


def scan_menu(target, output_dir):
    """
    Processes user selection for scans.

    Args:
        target (str): The target IP, range, or list.
        output_dir (str): Directory to store scan results.
    """
    # Validate prerequisites
    utils.validate_output_directory(output_dir)
    utils.validate_nmap_installation()

    # Mapping menu options to scanning operations
    options = {
        "1": scanning_operations.ping_sweep,
        "2": scanning_operations.quick_scan,
        "3": scanning_operations.detailed_port_scan,
        "4": scanning_operations.service_and_os_detection,
        "5": scanning_operations.vulnerability_scan,
        "6": scanning_operations.save_live_hosts,
        "7": scanning_operations.aggressive_scan,
        "8": scanning_operations.custom_scan,
        "9": scanning_operations.top_10_ports_scan,
        "10": scanning_operations.udp_scan,
        "11": scanning_operations.firewall_evasion_scan,
        "12": scanning_operations.script_scan,
    }

    # Main menu loop
    while True:
        try:
            display_menu()
            choice = input("Select an option: ").strip()

            if choice == "0":
                print("[INFO] Exiting script. Goodbye!")
                break

            if choice in options:
                print(f"\n[INFO] Starting scan for option [{choice}]...")
                options[choice](target, output_dir)
            else:
                print("[ERROR] Invalid option. Please try again.")
        except KeyboardInterrupt:
            print("\n[INFO] Script interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
