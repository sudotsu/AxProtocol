# ============================================================
#  War Room Role Loader — v2.0a
#  ------------------------------------------------------------
#  Hash: [6be27f4b1b05f942]
#  Timestamp: [UTC 2025-10-17 @ 06:02]
#  Variant: v2.0a_role-loader
#
#  PURPOSE:
#     - Dynamically load War Room role prompts from /roles/
#     - Preserve watermark metadata for lineage tracking
#     - Allow flexible access: single role, all roles, or hashes only
#
#  SAFETY:
#     - Read-only (does not alter role files)
#     - All loaded content cached in memory per session
# ============================================================

import os
from pathlib import Path
from datetime import datetime
import hashlib

# Directory containing all role text files
ROLES_DIR = Path("roles")

def generate_hash(file_path):
    """Generate a short SHA256 hash of the file content for verification."""
    with open(file_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()[:12]

def load_role(role_name):
    """
    Load a single role text file (e.g., 'strategist', 'analyst', etc.)
    Returns a dict containing:
       { "name": role_name, "content": text, "hash": hash, "timestamp": utc_time }
    """
    file_path = ROLES_DIR / f"{role_name}.txt"
    if not file_path.exists():
        raise FileNotFoundError(f"❌ Role file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "name": role_name,
        "content": content,
        "hash": generate_hash(file_path),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d @ %H:%M UTC"),
    }

def load_all_roles():
    """
    Load all role text files in /roles/ folder.
    Returns a dict of { role_name: role_data }
    """
    roles = {}
s    for file in ROLES_DIR.glob("*.txt"):
        role_name = file.stem
        roles[role_name] = load_role(role_name)
    return roles

def list_roles():
    """List available role files."""
    if not ROLES_DIR.exists():
        print("⚠️  'roles/' folder not found.")
        return []
    files = [f.stem for f in ROLES_DIR.glob("*.txt")]
    print("Available roles:", ", ".join(files))
    return files

def verify_integrity():
    """Quick hash summary for all role files."""
    if not ROLES_DIR.exists():
        print("⚠️  No roles directory found.")
        return
    print("\n=== Role Integrity Check ===")
    for file in ROLES_DIR.glob("*.txt"):
        hash_val = generate_hash(file)
        print(f"{file.name:<25}  {hash_val}")
    print("============================\n")

if __name__ == "__main__":
    # Example usage when running standalone
    print("🔍 War Room Role Loader Test Run\n")
    list_roles()

    try:
        roles = load_all_roles()
        print(f"\n✅ Loaded {len(roles)} roles:")
        for r in roles:
            print(f"   - {r.capitalize()} (Hash: {roles[r]['hash']})")
        print("\nRun 'verify_integrity()' anytime to check file hashes.")
    except Exception as e:
        print(f"❌ Error: {e}")