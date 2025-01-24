import subprocess
import ipaddress


def get_target():
    """Get the target IP/Range or generate a custom target list."""
    while True:
        print("\n[INFO] Choose your targeting method:")
        print("  [1] Enter an IP address or range (e.g., 192.168.1.0/24)")
        print("  [2] Generate a custom target list")
        print("  [3] Use network configuration to select a subnet")
        print("  [0] Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            return input_target()
        elif choice == "2":
            return generate_target_list()
        elif choice == "3":
            return get_network_config()
        elif choice == "0":
            print("Exiting target selection. Goodbye!")
            return None
        else:
            print("[ERROR] Invalid option. Please try again.")


def input_target():
    """Prompt user to input a valid IP address or range."""
    while True:
        target = input("Enter the target IP/Range (e.g., 192.168.1.0/24): ").strip()
        if validate_ip_range(target):
            return target
        else:
            print("[ERROR] Invalid IP/Range. Please enter a valid IP address or range.")


def generate_target_list():
    """Generates a custom target list and saves it to a file."""
    print("\n[INFO] Generate a custom target list.")
    target_file = input("Enter the filename to save the target list (e.g., targets.txt): ").strip()
    if not target_file:
        print("[ERROR] Filename cannot be empty.")
        return None

    print("Enter each target IP/Range on a new line. Type 'done' when finished.")
    targets = []
    while True:
        target = input("Target: ").strip()
        if target.lower() == "done":
            break
        if target and validate_ip_range(target):
            targets.append(target)
        else:
            print("[ERROR] Invalid IP/Range. Please enter a valid IP or range.")

    try:
        with open(target_file, "w") as f:
            f.write("\n".join(targets))
        print(f"[SUCCESS] Target list saved to {target_file}")
        return target_file
    except Exception as e:
        print(f"[ERROR] Failed to save target list: {e}")
        return None


def get_network_config():
    """Retrieve and display network configuration using ifconfig."""
    try:
        result = subprocess.run(["ifconfig"], capture_output=True, text=True, check=True)
        print("\n[INFO] Current Network Configuration:\n")
        interfaces = parse_network_config(result.stdout)
        print("\nAvailable Network Interfaces:")
        for idx, (interface, subnet) in enumerate(interfaces.items(), 1):
            print(f"  [{idx}] {interface} - {subnet}")

        choice = input("Select an interface by number or type 'custom' to enter manually: ").strip()
        if choice.lower() == "custom":
            return input_target()

        if choice.isdigit() and 1 <= int(choice) <= len(interfaces):
            selected_interface = list(interfaces.values())[int(choice) - 1]
            print(f"[INFO] Selected subnet: {selected_interface}")
            return selected_interface
        else:
            print("[ERROR] Invalid selection.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to retrieve network configuration: {e}")
        return None


def validate_ip_range(ip_range):
    """Validates if the input is a valid IP address or CIDR range."""
    try:
        ipaddress.ip_network(ip_range, strict=False)
        return True
    except ValueError:
        return False


def parse_network_config(ifconfig_output):
    """Parses the ifconfig output to extract network interfaces and subnets."""
    interfaces = {}
    current_interface = None

    for line in ifconfig_output.splitlines():
        if line and not line.startswith(" "):  # New interface block
            current_interface = line.split(":")[0]
        if "inet " in line and current_interface:
            try:
                ip = line.split()[1]
                subnet = f"{ip}/24"  # Default to /24 if not specified
                interfaces[current_interface] = subnet
            except IndexError:
                continue

    return interfaces
