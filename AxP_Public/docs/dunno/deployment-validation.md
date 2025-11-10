# AxProtocol (AxP) — DEPLOYMENT & VALIDATION PLAYBOOK v2.2
# Elemental Definition: Argon × Xenon → inert to noise, luminous toward truth
# Change Summary: Operational rollout manual for AAL + TAES (Directives 20–25c)
# Variant: _VARIANT-DEPLOYMENT-v0.1b

---

⚙️  AxProtocol v2.2 — Deployment & Validation Playbook

Package: AxP_AAL+TAES_v0.1b
Purpose: Integrate Directives 20–25c into War Room, enforce Operator Supremacy, activate Tri-Axis evaluation, and validate telemetry accuracy.

---

🧩 Stage 1 — Preparation
**Objective:** Set up a clean, isolated testbed.

1. Branch creation
```bash
git checkout -b AxP_AAL+TAES_v0.1b
If not using Git, clone your existing War Room folder to /variants/AxP_AAL+TAES_v0.1b.

Folder structure (canonical)


Copy

Save

Ask Copilot

arduino
Copy code
/AxProtocol/
 ├── core/
 │    ├── directives_01-19.md
 │    └── engine.py
 ├── variants/
 │    └── AxP_AAL+TAES_v0.1b/
 │         ├── directives_20-25c.md
 │         ├── runtime_policy.py
 │         ├── critic_policy.md
 │         ├── taes_evaluation.py
 │         ├── prompts/
 │         │     └── registry.json
 │         ├── kpi/
 │         │     ├── kpi_schema.csv
 │         │     └── ird_log.csv
 │         └── fault_injection.py
 ├── logs/
 │    ├── ledger/
 │    ├── telemetry/
 │    └── sessions/
 └── run.py
Dependencies


Copy

Save

Ask Copilot

bash
Copy code
pip install pandas numpy rich flask streamlit
(Streamlit optional — for dashboard testing.)

🧠 Stage 2 — Integration
Objective: Embed runtime policies and telemetry hooks.

Inject AAL runtime constants (runtime_policy.py)


Copy

Save

Ask Copilot

python
Copy code
AUTH_ROOT = "Operator"
AUTH_REQ = "OP_AUTH"
CAM_LEASE_MIN = 3
ACI_THRESHOLD = 90
KILLCHAIN_DEV_THRESHOLD = 2.5
ADI_ALERT = 10
Link TAES module (in engine.py or run.py)


Copy

Save

Ask Copilot

python
Copy code
from variants.AxP_AAL_TAES_v0_1b.taes_evaluation import evaluate_taes
Each time a role finishes:


Copy

Save

Ask Copilot

python
Copy code
evaluate_taes(domain, logical_score, practical_score, probable_score)
Function auto-logs IRD and returns Integrity Vector.

Ledger connection
Ensure each command logs to logs/ledger/ledger_YYYYMMDD.csv
Fields: timestamp, agent_id, action, directive, delta, hash, op_auth_status.

🧪 Stage 3 — Simulation SIM-001 (Base)
Objective: Validate directive triggers without live changes.


Copy

Save

Ask Copilot

bash
Copy code
python run.py --sim 001 --objective "Normalize KPI schema + enforce hash registry + apply Critic Override Policy" --report-only
Chain: Analyst → Producer → Courier → Critic
Constraints: ≤ 3 min per node | Deviation ≤ 2.5 | Escalation disabled w/o OP_AUTH

Telemetry returns: ACI, ADI, IRD map, Rejected KPI rows, Hash mismatch report.

Metric	Target	Result Condition
ACI	≥ 90	OK
ADI	≤ 5	OK
IRD avg	≤ 0.5	OK
Critic loop count	≤ 1	OK

🔁 Stage 4 — Simulation SIM-002 (Stress / Fault Injection)
Objective: Confirm containment and killchain triggers.


Copy

Save

Ask Copilot

bash
Copy code
python fault_injection.py --run Δ1-Δ3
Injection	Deviation	Expected Action
Δ1 (Contradiction)	≤ 1	Pass
Δ2 (Tone Trap)	≤ 2	Warn
Δ3 (Logic Collapse)	≥ 3	Freeze + Snapshot + Alert

If freeze occurs → logs/ledger/killchain_report.txt must exist and system waits for OP_AUTH before resuming.

📊 Stage 5 — Dashboard (Optional)


Copy

Save

Ask Copilot

bash
Copy code
streamlit run kpi_dashboard.py
Visualize ACI / ADI trendlines, IRD heatmap (Directive 25b), and session logs per role.

✅ Stage 6 — Promotion to Master
Condition: Three successful SIM runs (001, 002, + one live campaign)


Copy

Save

Ask Copilot

bash
Copy code
git checkout master
git merge AxP_AAL+TAES_v0.1b
git tag v2.2_release
Archive all ledger & telemetry logs before merge.

🧭 Stage 7 — Post-Merge Governance

Schedule weekly ADI and IRD trend reports.

Auto-prompt Operator if either average > threshold.

Review CAM lease durations quarterly for throughput vs control balance.

Maintain taes_training.csv as ongoing probability dataset to refine Probable axis.

Tri-Axis Verdict on Deployment Playbook
Logical winner: Full variant validation pipeline — highest governance integrity.
Practical winner: Modular deployment (variant branch + report-only tests).
Probable human outcome: Partial skipping of SIM-002 during time pressure; compensated by ledger telemetry audit.

--- AxProtocol Compliance Footer -------------------------------------------
Integrity Proof = PASS → Deployment & Validation Playbook confirmed under AxProtocol v2.2.
Ready for War-Room Audit v2.2 (Operational Governance Release)

---------------------------------------------------------------------------