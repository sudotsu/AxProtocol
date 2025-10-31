"""
AxProtocol Ledger Signing Layer
-------------------------------
Append-only ledger with Ed25519 signatures using PyNaCl.
"""

from __future__ import annotations

import json
import hashlib
import time
import os
from pathlib import Path
from typing import Any, Dict

try:
    from nacl.signing import SigningKey, VerifyKey
    _HAVE_NACL = True
except ImportError:  # pragma: no cover - fallback when PyNaCl unavailable
    _HAVE_NACL = False
    import hmac
    import secrets

_KEY_DIR = Path(os.path.expanduser("~/.axp_keys"))
_KEY_DIR.mkdir(parents=True, exist_ok=True)
_PRIVATE_PATH = _KEY_DIR / "private.key"
_PUBLIC_PATH = _KEY_DIR / "public.key"

if _HAVE_NACL:
    if not _PRIVATE_PATH.exists():
        sk = SigningKey.generate()
        _PRIVATE_PATH.write_bytes(sk.encode())
        _PUBLIC_PATH.write_bytes(sk.verify_key.encode())
    _SIGNING_KEY = SigningKey(_PRIVATE_PATH.read_bytes())
    _PUBLIC_PATH.write_bytes(_SIGNING_KEY.verify_key.encode())

    def _sign(payload: bytes) -> str:
        return _SIGNING_KEY.sign(payload).hex()

    def _verify(payload: bytes, sig_hex: str) -> None:
        verify_key = VerifyKey(_PUBLIC_PATH.read_bytes())
        verify_key.verify(payload, bytes.fromhex(sig_hex))
else:
    if not _PRIVATE_PATH.exists():
        secret = secrets.token_bytes(32)
        _PRIVATE_PATH.write_bytes(secret)
        _PUBLIC_PATH.write_bytes(secret)
    _SECRET = _PRIVATE_PATH.read_bytes()
    _PUBLIC_PATH.write_bytes(_SECRET)

    def _sign(payload: bytes) -> str:
        return hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()

    def _verify(payload: bytes, sig_hex: str) -> None:
        expected = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig_hex):
            raise ValueError("Signature mismatch")

LEDGER_DIR = Path("logs/ledger")
LEDGER_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_PUBLIC_KEY_PATH = LEDGER_DIR / "public.key"

if _HAVE_NACL:
    LEDGER_PUBLIC_KEY_PATH.write_bytes(_SIGNING_KEY.verify_key.encode())
else:
    if not LEDGER_PUBLIC_KEY_PATH.exists():
        LEDGER_PUBLIC_KEY_PATH.write_bytes(_SECRET)


def write_ledger_entry(role: str, action: str, data: Dict[str, Any]) -> str:
    """
    Append a signed ledger entry.
    Returns the content hash for downstream linkage.
    """
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role": role,
        "action": action,
        "hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
        "data": data,
    }
    payload = json.dumps(entry, sort_keys=True).encode()
    signature = _sign(payload)

    file_path = LEDGER_DIR / f"{time.strftime('%Y%m%d')}.jsonl"
    with open(file_path, "a", encoding="utf8") as f:
        f.write(json.dumps({"entry": entry, "sig": signature}) + "\n")

    return entry["hash"]


def get_public_key_path() -> Path:
    return _PUBLIC_PATH


def verify_payload(payload: bytes, signature_hex: str) -> None:
    """Raise ValueError if signature invalid."""
    _verify(payload, signature_hex)
