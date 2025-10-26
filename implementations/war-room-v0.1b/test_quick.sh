#!/bin/bash
# Quick multi-domain testing script

echo "=========================================="
echo "AxProtocol Quick Domain Tests"
echo "=========================================="
echo ""

# Test counter
PASS=0
FAIL=0

# Test function
run_test() {
    local domain=$1
    local objective=$2
    echo "Testing: $domain"
    echo "  Objective: ${objective:0:60}..."

    if DOMAIN=$domain TIER=DEV python run.py "$objective" > /dev/null 2>&1; then
        echo "  ✅ PASS"
        ((PASS++))
    else
        echo "  ❌ FAIL"
        ((FAIL++))
    fi
    echo ""
}

# Run tests
run_test "marketing" "Launch social media campaign for coffee shop"
run_test "technical" "Build REST API with user authentication"
run_test "ops" "Design employee onboarding workflow"
run_test "creative" "Create brand identity for eco startup"
run_test "education" "Develop Python programming course"

# Summary
echo "=========================================="
echo "Summary: $PASS passed, $FAIL failed"
echo "=========================================="

if [ $FAIL -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi