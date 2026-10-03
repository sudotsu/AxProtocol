"""Focused tests for the detached Sentinel ledger verifier."""

from __future__ import annotations

import hashlib
import hmac
import json

from axp.sentinel import verify_ledger as sentinel_verifier


class _Signer:
    """Create valid test signatures for the verifier's active signature mode."""

    def __init__(self):
        if sentinel_verifier._HAVE_NACL:
            from nacl.signing import SigningKey

            self._key = SigningKey.generate()
            self.public_bytes = self._key.verify_key.encode()
        else:
            self._key = b"sentinel-test-hmac-secret-32-byte!"
            self.public_bytes = self._key

    def sign_hex(self, payload: bytes) -> str:
        if sentinel_verifier._HAVE_NACL:
            return self._key.sign(payload).hex()
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()


def _record(signer: _Signer, data: dict) -> dict:
    entry = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "role": "TEST",
        "action": "verification",
        "hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
        "data": data,
    }
    payload = json.dumps(entry, sort_keys=True).encode()
    return {"entry": entry, "sig": signer.sign_hex(payload)}


def _ledger_with_key(tmp_path, monkeypatch):
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    signer = _Signer()
    public_key = ledger_dir / "public.key"
    public_key.write_bytes(signer.public_bytes)
    monkeypatch.setattr(sentinel_verifier, "PUB_KEY_FILE", str(public_key))
    return ledger_dir, signer


def test_sentinel_accepts_valid_signed_entry(tmp_path, monkeypatch):
    ledger_dir, signer = _ledger_with_key(tmp_path, monkeypatch)
    record = _record(signer, {"value": 1, "status": "clean"})
    (ledger_dir / "20260101.jsonl").write_text(json.dumps(record) + "\n", encoding="utf8")

    report = sentinel_verifier.verify_all(str(ledger_dir))

    assert report["verified"] is True
    assert report["files_checked"] == 1
    assert report["entries_checked"] == 1
    assert report["details"] == []
    assert report["signature_verification_available"] is True


def test_sentinel_detects_modified_data(tmp_path, monkeypatch):
    ledger_dir, signer = _ledger_with_key(tmp_path, monkeypatch)
    record = _record(signer, {"value": 1})
    record["entry"]["data"]["value"] = 999
    (ledger_dir / "20260101.jsonl").write_text(json.dumps(record) + "\n", encoding="utf8")

    report = sentinel_verifier.verify_all(str(ledger_dir))

    assert report["verified"] is False
    assert report["entries_checked"] == 1
    errors = {detail.get("error") for detail in report["details"]}
    assert "hash_mismatch" in errors
    assert "sig_invalid" in errors


def test_sentinel_counts_clean_and_bad_records(tmp_path, monkeypatch):
    ledger_dir, signer = _ledger_with_key(tmp_path, monkeypatch)
    valid = _record(signer, {"value": 1})
    ledger = ledger_dir / "20260101.jsonl"
    ledger.write_text(
        json.dumps(valid) + "\n" + "{not valid json}\n" + json.dumps(valid) + "\n",
        encoding="utf8",
    )

    report = sentinel_verifier.verify_all(str(ledger_dir))

    assert report["verified"] is False
    assert report["entries_checked"] == 3
    assert any(d.get("error") == "invalid_json" for d in report["details"])


def test_sentinel_does_not_claim_verified_without_public_key(tmp_path, monkeypatch):
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    signer = _Signer()
    monkeypatch.setattr(sentinel_verifier, "PUB_KEY_FILE", str(tmp_path / "missing-public.key"))

    valid = _record(signer, {"value": 1})
    (ledger_dir / "20260101.jsonl").write_text(json.dumps(valid) + "\n", encoding="utf8")

    report = sentinel_verifier.verify_all(str(ledger_dir))

    assert report["verified"] is False
    assert report["entries_checked"] == 1
    assert report["signature_verification_available"] is False
    assert any(d.get("error") == "pubkey_not_found" for d in report["details"])
