# AxProtocol

**A governance and reasoning framework for AI agents**

AxProtocol (AxP) enforces disciplined, traceable behavior through constitutional directives, measurable evaluation standards, and operator-controlled autonomy.

## 🎯 Overview

AxProtocol implements a layered protocol architecture that governs AI agent behavior through:

- **Constitutional Directives** (Layers 0-28): Immutable rules requiring operator ratification
- **Authority Assertion Layer (AAL)**: Operator control via OP_AUTH tokens and CAM leases
- **Tri-Axis Evaluation Standard (TAES)**: Reality alignment scoring system
- **Red-Team Governance**: Adversarial review and quality control

## 🏗️ Project Structure

```
AxProtocol/
├── protocol/           # Constitutional directives and governance rules
├── implementations/    # Concrete implementations (War Room, etc.)
├── docs/              # Documentation and guides
├── scouts/            # Intelligence and monitoring systems
├── scripts/           # Utility scripts
└── logs/              # Root-level audit logs (gitignored)
```

## 🚀 Quick Start

### War Room Implementation

The primary implementation is a five-role reasoning chain system:

```bash
cd implementations/war-room-v0.1b

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run a campaign (DEV tier)
TIER=DEV python run_axp.py "Your campaign objective here"

# Launch Operator Console
streamlit run app_axp.py
```

See [docs/operator-console.md](docs/operator-console.md) for detailed commands.

## 📋 Key Concepts

### TIER System
- **DEV**: Fast iterations with gpt-4o-mini
- **PREP**: Mid-grade quality with gpt-4o-turbo  
- **CLIENT**: Full quality with gpt-4o

### Five-Role Chain
```
Strategist → Analyst → Producer → Courier → Critic
```

Each role must self-score ≥85/100 across four dimensions (Transformation, Clarity, Reach, Return).

### Key Metrics
- **ACI** (Autonomy Control Index): Directive adherence, target ≥90
- **ADI** (Authority Drift Index): Divergence from operator intent, alert if >5
- **IRD** (Ideal-Reality Disparity): Logic vs. practical viability gap, triggers RRP if >0.5

## 📖 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive guide for Claude Code integration
- **[CHANGELOG.md](CHANGELOG.md)** - Ratified change history
- **[docs/operator-console.md](docs/operator-console.md)** - Console commands and controls
- **[Protocol Files](protocol/)** - Constitutional directives

## 🔒 Change Control

All protocol changes require operator ratification per Directive 0:

1. Changes must be explicitly ratified
2. Recorded in CHANGELOG.md with SHA256 hash
3. Include ratification block in modified files
4. Follow two-track system: Ratified (binding) vs. Exploratory (draft)

## 🛠️ Development

Current active branch: `master-dev`

### Running Tests

```bash
# Baseline validation
python run_axp.py --sim 001

# Fault injection stress testing
python fault_injection.py --run Δ1-Δ3
```

## 📊 Monitoring

- Session logs: `implementations/war-room-v0.1b/logs/sessions/`
- TAES evaluations: `ird_log.csv`
- Audit ledger: `logs/ledger/audit_ledger.db`

## 🤝 Contributing

This is a governed system. All contributions must follow the Change Control Process defined in Directive 0.

## 📄 License

[Add your license here]

---

**Built by AI systems builders, for AI systems.**
