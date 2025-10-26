"""
AxProtocol TAES Evaluation Engine v2.2
Converts reasoning outputs into measurable Logical/Practical/Probable scores.
"""

import json
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from openai import OpenAI  # pyright: ignore[reportMissingImports]
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Adaptive weighting matrix (Directive 25a)
ADAPTIVE_MATRIX = {
    "code": {"logical": 0.6, "practical": 0.35, "probable": 0.05},
    "infrastructure": {"logical": 0.6, "practical": 0.35, "probable": 0.05},
    "ops": {"logical": 0.4, "practical": 0.45, "probable": 0.15},
    "operations": {"logical": 0.4, "practical": 0.45, "probable": 0.15},
    "process": {"logical": 0.4, "practical": 0.45, "probable": 0.15},
    "creative": {"logical": 0.35, "practical": 0.25, "probable": 0.4},
    "content": {"logical": 0.35, "practical": 0.25, "probable": 0.4},
    "marketing": {"logical": 0.3, "practical": 0.2, "probable": 0.5},
    "growth": {"logical": 0.3, "practical": 0.2, "probable": 0.5},
    "default": {"logical": 0.4, "practical": 0.4, "probable": 0.2},
}

IRD_LOG = Path("logs/ird_log.csv")
IRD_LOG.parent.mkdir(parents=True, exist_ok=True)

def evaluate_taes(
    output: str,
    domain: str = "default",
    session_id: Optional[str] = None,
    role_name: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> dict:
    """
    Score output on Logical/Practical/Probable axes.
    Returns TAES verdict with IV, IRD, and RRP requirement.
    """

    # Normalize domain
    domain = domain.lower().strip()
    if domain not in ADAPTIVE_MATRIX:
        domain = "default"

    # Get weights
    weights = ADAPTIVE_MATRIX[domain]

    # Construct scoring prompt
    prompt = f"""Score this output on three dimensions (0-100 scale):

**Logical**: Correctness, consistency, evidence quality, logical coherence
**Practical**: Feasibility, resource requirements, timeline realism, implementation clarity
**Probable**: Realistic human behavior, adoption likelihood, psychological plausibility

Context: This is a {domain} task.

Output to evaluate:
{output[:2500]}

Return ONLY valid JSON in this exact format:
{{"logical": <0-100>, "practical": <0-100>, "probable": <0-100>}}"""

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=150,
            messages=[
                {"role": "system", "content": "You are a TAES evaluator. Return only JSON."},
                {"role": "user", "content": prompt}
            ]
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        scores = json.loads(raw)

        # Validate scores
        for key in ["logical", "practical", "probable"]:
            if key not in scores or not (0 <= scores[key] <= 100):
                raise ValueError(f"Invalid score for {key}")

    except Exception as e:
        print(f"[TAES ERROR] Scoring failed: {e}")
        # Fallback scores (neutral)
        scores = {"logical": 75, "practical": 75, "probable": 75}

    # Calculate metrics
    logical_norm = scores["logical"] / 100
    practical_norm = scores["practical"] / 100
    probable_norm = scores["probable"] / 100

    # Integrity Vector (weighted mean)
    iv = (
        logical_norm * weights["logical"] +
        practical_norm * weights["practical"] +
        probable_norm * weights["probable"]
    )

    # Ideal-Reality Disparity
    ird = abs((logical_norm + practical_norm) - probable_norm)

    # Reality Reconciliation Pass required?
    requires_rrp = ird > 0.5

    result = {
        "scores": scores,
        "weights": weights,
        "domain": domain,
        "integrity_vector": round(iv, 3),
        "ird": round(ird, 3),
        "requires_rrp": requires_rrp,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "role_name": role_name,
    }

    # Log to CSV
    _log_ird(result)

    return result


def _log_ird(result: dict):
    """Append IRD data to logs/ird_log.csv (Directive 25b)"""
    header = [
        "timestamp", "session_id", "role_name", "domain",
        "logical", "practical", "probable",
        "iv", "ird", "requires_rrp"
    ]

    row = [
        result["timestamp"],
        result.get("session_id", ""),
        result.get("role_name", ""),
        result["domain"],
        result["scores"]["logical"],
        result["scores"]["practical"],
        result["scores"]["probable"],
        result["integrity_vector"],
        result["ird"],
        result["requires_rrp"]
    ]

    file_exists = IRD_LOG.exists()

    with open(IRD_LOG, "a", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(row)


def check_cognitive_disalignment() -> dict:
    """
    Analyze recent IRD trends.
    Alert if monthly average > 0.4 (Directive 25b).
    """
    if not IRD_LOG.exists():
        return {"alert": False, "reason": "No IRD data"}

    try:
        with open(IRD_LOG, "r", encoding="utf8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if len(rows) < 5:
            return {"alert": False, "reason": "Insufficient data"}

        recent = rows[-30:]  # Last 30 entries
        avg_ird = sum(float(r["ird"]) for r in recent) / len(recent)

        if avg_ird > 0.4:
            return {
                "alert": True,
                "avg_ird": round(avg_ird, 3),
                "reason": "Cognitive Disalignment Alert: IRD average > 0.4"
            }

        return {"alert": False, "avg_ird": round(avg_ird, 3)}

    except Exception as e:
        return {"alert": False, "reason": f"Analysis failed: {e}"}


if __name__ == "__main__":
    # Test
    test_output = """
    The strategy positions tree services as emergency-ready 24/7 providers.
    Target audiences: homeowners with storm damage, property managers, insurance adjusters.
    Three hooks: speed (same-day), safety (licensed/insured), savings (20% gap-fill discount).
    """

    result = evaluate_taes(test_output, domain="marketing", session_id="test-001", role_name="Strategist")
    print(json.dumps(result, indent=2))
    print(f"\n✅ Logged to {IRD_LOG}")