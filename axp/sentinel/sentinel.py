"""Sentinel CLI Auditor.

Thin command-line wrapper around the detached read-only verifier. This module
must not import AxProtocol's producer-side signing implementation or initialize
private signing-key state.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

try:
    from .verify_ledger import verify_all
except ImportError:  # pragma: no cover - supports direct/Docker-style execution
    from verify_ledger import verify_all

logger = logging.getLogger("axprotocol.sentinel")

LOCAL_LEDGER_DIR = os.getenv("AXP_LEDGER_DIR", "logs/ledger")
REPORT_DIR = Path(os.getenv("AXP_REPORTS_DIR", "logs/reports"))
REPORT_PATH = REPORT_DIR / "sentinel_report.json"


def verify_ledger(ledger_dir: str = LOCAL_LEDGER_DIR) -> dict:
    """Verify supported ledger artifacts and persist a local report.

    Verification itself is delegated to `verify_all`, which opens the SQLite
    ledger read-only and only reads JSONL/public-key evidence. No signing key is
    created or loaded by this CLI path.
    """
    report = verify_all(ledger_dir=ledger_dir)

    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf8")
    except OSError as exc:
        logger.error("Failed to write Sentinel report: %s", exc)

    return report


if __name__ == "__main__":
    result = verify_ledger()
    print(json.dumps(result, indent=2))
