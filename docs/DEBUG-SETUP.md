# AxProtocol Multi-Domain Debugging Guide

## Quick Diagnostic

Run these commands in order to identify the issue:

### Step 1: Check Python and Dependencies

```bash
cd implementations/war-room-v0.1b

# Check Python version (need 3.8+)
python --version

# Check if OpenAI library installed
python -c "import openai; print(openai.__version__)"

# Check if dotenv installed
python -c "import dotenv; print('dotenv OK')"
```

### Step 2: Test Individual Components

**Test 1: Can Python find the files?**

```bash
python -c "from pathlib import Path; print(Path('run.py').exists())"
python -c "from pathlib import Path; print(Path('DomainConfig.json').exists())"
python -c "from pathlib import Path; print(Path('domain_detector.py').exists())"
```

**Test 2: Can we import domain_detector?**

```bash
python -c "from domain_detector import detect_domain; print('Import OK')"
```

**Test 3: Can we import load_roles?**

```bash
python -c "from load_roles import load_roles_by_pattern; print('Import OK')"
```

**Test 4: Test domain detection directly**

```bash
python -c "from domain_detector import detect_domain; print(detect_domain('Build an API'))"
```

### Step 3: Test run.py Directly

**Simple test:**

```bash
python run.py "Test objective" 2>&1 | head -20
```

This will show the first 20 lines of output/errors.

---

## Common Issues and Fixes

### Issue 1: Module Not Found

```
ModuleNotFoundError: No module named 'domain_detector'
```

**Fix:**

```bash
# Make sure you're in the right directory
cd implementations/war-room-v0.1b
pwd

# Try running from this directory
python run.py "Test"
```

### Issue 2: DomainConfig.json Missing

```
FileNotFoundError: DomainConfig.json
```

**Fix:**
Create the DomainConfig.json file in the same directory as run.py.

### Issue 3: OpenAI API Key Missing

```
OpenAI initialization failed
```

**Fix:**

```bash
# Check if .env exists
ls -la .env

# Check if OPENAI_API_KEY is set
cat .env | grep OPENAI_API_KEY

# Or set it directly
export OPENAI_API_KEY="your-key-here"
```

### Issue 4: Roles Directory Missing

```
Role file not found: roles/marketing/strategist_stable.txt
```

**Fix:**

```bash
# Create the directory structure
mkdir -p roles/marketing roles/ops roles/technical roles/creative roles/education

# Run setup script
./setup_multi_domain.sh
```

### Issue 5: Import Error from run.py

```
ImportError: cannot import name 'DomainDetector'
```

**Fix:** Make sure domain_detector.py is in the same directory and has no syntax errors:

```bash
python -m py_compile domain_detector.py
```

---

## Step-by-Step Verification

Run this verification script:

```bash
#!/bin/bash
echo "AxProtocol Setup Verification"
echo "=============================="
echo ""

# 1. Check directory
echo "1. Checking directory..."
if [ -f "run.py" ]; then
    echo "   ✅ run.py found"
else
    echo "   ❌ run.py NOT found"
    echo "   You need to be in: implementations/war-room-v0.1b/"
    exit 1
fi

# 2. Check required files
echo ""
echo "2. Checking required files..."
for file in "DomainConfig.json" "domain_detector.py" "load_roles.py" "run.py"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file MISSING"
    fi
done

# 3. Check Python imports
echo ""
echo "3. Checking Python imports..."
python -c "import openai" 2>/dev/null && echo "   ✅ openai" || echo "   ❌ openai (run: pip install openai)"
python -c "import dotenv" 2>/dev/null && echo "   ✅ dotenv" || echo "   ❌ dotenv (run: pip install python-dotenv)"
python -c "from pathlib import Path" 2>/dev/null && echo "   ✅ pathlib" || echo "   ❌ pathlib"

# 4. Check custom imports
echo ""
echo "4. Checking custom modules..."
python -c "from domain_detector import DomainDetector" 2>/dev/null && echo "   ✅ domain_detector" || echo "   ❌ domain_detector"
python -c "from load_roles import load_roles_by_pattern" 2>/dev/null && echo "   ✅ load_roles" || echo "   ❌ load_roles"

# 5. Check roles directory
echo ""
echo "5. Checking roles directory..."
if [ -d "roles" ]; then
    echo "   ✅ roles/ directory exists"
    for domain in marketing ops technical creative education; do
        if [ -d "roles/$domain" ]; then
            count=$(find "roles/$domain" -name "*.txt" 2>/dev/null | wc -l)
            echo "   ✅ roles/$domain ($count files)"
        else
            echo "   ❌ roles/$domain MISSING"
        fi
    done
else
    echo "   ❌ roles/ directory MISSING"
fi

# 6. Check .env
echo ""
echo "6. Checking environment..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    if grep -q "OPENAI_API_KEY" .env; then
        echo "   ✅ OPENAI_API_KEY found in .env"
    else
        echo "   ❌ OPENAI_API_KEY NOT in .env"
    fi
else
    echo "   ⚠️  .env file missing (optional if using env vars)"
fi

echo ""
echo "=============================="
echo "Verification complete!"
```

Save as `verify_setup.sh` and run:

```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

---

## Manual Test (Bypass test script)

If the test script fails, try running manually:

```bash
# Test 1: Simple run
python run.py "Test campaign"

# Test 2: With domain specified
DOMAIN=marketing python run.py "Test campaign"

# Test 3: Show full error
python run.py "Test" 2>&1 | tee error.log
cat error.log
```

---

## Get Full Error Message

Since the error was truncated, run this to see the complete error:

```bash
cd implementations/war-room-v0.1b
python run.py "Test objective" 2>&1 > full_error.txt
cat full_error.txt
```

Then share the full error message so I can help fix it!
