# Sentinel

Sentinel is the detached verification side of the AxProtocol project.

AxProtocol produces work and audit evidence. Sentinel asks whether that evidence is still internally consistent and, where signatures are available, authentic to the expected signing key.

That distinction matters. Sentinel is most useful when treated as a **separate trust boundary**, not as another reasoning role in the same chain.

## Why Sentinel exists

A multi-agent or multi-stage AI system can produce polished output while still leaving unanswered questions:

- Was the recorded result modified after the run?
- Was a record actually signed by the expected key holder?
- Was a link in the execution history changed?
- Did a ledger record become malformed?
- Did the system preserve the configuration fingerprint it claimed to use?
- Can an auditor inspect evidence without giving the auditor write access to the producer?

Sentinel is an early answer to those questions. It is intentionally more mechanical than the AxProtocol reasoning chain: parse records, recompute hashes, verify links/signatures, emit a report.

## The two-system model

```text
                     PRODUCER TRUST DOMAIN

 Objective
    |
    v
 AxProtocol chain
 Strategist -> Analyst -> Producer -> Courier -> Critic
    |
    +--> execution events -----------> SQLite hash-chain ledger
    |
    +--> TAES evaluations -----------> signed JSONL ledger
    |                                  + config_hash
    |
    v
 outputs

                  read-only ledger volume / exported evidence
                                |
                                v

                     AUDITOR TRUST DOMAIN

              +-----------------------+
              |       Sentinel        |
              |-----------------------|
              | SQLite chain verify   |
              | JSONL hash verify     |
              | signature verify      |
              | report failures       |
              +-----------------------+
```

The strongest deployment is one in which Sentinel does **not** share write access, signing authority, or mutable application state with the producer.

The included Docker Compose layout already moves in that direction: AxProtocol writes the ledger volume while the Sentinel container mounts the same volume read-only.

## There are two ledger formats in this repository

This is important historical context and was easy to miss before the 2026 reconciliation.

### 1. Main execution ledger — SQLite hash chain

The current modular chain still imports the historical top-level `ledger.py` module. Role executions are written to:

```text
logs/ledger/audit_ledger.db
```

Each row stores `previous_hash` and `current_hash`. The writer computes:

```text
current_hash = SHA256(
    timestamp | agent_id | action | output_hash | previous_hash
)[:16]
```

That gives the main role-execution history a record-to-record chain.

### 2. Signed TAES ledger — JSONL

`taes_evaluation.py` also writes records through `axp/governance/ledger.py` to dated JSONL files under the same ledger directory.

For these records:

```text
entry.hash = SHA256(canonical_json(entry.data))
entry.sig  = Sign(canonical_json(entry))
```

With PyNaCl installed, signing uses Ed25519. A compatibility HMAC fallback exists when PyNaCl is unavailable.

### Why keep both visible?

The two formats capture different properties:

- the SQLite ledger gives execution-order linkage;
- the signed JSONL ledger gives per-entry cryptographic authentication and config fingerprints for TAES records.

They are not yet one unified audit format. Sentinel now verifies both instead of pretending only one exists.

## What Sentinel verifies today

The detached verifier lives primarily in:

- `axp/sentinel/verify_ledger.py` — deterministic verification for both ledger formats;
- `axp/sentinel/sentinel.py` — CLI-oriented verifier/report writer;
- `axp/sentinel/sentinel_app.py` — detached FastAPI verification service;
- `Dockerfile.sentinel` — minimal Sentinel container;
- `verify/test_sentinel_verification.py` — focused contract tests;
- `verify/test_fault_injection_delta4.py` — signed-ledger tampering tests.

### Signed JSONL checks

For each non-empty JSONL record, Sentinel checks:

1. The record is valid JSON.
2. An `entry` object exists.
3. `entry.data` is an object.
4. `entry.hash` equals SHA-256 of canonical JSON for `entry.data`.
5. A signature exists.
6. If the verification key is available, the signature over the full canonical `entry` object verifies.
7. Missing verification keys fail closed: content hashes can still be inspected, but Sentinel does not claim cryptographic verification.

### SQLite chain checks

For `audit_ledger.db`, Sentinel opens the database read-only and checks every row in ID order:

1. The stored `previous_hash` equals `genesis` for the first row or the prior row's `current_hash` thereafter.
2. The expected `current_hash` recomputed from the writer's formula matches the stored value.
3. Database/read/schema failures are reported rather than silently ignored.

The historical in-process `verify_hash_chain()` recomputed the current hash but did not explicitly reject a forged `previous_hash` field when the current hash remained unchanged. Detached Sentinel now checks both the stored link and the derived hash.

### Combined report

`verify_all()` reports:

- overall verification status;
- combined records checked;
- signed JSONL status/details;
- SQLite chain status/details;
- signature mode;
- whether signature verification was actually available.

The overall result is true only when at least one supported audit artifact exists and every present artifact verifies successfully.

## A verification bug found during the ZIP reconciliation

The signed-ledger writer stores `entry.hash` as SHA-256 of `entry.data`.

One historical Sentinel verifier instead hashed the **entire entry** and compared that digest to `entry.hash`. Valid records could therefore be reported as tampered with.

The reconciliation fixes the verifier to match the writer's contract and adds direct tests for valid, modified, malformed, and missing-key cases.

Another bug reported `entries_checked` as the number of errors rather than the number of records examined. That is also fixed.

## Running Sentinel

### CLI verifier

From a source checkout with a local ledger:

```bash
python -m axp.sentinel.sentinel
```

The CLI expects local audit material under `logs/ledger/` and writes a report under `logs/reports/`.

### Detached HTTP verifier

For source execution, point the audit paths at locations Sentinel can read/write:

```bash
export AXP_LEDGER_DIR="$PWD/logs/ledger"
export AXP_REPORTS_DIR="$PWD/logs/reports"
export AXP_PUBLIC_KEY="$PWD/logs/ledger/public.key"
uvicorn axp.sentinel.sentinel_app:app --host 127.0.0.1 --port 8080
```

Endpoints:

- `GET /health` — service status and configured paths;
- `GET /verify` — execute a verification pass and persist the report;
- `GET /reports` — list recent report filenames.

### Docker

The intended detached deployment is:

```bash
docker compose build sentinel
docker compose up sentinel
```

In `docker-compose.yml`, the ledger is mounted into Sentinel read-only:

```text
axp-ledger:/audit/ledger:ro
```

That read-only boundary is more important than the HTTP API. An auditor that can rewrite the evidence it audits is a weaker auditor.

## Sentinel is not `sentinel_api.py`

The repository contains a historical naming collision.

`sentinel_api.py` is an HTTP API for **executing the AxProtocol reasoning chain**. It exposes endpoints such as `POST /run` and imports `run_chain`.

The actual detached Sentinel verification API is:

```text
axp/sentinel/sentinel_app.py
```

The old filename is retained for compatibility/history, but it should not be described as the independent auditor.

There is also `axp/utils/sentinel.py`, an earlier heuristic output-quality helper named `sentinel_verify`. It performs simple reference/overconfidence heuristics inside chain results. It is conceptually related but is **not** the deterministic detached verifier described here.

## Strengths

### 1. Deterministic and inspectable

The integrity checks do not require an LLM. Hash links, content hashes, JSON validity, and signatures are mechanically reproducible.

### 2. Covers the main chain and TAES evidence

Sentinel now audits both the SQLite execution chain and signed TAES JSONL stream. That is significantly more useful than verifying a side ledger in isolation.

### 3. Can be separated from the producer

The Docker architecture gives Sentinel read-only ledger access and a separate report volume, creating the beginnings of an independent audit plane.

### 4. Cryptographic tamper evidence on signed records

With Ed25519 enabled, modification of a signed JSONL entry can be detected without possessing the private signing key.

### 5. Order/tamper evidence on execution records

The SQLite ledger's previous/current hash linkage lets Sentinel detect broken links and altered row content used in the hash formula.

### 6. Useful after the model call is over

Verification can happen later, elsewhere, or repeatedly. An auditor does not need the original model process to re-explain what happened.

### 7. Generalizable primitive

The core idea does not require a five-role AI chain. The same pattern can audit agent actions, policy decisions, CI artifacts, model evaluations, tool calls, or deployment attestations.

## Weaknesses and current limitations

Sentinel is promising, but the current implementation is not a complete independent assurance system.

### 1. Integrity is not semantic truth

A valid chain or signature does **not** prove the model output was true, safe, complete, unbiased, or well reasoned.

Sentinel currently verifies evidence integrity better than evidence quality.

### 2. The two ledger systems are fragmented

Execution events and TAES records use different formats and different guarantees. Correlating them into one end-to-end provenance graph is still incomplete.

A future unified envelope should include role/action identity, session ID, previous-record linkage, config fingerprint, signature, and explicit event type in one consistent format.

### 3. Key custody is not truly independent yet

`axp/governance/ledger.py` creates and stores the signing key on the producer side. If an attacker controls both producer state and the private key, the attacker can generate newly signed false records.

A stronger design would move private-key custody into KMS/HSM/TPM-backed signing or a separate signing service.

### 4. HMAC fallback is not an asymmetric trust boundary

When PyNaCl is unavailable, the signed ledger falls back to HMAC. HMAC verification requires the same secret used for signing, so the mirrored `public.key` is not actually public in that mode.

The fallback is useful for compatibility/testing but is not equivalent to detached Ed25519 verification.

### 5. The SQLite chain is not signed

The SQLite chain can reveal many modifications, but a party with full write access can potentially rebuild the database and recompute a fresh internally consistent chain.

Its `current_hash` is also truncated to 16 hexadecimal characters (64 bits), which is weaker than retaining the full SHA-256 digest.

### 6. Signed JSONL entries are not chained to one another

Each JSONL entry is independently signed, but valid signed rows are not linked with `prev_hash` or a Merkle structure.

A valid older signed record could therefore be deleted without invalidating the signature on later records. External checkpoints, sequence commitments, or a transparency-log design would strengthen completeness guarantees.

### 7. "Append-only" is currently an application/storage convention

Normal filesystem files and SQLite databases are mutable. Verification reveals many changes, but storage itself is not WORM/immutable.

Stronger deployments would replicate or anchor checkpoints into object-lock storage, a remote transparency service, or another independently controlled system.

### 8. Config fingerprints are recorded, not fully independently attested

TAES signed entries can contain a `config_hash`. Sentinel verifies that the signed entry is intact; it does not yet reconstruct the historical configuration snapshot and prove the fingerprint corresponded to the exact files active at that moment.

### 9. No external timestamp/notarization

A chain or signature does not by itself prove when the record first existed. External timestamping or periodically published signed checkpoints would improve chronology guarantees.

### 10. Limited operational response

The current service produces reports. It does not yet provide alert routing, severity policies, incident workflows, remote attestation, or automated quarantine.

## Threat model: what Sentinel can and cannot tell you

| Scenario | Current Sentinel | Notes |
|---|---|---|
| Change signed `entry.data` after signing | Detects | Data hash and signature fail |
| Change signed role/action/timestamp | Detects | Signature fails |
| Corrupt signed JSONL | Detects | Parser failure is reported |
| Remove JSONL public key | Detects inability to authenticate | Signed stream fails closed |
| Modify an SQLite row covered by current-hash formula | Detects | Recomputed hash fails |
| Alter SQLite `previous_hash` link only | Detects | Detached verifier checks stored link explicitly |
| Delete/reorder SQLite rows without rebuilding downstream chain | Detects | Link/hash checks break |
| Rebuild whole SQLite DB after total host compromise | Not independently detectable | Needs external signatures/checkpoints |
| Delete a complete valid signed JSONL record | Not reliably detectable | Needs sequence commitment/transparency log |
| Replace signed ledger + private key after total producer compromise | Not independently detectable | Requires independent key custody/external anchor |
| Signed model output contains a factual lie | Not cryptographically detectable | Needs semantic/evidence evaluation |
| Historical config differs from claimed config hash | Not independently proven today | Needs archived config snapshot/attestation |
| Producer tries to rewrite ledger through Sentinel container | Reduced by deployment | Ledger mount is read-only in Compose |

## Potential directions

Sentinel may ultimately be the more reusable part of the project because verification can sit outside the model and outside a specific prompt architecture.

### Unify the audit envelope

A single event format could combine the best properties currently split across SQLite and JSONL:

- full SHA-256 content digest;
- previous-event hash;
- monotonically increasing sequence/session coordinates;
- Ed25519 signature;
- config/policy fingerprint;
- producer/tool/model identity;
- event type and authorization context.

### Independent key custody

- cloud KMS or HSM-backed signing;
- TPM/device-bound keys;
- separate signer service;
- key rotation and signed key-transition records.

### Transparency-log semantics

- `prev_hash` plus periodic Merkle roots;
- inclusion and consistency proofs;
- externally published checkpoints;
- immutable/WORM storage replication.

### Configuration and policy attestation

- archive the exact governance/config snapshot used for a run;
- recompute `config_hash` independently;
- sign policy bundles;
- detect unauthorized rule drift;
- report "same model, different policy" changes explicitly.

### Agent/tool provenance

Extend records to include:

- tool invocation identity;
- selected model/provider/version;
- prompt/config identifiers;
- source/evidence references;
- authorization decision;
- requested vs executed action;
- human approval where required;
- result hashes.

### CI and artifact verification

Sentinel can verify signed build/test artifacts independently from the agent that generated code, creating a useful boundary between "AI changed this" and "independent checks attest to these properties."

### Semantic audit plugins

Keep cryptographic verification deterministic, then layer optional auditors for:

- citation/evidence coverage;
- policy violations;
- unsupported certainty;
- inconsistent claims;
- schema invariants;
- domain-specific risk rules.

Those checks should remain clearly distinguishable from cryptographic integrity so a probabilistic evaluator is never mistaken for a signature verifier.

### Cross-system use

A generalized Sentinel could audit event streams from systems that never use AxProtocol at all. The producer would only need to emit records conforming to a documented audit-envelope format.

That direction turns Sentinel from "AxProtocol's watchdog" into an independent provenance and verification layer.

## Design principle

The long-term value proposition is not that Sentinel makes an AI system infallible.

It is that **the system producing a result should not be the only system allowed to tell you whether the evidence around that result is intact**.

That is the architectural idea worth preserving and extending.
