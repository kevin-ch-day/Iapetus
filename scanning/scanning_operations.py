# scanning_operations.py
import subprocess
from config import app_config


def run_command(command, output_file):
    """Executes a shell command and saves the output to a file."""
    try:
        print(f"\n[INFO] Running: {command}")
        with open(output_file, "w") as f:
            subprocess.run(command, shell=True, stdout=f, stderr=subprocess.STDOUT, text=True, check=True)
        print(f"[SUCCESS] Results saved to {output_file}\n")
        analyze_results(output_file)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}")


def analyze_results(output_file):
    """Analyzes the output file and provides insights."""
    try:
        with open(output_file, "r") as f:
            data = f.readlines()

        print("\n[INFO] Analysis of Scan Results:")

        # Total lines in the output
        total_lines = len(data)
        print(f"  - Total lines in the output: {total_lines}")

        # Extract open ports
        open_ports = [line for line in data if "open" in line.lower()]
        if open_ports:
            print(f"  - Open ports detected: {len(open_ports)}")
            for port in open_ports[:10]:  # Limit to 10 results
                print(f"    > {port.strip()}")
        else:
            print("  - No open ports detected.")

        # Extract filtered ports
        filtered_ports = [line for line in data if "filtered" in line.lower()]
        if filtered_ports:
            print(f"  - Filtered ports detected: {len(filtered_ports)}")
            for port in filtered_ports[:5]:  # Limit to 5 results
                print(f"    > {port.strip()}")

        # Extract services
        services = [line for line in data if "service" in line.lower()]
        unique_services = set(services)
        if services:
            print(f"  - Services detected: {len(unique_services)}")
            for service in unique_services[:5]:  # Limit to 5 results
                print(f"    > {service.strip()}")

        # Extract hostnames
        hostnames = [line for line in data if "Nmap scan report for" in line]
        if hostnames:
            print(f"  - Hostnames detected: {len(hostnames)}")
            for hostname in hostnames[:5]:  # Limit to 5 results
                print(f"    > {hostname.strip()}")

    except Exception as e:
        print(f"[ERROR] Failed to analyze results: {e}")


# Nmap Scan Functions
def ping_sweep(target, output_dir):
    run_command(f"nmap -sn {target}", f"{output_dir}/ping_sweep.txt")


def quick_scan(target, output_dir):
    run_command(f"nmap -T4 -F {target}", f"{output_dir}/quick_scan.txt")


def detailed_port_scan(target, output_dir):
    run_command(f"nmap -p- -T4 {target}", f"{output_dir}/detailed_port_scan.txt")


def service_and_os_detection(target, output_dir):
    run_command(f"nmap -sV -sC -O {target}", f"{output_dir}/service_os_detection.txt")


def vulnerability_scan(target, output_dir):
    run_command(f"nmap --script vuln {target}", f"{output_dir}/vulnerability_scan.txt")


def save_live_hosts(target, output_dir):
    intermediate_file = f"{output_dir}/live_hosts.txt"
    cleaned_file = f"{output_dir}/live_hosts_cleaned.txt"
    command = (
        f"nmap -sn {target} -oG {intermediate_file} && "
        f"awk '/Up$/{{print $2}}' {intermediate_file} > {cleaned_file}"
    )
    run_command(command, cleaned_file)


def aggressive_scan(target, output_dir):
    run_command(f"nmap -A {target}", f"{output_dir}/aggressive_scan.txt")


def top_10_ports_scan(target, output_dir):
    run_command(f"nmap --top-ports 10 {target}", f"{output_dir}/top_vulnerable_ports.txt")


def udp_scan(target, output_dir):
    run_command(f"nmap -sU {target}", f"{output_dir}/udp_scan.txt")


def firewall_evasion_scan(target, output_dir):
    run_command(f"nmap -f {target}", f"{output_dir}/firewall_evasion_scan.txt")


def script_scan(target, output_dir):
    run_command(f"nmap --script http-enum {target}", f"{output_dir}/http_enum_scan.txt")


def custom_scan(target, output_dir):
    command = input("Enter your custom Nmap command: ").strip()
    if not command:
        print("[ERROR] Custom command cannot be empty.")
        return
    output_file = input("Enter the filename to save results (e.g., custom_scan.txt): ").strip()
    if not output_file:
        print("[ERROR] Filename cannot be empty.")
        return
    run_command(command, f"{output_dir}/{output_file}")
