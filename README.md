# AxProtocol v2.6 — Config‑Driven, Sentinel‑Audited Reasoning OS

AxProtocol is a **self-auditing, directive-aware AI reasoning kernel**.  
Every chain runs multi-role agents (Strategist → Analyst → Producer → Courier → Critic), is scored by TAES (Truth / Alignment / Efficiency / Signal) and is governed by hard and soft “directive” signals. All output is logged to an **append-only, cryptographically signed ledger** and independently verified by a detached **Sentinel** auditor.

---

## 1. Where We Stand (October 31, 2025)

### Core Kernel
- Multi-role reasoning pipeline with schema-validated JSON slices (`run_axp.py`).
- Config-driven prompts & behaviours (domain-specific roles under `roles/<domain>/`).
- Governance coupling (`config/governance_coupling.json`) with:
  - **Hard gates**: D3 contradiction, D2 ambiguity, D7/D11 precedence, D13 sycophancy, D20–24 overconfidence (caps IV, raises IRD, forces RRP).
  - **Soft gates**: D0 change control, Secrets/PII, Fabrication, Domain misrouting, Observability gap, Redundancy (logged for audits).
- TAES evaluation wired to ledger (`taes_evaluation.py`): each scoring writes a signed entry and returns `ledger_hash`.
- Deterministic pytest suites (`verify/`) covering directive enforcement and TAES integrity.

### Governance & Auditing
- **Ledger signing layer** (`axp/governance/ledger.py`): Ed25519 signatures (HMAC fallback) with keys stored in `~/.axp_keys` and public key mirrored to `logs/ledger/public.key`.
- **Sentinel auditor** (`axp/sentinel/sentinel.py`, `verify_ledger.py`, `sentinel_app.py`):
  - `/health` endpoint.
  - `/verify` recomputes hashes & signatures, writes timestamped reports under `logs/reports/`.
  - `/reports` lists recent audits.
- GitHub Action (`.github/workflows/deploy.yml`) builds both images, pushes to GHCR, SCPs compose/env to VPS, and restarts stack via SSH.
- Smoke script (`scripts/smoke.sh`) hits app root, Sentinel health, and `/verify`.

### Deployment Assets
- `docker-compose.yml`: Traefik v2.11 + AxP + Sentinel, TLS via ACME, rate limiting.
- `Dockerfile.axp` / `Dockerfile.sentinel`.
- Production `.env` contains ACME domains, image tags, signup controls, etc.
- `env.example` documents every variable required for AxP, Sentinel, waitlist API, and frontend.

### State of the UX
- Streamlit console (`app_axp.py`) shows TAES tables, registry summaries, governance signals, Sentinel score, and drift entries.
- Allowlist gate: first 50 users remain free (`ENABLE_SIGNUP`, `config/allowlist.txt`).
- About tab documents governance promise (Truth > Obedience, signed ledger, independent Sentinel).

---

## 2. What’s New Since v2.5

| Area | v2.5 | v2.6 |
|------|------|------|
| Governance | Hard-coded gates | JSON-configured coupling (hard + soft) |
| Auditing | Ledger hash only | Ed25519-signed ledger + Sentinel verification |
| UI | Basic metrics | Advanced governance panel, Sentinel score, registry smart view |
| DevOps | Manual deploy | Dockerized stack, Traefik TLS, GH Actions build & deploy, smoke tests |
| Config | Ad-hoc env vars | `env.example` + `.env` restructure, config/ directory |
| Testing | Directive + TAES tests | Same + ledger signature test (`test_ledger_signatures`) |

---

## 3. Deployment Architecture (Current)

```
┌─────────────────────────────┐
│           Traefik           │
│  HTTPS (ACME TLS), rate-lim │
└────────────┬────────────────┘
   8443 (AxP)│      │443 (Sentinel)
             │      │
┌────────────▼──┐  ┌▼─────────────┐
│   AxProtocol  │  │   Sentinel   │
│ (Streamlit/   │  │ (FastAPI:    │
│  kernel)      │  │  /health,    │
│               │  │  /verify,    │
│ - writes logs │  │  /reports)   │
│ - writes      │  │ - reads      │
│   signed      │  │   read-only  │
│   ledger      │  │   ledger     │
└──────┬────────┘  └──────┬───────┘
       │                   │
       │ mounts            │ mounts (read-only)
┌──────▼────────┐    ┌─────▼─────────┐
│ logs/ledger   │    │ logs/reports  │
│ (jsonl +      │    │ (sentinel     │
│  public key)  │    │  outputs)     │
└───────────────┘    └───────────────┘
```

GitHub Actions pushes fresh images to GHCR, then SSHes into the VPS to `docker compose pull` + `up -d`.  
Smoke script ensures endpoints respond and `/verify` returns a result.

---

## 4. Hardening / To-Do (Next Up)

| Priority | Item | Notes |
|----------|------|-------|
| 🔐 | **Move signing key to KMS/HSM** | Wallet for Ed25519 private key; only mount public key to containers |
| 🔄 | **Schema compliance audit** | Producer/Courier fallback for audit prompts; add `SHAPE_COMPLIANCE` soft signal |
| 🧪 | **Canary rollout** | Shadow traffic + rollback when swapping models/prompts |
| 🌐 | **CORS & rate limits on public API** | Frontend waitlist API currently wide-open |
| 📦 | **Sentinel GitHub Action** | Publish `/verify` report automatically post deploy |
| 🌱 | **Merklized public anchoring** | Anchor ledger roots (e.g., onchain or notarized log) |
| 🧾 | **Waitlist backend** | Vercel deployment (FastAPI) with MongoDB integration |
| 📊 | **Metrics / analytics** | Add Plausible or PostHog dashboards |

---

## 5. Quick Start

```bash
# clone + install
git clone https://github.com/axprotocol/axprotocol.git
cd AxProtocol
pip install -r requirements.txt

# run deterministic tests
pytest verify/ -q

# dry-run governance detectors (no ledger write)
python run_axp.py --smoke-governance
```

To start the Streamlit console locally:
```bash
streamlit run app_axp.py
```

Deployment (Docker):
```bash
docker compose build
docker compose up -d
`${DOMAIN_APP}` `./scripts/smoke.sh`
```

---

## 6. Repository Map (abridged)

```
AxProtocol/
├─ app_axp.py              # Operator console (Streamlit)
├─ run_axp.py              # Multi-agent chain orchestrator
├─ taes_evaluation.py      # TAES scoring + ledger logging
├─ axp/governance/
│    ├─ ledger.py          # Ed25519 signing utilities
│    └─ coupling.py        # Config loader, soft/hard signal helpers
├─ axp/sentinel/
│    ├─ sentinel.py        # CLI auditor (hash + sig verify)
│    ├─ verify_ledger.py   # Shared verification logic
│    └─ sentinel_app.py    # FastAPI (health/verify/reports)
├─ config/
│    ├─ governance_coupling.json
│    ├─ logging.yaml
│    ├─ auth_settings.yaml
│    └─ taes_weights.json
├─ logs/                   # session logs, ledger jsonl, reports
├─ roles/<domain>/         # role prompts (strategist, analyst, ...)
├─ verify/
│    ├─ test_directive_enforcement_core.py
│    ├─ test_taes_adherence.py
│    └─ ...
├─ docker-compose.yml
├─ Dockerfile.axp
├─ Dockerfile.sentinel
├─ scripts/smoke.sh
├─ env.example
└─ README.md
```

---

## 7. Sentinel Self-Audit Example

The self-audit prompt used in testing:
```
Objective (AxProtocol Self-Audit)
Conduct a full post-mortem on AxProtocol’s last reasoning run...
```
Highlights from the latest run:
- Strategist & Analyst produced robust S/A slices.
- Producer/Courier strict-mode failed for audit format → logged empty arrays.
- Critic flagged D2, D3, D7, D13 issues and ledger gaps.
→ Next action: add audit-friendly schema + SHAPE_COMPLIANCE soft signal.

Sentinel score is visible in the UI (“Advanced: Governance Signals”).  
Drift entries are mirrored to `results['governance']['drift']` and the ledger delta.

---

## 8. Licensing

Evaluation license in `AxProtocol_Evaluation_License_v0.1.txt`.  
Commercial use requires written authorization.

---

**AxProtocol: Truth > Obedience.  
Signed. Sentineled. Config-driven.**  
