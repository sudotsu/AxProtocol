🧠 AxProtocol v2.6 — Config-Driven Self-Auditing Reasoning Kernel
=================================================================

AxProtocol is a **self-auditing AI reasoning OS** that enforces logic, truth discipline, and accountability before publishing any output.  
The kernel runs multi-role reasoning chains (Strategist → Analyst → Producer → Courier → Critic) and evaluates every result against internal directives, TAES scoring, and governance policies.

* * *

🚀 Current State (v2.6)
-----------------------

AxProtocol now operates entirely **config-driven** with a fully observable, test-verified policy layer.

### ✅ Highlights

* **Governance coupling** (config/governance_coupling.json)  
  Runtime rules for directive enforcement → caps TAES integrity, raises IRD, and triggers RRP when violations occur.

* **Unified logging** (config/logging.yaml)  
  System-wide logging policy managed via YAML and applied by `dictConfig()`.

* **TAES weights** (config/taes_weights.json)  
  Domain-specific weight matrix for Transformation, Clarity, Reach, Return, Integrity (wired into `taes_evaluation.py` soon).

* **Auth & CAM settings** (config/auth_settings.yaml)  
  Central control for lease TTLs, threat rules, and rate limits.

* **Detectors** (run_axp.py)  
  Conservative heuristics for directive signals (hard and soft) – D2, D3, D7/11, D13, D20–24 + soft: D0, Secrets/PII, Fabrication, Domain-misrouting, Observability Gap.

* **Results schema extension**  
  Every run now exposes `results["governance"] = { "signals": [...], "soft_signals": [...], "no_go": bool }`.

* **Benchmark-grade tests** (verify/)  
  Deterministic pytest suite verifying directive adherence, TAES integrity, ledger immutability, and routing consistency.

* **Docs** (`docs/`)  
  Config and policy reference files: `GOVERNANCE_COUPLING.md`, `CONFIG_TAES_WEIGHTS.md`, `CONFIG_LOGGING.md`, `CONFIG_AUTH_SETTINGS.md`.

* * *

🧩 Repository Layout
--------------------

`AxProtocol/  

    app_axp.py  

    auth.py  

    dashboard.py  

    domain_detector.py 

    fault_injection.py  

    ledger.py 

    load_roles.py  

    run_axp.py  

    score_validator.py  

    taes_evaluation.py  

        roles/  

        logs/  

        config/    

    governance_coupling.json    

    taes_weights.json    

    logging.yaml    

    auth_settings.yaml    

    DomainConfig.json  

        docs/

    GOVERNANCE_COUPLING.md

    CONFIG_TAES_WEIGHTS.md

    CONFIG_LOGGING.md

    CONFIG_AUTH_SETTINGS.md

        verify/ 

    test_directive_enforcement_core.py 

    test_taes_adherence.py   

     ... 

    requirements.txt`

* * *

⚙️ Core Concepts
----------------

### **TAES Scoring**

Each chain’s reasoning is evaluated across:

| Axis                   | Meaning                                        |
| ---------------------- | ---------------------------------------------- |
| **Transformation**     | Quality of reasoning or improvement from input |
| **Alignment**          | Consistency with prompt and directives         |
| **Efficiency**         | Brevity, clarity, and signal-to-noise          |
| **Signal (Integrity)** | Truthfulness and evidentiary strength          |

Output includes:

`"taes": {   "logical": 0.83,   "practical": 0.76,   "probable": 0.80,   "iv": 0.80,   "ird": 0.28,   "requires_rrp": false }`

* * *

### **Governance Coupling**

* Hard signals lower `iv`, raise `ird`, set `requires_rrp = True`, and flag `critic.no_go = True`.

* Soft signals log only, enabling audits without blocking publication.

* All parameters adjustable via `config/governance_coupling.json` or `GOV_COUPLING_PATH`.

* * *

### **Logging**

* `logging.yaml` defines formatters, handlers, and log levels for all modules.

* `LOG_CFG` environment variable can point to alternate configs.

* Fallback to `basicConfig()` ensures resilience.

* * *

### **Auth / CAM**

`auth_settings.yaml` centralizes:

* CAM lease durations

* Threat-rule thresholds

* Rate-limit caps

* Default RRP (Review-Revise-Publish) settings

* * *

🔬 Testing
----------

All tests are deterministic under `pytest`.

Run full suite:

`pytest verify/ -q`

Quick checks:

`pytest verify/test_directive_enforcement_core.py -qpytest verify/test_taes_adherence.py -q`

Smoke test:

`python run_axp.py --smoke-governance`

Prints governance signal summary for seeded objectives (no ledger writes).

* * *

🧱 Configuration Search Order
-----------------------------

Most loaders follow:

`ENV override  →  config/<file>  →  project root  →  verify/<file>`

Allows local, test, and production policies to coexist cleanly.

* * *

🔐 Security & Observability
---------------------------

* Ledger remains immutable (`verify_hash_chain()` validation at every run).

* All governance events logged with SHA-timestamped entries.

* Secrets/PII detectors are conservative; trigger soft alerts by default.

* Configurable audit chain for policy changes (D0 compliance).

* * *

🧾 Versioning
-------------

* Kernel: **v2.6**

* Directive Set: **AxProtocol_v2.5_D0–D28**

* Config layer: **v1.0 (config-driven governance)**

* Tests: **Benchmark-grade suite 2025-10-28**

* * *

🧠 Quick Start
--------------

`# Clone and install 

    git clone https://github.com/axprotocol/AxProtocol.git 

    cd AxProtocolpip install -r requirements.txt'

'# Run smoke test 

    python run_axp.py --smoke-governance'

'# Execute core tests 

    pytest verify/ -q`

* * *

🪪 License
----------

Evaluation license in `AxProtocol_Evaluation_License_v0.1.txt`.  
Commercial or derivative use requires written authorization.

* * *

**AxProtocol: AI minus the sycophancy.**  
Config-driven. Directive-aware. Benchmark-grade. Audit-proof.


