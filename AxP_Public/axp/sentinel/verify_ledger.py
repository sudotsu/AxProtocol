import json
import glob
import hashlib
import os
from typing import List, Dict

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

PUB_KEY_ENV = "AXP_PUBLIC_KEY"
PUB_KEY_FILE = os.environ.get(PUB_KEY_ENV, "/audit/ledger/public.key")


def _verify_sig(entry: Dict[str, any], sig_hex: str, pubkey: bytes) -> bool:
    msg = json.dumps(entry, sort_keys=True).encode()
    try:
        VerifyKey(pubkey).verify(msg, bytes.fromhex(sig_hex))
        return True
    except BadSignatureError:
        return False


def verify_all(ledger_dir: str = "/audit/ledger") -> Dict[str, any]:
    files = sorted(glob.glob(os.path.join(ledger_dir, "*.jsonl")))
    if not files:
        return {"verified": False, "details": ["no_ledger_files"]}

    details: List[Dict[str, any]] = []
    ok = True
    pubkey = None
    if os.path.exists(PUB_KEY_FILE):
        pubkey = open(PUB_KEY_FILE, "rb").read()

    for fp in files:
        with open(fp, "r", encoding="utf8") as f:
            for line_num, line in enumerate(f, start=1):
                rec = json.loads(line)
                entry = rec.get("entry", {})
                sig = rec.get("sig")
                payload_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
                if payload_hash != entry.get("hash"):
                    ok = False
                    details.append({"file": fp, "line": line_num, "error": "hash_mismatch"})
                if pubkey and sig:
                    if not _verify_sig(entry, sig, pubkey):
                        ok = False
                        details.append({"file": fp, "line": line_num, "error": "sig_invalid"})

    return {"verified": ok, "details": details}
