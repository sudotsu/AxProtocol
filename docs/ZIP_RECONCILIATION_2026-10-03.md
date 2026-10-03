# AxProtocol ZIP Reconciliation — 2026-10-03

This document records the reconciliation of the attached historical `AxProtocol.zip` into the canonical GitHub repository.

## Source archive

- Archive: `AxProtocol.zip`
- SHA-256: `9ac2c44ec3c0f63c92a537a8bb208119f86dc03a926046d943d51c214f51e226`
- Extracted project files observed: 348
- Approximate extracted size: 3.7 MB

The goal of this reconciliation is that future explanations of the project can point to the repository instead of requiring the ZIP again.

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

This reconciliation restores missing documentation from the archive and adds new canonical documentation that explains the repository as it exists now.

Restored documentation includes configuration, app/dashboard/auth, and implementation history under `docs/`.

New documentation includes:

- `docs/PROJECT_HISTORY.md`
- `docs/SENTINEL.md`
- this reconciliation record

The README is also being revised so the repository can stand alone as the explanation of the project.

## Important code issues discovered during reconciliation

The ZIP review was not treated as a simple file-copy exercise. Running and inspecting the code exposed several concrete issues.

### Sentinel hash verification mismatch

The ledger writer stores:

```text
entry.hash = SHA256(entry.data)
```

One detached Sentinel verifier was instead hashing the entire `entry` object and comparing that digest to `entry.hash`, causing valid records to be reported as mismatches.

The reconciliation fixes the verifier to match the writer's contract and adds focused Sentinel tests.

### Incorrect Sentinel entry counts

Both Sentinel verification paths counted error records rather than actual records examined. A clean ledger could therefore report zero entries checked.

The reconciliation fixes the counters.

### Missing-key behavior

A verifier without its public verification key cannot establish authenticity. The detached verifier now fails closed instead of allowing a clean overall result while silently skipping signature verification.

### Offline utility coupling to OpenAI

Importing offline utilities such as config fingerprinting executed `axp.utils.__init__`, which eagerly imported the OpenAI client. That made non-LLM verification/tooling depend on the model SDK unnecessarily.

The package initializer now exposes LLM helpers lazily so offline audit utilities can be imported independently.

### Wheel omitted the implementation

The historical `pyproject.toml` explicitly listed only `axprotocol` and `axp` as packages. The resulting wheel built successfully but contained essentially only `axprotocol/__init__.py`, omitting the actual `axp/*` implementation.

A local reproduction produced an approximately 8 KB wheel with no orchestration/Sentinel implementation.

The reconciliation switches setuptools to namespace-aware package discovery. A local rebuild produced an approximately 45 KB wheel containing files such as:

- `axp/orchestration/chain.py`
- `axp/governance/ledger.py`
- `axp/sentinel/verify_ledger.py`
- `axp/utils/config_fingerprint.py`

CI now checks wheel contents explicitly so a "successful" empty package build cannot silently recur.

### Fault-injection suite status

After removing accidental LLM import coupling and running the verification suite in a clean local ledger state, the implemented suites largely pass. The historical Δ1-Δ3 wrapper still contains explicitly unfinished/legacy paths, including a score-manipulation class that prints `Not yet implemented`.

CI therefore distinguishes:

- blocking implemented verification, including Δ4 ledger-tampering and focused Sentinel tests;
- non-blocking known unfinished Δ1-Δ3 fault-injection work.

This preserves the unfinished state visibly rather than pretending those tests are complete.

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
- implemented verification suites;
- Sentinel contract tests;
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
- why Sentinel is a distinct audit component;
- the meaningful historical documentation recovered from the ZIP;
- known weaknesses and unfinished areas;
- and the current reproducible verification/package state.

The original archive hash above remains here as provenance, but routine project explanation should no longer require attaching the ZIP.
