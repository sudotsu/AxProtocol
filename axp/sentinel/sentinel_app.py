from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import json

from verify_ledger import verify_all

REPORTS_DIR = "/audit/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

app = FastAPI(title="AxProtocol Sentinel", version="1.0")


@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.get("/verify")
def verify():
    res = verify_all()
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(REPORTS_DIR, f"sentinel_{stamp}.json")
    with open(path, "w", encoding="utf8") as f:
        json.dump(res, f, indent=2)
    return JSONResponse(res)


@app.get("/reports")
def list_reports():
    files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith(".json")])[-30:]
    return {"reports": files}
