"""Focused tests for the detached Sentinel ledger verifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nacl.signing import SigningKey

from axp.sentinel import verify_ledger as sentinel_verifier


def _record(signing_key: SigningKey, data: dict) -> dict:
    entry = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "role": "TEST",
        "action": "verification",
        "hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
        "data": data,
    }
    payload = json.dumps(entry, sort_keys=True).encode()
    signature = signing_key.sign(payload).hex()
    return {"entry": entry, "sig": signature}


def _write_fixture(tmp_path: Path, monkeypatch, records: list[dict]) -> Path:
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()

    signing_key = SigningKey.generate()
    public_key = ledger_dir / "public.key"
    public_key.write_bytes(signing_key.verify_key.encode())
    monkeypatch.setattr(sentinel_verifier, "PUB_KEY_FILE", str(public_key))

    ledger = ledger_dir / "20260101.jsonl"
    with ledger.open("w", encoding="utf8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return ledger_dir


def test_sentinel_accepts_valid_signed_entry(tmp_path, monkeypatch):
    signing_key = SigningKey.generate()
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    public_key = ledger_dir / "public.key"
    public_key.write_bytes(signing_key.verify_key.encode())
    monkeypatch.setattr(sentinel_verifier, "PUB_KEY_FILE", str(public_key))

    record = _record(signing_key, {"value": 1, "status": "clean"})
    (ledger_dir / "20260101.jsonl").write_text(json.dumps(record) + "\n", encoding="utf8")

    report = sentinel_verifier.verify_all(str(ledger_dir))

    assert report["verified"] is True
    assert report["files_checked"] == 1
    assert report["entries_checked"] == 1
    assert report["details"] == []
    assert report["signature_verification_available"] is True


def test_sentinel_detects_modified_data(tmp_path, monkeypatch):
    signing_key = SigningKey.generate()
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    public_key = ledger_dir / "public.key"
    public_key.write_bytes(signing_key.verify_key.encode())
    monkeypatch.setattr(sentinel_verifier, "PUB_KEY_FILE", str(public_key))

    record = _record(signing_key, {"value": 1})
    record["entry"]["data"]["value"] = 999
    (ledger_dir / "20260101.jsonl").write_text(json.dumps(record) + "\n", encoding="utf8")

    report = sentinel_verifier.verify_all(str(ledger_dir))

    assert report["verified"] is False
    assert report["entries_checked"] == 1
    errors = {detail.get("error") for detail in report["details"]}
    assert "hash_mismatch" in errors
    assert "sig_invalid" in errors


def test_sentinel_counts_clean_and_bad_records(tmp_path, monkeypatch):
    signing_key = SigningKey.generate()
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    public_key = ledger_dir / "public.key"
    public_key.write_bytes(signing_key.verify_key.encode())
    monkeypatch.setattr(sentinel_verifier, "PUB_KEY_FILE", str(public_key))

    valid = _record(signing_key, {"value": 1})
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
    signing_key = SigningKey.generate()
    ledger_dir = tmp_path / "ledger"
    ledger_dir.mkdir()
    monkeypatch.setattr(sentinel_verifier, "PUB_KEY_FILE", str(tmp_path / "missing-public.key"))

    valid = _record(signing_key, {"value": 1})
    (ledger_dir / "20260101.jsonl").write_text(json.dumps(valid) + "\n", encoding="utf8")

    report = sentinel_verifier.verify_all(str(ledger_dir))

    assert report["verified"] is False
    assert report["entries_checked"] == 1
    assert report["signature_verification_available"] is False
    assert any(d.get("error") == "pubkey_not_found" for d in report["details"])
