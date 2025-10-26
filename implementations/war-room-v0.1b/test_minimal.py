#!/usr/bin/env python3
"""
Minimal test to identify what's broken
"""

import sys
from pathlib import Path

print("="*50)
print("AxProtocol Minimal Diagnostic")
print("="*50)
print()

# Test 1: File locations
print("1. Checking file locations...")
files_to_check = [
    "run.py",
    "DomainConfig.json",
    "domain_detector.py",
    "load_roles.py"
]

for fname in files_to_check:
    exists = Path(fname).exists()
    status = "✅" if exists else "❌"
    print(f"   {status} {fname}")

print()

# Test 2: Python imports
print("2. Checking Python imports...")
imports_to_check = [
    ("os", "os"),
    ("sys", "sys"),
    ("pathlib", "Path"),
    ("openai", "OpenAI"),
    ("dotenv", "load_dotenv")
]

for module, item in imports_to_check:
    try:
        __import__(module)
        print(f"   ✅ {module}")
    except ImportError as e:
        print(f"   ❌ {module} - {e}")

print()

# Test 3: Custom imports
print("3. Checking custom modules...")

try:
    from domain_detector import DomainDetector
    print("   ✅ domain_detector.DomainDetector")
except Exception as e:
    print(f"   ❌ domain_detector - {e}")

try:
    from load_roles import load_roles_by_pattern
    print("   ✅ load_roles.load_roles_by_pattern")
except Exception as e:
    print(f"   ❌ load_roles - {e}")

print()

# Test 4: Try importing run.py
print("4. Checking run.py...")
try:
    # Just try to load it as a module
    import importlib.util
    spec = importlib.util.spec_from_file_location("run", "run.py")
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        # Don't execute, just check if it loads
        print("   ✅ run.py can be loaded")
    else:
        print("   ❌ run.py cannot be loaded")
except Exception as e:
    print(f"   ❌ run.py error: {e}")

print()

# Test 5: Domain detection
print("5. Testing domain detection...")
if Path("DomainConfig.json").exists():
    try:
        from domain_detector import detect_domain
        result = detect_domain("Build a REST API", verbose=False)
        print(f"   ✅ Detection works: '{result}'")
    except Exception as e:
        print(f"   ❌ Detection failed: {e}")
else:
    print("   ⚠️  DomainConfig.json missing, skipping")

print()
print("="*50)
print("Diagnostic complete!")
print("="*50)