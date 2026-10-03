"""
Detached Sentinel verification utilities.

AxProtocol currently emits two audit streams into the ledger directory:

1. `*.jsonl` signed records from `axp.governance.ledger` (used by TAES and
   verification paths). Each record contains a SHA-256 hash of `entry.data` and
   a signature over the complete entry.
2. `audit_ledger.db`, the SQLite hash-chain used by the main role-execution
   chain through the historical top-level `ledger.py` module.

Sentinel verifies both formats without importing or executing the LLM runtime.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    _HAVE_NACL = True
except ImportError:
    _HAVE_NACL = False
    import hmac

logger = logging.getLogger("axprotocol.sentinel")

PUB_KEY_ENV = "AXP_PUBLIC_KEY"
# When unset, Sentinel discovers public.key inside the ledger directory passed
# to verify_all(). Keeping this mutable also makes isolated tests straightforward.
PUB_KEY_FILE = os.environ.get(PUB_KEY_ENV)
SQLITE_LEDGER_NAME = "audit_ledger.db"


def _verify_sig(entry: Dict[str, Any], sig_hex: str, pubkey: bytes) -> bool:
    """Verify the signature over canonical JSON for a signed JSONL entry.

    Current Ed25519 records store a detached 64-byte signature. Historical
    records produced before the signature-contract fix stored PyNaCl's complete
    ``SignedMessage`` (64-byte signature followed by the payload) as hex. The
    latter format is accepted only when its recovered payload exactly matches
    the canonical entry being verified.
    """
    if not _HAVE_NACL:
        # Compatibility fallback. This is symmetric authentication, not a true
        # detached public-key trust boundary; see docs/SENTINEL.md.
        try:
            msg = json.dumps(entry, sort_keys=True).encode()
            expected = hmac.new(pubkey, msg, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, sig_hex)
        except Exception:
            return False

    try:
        msg = json.dumps(entry, sort_keys=True).encode()
        signature = bytes.fromhex(sig_hex)
        verify_key = VerifyKey(pubkey)

        if len(signature) == 64:
            verify_key.verify(msg, signature)
            return True

        # Backward compatibility for records created with
        # SigningKey.sign(payload).hex() instead of .signature.hex().
        if len(signature) == 64 + len(msg):
            recovered = verify_key.verify(signature)
            return recovered == msg

        logger.warning(
            "Signature verification error: invalid Ed25519 signature length %s",
            len(signature),
        )
        return False
    except BadSignatureError:
        return False
    except Exception as e:
        logger.warning(f"Signature verification error: {e}")
        return False


def _verify_jsonl(ledger_path: Path) -> Dict[str, Any]:
    """Verify signed JSONL ledger files in *ledger_path*."""
    files = sorted(ledger_path.glob("*.jsonl"))
    if not files:
        return {
            "present": False,
            "verified": None,
            "details": [],
            "files_checked": 0,
            "entries_checked": 0,
            "signature_mode": "ed25519" if _HAVE_NACL else "hmac-fallback",
            "signature_verification_available": False,
        }

    details: List[Dict[str, Any]] = []
    verified = True
    entries_checked = 0
    pubkey: Optional[bytes] = None

    pubkey_path = Path(PUB_KEY_FILE) if PUB_KEY_FILE else ledger_path / "public.key"
    if pubkey_path.exists():
        try:
            pubkey = pubkey_path.read_bytes()
        except IOError as e:
            verified = False
            details.append({
                "source": "signed_jsonl",
                "error": "pubkey_read_failed",
                "reason": str(e),
            })
    else:
        # Hash verification can still run, but authenticity is not established.
        verified = False
        details.append({
            "source": "signed_jsonl",
            "error": "pubkey_not_found",
            "path": str(pubkey_path),
            "note": "content hashes can be checked, signatures cannot",
        })

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf8") as f:
                for line_num, line in enumerate(f, start=1):
                    if not line.strip():
                        continue
                    entries_checked += 1

                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError as e:
                        verified = False
                        details.append({
                            "source": "signed_jsonl",
                            "file": str(file_path),
                            "line": line_num,
                            "error": "invalid_json",
                            "reason": str(e),
                        })
                        continue

                    entry = rec.get("entry")
                    sig = rec.get("sig")
                    if not isinstance(entry, dict) or not entry:
                        verified = False
                        details.append({
                            "source": "signed_jsonl",
                            "file": str(file_path),
                            "line": line_num,
                            "error": "missing_entry",
                        })
                        continue

                    try:
                        data = entry.get("data")
                        if not isinstance(data, dict):
                            raise ValueError("entry.data must be an object")
                        expected_hash = hashlib.sha256(
                            json.dumps(data, sort_keys=True).encode()
                        ).hexdigest()
                        if expected_hash != entry.get("hash"):
                            verified = False
                            details.append({
                                "source": "signed_jsonl",
                                "file": str(file_path),
                                "line": line_num,
                                "error": "hash_mismatch",
                                "expected": expected_hash,
                                "actual": entry.get("hash"),
                            })
                    except Exception as e:
                        verified = False
                        details.append({
                            "source": "signed_jsonl",
                            "file": str(file_path),
                            "line": line_num,
                            "error": "hash_computation_failed",
                            "reason": str(e),
                        })

                    if not sig:
                        verified = False
                        details.append({
                            "source": "signed_jsonl",
                            "file": str(file_path),
                            "line": line_num,
                            "error": "missing_signature",
                        })
                    elif pubkey and not _verify_sig(entry, sig, pubkey):
                        verified = False
                        details.append({
                            "source": "signed_jsonl",
                            "file": str(file_path),
                            "line": line_num,
                            "error": "sig_invalid",
                        })
        except IOError as e:
            verified = False
            details.append({
                "source": "signed_jsonl",
                "file": str(file_path),
                "error": "file_read_failed",
                "reason": str(e),
            })

    return {
        "present": True,
        "verified": verified,
        "details": details,
        "files_checked": len(files),
        "entries_checked": entries_checked,
        "signature_mode": "ed25519" if _HAVE_NACL else "hmac-fallback",
        "signature_verification_available": pubkey is not None,
    }


def verify_sqlite_chain(db_path: Path) -> Dict[str, Any]:
    """Verify the historical/main SQLite execution hash chain read-only.

    The writer in top-level `ledger.py` computes:

        current_hash = SHA256(
            timestamp|agent_id|action|output_hash|previous_hash
        )[:16]

    Sentinel independently checks both the stored `previous_hash` link and the
    recomputed `current_hash` for every row in ID order.
    """
    if not db_path.exists():
        return {
            "present": False,
            "verified": None,
            "details": [],
            "entries_checked": 0,
        }

    details: List[Dict[str, Any]] = []
    rows = []
    try:
        uri = f"file:{db_path.resolve()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            rows = conn.execute(
                "SELECT id, timestamp, agent_id, action, output_hash, "
                "previous_hash, current_hash FROM audit_log ORDER BY id"
            ).fetchall()
    except sqlite3.DatabaseError as e:
        return {
            "present": True,
            "verified": False,
            "details": [{
                "source": "sqlite_hash_chain",
                "file": str(db_path),
                "error": "sqlite_read_failed",
                "reason": str(e),
            }],
            "entries_checked": 0,
        }

    for index, row in enumerate(rows):
        (
            entry_id,
            timestamp,
            agent_id,
            action,
            output_hash,
            previous_hash,
            current_hash,
        ) = row

        expected_prev = "genesis" if index == 0 else rows[index - 1][6]
        if previous_hash != expected_prev:
            details.append({
                "source": "sqlite_hash_chain",
                "file": str(db_path),
                "entry_id": entry_id,
                "error": "previous_hash_mismatch",
                "expected": expected_prev,
                "actual": previous_hash,
            })

        hash_input = f"{timestamp}|{agent_id}|{action}|{output_hash}|{expected_prev}"
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        if current_hash != expected_hash:
            details.append({
                "source": "sqlite_hash_chain",
                "file": str(db_path),
                "entry_id": entry_id,
                "error": "current_hash_mismatch",
                "expected": expected_hash,
                "actual": current_hash,
            })

    return {
        "present": True,
        "verified": len(details) == 0,
        "details": details,
        "entries_checked": len(rows),
    }


def verify_all(ledger_dir: str = "/audit/ledger") -> Dict[str, Any]:
    """Verify every supported audit artifact in *ledger_dir*.

    The overall result is true only when at least one supported ledger artifact
    exists and every present artifact verifies successfully.
    """
    ledger_path = Path(ledger_dir)
    if not ledger_path.exists():
        return {
            "verified": False,
            "details": [{"error": "ledger_dir_not_found", "path": ledger_dir}],
            "files_checked": 0,
            "entries_checked": 0,
            "signed_jsonl": {"present": False, "verified": None},
            "sqlite_hash_chain": {"present": False, "verified": None},
        }

    signed = _verify_jsonl(ledger_path)
    sqlite_report = verify_sqlite_chain(ledger_path / SQLITE_LEDGER_NAME)

    present_reports = [r for r in (signed, sqlite_report) if r.get("present")]
    if not present_reports:
        return {
            "verified": False,
            "details": [{"error": "no_supported_ledger_artifacts"}],
            "files_checked": 0,
            "entries_checked": 0,
            "signed_jsonl": signed,
            "sqlite_hash_chain": sqlite_report,
        }

    details = list(signed.get("details", [])) + list(sqlite_report.get("details", []))
    verified = all(r.get("verified") is True for r in present_reports)

    return {
        "verified": verified,
        "details": details,
        "files_checked": signed.get("files_checked", 0) + (1 if sqlite_report.get("present") else 0),
        "entries_checked": signed.get("entries_checked", 0) + sqlite_report.get("entries_checked", 0),
        "signature_mode": signed.get("signature_mode"),
        "signature_verification_available": signed.get("signature_verification_available", False),
        "signed_jsonl": signed,
        "sqlite_hash_chain": sqlite_report,
    }
