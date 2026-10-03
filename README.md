# AxProtocol + Sentinel

AxProtocol is an early AI reasoning/governance project built around explicit role separation, configurable directives, TAES evaluation, audit trails, and fault-injection tests.

**Sentinel is the other half of the project:** a detached verification system intended to inspect the evidence AxProtocol leaves behind without simply trusting the producer's own claim that everything is intact.

This was the creator's first substantial AI project, started roughly **four months after beginning to use AI tools**. The repository is intentionally preserved as both working software and a record of how the architecture evolved.

> **Current framing:** AxProtocol produces work and audit evidence. Sentinel independently verifies the integrity of that evidence.

## Why this repository exists

The original project asked a practical question:

**Can an AI workflow be made more explicit, inspectable, and accountable by separating reasoning responsibilities, encoding governance rules, scoring behavior, and recording what happened?**

That produced AxProtocol: a multi-role chain with domain-specific instructions, TAES evaluation, directive enforcement, config fingerprints, audit ledgers, and adversarial tests.

Sentinel emerged from a second question that may be more generalizable:

**Should the system that produced an AI result also be the only system allowed to tell you whether the evidence around that result is trustworthy?**

Sentinel's answer is no. The verifier is deliberately mechanical: read evidence, recompute hashes, verify links/signatures, and report what fails.

## The architecture: producer + auditor

```text
                     PRODUCER TRUST DOMAIN

 Objective
    |
    v
 AxProtocol
 Strategist -> Analyst -> Producer -> Courier -> Critic
    |
    +--> domain/directive governance
    +--> TAES evaluation
    +--> config fingerprinting
    +--> execution audit records
    |
    +----------------------------+
                                 |
                                 v
                     AUDIT EVIDENCE

              SQLite execution hash chain
                         +
                  signed JSONL records
                         |
                         | read-only / exported evidence
                         v

                     AUDITOR TRUST DOMAIN

                    Sentinel
              +--------------------+
              | parse records      |
              | verify chain links |
              | recompute hashes   |
              | verify signatures  |
              | emit reports       |
              +--------------------+
```

The intended trust boundary matters more than the names: **the auditor should not need write access to the evidence it audits or the private authority used to create that evidence.**

For the detailed Sentinel threat model, current guarantees, weaknesses, and potential, read **[`docs/SENTINEL.md`](docs/SENTINEL.md)**.

---

# Sentinel

Sentinel deserves separate treatment because it is not simply the last role in the AxProtocol chain.

It is a detached audit component with a different job, different failure modes, and potentially broader uses than the original reasoning architecture.

## What Sentinel verifies today

The repository currently has **two audit-ledger formats**, both of which Sentinel now understands.

### 1. Main execution ledger: SQLite hash chain

The role-execution path records events in:

```text
logs/ledger/audit_ledger.db
```

Each row carries a `previous_hash` and `current_hash`. Sentinel opens the database read-only and verifies both the stored link to the preceding row and the recomputed current hash.

This captures execution-order integrity for the main role chain.

### 2. Signed TAES ledger: JSONL

TAES/governance paths also produce dated JSONL records under `logs/ledger/`.

Those records use this contract:

```text
entry.hash = SHA256(canonical_json(entry.data))
entry.sig  = Sign(canonical_json(entry))
```

With PyNaCl installed, signatures use Ed25519. A compatibility HMAC fallback exists, but it is **not** equivalent to asymmetric detached verification because the verifier must possess the shared secret.

Sentinel validates record structure, the stored data hash, signatures, malformed input, and whether signature verification was actually available.

## Why Sentinel is interesting

Its strongest properties are not AI-specific:

- deterministic verification does not require another model call;
- auditing can happen later, elsewhere, or repeatedly;
- the verifier can run with read-only access to producer evidence;
- signed records provide tamper evidence without sharing the private signing key;
- a chain can reveal broken execution-history links;
- the same model can extend to agent actions, CI artifacts, policy decisions, tool calls, or deployment attestations.

## What Sentinel does **not** prove

Sentinel should not be oversold.

A valid hash chain or signature does **not** prove that an AI answer was true, safe, unbiased, complete, or intelligent. It proves narrower properties about the recorded evidence.

Important current limitations include:

- the SQLite execution chain is hash-linked but not independently signed;
- the JSONL records are signed but are not themselves sequence-linked;
- private signing-key custody still lives on the producer side;
- HMAC fallback is symmetric rather than a real public-key trust boundary;
- normal files/SQLite are mutable storage, not WORM storage;
- the two ledger formats are not yet one unified provenance graph;
- config fingerprints are recorded but historical config snapshots are not independently reconstructed by Sentinel;
- there is no external timestamp/notarization or transparency-log checkpoint today;
- cryptographic integrity is different from semantic truth.

Those weaknesses are documented in detail rather than hidden. See [`docs/SENTINEL.md`](docs/SENTINEL.md).

## Where Sentinel could go

The most valuable next directions are likely:

- one unified signed audit envelope for executions, TAES events, tools, approvals, and config state;
- full SHA-256 hashes plus previous-event linkage and monotonic sequence coordinates;
- KMS/HSM/TPM-backed key custody;
- Merkle roots / transparency-log checkpoints;
- immutable or externally controlled storage replication;
- policy/config snapshot attestation;
- agent and tool provenance;
- independent verification of AI-generated CI/build artifacts;
- optional semantic-audit plugins layered **on top of**, not confused with, deterministic cryptographic verification.

The long-term architectural idea is simple:

**The producer should not be the only party allowed to attest to the integrity of its own evidence.**

---

# AxProtocol

AxProtocol is the producer/reasoning side of the project.

## Multi-role chain

The central execution model separates work across five roles:

```text
Objective
   |
   v
Strategist
   |
   v
Analyst
   |
   v
Producer
   |
   v
Courier
   |
   v
Critic
   |
   v
Results + evaluation + audit evidence
```

The original goal was not to claim that five prompts are inherently smarter than one. It was to make responsibilities explicit enough that behavior could be constrained, scored, inspected, and challenged at known boundaries.

## Major concepts

### Directive-based governance

Protocol documents and configuration encode hard/soft governance signals and role constraints. Historical directive material is preserved under `protocol/` and `legacy/`.

### TAES evaluation

TAES evaluates behavior using configurable dimensions/weights. The project evolved through multiple scoring implementations, domain weights, and validation tests.

### Domain specialization

Role definitions exist for multiple domains, including:

- marketing;
- technical;
- operations;
- creative;
- education;
- product;
- strategy;
- research;
- finance.

### Config fingerprinting

The project can compute a configuration fingerprint over governance/config/protocol material and attach that fingerprint to signed audit records, providing a way to detect or investigate policy drift.

### Fault injection

The verification suite includes adversarial/fault-injection work. Δ4 ledger-tampering tests are implemented and blocking in CI. Some historical Δ1-Δ3 wrapper paths remain unfinished/legacy and are deliberately visible as non-blocking CI rather than being represented as complete.

---

# Repository map

```text
AxP/
├── axprotocol/                 # Public Python import surface
├── axp/
│   ├── orchestration/          # Modular role-chain execution
│   ├── governance/             # Signed ledger + governance coupling
│   ├── directives/             # Directive loading/composition
│   ├── detection/              # Governance signal detection
│   ├── validation/             # Validators
│   ├── sentinel/               # Detached Sentinel verifier/API/CLI
│   └── utils/                  # Shared utilities/config fingerprinting
├── config/                     # Governance, roles, TAES, logging, auth config
├── roles/                      # Domain-specific role definitions
├── protocol/                   # v2.4-era protocol/directive documents
├── legacy/                     # Earlier implementations/directive history
├── verify/                     # Verification + fault-injection tests
├── scripts/                    # Validation/smoke/support scripts
├── docs/                       # Restored docs + canonical architecture/history
├── auth.py                     # Historical/current auth runtime module
├── ledger.py                   # Main SQLite execution ledger
├── taes_evaluation.py          # TAES evaluator + signed ledger writes
├── domain_detector.py          # Domain routing
├── load_roles.py               # Historical role loader still used by modular path
├── run_axp.py                  # CLI/runtime entry point
├── app_axp.py                  # Streamlit app
├── sentinel_api.py             # Historical name: AxProtocol chain-execution API
├── Dockerfile.sentinel         # Detached Sentinel container
└── docker-compose.yml          # AxProtocol + Sentinel deployment topology
```

### Naming warning: `sentinel_api.py`

`sentinel_api.py` is a historical filename for the **AxProtocol chain-execution API**. It is not the detached verification service.

The actual detached Sentinel HTTP app is:

```text
axp/sentinel/sentinel_app.py
```

There is also an older heuristic helper at `axp/utils/sentinel.py`; it is not the cryptographic auditor either.

---

# Running from source

A source checkout is currently the **canonical way to explore the whole project**, because several runtime resources live as repository-root config/protocol/role files and the packaging story is still being hardened.

```bash
git clone https://github.com/sudotsu/AxP.git
cd AxP
python -m venv .venv
```

Activate the environment, then install the declared stack you need. For the complete development/test surface:

```bash
python -m pip install --upgrade pip
python -m pip install ".[dev,api,ui,vector]"
```

## AxProtocol runtime

AxProtocol model execution requires an OpenAI-compatible runtime configured by the existing code, including an API key for real model calls:

```bash
export OPENAI_API_KEY="..."
python run_axp.py "Your objective here"
```

The governance-only smoke path is designed not to require a live model call:

```bash
python run_axp.py --smoke-governance
```

Streamlit UI:

```bash
streamlit run app_axp.py
```

## Detached Sentinel

Sentinel's integrity-verification logic itself does not need a model API call.

CLI-style local verification:

```bash
python -m axp.sentinel.sentinel
```

Detached HTTP verifier from source:

```bash
export AXP_LEDGER_DIR="$PWD/logs/ledger"
export AXP_REPORTS_DIR="$PWD/logs/reports"
export AXP_PUBLIC_KEY="$PWD/logs/ledger/public.key"
uvicorn axp.sentinel.sentinel_app:app --host 127.0.0.1 --port 8080
```

Endpoints:

- `GET /health`
- `GET /verify`
- `GET /reports`

Docker topology:

```bash
docker compose build
docker compose up
```

The Sentinel container mounts the ledger read-only in the intended compose architecture.

---

# Verification and CI

The repository now contains a clean-run GitHub Actions workflow that installs the project's declared dependencies rather than relying on whatever happens to be preinstalled on an interactive machine.

It checks:

- Python source compilation;
- governance/config validation;
- implemented verification suites on Python 3.10, 3.11, and 3.12;
- Δ4 tamper tests;
- focused Sentinel tests for signed JSONL and SQLite ledgers;
- governance smoke execution;
- Python wheel construction;
- expected implementation files inside the wheel;
- installed-package imports away from the source checkout;
- known unfinished Δ1-Δ3 fault-injection paths as visible, non-blocking work.

Run the implemented verification set locally with:

```bash
pytest -q \
  verify/test_config_hash.py \
  verify/test_directive_enforcement_core.py \
  verify/test_fault_injection_delta4.py \
  verify/test_sentinel_verification.py \
  verify/test_taes_adherence.py
```

## Packaging status

A reconciliation review found that the historical wheel configuration successfully built a package while omitting almost the entire `axp/` implementation. Package discovery has been corrected and CI now asserts that core implementation files are actually present.

The project still has a historical source-layout issue: important runtime resources live at repository root (`config/`, `protocol/`, `roles/`, `DomainConfig.json`) and several modules resolve them relative to the checkout/current working directory. Until those resources are migrated into an install-safe package-resource layout, **a source checkout is more complete than treating the wheel as a fully self-contained distribution**.

That limitation is explicit here so a successful wheel build is not confused with a fully production-hardened package release.

---

# Historical context and recovered ZIP

This repository was reconciled against the creator's historical `AxProtocol.zip` so the remote can serve as the canonical explanation of the project.

The archive itself is not committed wholesale because it contained machine/runtime state that does not belong in source control: `.env`, auth/session databases, logs, generated reports/data, caches, package metadata, and duplicate nested ZIPs.

Meaningful missing documentation was restored, and the reconciliation process also uncovered/fixed real implementation issues rather than simply copying files.

Read:

- [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md) — origin and architectural evolution;
- [`docs/ZIP_RECONCILIATION_2026-10-03.md`](docs/ZIP_RECONCILIATION_2026-10-03.md) — what was recovered, fixed, tested, and deliberately excluded;
- [`docs/SENTINEL.md`](docs/SENTINEL.md) — Sentinel's design, threat model, strengths, weaknesses, and potential.

## Version labels

Historical material refers to v2.4, v2.5, and v2.7, while Python package metadata currently identifies the package as `2.4.0`.

Those labels were not maintained as a clean semantic-release train. This repository preserves that history rather than inventing a release chronology after the fact.

---

# Current state in one sentence

**AxProtocol is an ambitious early attempt to make AI reasoning structured and auditable; Sentinel is the more independent verification layer that can potentially outgrow the original reasoning framework and become a general provenance/audit system of its own.**
