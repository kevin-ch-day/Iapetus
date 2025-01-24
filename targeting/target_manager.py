# target_handler.py
# Module for managing predefined and dynamic target IPs or ranges.

import os
import json

# Path to the dynamic targets file
TARGET_FILE = "targets/targets.json"

# Predefined list of IP targets (hardcoded)
PREDEFINED_TARGETS = [
    "192.168.1.0/24",
    "192.168.2.0/24",
    "10.0.0.1/32",
    "172.16.0.0/16",
]


def get_predefined_targets():
    """Returns the predefined target list."""
    return PREDEFINED_TARGETS


def load_targets_from_file():
    """Load dynamic targets from the target file."""
    if not os.path.exists(TARGET_FILE):
        print(f"[INFO] Target file {TARGET_FILE} does not exist. Creating a new one...")
        save_targets_to_file([])
        return []
    try:
        with open(TARGET_FILE, "r") as f:
            targets = json.load(f)
            print(f"[INFO] Loaded {len(targets)} targets from {TARGET_FILE}.")
            return targets
    except Exception as e:
        print(f"[ERROR] Failed to load targets from file: {e}")
        return []


def save_targets_to_file(targets):
    """Save dynamic targets to the target file."""
    os.makedirs(os.path.dirname(TARGET_FILE), exist_ok=True)
    try:
        with open(TARGET_FILE, "w") as f:
            json.dump(targets, f, indent=4)
        print(f"[SUCCESS] Targets saved to {TARGET_FILE}.")
    except Exception as e:
        print(f"[ERROR] Failed to save targets to file: {e}")


def add_target(target):
    """Add a new target to the dynamic target list."""
    targets = load_targets_from_file()
    if target not in targets:
        targets.append(target)
        save_targets_to_file(targets)
        print(f"[SUCCESS] Added target: {target}")
    else:
        print(f"[INFO] Target {target} already exists in the list.")


def remove_target(target):
    """Remove a target from the dynamic target list."""
    targets = load_targets_from_file()
    if target in targets:
        targets.remove(target)
        save_targets_to_file(targets)
        print(f"[SUCCESS] Removed target: {target}")
    else:
        print(f"[INFO] Target {target} does not exist in the list.")


def get_all_targets():
    """Return all targets (predefined and dynamic)."""
    predefined = get_predefined_targets()
    dynamic = load_targets_from_file()
    print(f"[INFO] Returning {len(predefined)} predefined and {len(dynamic)} dynamic targets.")
    return predefined + dynamic


def display_targets():
    """Display all targets (predefined and dynamic)."""
    predefined = get_predefined_targets()
    dynamic = load_targets_from_file()

    print("\n[INFO] Predefined Targets:")
    for idx, target in enumerate(predefined, 1):
        print(f"  [{idx}] {target}")

    print("\n[INFO] Dynamic Targets:")
    for idx, target in enumerate(dynamic, 1):
        print(f"  [{idx}] {target}")
