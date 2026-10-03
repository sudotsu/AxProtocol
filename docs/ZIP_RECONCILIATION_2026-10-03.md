# AxProtocol ZIP Reconciliation — 2026-10-03

This document records the reconciliation of the historical `AxProtocol.zip` into the canonical GitHub repository.

## Source archive

- Archive: `AxProtocol.zip`
- SHA-256: `9ac2c44ec3c0f63c92a537a8bb208119f86dc03a926046d943d51c214f51e226`
- Extracted project files observed during reconciliation: 348
- Approximate extracted size: 3.7 MB

The goal is that future explanations of the project can point to the repository instead of requiring the ZIP again.

## Canonical repository selected

The largest and most developed matching repository under the connected GitHub account was:

```text
sudotsu/AxP
```

Its existing default branch is `master`.

The reconciliation work was performed on a feature branch and proposed through a pull request rather than pushed directly into `master`.

## What the ZIP confirmed

The archive contains the same major project families already represented in the repository:

- modular `axp/` implementation;
- `axprotocol/` public package surface;
- role definitions;
- protocol/directive documents;
- governance and ledger code;
- Sentinel verifier/service;
- verification/fault-injection tests;
- Streamlit/UI/auth/dashboard code;
- Docker and deployment artifacts;
- packaging metadata;
- historical/legacy materials.

The most meaningful missing material was documentation/history rather than a second, completely different implementation.

## Restored or added to the repository

Restored ZIP documentation includes configuration, app/dashboard/auth, and implementation-history material under `docs/`.

New canonical documentation includes:

- `docs/PROJECT_HISTORY.md`
- `docs/SENTINEL.md`
- `docs/auth_dashboard_docs/ARCHIVE_INDEX.md`
- this reconciliation record
- a rewritten top-level `README.md`

The README now frames the project as two coupled systems: AxProtocol as producer/reasoning/governance and Sentinel as a separate auditor.

## Important code issues discovered during reconciliation

The ZIP review was not treated as a simple file-copy exercise. Running and inspecting the code exposed concrete architectural and implementation issues.

### Sentinel hash verification mismatch

The signed JSONL writer stores:

```text
entry.hash = SHA256(entry.data)
```

One detached Sentinel verifier was instead hashing the entire `entry` object and comparing that digest to `entry.hash`, causing legitimate records to be reported as mismatches.

The verifier now matches the writer's actual contract and has focused tests for clean, modified, malformed, and unauthenticated records.

### Incorrect Sentinel entry counts

Historical Sentinel paths reported the number of error details as `entries_checked`. A clean ledger could therefore claim that zero entries were examined.

The counters now count actual non-empty records processed.

### Sentinel originally covered only one of two ledgers

The repository contains two distinct audit mechanisms:

1. the main role-execution path writes a SQLite hash chain through top-level `ledger.py`;
2. TAES/governance paths write signed JSONL records through `axp/governance/ledger.py`.

Detached Sentinel historically verified only the signed JSONL stream.

It now verifies **both**:

- signed JSONL data hashes/signatures;
- the SQLite `previous_hash` links and recomputed `current_hash` values, opening the DB read-only.

This makes Sentinel materially relevant to the actual role-execution chain instead of only to a side evidence stream.

### Missing-key behavior

A signed-record verifier without its verification key cannot establish authenticity. Sentinel now fails closed for that signed stream rather than silently skipping signature verification while returning a clean result.

### Offline utility coupling to OpenAI

Importing offline utilities such as config fingerprinting executed `axp.utils.__init__`, which eagerly imported the OpenAI client. That made non-LLM verification/tooling depend on the model SDK unnecessarily.

LLM helpers are now exposed lazily so offline audit utilities can be imported independently.

### Detached Sentinel API import path

`axp/sentinel/sentinel_app.py` historically used a top-level `from verify_ledger import verify_all`, matching its Docker copy layout but not a normal source/package import.

It now prefers the package-relative import and retains a Docker-compatible fallback.

### Historical naming collision

`sentinel_api.py` is actually the AxProtocol chain-execution FastAPI service (`POST /run`), not the detached Sentinel auditor.

The detached audit API is `axp/sentinel/sentinel_app.py`.

The new README and Sentinel documentation call this out explicitly rather than perpetuating the ambiguous naming.

### Wheel omitted most of the implementation

The historical `pyproject.toml` explicitly listed only `axprotocol` and `axp` as packages. The resulting wheel built successfully but contained essentially only `axprotocol/__init__.py`, omitting the actual `axp/*` implementation.

A local reproduction produced an approximately 8 KB wheel with no orchestration/Sentinel implementation.

Package discovery now uses namespace-aware setuptools discovery, and the historical top-level modules still required by the modular chain are explicitly packaged. CI asserts the presence of representative orchestration, governance, Sentinel, and utility modules in the wheel.

A local rebuild after the first package-discovery correction grew to approximately 45 KB and contained the previously omitted `axp/*` implementation.

### Packaging is improved, but source checkout remains canonical

The code/package-discovery failure above is fixed, but the project still has a historical layout limitation: runtime resources such as

```text
config/
protocol/
roles/
DomainConfig.json
```

live at repository root and multiple modules resolve them relative to a source checkout/current working directory.

Those resources have not yet been migrated into one install-safe package-resource scheme. The README therefore explicitly treats a source checkout as the canonical complete runtime rather than claiming that a successful wheel build is a fully self-contained production distribution.

### Fault-injection suite status

After removing accidental LLM import coupling and running verification in a clean ledger state, the implemented suites largely pass. The historical Δ1-Δ3 wrapper still contains explicitly unfinished/legacy paths, including a score-manipulation class that reports `Not yet implemented`.

CI therefore distinguishes:

- blocking implemented verification, including Δ4 ledger-tampering and focused Sentinel tests;
- non-blocking known unfinished Δ1-Δ3 fault-injection work.

This preserves the unfinished state visibly rather than pretending those tests are complete.

## Historical auth/dashboard delivery documents

The ZIP contains several large v2.5 delivery documents using phrases such as `PRODUCTION HARDENED`, `PRODUCTION READY`, and speculative ROI/value claims.

They are useful as historical evidence of how the project was being developed and described, but they are repetitive and should not be promoted as current verified claims.

Instead of copying those assertions into canonical documentation, `docs/auth_dashboard_docs/ARCHIVE_INDEX.md` inventories the files, sizes, and subjects and clearly marks them as historical delivery material.

## Files deliberately not copied from the ZIP

The archive also contains machine/runtime state that should not become canonical source history.

### Secrets and environment state

Excluded:

```text
.env
```

A real `.env` should never be copied into version control. The repository already has `env.example` for documented configuration.

### Authentication/session databases

Excluded examples:

```text
logs/auth/api_keys.db
logs/auth/sessions.db
logs/ledger/audit_ledger.db
```

These are runtime state and may contain sensitive or machine-specific information.

### Runtime logs and generated data

Excluded examples include:

- application logs;
- session logs;
- error logs;
- KPI/IRD CSVs;
- generated reports.

Those files are evidence of historical runs, not required source code, and may embed user/project data.

### Python/build/test caches

Excluded:

- `__pycache__/`
- `.pytest_cache/`
- `axprotocol.egg-info/`
- generated bytecode/build metadata.

These can be reproduced and do not belong in source control.

### Nested ZIPs containing duplicate material

The archive contains several nested ZIP files, including config/role/validation bundles. Where the extracted underlying files are already present, the nested archive adds no canonical information and is omitted.

Examples include:

- `config/axprotocol_config_files.zip`
- `roles/marketing/marketing_roles.zip`
- `scripts/validate_scripts.zip`
- `verify/verify.zip`

The repository should store the readable source, not duplicate opaque archives of the same source.

## Security note

This reconciliation did **not** promote local runtime credentials or databases into Git history. That is intentional even though the source archive remains useful as provenance.

If the repository is ever made public, a separate secrets/history audit is still appropriate because historical Git commits predate this reconciliation.

## Verification strategy added

A new GitHub Actions workflow installs the declared project stack on clean hosted runners and performs:

- package installation;
- source compilation;
- governance/config validation;
- implemented verification suites on supported Python versions;
- signed-ledger and SQLite Sentinel contract tests;
- governance smoke testing;
- wheel building;
- wheel content assertions;
- installed-package imports from outside the source checkout;
- non-blocking visibility into unfinished Δ1-Δ3 tests.

This is intentionally stronger than relying on whatever libraries happen to be installed in an interactive environment.

## Remaining historical ambiguity

The repository uses several development labels (`v2.4`, `v2.5`, `v2.7`) while package metadata currently remains `2.4.0`.

This reconciliation does not invent a clean release history that did not exist. A future deliberate release pass can normalize versions after deciding what should constitute the next supported release.

## Result

After this work, the repository is intended to be the canonical reference for:

- what AxProtocol was trying to do;
- how the multi-role/governance system works;
- why Sentinel is a distinct and potentially more general audit component;
- both audit-ledger formats and their actual guarantees;
- the meaningful historical documentation recovered from the ZIP;
- known weaknesses and unfinished areas;
- and the current reproducible verification/package state.

The original archive hash above remains as provenance, but routine project explanation should no longer require attaching the ZIP.
