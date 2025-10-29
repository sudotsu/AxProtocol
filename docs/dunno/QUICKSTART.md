# AxProtocol Quick Start Guide

Get up and running with AxProtocol War Room in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Git (optional, for cloning)

## Installation

### 1. Navigate to War Room

```bash
cd implementations/war-room-v0.1b
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env  # or use any text editor
```

Required in `.env`:
```
OPENAI_API_KEY=sk-your-key-here
TIER=DEV
DOMAIN=marketing
```

## Your First Campaign

### Run a Simple Campaign

```bash
TIER=DEV python run_axp.py "Create a social media strategy for a new coffee shop"
```

**What happens:**
1. Strategist creates high-level plan
2. Analyst validates logic and metrics
3. Producer generates creative content
4. Courier optimizes delivery
5. Critic performs final review

Each role self-scores ≥85/100 or triggers revision.

### View Results

Outputs are saved to `logs/sessions/YYYY-MM-DD_HH-MM_dev.log`

## Launch Operator Console

For real-time monitoring and control:

```bash
streamlit run app_axp.py
```

Opens dashboard at `http://localhost:8501` with:
- Live chain execution
- TAES metrics
- Audit ledger verification
- Operator override controls

## Understanding TIER System

### DEV - Fast Iterations
```bash
TIER=DEV python run_axp.py "objective"
```
- Uses: gpt-4o-mini
- Cost: ~$0.001 per run
- Speed: Fast
- Use for: Testing, prototyping

### PREP - Mid-Grade
```bash
TIER=PREP python run_axp.py "objective"
```
- Uses: gpt-4o-turbo
- Cost: ~$0.01 per run
- Speed: Medium
- Use for: Internal review

### CLIENT - Full Quality
```bash
TIER=CLIENT python run_axp.py "objective"
```
- Uses: gpt-4o
- Cost: ~$0.05 per run
- Speed: Thorough
- Use for: Client deliverables

## Domain Selection

Adjust TAES weighting for your use case:

```bash
# Marketing campaigns
TIER=DEV DOMAIN=marketing python run_axp.py "objective"

# Technical documentation
TIER=DEV DOMAIN=code python run_axp.py "objective"

# Process optimization
TIER=DEV DOMAIN=ops python run_axp.py "objective"

# Creative content
TIER=DEV DOMAIN=creative python run_axp.py "objective"
```

## Example Campaigns

### Marketing
```bash
TIER=DEV python run_axp.py "Launch campaign for eco-friendly water bottles targeting millennials"
```

### Technical
```bash
TIER=PREP DOMAIN=code python run_axp.py "Create API documentation for user authentication system"
```

### Operations
```bash
TIER=DEV DOMAIN=ops python run_axp.py "Design onboarding process for remote team members"
```

## Understanding Output

Each role produces:
- **Deliverable**: Core output
- **Self-Scores**: 4 dimensions (85+ required)
  - Transformation
  - Clarity
  - Reach
  - Return
- **TAES Scores**: 3 axes (0-100)
  - Logical
  - Practical
  - Probable

### Good Output Example
```
Strategist Score: 91/100 ✓
Analyst Score: 89/100 ✓
Producer Score: 93/100 ✓
Courier Score: 87/100 ✓
Critic Score: 90/100 ✓

ACI: 94 ✓ (target ≥90)
IRD: 0.3 ✓ (target ≤0.5)
```

### Failed Output Example
```
Producer Score: 78/100 ✗
→ Triggers Recursive Proof Loop (Directive 15)
→ Producer must revise and re-score
```

## Operator Commands

### Grant Override Authority
```bash
OP_AUTH --grant --duration=60m
```

### Terminate Chain
```bash
OPERATOR_KILLCHAIN --now
```

### Extend CAM Lease
```bash
OP_AUTH --extend-cam --ttl=5m
```

See [docs/operator-console.md](../../docs/operator-console.md) for full reference.

## Monitoring & Logs

### Session Logs
```
logs/sessions/YYYY-MM-DD_HH-MM_[tier].log
```

### TAES Evaluations
```
logs/ird_log.csv
```

### Audit Ledger
```
logs/ledger/audit_ledger.db
```

## Troubleshooting

### "OpenAI API key not found"
→ Check `.env` file has `OPENAI_API_KEY=sk-...`

### "Role score below threshold"
→ Normal behavior, chain will auto-revise

### "CAM lease expired"
→ Auto-suspends after 3 minutes, extend or restart

### Import errors
→ Ensure virtual environment is activated
→ Run `pip install -r requirements.txt` again

## Advanced Features

### Run Baseline Validation
```bash
python run_axp.py --sim 001
```

### Fault Injection Testing
```bash
python fault_injection.py --run Δ1-Δ3
```

### Custom Role Definitions
Edit files in `roles/` directory and set:
```
BUILD_TYPE=experimental
```

## Protocol Governance

This system operates under **Directive 0 (Change Control)**:
- All protocol changes require operator ratification
- Changes logged in `CHANGELOG.md`
- See [protocol/](../../protocol/) for constitutional directives

## Key Metrics Reference

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| ACI (Autonomy Control) | ≥90 | <85 |
| ADI (Authority Drift) | ≤5 | >10 |
| IRD (Reality Disparity) | ≤0.5 | >0.7 |
| Role Scores | ≥85/100 | <85 |

## Next Steps

1. ✅ Run first test campaign
2. ⬜ Explore operator console
3. ⬜ Review session logs
4. ⬜ Try different domains
5. ⬜ Read protocol directives
6. ⬜ Customize role definitions

## Getting Help

- **Documentation**: See [CLAUDE.md](../../CLAUDE.md)
- **Operator Console**: See [docs/operator-console.md](../../docs/operator-console.md)
- **Protocol**: See [protocol/](../../protocol/)
- **Architecture**: See [README.md](../../README.md)

## Common Workflows

### Development Iteration
```bash
# Fast testing
TIER=DEV python run_axp.py "test objective 1"
TIER=DEV python run_axp.py "test objective 2"
TIER=DEV python run_axp.py "test objective 3"
```

### Pre-Client Review
```bash
# Higher quality
TIER=PREP python run_axp.py "client draft objective"
# Review logs/sessions/latest
# Make adjustments
```

### Final Deliverable
```bash
# Full quality
TIER=CLIENT DOMAIN=marketing python run_axp.py "final client objective"
```

---

**You're ready to start!** Run your first campaign and watch the five-role chain in action.

```bash
TIER=DEV python run_axp.py "Your objective here"
```
