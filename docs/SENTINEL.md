# Sentinel

Sentinel is the detached verification side of the AxProtocol project.

AxProtocol produces work. Sentinel asks whether the audit evidence around that work is internally intact.

That distinction matters. Sentinel is most useful when treated as a **separate trust boundary**, not as another stage in the same reasoning chain.

## Why Sentinel exists

A multi-agent or multi-stage AI system can produce polished output while still leaving unanswered questions:

- Was the recorded result modified after the run?
- Was the record actually produced by the holder of the expected signing key?
- Did a ledger record become malformed or disappear?
- Did the system preserve the configuration fingerprint it claimed to use?
- Can an auditor inspect evidence without giving the auditor write access to the producer?

Sentinel is the beginning of an answer to those questions. It is intentionally more mechanical than the AxProtocol reasoning chain: parse records, recompute hashes, verify signatures, emit a report.

## The two-system model

```text
                     PRODUCER TRUST DOMAIN

 Objective
    |
    v
 AxProtocol chain
 Strategist -> Analyst -> Producer -> Courier -> Critic
    |
    +--> TAES / governance signals
    +--> config fingerprint
    +--> signed ledger record
                 |
                 | read-only ledger mount / exported artifact
                 v

                     AUDITOR TRUST DOMAIN

              +------------------+
              |     Sentinel     |
              |------------------|
              | parse JSONL      |
              | recompute hash   |
              | verify signature |
              | report failures  |
              +------------------+
```

The strongest deployment is one in which Sentinel does **not** share write access, signing authority, or mutable application state with the producer.

The included Docker Compose file already moves in this direction: AxProtocol writes the ledger volume while the Sentinel container mounts that ledger read-only.

## What Sentinel verifies today

The detached verifier lives primarily in:

- `axp/sentinel/verify_ledger.py` — deterministic ledger verification logic
- `axp/sentinel/sentinel.py` — CLI-oriented verifier/report writer
- `axp/sentinel/sentinel_app.py` — detached FastAPI verification service
- `Dockerfile.sentinel` — minimal Sentinel container
- `verify/test_sentinel_verification.py` — focused contract tests
- `verify/test_fault_injection_delta4.py` — ledger-tampering tests

For each non-empty JSONL record, the verifier now checks:

1. The record is valid JSON.
2. An `entry` object exists.
3. `entry.data` is an object.
4. `entry.hash` equals SHA-256 of canonical JSON for `entry.data`.
5. A signature exists.
6. If the verification key is available, the signature over the full canonical `entry` object verifies.

The report records files checked, actual records checked, verification mode, and specific failures.

### Hash and signature contract

The writer and verifier must agree on two different integrity objects:

```text
entry.hash = SHA256(canonical_json(entry.data))

entry.sig  = Sign(canonical_json(entry))
```

The data hash answers: **did the payload change?**

The signature answers: **was this exact entry signed by the expected key holder?**

A historical implementation bug made one verifier recompute the hash over the entire entry and compare it to the data hash. This repository reconciliation fixes that mismatch and adds tests around the contract.

## Running Sentinel

### CLI verifier

From a source checkout with a local ledger:

```bash
python -m axp.sentinel.sentinel
```

The CLI expects the local ledger under `logs/ledger/` and writes a report under `logs/reports/`.

### Detached HTTP verifier

For source execution, point the audit paths at locations Sentinel can read/write:

```bash
export AXP_LEDGER_DIR="$PWD/logs/ledger"
export AXP_REPORTS_DIR="$PWD/logs/reports"
export AXP_PUBLIC_KEY="$PWD/logs/ledger/public.key"
uvicorn axp.sentinel.sentinel_app:app --host 127.0.0.1 --port 8080
```

Endpoints:

- `GET /health` — service status and configured paths
- `GET /verify` — execute a verification pass and persist the report
- `GET /reports` — list recent report filenames

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

That read-only boundary is more important than the API surface. An auditor that can rewrite the evidence it audits is a weaker auditor.

## Sentinel is not `sentinel_api.py`

The repository contains a historical naming collision.

`sentinel_api.py` is an HTTP API for **executing the AxProtocol reasoning chain**. It exposes endpoints such as `POST /run` and imports `run_chain`.

The actual detached Sentinel verification API is:

```text
axp/sentinel/sentinel_app.py
```

The old filename is retained for compatibility/history, but documentation should not treat it as the independent auditor.

There is also `axp/utils/sentinel.py`, an earlier heuristic output-quality helper named `sentinel_verify`. That code performs simple content/reference heuristics inside the reasoning result. It is conceptually useful, but it is **not the cryptographic detached Sentinel** described on this page.

## Strengths

### 1. Deterministic and inspectable

The core verifier does not need an LLM to decide whether a hash or signature matches. That keeps the most important integrity checks reproducible and debuggable.

### 2. Can be separated from the producer

The Docker architecture gives Sentinel read-only ledger access and a separate report volume. This creates the beginnings of an independent audit plane.

### 3. Cryptographic tamper evidence

With Ed25519 enabled, modification of a signed entry can be detected without possessing the private signing key.

### 4. Useful after the model call is over

Verification can happen later, elsewhere, or repeatedly. The auditor does not need to trust the original runtime process to re-explain what happened.

### 5. Generalizable primitive

Nothing fundamental about the verifier requires a five-role AI chain. The pattern can be generalized to other signed event streams: agent actions, policy decisions, CI artifacts, model evaluations, tool calls, or deployment attestations.

## Weaknesses and current limitations

These are important. Sentinel is promising, but the current implementation is not a complete independent assurance system.

### 1. Signature integrity is not semantic truth

A valid signature proves that a key holder signed an entry. It does **not** prove the model output was true, safe, complete, unbiased, or well reasoned.

Sentinel currently verifies evidence integrity better than evidence quality.

### 2. Key custody is not truly independent yet

`axp/governance/ledger.py` creates and stores the signing key on the producer side. If an attacker controls both producer state and the private key, the attacker can generate newly signed false records.

A stronger design would move private-key custody into KMS/HSM/TPM-backed signing or a separate signing service.

### 3. HMAC fallback is not an asymmetric trust boundary

When PyNaCl is unavailable, the current ledger code falls back to HMAC. HMAC verification requires the same secret used for signing, so the mirrored `public.key` is not actually public in that mode.

The fallback is useful for compatibility/testing but should not be presented as equivalent to detached Ed25519 verification.

### 4. No record-to-record hash chain or Merkle structure

Entries are individually hashed and signed, but the current JSONL ledger does not cryptographically chain each record to its predecessor.

Consequences:

- a valid older signed record could potentially be deleted without making another record's signature invalid;
- complete-history proofs are weak;
- efficient inclusion proofs are unavailable.

A `prev_hash`, Merkle tree, or transparency-log design would strengthen this substantially.

### 5. "Append-only" is currently an application convention

A normal filesystem file is mutable. Signatures reveal many modifications, but storage itself is not WORM/immutable.

Stronger deployments would replicate or anchor records into object-lock storage, a remote transparency service, or another independently controlled system.

### 6. Config fingerprints are recorded, not fully independently attested

AxProtocol can place a `config_hash` in ledger entries. Sentinel currently verifies that the signed entry is intact; it does not independently reconstruct the historical configuration snapshot and prove that the fingerprint corresponded to the exact files in use at that moment.

That is a major potential extension.

### 7. Missing key means authenticity cannot be established

The verifier now fails closed rather than returning a clean overall result when the verification key is missing. It can still inspect content hashes, but it must not claim cryptographic verification.

### 8. No external timestamp/notarization

A valid signature does not by itself prove *when* the record existed. External timestamping or periodic signed checkpoints would improve chronology guarantees.

### 9. Limited operational response

The current service produces reports. It does not yet provide alert routing, severity policies, incident workflows, remote attestation, or automated quarantine.

## Threat model: what Sentinel can and cannot tell you

| Scenario | Current Sentinel | Notes |
|---|---|---|
| Change `entry.data` after signing | Detects | Hash and signature should fail |
| Change role/action/timestamp after signing | Detects | Signature should fail |
| Corrupt JSON | Detects | Parser failure is reported |
| Remove public key | Detects inability to authenticate | Overall verification fails closed |
| Delete a whole valid ledger line | Not reliably detectable by current record format | Needs chaining/checkpoints/external count |
| Replace full ledger + signing key after total host compromise | Not independently detectable | Requires separate key custody / external anchor |
| Signed model output contains a factual lie | Not cryptographically detectable | Needs semantic/evidence evaluation |
| Historical config differs from claimed config hash | Not independently proven today | Needs archived config snapshot/attestation |
| Producer tries to rewrite ledger through Sentinel container | Reduced by deployment | Ledger mount is read-only in Compose |

## Potential directions

Sentinel may ultimately be the more reusable part of the project because verification can sit outside the model and outside a specific prompt architecture.

High-value directions include:

### Independent key custody

- cloud KMS or HSM-backed signing;
- TPM/device-bound keys;
- separate signer service;
- key rotation and signed key-transition records.

### Transparency-log semantics

- `prev_hash` on every record;
- Merkle roots/checkpoints;
- inclusion and consistency proofs;
- periodic checkpoint publication to an external location;
- immutable/WORM storage replication.

### Configuration and policy attestation

- archive the exact governance/config snapshot used for a run;
- recompute `config_hash` independently;
- sign policy bundles;
- detect unauthorized rule drift;
- report "same model, different policy" changes explicitly.

### Agent/tool provenance

Extend ledger records beyond final text to include:

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

Those checks should remain distinguishable from cryptographic integrity so a probabilistic evaluator never gets mistaken for a signature verifier.

### Cross-system use

A generalized Sentinel could audit event streams from systems that never use AxProtocol at all. The producer would only need to emit records conforming to a documented signed-envelope format.

That direction turns Sentinel from "AxProtocol's watchdog" into an independent provenance and verification layer.

## Design principle

The long-term value proposition is not that Sentinel makes an AI system infallible.

It is that **the system producing a result should not be the only system allowed to tell you whether the evidence around that result is intact**.

That is the architectural idea worth preserving and extending.
