"""
AxProtocol Score Validation — Directive 16 enforcement
Extracts role self-scores and validates against 85/100 threshold.
"""

import re
from typing import Optional

def extract_scores(output: str) -> Optional[dict]:
    """
    Parse role output for self-reported scores.
    Expected format:
        Transformation: 87/100
        Clarity: 91/100
        Reach: 85/100
        Return: 89/100
    """
    pattern = r"(Transformation|Clarity|Reach|Return|Logical|Practical|Probable):\s*(\d+)(?:/100)?"
    matches = re.findall(pattern, output, re.IGNORECASE)

    if not matches:
        return None

    scores = {}
    for dimension, value in matches:
        scores[dimension.lower()] = int(value)

    return scores


def validate_scores(scores: dict, threshold: int = 85) -> dict:
    """
    Check if scores meet threshold.
    Returns validation result with pass/fail and details.
    """
    if not scores:
        return {
            "valid": False,
            "reason": "No scores found in output",
            "scores": {},
            "average": 0
        }

    avg = sum(scores.values()) / len(scores)
    passed = avg >= threshold

    below_threshold = {k: v for k, v in scores.items() if v < threshold}

    return {
        "valid": passed,
        "scores": scores,
        "average": round(avg, 1),
        "threshold": threshold,
        "below_threshold": below_threshold,
        "reason": f"Average {avg:.1f} {'≥' if passed else '<'} {threshold}" if scores else "No scores"
    }


def format_score_block(scores: dict) -> str:
    """Generate score table for logging/display."""
    lines = ["Score Summary:"]
    for dim, val in scores.items():
        lines.append(f"  {dim.capitalize()}: {val}/100")
    avg = sum(scores.values()) / len(scores)
    lines.append(f"  Average: {avg:.1f}/100")
    return "\n".join(lines)


if __name__ == "__main__":
    # Test
    sample = """
    ## Strategist Output
    Positioning: 24/7 emergency tree services for Omaha homeowners.

    Score Table:
    Transformation: 87/100
    Clarity: 91/100
    Reach: 85/100
    Return: 89/100
    """

    scores = extract_scores(sample)
    validation = validate_scores(scores, threshold=85)

    print(format_score_block(scores))
    print(f"\nValidation: {'✅ PASS' if validation['valid'] else '❌ FAIL'}")
    print(f"Reason: {validation['reason']}")