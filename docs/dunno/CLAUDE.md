# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AxProtocol (AxP) is a governance and reasoning framework for AI agents. It enforces disciplined, traceable behavior through constitutional directives, measurable evaluation standards, and operator-controlled autonomy. The system implements a layered protocol architecture with modular implementations.

## Core Architecture Layers

The protocol is structured in hierarchical directive layers (0-28):

- **Layer 0 (Directive 0)**: Constitutional change control - all modifications must be ratified by Operator
- **Layers 1-14**: Foundational logic discipline (anti-sycophancy, contradiction detection, assumption validation)
- **Layers 15-19**: Applied discipline for War Room integration
- **Layers 20-24**: Authority Assertion Layer (AAL) - operator control via OP_AUTH tokens and CAM leases
- **Layers 25-25c**: Tri-Axis Evaluation Standard (TAES) - reality alignment scoring
- **Layers 26-28**: Red-Team / Devil's-Advocate Layer (RDL) - adversarial governance

Directive documents are located in the `protocol/` directory with the naming pattern `v*-*.txt`.

## War Room Implementation

The primary implementation is located at `implementations/war-room-v0.1b/`. This is a five-role reasoning chain system:

**Role Chain Flow:**
```
Strategist → Analyst → Producer → Courier → Critic
```

Each role has specific deliverables and must self-score across four dimensions (Transformation, Clarity, Reach, Return) with a minimum threshold of 85/100 per Directive 16.

### Key Python Modules

- **run_axp.py** (25,535 lines): Main orchestrator for the War Room reasoning chain. Loads all directives, implements the five-role chain, enforces TAES evaluation after each role, validates scores, manages ledger logging and CAM lease tracking.

- **taes_evaluation.py** (6,611 lines): TAES Tri-Axis Evaluation engine. Scores outputs on Logical, Practical, and Probable axes (0-100 scale). Uses adaptive weighting matrices by domain (code/marketing/ops/creative). Calculates Integrity Vector (IV) and Ideal-Reality Disparity (IRD). Triggers Reality Reconciliation Pass (RRP) when IRD > 0.5.

- **ledger.py** (5,227 lines): Immutable Audit Ledger implementation using SQLite with SHA256 hash chains. Prevents tampering through append-only entries. Located at `logs/ledger/audit_ledger.db`.

- **auth.py** (4,203 lines): OP_AUTH token management (JWT-based) and CAM Lease implementation. CAM leases expire after 3 minutes OR when ACI ≥90, whichever comes first. Auto-suspends if unacknowledged halt > 60s.

- **score_validator.py** (2,456 lines): Extracts role self-scores, validates against 85/100 threshold, enforces Recursive Proof Loop (Directive 15).

- **load_roles.py** (4,187 lines): Loads role definitions from `roles/` directory and injects AxProtocol directives into system prompts.

- **app_axp.py**: Streamlit-based Operator Console UI with real-time ledger verification, cognitive disalignment alerts, TAES metrics dashboard.

### Role Definitions

Located in `implementations/war-room-v0.1b/roles/`:
- `strategist_stable.txt` - Campaign architect
- `analyst_stable.txt` - Logic filter and metrics engineer
- `producer_stable.txt` - Creative executor
- `courier_stable.txt` - Delivery optimization
- `critic_stable.txt` - Final quality gate with freeze authority

## Running the System

### Environment Configuration

Create a `.env` file in the War Room directory with:

```
OPENAI_API_KEY=sk-...
TIER=DEV|PREP|CLIENT
DOMAIN=marketing|ops|code|creative
MODEL_DEV=gpt-4o-mini
MODEL_PREP=gpt-4o-turbo
MODEL_CLIENT=gpt-4o
OP_AUTH_SECRET=your-secret
BUILD_TYPE=stable
```

### TIER System

- `DEV`: Uses gpt-4o-mini (cheap iterations)
- `PREP`: Uses gpt-4o-turbo (mid-grade)
- `CLIENT`: Uses gpt-4o (full quality)

### Commands

Run from `implementations/war-room-v0.1b/`:

```bash
# Install dependencies
pip install -r requirements.txt

# Run War Room chain (dev tier)
TIER=DEV python run_axp.py "Your campaign objective here"

# Run with specific domain and client tier
TIER=CLIENT DOMAIN=marketing python run_axp.py "Campaign objective..."

# Launch Operator Console UI
streamlit run app_axp.py

# Run baseline validation simulation
python run_axp.py --sim 001

# Inject fault stress testing
python fault_injection.py --run Δ1-Δ3
```

## Key Metrics and Thresholds

**ACI (Autonomy Control Index)**: Measures directive adherence. Target: ≥90

**ADI (Authority Drift Index)**: Tracks divergence from operator intent. Alert thresholds:
- >10 → auto-suspend
- >5 for 3 sessions → protocol audit

**IRD (Ideal-Reality Disparity)**: Measures gap between theoretical and practical viability.
- >0.5 → triggers Reality Reconciliation Pass (RRP)
- Monthly avg >0.4 → Cognitive Disalignment Alert

**Score Threshold**: All role self-scores must be ≥85/100 (Directive 16)

## TAES Domain Weighting Matrices

Applied per Directive 25a:

```
Code/Infrastructure: Logical 0.6 | Practical 0.35 | Probable 0.05
Marketing/Growth:    Logical 0.3 | Practical 0.2  | Probable 0.5
Operations/Process:  Logical 0.4 | Practical 0.45 | Probable 0.15
Creative/Content:    Logical 0.35| Practical 0.25 | Probable 0.4
```

## Logging and Telemetry

All logs are stored in `implementations/war-room-v0.1b/logs/`:

- **sessions/**: Session logs named `YYYY-MM-DD_HH-MM_[tier].log`
- **ird_log.csv**: TAES evaluation records (timestamp, session_id, role_name, domain, logical, practical, probable, iv, ird, requires_rrp)
- **ledger/audit_ledger.db**: SQLite database with hash-chain integrity

## Operator Console Commands

From `docs/operator-console.md`:

```bash
# Grant operator override
OP_AUTH --grant --duration=60m

# Terminate autonomous chain
OPERATOR_KILLCHAIN --now

# Extend CAM lease
OP_AUTH --extend-cam --ttl=5m

# Trigger Override Mode (high-risk)
OP_AUTH --mode OOM --ttl=6h
```

## Change Control Process

Per Directive 0, all protocol changes must:

1. Be explicitly ratified by Operator
2. Be recorded in `CHANGELOG.md` with SHA256 hash
3. Follow the two-track system: Ratified (binding) vs. Exploratory (draft)
4. Include ratification block in changed files:

```
--- Ratification ------------------------------------------
Status: Ratified
Authorized by: Operator
Date: YYYY-MM-DD
Reason: <summary>
---
```

## Deployment Validation Pipeline

From `docs/deployment-validation.md` (formerly in deploy/ directory):

```bash
# Stage 1: Preparation - testbed setup
# Stage 2: Integration - AAL runtime policies, TAES module linking
# Stage 3: SIM-001 baseline validation
python run_axp.py --sim 001

# Stage 4: SIM-002 stress testing
python fault_injection.py --run Δ1-Δ3

# Stage 5: Dashboard launch
streamlit run app_axp.py

# Stage 6: Verify KPIs
# Check: ACI≥90, ADI≤5, IRD≤0.5

# Stage 7: Promotion to master with archival
git merge AxP_AAL+TAES_v0.1b
```

## Directory Structure

```
AxProtocol/
├── protocol/                  # Constitutional governance documents
│   ├── v0-change-control.txt
│   ├── v2.1a-core-directives.txt
│   ├── v2.1b-war-room-integration.txt
│   ├── v2.1c-authority-layer.txt
│   ├── v2.2-taes-evaluation.txt
│   ├── v2.3-red-team-layer.txt
│   └── v2.3-consolidated.txt
├── docs/                      # Documentation and guides
│   ├── operator-console.md
│   └── deployment-validation.md
├── scouts/                    # Intelligence & monitoring systems
├── scripts/                   # Utility scripts
│   └── sync_bridge.py        # Git-automated Bridge.md sync utility
├── implementations/           # Concrete implementations
│   └── war-room-v0.1b/       # Primary implementation
│       ├── run_axp.py        # Main orchestrator
│       ├── taes_evaluation.py
│       ├── ledger.py
│       ├── auth.py
│       ├── score_validator.py
│       ├── load_roles.py
│       ├── app_axp.py        # Streamlit UI
│       ├── roles/            # Five role definitions
│       ├── logs/             # Telemetry output (gitignored)
│       └── archived/         # Retired code versions
├── logs/                      # Root-level logs (gitignored)
├── CHANGELOG.md              # Ratified change ledger
├── README.md                 # Project overview
└── .gitignore                # Version control exclusions

```

## Important Implementation Notes

1. **Hash Chain Integrity**: The ledger system uses SHA256 hash chains. Each entry includes the previous hash to prevent tampering. Weekly verification is required.

2. **CAM Lease Expiry**: The system will auto-suspend after 3 minutes of autonomy OR when ACI ≥90. Always monitor for lease expiration alerts.

3. **Critic Override Authority**: The Critic role can freeze the entire chain if contradictions are detected (Directive 7). This is by design for quality control.

4. **IRD Trend Monitoring**: Review `logs/ird_log.csv` regularly. Rising IRD trends indicate cognitive disalignment between ideal reasoning and practical outcomes.

5. **No Silent Evolution**: All directive changes require explicit operator ratification. Never modify core directives without updating CHANGELOG.md.

6. **Role Self-Scoring**: Each role must include self-scores for Transformation, Clarity, Reach, and Return. Scores below 85 trigger revision loops.

## Scouts Intelligence System

Located in `scouts/gemini-first-test.md`, implements "The Curve" monitoring system that scans for:
- AI framework launches and capability updates
- Agent autonomy improvements
- Local/hybrid deployment frameworks
- Emerging monetization opportunities

Classification tiers: Immediate ROI (30 days), Near-Term Leverage (90 days), Watchlist (6+ months), Theoretical Horizon.

## Git Workflow

- Main branch: `master`
- Current dev branch: `master-dev`
- Status: Clean (as of conversation start)

When committing changes to core protocol files, ensure CHANGELOG.md is updated with ratification entries.
