# Project History and Context

AxProtocol was the creator's first substantial AI project, started roughly four months after beginning to use AI tools.

That context matters when reading this repository. It is simultaneously:

- an early attempt to turn prompting principles into an explicit governance protocol;
- a multi-role reasoning/orchestration experiment;
- a test bed for deterministic scoring and fault injection;
- an early software product with UI, auth, deployment, packaging, and domain-specific roles;
- and, through Sentinel, an exploration of separating **generation** from **verification**.

The repository accumulated quickly and contains multiple generations of the same idea. Historical names and version labels are therefore not perfectly normalized.

## Rough evolution visible in the repository

### Directive / protocol phase

The `legacy/` and `protocol/` directories preserve early directive sets and the v2.1-v2.4 protocol documents. These documents capture the project's original emphasis on explicit reasoning rules, precedence, change control, red-team behavior, and TAES evaluation.

### War-room / multi-role phase

The runtime evolved toward a role chain:

```text
Strategist -> Analyst -> Producer -> Courier -> Critic
```

The intention was to make responsibilities explicit rather than asking one model invocation to perform every kind of reasoning at once.

### Domain specialization

`roles/` and `DomainConfig.json` expanded the system beyond a single marketing-oriented workflow into technical, operations, creative, education, product, strategy, research, finance, and other domain-specific behavior.

### Governance and audit phase

The project added:

- directive signal detection;
- TAES scoring;
- config fingerprints;
- signed ledger records;
- fault-injection suites;
- the detached Sentinel verifier.

This is where the architecture became more interesting than a prompt framework: the system began producing evidence that another process could audit.

### Productization phase

The repository also contains work on:

- Streamlit UI;
- authentication and dashboarding;
- FastAPI endpoints;
- Docker/Traefik deployment;
- packaging/PyPI metadata;
- verification scripts and CI concepts.

Some of that productization was incomplete or internally inconsistent. The 2026 repository reconciliation intentionally preserves those facts rather than rewriting history to make the project look cleaner than it was.

## Version labels

The repository contains documents referring to v2.4, v2.5, and v2.7, while Python package metadata still identifies the package as `2.4.0`.

This reconciliation does **not** pretend those labels were a clean release train. Until a deliberate release/versioning decision is made, treat them as historical development labels rather than a reliable semantic-version sequence.

## What is legacy versus current

A useful mental model:

- `legacy/` — intentionally historical implementations/directives;
- `protocol/` — protocol documents and governance concepts;
- `roles/` — domain-specific role definitions;
- `axp/` — modularized implementation;
- `axprotocol/` — public Python import surface;
- `verify/` — verification/fault-injection tests;
- `axp/sentinel/` — detached cryptographic audit path;
- `docs/` — restored documentation and architectural explanation.

Top-level Python files include both current entry points and historical compatibility code. Read the README and module docs before assuming every similarly named file represents the same subsystem.

## Why Sentinel deserves separate attention

The original system mostly asked: **how do we make an AI reasoning process more structured and accountable?**

Sentinel introduces a different question: **how can a separate process verify evidence produced by that system without simply trusting the producer's own claim that everything is fine?**

That second question generalizes beyond AxProtocol and beyond any particular model architecture. See [`SENTINEL.md`](SENTINEL.md) for the current design, limitations, and potential.

## Preservation policy

The repository should preserve source, protocol history, meaningful documentation, tests, and architecture artifacts.

It should not preserve accidental machine state as source control history. Local `.env` files, authentication databases, runtime logs, caches, generated package metadata, and similar artifacts are excluded even when they appeared in the recovered project ZIP.

See [`ZIP_RECONCILIATION_2026-10-03.md`](ZIP_RECONCILIATION_2026-10-03.md) for the reconciliation record.
