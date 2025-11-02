"""
Sentinel autonomous auditor for AxProtocol ledgers.
"""

from __future__ import annotations

import glob
import json
import hashlib
from pathlib import Path
from typing import List
import sys

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from axp.governance.ledger import get_public_key_path, verify_payload

PUB_KEY_PATH = get_public_key_path()

REPORT_DIR = Path("logs/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = REPORT_DIR / "sentinel_report.json"


def verify_ledger() -> dict:
    _ = PUB_KEY_PATH.exists()
    files = sorted(glob.glob("logs/ledger/*.jsonl"))
    results: List[dict] = []
    verified = True

    for file in files:
        with open(file, "r", encoding="utf8") as f:
            for line_no, line in enumerate(f, start=1):
                rec = json.loads(line)
                entry = rec.get("entry", {})
                sig_hex = rec.get("sig")
                payload = json.dumps(entry, sort_keys=True).encode()
                expected_hash = hashlib.sha256(json.dumps(entry.get("data", {}), sort_keys=True).encode()).hexdigest()
                if entry.get("hash") != expected_hash:
                    verified = False
                    results.append({"file": file, "line": line_no, "error": "Hash mismatch"})
                    continue
                try:
                    verify_payload(payload, sig_hex)
                except Exception as exc:
                    verified = False
                    results.append({"file": file, "line": line_no, "error": f"Signature invalid: {exc}"})

    report = {"verified": verified, "details": results, "ledger_files": files}
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf8")
    return report


if __name__ == "__main__":
    verify_ledger()
