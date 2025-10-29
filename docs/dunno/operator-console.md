# AxProtocol (AxP) — OPERATOR CONSOLE SHEET v2.2

**Purpose:** Fast reference for enforcing directives, triggering runtime logic, and interpreting telemetry.  
**Applies to:** All AxP-compliant agents running v2.2 (Core + AAL + TAES)

---

## 🔹 AUTH CONTROL

- **Grant Operator override:**  
  `OP_AUTH --grant --duration=60m`

- **Terminate autonomous chain:**  
  `OPERATOR_KILLCHAIN --now`

- **Extend CAM lease:**  
  `OP_AUTH --extend-cam --ttl=5m`

- **Trigger OOM (Override Mode, high-risk):**  
  `OP_AUTH --mode OOM --ttl=6h`

---

## 🔹 TAES SCORING (Directive 25)

- **Standard Evaluation Block:**

Verdict: • Logical winner: [] • Practical winner: [] • Probable human outcome: [_____]

- **Domain weights (Directive 25a):**

Code:      Logical 0.6 / Practical 0.35 / Probable 0.05
Ops:       Logical 0.4 / Practical 0.45 / Probable 0.15
Creative:  Logical 0.35 / Practical 0.25 / Probable 0.4
Marketing: Logical 0.3 / Practical 0.2 / Probable 0.5

- **Auto-recalc threshold:**  
`IRD > 0.5` triggers Reality Reconciliation Pass (RRP)

- **Manual trigger example:**  
`evaluate_taes(domain="ops", L=0.45, P=0.4, H=0.1)`

---

## 🔹 TELEMETRY FLAGS (AAL + TAES)

- **CAM Lease Expired (Directive 21):**  
Trigger halt + wait for `OP_AUTH`

- **Authority Drift Index (Directive 24):**

ADI > 10 → auto-suspend
ADI > 5 for 3 sessions → protocol audit

- **Ideal-Reality Disparity (Directive 25b):**

IRD > 0.5 → RRP required
IRD avg > 0.4 → Disalignment Alert

- **Deviation Threshold (Directive 23):**  
`Deviation ≥ 2.5 for 2 cycles` → Freeze + Snapshot + Alert

---

## 🔹 SIMULATION FLAGS

- **Run base test:**  
`python run.py --sim 001`

- **Inject fault stress:**  
`python fault_injection.py --run Δ1-Δ3`

- **Review IRD logs:**  
`open kpi/ird_log.csv`

- **Launch dashboard:**  
`streamlit run kpi_dashboard.py`

---

## 🔹 LOGGING FORMAT

- **Ledger entry:**  
`timestamp, agent_id, action, directive, delta, hash, op_auth_status`

- **KPI file:**  
`ACI, ADI, IRD, Reasoning Verdict, Outcome Path`

---

## 🧠 Operator Reminder

> **"Precision is not politeness. Truth is not tone. This system does not exist to impress — it exists to finish."**