"""
Ledger Verification Utilities
-----------------------------
Shared verification logic for the detached Sentinel auditor.

Sentinel is intentionally able to verify ledger artifacts without importing the
AxProtocol LLM/orchestration stack. The ledger writer stores `entry["hash"]` as
the SHA-256 digest of `entry["data"]`; Sentinel must validate that exact contract
before checking the signature over the complete entry object.
"""

import json
import hashlib
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    _HAVE_NACL = True
except ImportError:
    _HAVE_NACL = False
    import hmac

logger = logging.getLogger("axprotocol.sentinel")

PUB_KEY_ENV = "AXP_PUBLIC_KEY"
PUB_KEY_FILE = os.environ.get(PUB_KEY_ENV, "/audit/ledger/public.key")


def _verify_sig(entry: Dict[str, Any], sig_hex: str, pubkey: bytes) -> bool:
    """Verify the signature over the canonical JSON representation of an entry."""
    if not _HAVE_NACL:
        # HMAC fallback verification. In fallback mode the mirrored "public" key
        # is necessarily the shared secret; see docs/SENTINEL.md for limitations.
        try:
            secret = pubkey
            msg = json.dumps(entry, sort_keys=True).encode()
            expected = hmac.new(secret, msg, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, sig_hex)
        except Exception:
            return False

    try:
        msg = json.dumps(entry, sort_keys=True).encode()
        VerifyKey(pubkey).verify(msg, bytes.fromhex(sig_hex))
        return True
    except BadSignatureError:
        return False
    except Exception as e:
        logger.warning(f"Signature verification error: {e}")
        return False


def verify_all(ledger_dir: str = "/audit/ledger") -> Dict[str, Any]:
    """Verify every JSONL ledger record in *ledger_dir*.

    Checks performed per non-empty record:
    1. JSON structure can be parsed.
    2. `entry.data` is an object and its canonical SHA-256 equals `entry.hash`.
    3. If a verification key is available, the signature over the full entry is valid.

    The function is read-only with respect to the ledger.
    """
    ledger_path = Path(ledger_dir)
    if not ledger_path.exists():
        logger.warning(f"Ledger directory does not exist: {ledger_dir}")
        return {
            "verified": False,
            "details": [{"error": "ledger_dir_not_found", "path": ledger_dir}],
            "files_checked": 0,
            "entries_checked": 0,
        }

    files = sorted(ledger_path.glob("*.jsonl"))
    if not files:
        logger.warning(f"No ledger files found in {ledger_dir}")
        return {
            "verified": False,
            "details": [{"error": "no_ledger_files"}],
            "files_checked": 0,
            "entries_checked": 0,
        }

    details: List[Dict[str, Any]] = []
    verified = True
    entries_checked = 0
    pubkey: Optional[bytes] = None

    pubkey_path = Path(PUB_KEY_FILE)
    if pubkey_path.exists():
        try:
            pubkey = pubkey_path.read_bytes()
        except IOError as e:
            logger.error(f"Failed to read public key: {e}")
            return {
                "verified": False,
                "details": [{"error": "pubkey_read_failed", "reason": str(e)}],
                "files_checked": len(files),
                "entries_checked": 0,
            }
    else:
        # Hash verification remains useful without a key, but the report must not
        # imply cryptographic authenticity was established.
        verified = False
        details.append({
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
                                "file": str(file_path),
                                "line": line_num,
                                "error": "hash_mismatch",
                                "expected": expected_hash,
                                "actual": entry.get("hash"),
                            })
                    except Exception as e:
                        verified = False
                        details.append({
                            "file": str(file_path),
                            "line": line_num,
                            "error": "hash_computation_failed",
                            "reason": str(e),
                        })

                    if not sig:
                        verified = False
                        details.append({
                            "file": str(file_path),
                            "line": line_num,
                            "error": "missing_signature",
                        })
                    elif pubkey and not _verify_sig(entry, sig, pubkey):
                        verified = False
                        details.append({
                            "file": str(file_path),
                            "line": line_num,
                            "error": "sig_invalid",
                        })
        except IOError as e:
            verified = False
            details.append({
                "file": str(file_path),
                "error": "file_read_failed",
                "reason": str(e),
            })

    return {
        "verified": verified,
        "details": details,
        "files_checked": len(files),
        "entries_checked": entries_checked,
        "signature_mode": "ed25519" if _HAVE_NACL else "hmac-fallback",
        "signature_verification_available": pubkey is not None,
    }
