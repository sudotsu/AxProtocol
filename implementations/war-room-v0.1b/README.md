# AxProtocol War Room (v2.3)

The War Room is the operational engine of AxProtocol.
It converts the framework’s directive logic into live, monetizable outputs.

---

## 🔧 Quick Start

### 1. Install dependencies

From your AxProtocol root folder:

````bash
pip install streamlit openai python-dotenv pandas numpy rich flask
2. Launch the Operator Console
Windows (PowerShell)


Copy

Save

Ask Copilot

powershell
Copy code
$env:TIER = "DEV"
streamlit run variants/AxP_AAL+TAES_v0.1b/War-Room/app.py
Mac/Linux (bash or WSL)


Copy

Save

Ask Copilot

bash
Copy code
TIER=DEV streamlit run variants/AxP_AAL+TAES_v0.1b/War-Room/app.py
Set TIER to DEV, PREP, or CLIENT
DEV = cheap iterations (gpt-4o-mini)
PREP = mid-grade prep (gpt-4o-turbo)
CLIENT = full quality (gpt-4o)

The console will open in your browser at
http://localhost:8501

⚙️ Structure
File	Purpose
run.py	Main orchestrator; loads directives, runs LLM calls, logs results
app.py	Streamlit Operator Console interface
load_roles.py	Role definitions aligned with Directives 1–28
.env	Environment variables (API keys, model tiers, default TIER)
/logs/sessions/	Output and ROI logs generated automatically

🧭 Usage Tips
Enter tasks or transcripts in the text box and click Run War Room.

Every session is saved to /logs/sessions/YYYY-MM-DD_HH-MM.log.

If [Tier: Immediate ROI] appears in output, a matching .json file is created for automation tools.

Switch tiers to control quality and cost.

🧩 Directive Scope
This War Room is compliant with AxProtocol v2.3, incorporating:

Core Directives 1–14 (Foundational logic discipline)

Addendum 15–19 (Applied discipline / War-Room integration)

AAL 20–24 (Authority Assertion Layer)

TAES 25–25c (Tri-Axis Evaluation Standard)

RDL 26–28 (Red-Team / Devil’s-Advocate Layer)

🧱 Logging
Outputs and metadata are written to:


Copy

Save

Ask Copilot

bash
Copy code
logs/sessions/
  ├── 2025-10-22_18-44-01_dev.log
  ├── 2025-10-22_18-44-01_dev_ROI.json
📘 Change Control
AxProtocol follows Directive 0 (Change Control Clause).
All future modifications must be ratified in the main repo’s CHANGELOG.md before they are considered binding.


Copy

Save

Ask Copilot

markdown
Copy code

---

## 🧭 2️⃣  Consolidating Directives

You *don’t* have to merge them into one file for functionality—your `run.py` already loads all of them correctly—but **having a consolidated version** helps when:
- You want a printable / reference copy (for clients or partners).
- You need to hash a single “Full AxProtocol Constitution” for verification.

### Recommended approach
1. Leave the individual files as-is (`MASTER`, `ADDENDUM`, `AAL`, `TAES`, `RDL`).
2. Create an automated merge file:

```bash
type AxProtocol_v2.1a_MASTER.txt AxProtocol_v2.1b_ADDENDUM-WarRoomIntegration.txt AxProtocol_v2.1c_LAYER-AAL.txt AxProtocol_v2.2_LAYER-TAES.txt AxProtocol_v2.3_LAYER-RDL.txt > AxProtocol_v2.3_FULL.txt
(That type command works on Windows; use cat on Mac/Linux.)

Name the result:


Copy

Save

Ask Copilot

Copy code
AxProtocol_v2.3_FULL.txt
Keep it in /core/ or root for easy export.

That way:

Each layer remains modular for edits and versioning.

You have one consolidated file for review, hashing, or documentation.
````
