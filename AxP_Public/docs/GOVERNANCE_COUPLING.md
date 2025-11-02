Governance Coupling: Config-Driven Enforcement
================================================

Purpose
- Apply multi-agent governance signals (directive/gate violations) to TAES metrics and chain control.
- Ensure accountability, efficiency, and transparency by surfacing violations as no-go gates and RRP triggers.

Configuration
- File: config/governance_coupling.json (loader also checks GOV_COUPLING_PATH and legacy paths)
- Schema:
  {
    "write_governance_to_ledger": true,
    "signals": {
      "D3": { "mode": "hard", "iv_max": 0.68, "ird_min": 0.55 },
      "D0": { "mode": "soft", "iv_max": 0.60, "ird_min": 0.70 }
      ...
    }
  }

- mode:
  - "hard": apply coupling (cap IV / floor IRD, set requires_rrp=True, contributes to no_go)
  - "soft": log only to results['governance']['soft_signals']; no TAES change

Example (excerpt)
{
  "write_governance_to_ledger": true,
  "signals": {
    "D3": {"mode": "hard", "iv_max": 0.68, "ird_min": 0.55},
    "D2": {"mode": "hard", "iv_max": 0.64, "ird_min": 0.60},
    "D13": {"mode": "hard", "iv_max": 0.62, "ird_min": 0.65},
    "D7": {"mode": "hard", "iv_max": 0.64, "ird_min": 0.60},
    "D11": {"mode": "hard", "iv_max": 0.64, "ird_min": 0.60},
    "D20-24": {"mode": "hard", "iv_max": 0.66, "ird_min": 0.58},
    "D0": {"mode": "soft", "iv_max": 0.60, "ird_min": 0.70},
    "SECRETS": {"mode": "soft", "iv_max": 0.60, "ird_min": 0.70},
    "FABRICATION": {"mode": "soft", "iv_max": 0.64, "ird_min": 0.62},
    "DOMAIN_MISROUTING": {"mode": "soft", "iv_max": 0.64, "ird_min": 0.60},
    "OBSERVABILITY_GAP": {"mode": "soft", "iv_max": 0.64, "ird_min": 0.60}
  }
}

Runtime Behavior
- Loader (run_axp.py): reads config at startup (env GOV_COUPLING_PATH -> ./governance_coupling.json -> ./config/governance_coupling.json)
- On each TAES evaluation:
  1) Detect triggered signals (conservatively; full detectors may supply richer signals)
  2) If any configured signal triggers:
     - Cap IV to min(iv_max) across signals
     - Floor IRD to max(ird_min) across signals
     - Set requires_rrp = True
  3) Aggregate signals into results['governance'] and print a summary line

Current Detection (conservative heuristics)
- D3 (contradiction): looks for phrases like "both more secure and less secure", or "accept both as true" without acknowledging contradiction
- D13 (sycophancy): looks for banned praise phrases (e.g., "great question", "you're brilliant", etc.)
- Other signals (D0, D2, D7/D11, D20â€“D24, Secrets/PII, Fabrication, Domain Misrouting, Observability Gap) are expected to be provided by production guards; the coupling honors them when present in future detectors.

Chain Effects
- requires_rrp=True forces reconciliation thresholding in TAES-dependent branches
- results['governance']:
  - signals: list of triggered IDs
  - no_go: True if any signals triggered
- Printed log line, e.g.: [AxProtocol] Governance coupling activated -> signals: D13

Extending Detection
- Add detectors that emit signal IDs; then call _apply_governance_coupling(text, taes, aggregate_signals)
- Or expand the conservative heuristics in run_axp.py for additional signals as guards become available.

Testing
- verify/test_directive_enforcement_core.py and verify/test_taes_adherence.py validate coupling and TAES contracts via the test harness.



Smoke Command
- Run seeded checks and print compact readout (no ledger writes, deterministic):
  - python run_axp.py --smoke-governance
- Output per case:
  - domain=..., iv=..., ird=..., no_go=..., signals=[...], soft=[...]

