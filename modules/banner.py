from config import app_config

def display_banner():
    """Display the application banner."""
    print(f"""
################################################################################
#                              {app_config.APP_NAME}                           #
#                  Advanced Interactive Nmap Tool for Red Teaming             #
################################################################################

Purpose:
  {app_config.APP_DESCRIPTION}

Key Features:
  - Ping Sweep: Identify live hosts in the target network.
  - Quick Scans: Perform fast scans on common ports.
  - Detailed Port Scanning: Explore all ports for deep analysis.
  - Vulnerability Assessment: Leverage Nmap's vulnerability scripts.
  - Service and OS Detection: Gather information about services and operating systems.
  - Custom Scans: Define custom Nmap commands for advanced users.

About:
  Version : {app_config.APP_VERSION}
################################################################################
""")
