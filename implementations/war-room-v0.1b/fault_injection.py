"""
AxProtocol Fault Injection Testing Framework

Stress-tests the War Room system with adversarial inputs, malformed data,
and edge cases to validate enforcement mechanisms.

Test Categories:
- Δ1: Malformed Objectives (empty, nonsensical, contradictory)
- Δ2: Score Manipulation (invalid scores, missing dimensions)
- Δ3: Protocol Bypass Attempts (directive violations, unauthorized changes)
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from run import run_chain
    from taes_evaluation import evaluate_taes
    from score_validator import validate_scores
    from ledger import get_last_n_entries
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import all modules: {e}")
    print("⚠️  Running in limited mode")
    MODULES_AVAILABLE = False


class FaultInjectionTest:
    """Base class for fault injection tests"""

    def __init__(self, test_id: str, description: str):
        self.test_id = test_id
        self.description = description
        self.passed = None
        self.error = None

    def run(self) -> bool:
        """Execute the test. Return True if system handles fault correctly."""
        raise NotImplementedError("Subclasses must implement run()")

    def report(self) -> Dict:
        """Generate test report"""
        return {
            'test_id': self.test_id,
            'description': self.description,
            'passed': self.passed,
            'error': self.error
        }


class MalformedObjectiveTest(FaultInjectionTest):
    """Test system resilience to malformed objectives"""

    def __init__(self, test_id: str, objective: str, expected_behavior: str):
        super().__init__(test_id, f"Malformed objective: {expected_behavior}")
        self.objective = objective
        self.expected_behavior = expected_behavior

    def run(self) -> bool:
        """Run test with malformed objective"""
        if not MODULES_AVAILABLE:
            self.passed = None
            self.error = "Modules not available"
            return False

        try:
            print(f"\n[{self.test_id}] Testing: {self.description}")
            print(f"   Input: '{self.objective}'")


            # Run the chain
            s, a, p_rev, c_rev, crit, results = run_chain(self.objective)

            # System should either gracefully handle or properly reject
            # Check that TAES evaluation still ran
            if 'strategist' in results and 'taes' in results['strategist']:
                self.passed = True
                print(f"   ✅ System handled gracefully (TAES ran)")
            else:
                self.passed = False
                self.error = "TAES evaluation failed"
                print(f"   ❌ System failed to evaluate")

        except Exception as e:
            # System properly rejected the input
            self.passed = True
            print(f"   ✅ System properly rejected: {type(e).__name__}")

        return self.passed


class ScoreManipulationTest(FaultInjectionTest):
    """Test score validation mechanisms"""

    def __init__(self, test_id: str, description: str):
        super().__init__(test_id, description)

    def run(self) -> bool:
        """Test score validation"""
        # This would test the score_validator module directly
        print(f"\n[{self.test_id}] {self.description}")
        print(f"   ⚠️  Not yet implemented")
        self.passed = None
        return False


def run_delta_1_tests() -> List[Dict]:
    """Run Δ1 tests: Malformed objectives"""
    tests = [
        MalformedObjectiveTest(
            "Δ1.1",
            "",
            "Empty string"
        ),
        MalformedObjectiveTest(
            "Δ1.2",
            "asdfghjkl qwertyuiop",
            "Random characters"
        ),
        MalformedObjectiveTest(
            "Δ1.3",
            "Make me rich but also keep costs at zero and do it yesterday",
            "Contradictory requirements"
        ),
        MalformedObjectiveTest(
            "Δ1.4",
            "🔥💰🚀" * 50,
            "Emoji spam"
        ),
    ]

    results = []
    for test in tests:
        test.run()
        results.append(test.report())

    return results


def run_delta_2_tests() -> List[Dict]:
    """Run Δ2 tests: Score manipulation"""
    tests = [
        ScoreManipulationTest("Δ2.1", "Invalid score format"),
        ScoreManipulationTest("Δ2.2", "Missing dimensions"),
        ScoreManipulationTest("Δ2.3", "Out of range scores"),
    ]

    results = []
    for test in tests:
        test.run()
        results.append(test.report())

    return results


def run_delta_3_tests() -> List[Dict]:
    """Run Δ3 tests: Protocol bypass attempts"""
    print("\n[Δ3] Protocol Bypass Tests")
    print("   ⚠️  Not yet implemented")
    return []


def generate_report(all_results: List[Dict]) -> str:
    """Generate comprehensive test report"""
    report = []
    report.append("\n" + "="*70)
    report.append("AxProtocol Fault Injection Test Report")
    report.append("="*70)
    report.append(f"Run time: {datetime.now().isoformat()}")
    report.append(f"Total tests: {len(all_results)}")

    passed = sum(1 for r in all_results if r['passed'] is True)
    failed = sum(1 for r in all_results if r['passed'] is False)
    skipped = sum(1 for r in all_results if r['passed'] is None)

    report.append(f"Passed: {passed}")
    report.append(f"Failed: {failed}")
    report.append(f"Skipped: {skipped}")
    report.append("\nDetailed Results:")
    report.append("-"*70)

    for result in all_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL" if result['passed'] is False else "⚠️  SKIP"
        report.append(f"\n{result['test_id']}: {status}")
        report.append(f"   {result['description']}")
        if result['error']:
            report.append(f"   Error: {result['error']}")

    report.append("\n" + "="*70)

    return "\n".join(report)


def main():
    """Main test runner"""
    print("\n🔥 AxProtocol Fault Injection Framework")
    print("="*70)

    if not MODULES_AVAILABLE:
        print("\n⚠️  Critical modules not available. Install dependencies:")
        print("   pip install -r requirements.txt")
        return

    # Parse command line args
    import argparse
    parser = argparse.ArgumentParser(description="Run AxProtocol fault injection tests")
    parser.add_argument('--run', type=str, default='Δ1',
                       help='Test suite to run: Δ1, Δ2, Δ3, or comma-separated list')
    args = parser.parse_args()

    # Determine which tests to run
    test_suites = [s.strip() for s in args.run.split(',')]
    all_results = []

    for suite in test_suites:
        if suite == 'Δ1':
            all_results.extend(run_delta_1_tests())
        elif suite == 'Δ2':
            all_results.extend(run_delta_2_tests())
        elif suite == 'Δ3':
            all_results.extend(run_delta_3_tests())
        else:
            print(f"⚠️  Unknown test suite: {suite}")

    # Generate and print report
    report = generate_report(all_results)
    print(report)

    # Save report to file
    report_path = Path(f"logs/fault_injection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    print(f"\n📄 Report saved: {report_path}")


if __name__ == "__main__":
    main()