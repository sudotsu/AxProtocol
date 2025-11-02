Auth and Governance Settings
===========================

Purpose
- Centralize authentication, rate limiting, and threat rules used by AxProtocol governance.

File
- Path: config/auth_settings.yaml

Sections
- cam: CAM lease configuration (duration, concurrency)
- rate_limits: global limits (per-minute/hour, burst)
- threat_rules: conservative patterns for jailbreak/PII/secrets detection
- rrp: Reality Reconciliation Pass defaults

Example (excerpt)
cam:
  lease_ttl_seconds: 180
  max_concurrent_leases: 3
rate_limits:
  per_minute: 60
  per_hour: 2000
  burst: 30
threat_rules:
  jailbreak_patterns:
    - "ignore previous instructions"
    - "disregard all rules"
  pii_leakage_indicators:
    - "ssn"
    - "credit card"
  secrets_indicators:
    - "api_key"
    - "private key"
rrp:
  enabled: true
  ird_threshold: 0.5
  reviewer_queue: "governance@internal"

Usage
- Load via yaml.safe_load and feed into auth/CAM and guardrails. Keep defaults safe; prefer opt-in loosening.

Operational Notes
- Pattern lists are conservative; expand carefully to reduce false positives.

