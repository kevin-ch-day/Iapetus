# app_config.py
# Configuration file for storing constants and application metadata

# Application Information
APP_NAME = "Iapetus Network Scanner"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A modular Nmap-based network scanning tool for red team operations."

# Default Output Directory
OUTPUT_DIR = "nmap_results"

# Scan Menu Options
SCAN_OPTIONS = {
    "1": "Ping Sweep",
    "2": "Quick Scan",
    "3": "Detailed Port Scan",
    "4": "Service and OS Detection",
    "5": "Vulnerability Scan",
    "6": "Save Live Hosts",
    "7": "Aggressive Scan",
    "8": "Custom Scan",
    "9": "Top 10 Vulnerable Ports Scan",
    "10": "UDP Scan",
    "11": "Firewall Evasion Scan",
    "12": "Script Scan",
    "0": "Exit"
}

# Nmap Command Templates
NMAP_COMMANDS = {
    "1": "nmap -sn {target}",
    "2": "nmap -T4 -F {target}",
    "3": "nmap -p- -T4 {target}",
    "4": "nmap -sV -sC -O {target}",
    "5": "nmap --script vuln {target}",
    "6": "nmap -sn {target} -oG {output_dir}/live_hosts.txt && awk '/Up$/{{print $2}}' {output_dir}/live_hosts.txt > {output_dir}/live_hosts_cleaned.txt",
    "7": "nmap -A {target}",
    "9": "nmap --top-ports 10 {target}",
    "10": "nmap -sU {target}",
    "11": "nmap -f {target}",
    "12": "nmap --script http-enum {target}"
}

# Analysis Settings
ANALYSIS_LINE_LIMIT = 10
