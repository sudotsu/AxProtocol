# ============================================================
#  War Room Role Loader — v2.1 (Version-Aware)
#  ------------------------------------------------------------
#  Hash: [92e0c1bb4d8a7123]
#  Timestamp: [UTC 2025-10-17 @ 06:20]
#  Variant: v2.1_role-loader_versioned
# ============================================================

import os
from pathlib import Path
from datetime import datetime
import hashlib

ROLES_DIR = Path("roles")

def generate_hash(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()[:12]

def load_role(role_name, version_filter=None):
    """
    Load a role file by name and optional version substring.
    Example:
       load_role("strategist", version_filter="stable")
       load_role("producer", version_filter="v2.0a")
    """
    # Find all matches for the role
    candidates = list(ROLES_DIR.glob(f"{role_name}*.txt"))
    if not candidates:
        raise FileNotFoundError(f"❌ No files found matching {role_name} in {ROLES_DIR}")

    if version_filter:
        candidates = [f for f in candidates if version_filter.lower() in f.name.lower()]
        if not candidates:
            raise FileNotFoundError(f"❌ No files found for {role_name} containing '{version_filter}'")

    # Prefer lexicographically latest file if multiple
    file_path = sorted(candidates)[-1]

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "file": file_path.name,
        "name": role_name,
        "version": version_filter or "auto-latest",
        "content": content,
        "hash": generate_hash(file_path),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d @ %H:%M UTC"),
    }

def load_roles_by_pattern(pattern="stable"):
    """
    Load all roles whose filenames contain a given pattern (e.g., 'stable', 'v2.0a', 'dev').
    """
    roles = {}
    for file in ROLES_DIR.glob("*.txt"):
        if pattern.lower() in file.name.lower():
            roles[file.stem.split("_")[0]] = load_role(file.stem.split("_")[0], pattern)
    return roles

def list_roles():
    print("\nAvailable role files:")
    for f in ROLES_DIR.glob("*.txt"):
        print(f"  - {f.name}")
    print("")

def verify_integrity():
    print("\n=== Role Integrity Check ===")
    for file in ROLES_DIR.glob("*.txt"):
        h = generate_hash(file)
        print(f"{file.name:<30} {h}")
    print("============================\n")

if __name__ == "__main__":
    print("🔍 War Room Role Loader — Version-Aware Mode\n")
    list_roles()

    try:
        stable_roles = load_roles_by_pattern("stable")
        print(f"✅ Loaded {len(stable_roles)} stable roles:")
        for name, data in stable_roles.items():
            print(f"  - {name.capitalize()} ({data['file']})")
    except Exception as e:
        print(f"❌ Error: {e}")
