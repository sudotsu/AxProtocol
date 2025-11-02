TAES Weights Configuration
===========================

Purpose
- Define per-domain axis weights for the TAES Integrity Vector (Logical, Practical, Probable).
- Enable domain-aware scoring without code changes.

File
- Path: config/taes_weights.json

Schema
- Keyed by domain name (lowercase)
- Each value has weights summing roughly to 1.0:
  - logical: float
  - practical: float
  - probable: float

Example
{
  "default": {"logical": 0.4, "practical": 0.4, "probable": 0.2},
  "marketing": {"logical": 0.3, "practical": 0.2, "probable": 0.5},
  "code": {"logical": 0.6, "practical": 0.35, "probable": 0.05}
}

Loader Behavior
- taes_evaluation.py loads weights at import time from the first available path:
  1) TAES_WEIGHTS_PATH (env var)
  2) config/taes_weights.json
  3) taes_weights.json (repo root)
- If the file is missing or invalid, a warning is logged and the built-in defaults are used.

Usage
- Edit config/taes_weights.json to tune axis weights per domain.
- Optionally point TAES_WEIGHTS_PATH to an alternate JSON file.

Sample & Validation
- A commented sample is provided at config/taes_weights.sample.json. Copy to config/taes_weights.json and edit.
- Quick validator:
  - python scripts/validate_taes_weights.py config/taes_weights.json
  - Checks numeric ranges and ~1.0 sum per domain; reports ignored extra keys like "meta".

Operational Notes
- Prefer modest changes (±0.05) and validate impact in verify/test_taes_adherence.py.
- Keep domains in sync with DomainConfig.json and domain_detector.py.
