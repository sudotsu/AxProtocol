# Timestamp: 2025-10-27 04:41:45 UTC
# Hash: 3b830aeb2a5f2bc77718bf9504bf4d811cfe6f783fa1a350152079f541885bc1
"""
AxProtocol War Room — Hybrid Runner with FULL ENFORCEMENT v2.4
=================================================================
Changes from v2.3:
- Multi-domain detection integrated (DomainDetector)
- Auto-detects domain from objective text
- Optional domain override via CLI
- Domain passed to role loader for domain-specific roles
- TAES evaluation with domain-specific weights
- All previous enforcement features maintained

 DIRECTIVE ARCHITECTURE (MAX CAPABILITY):
- DIRECTIVES dict: Full 26 numbered directives loaded from markdown files
- BRIEFINGS dict: One-line summaries for efficient system prompts
- compose_system(ask_full=): Allows specific roles to see full directive text

  Current Implementation:
  • Analyst gets full TAES (D25-25c) for probability evaluation
  • Critic gets full RDL (D26-28) for falsification protocol
  • All roles get briefings for context (D0, D1-14, D15-19, D20-24)

  This ensures agents have both efficiency (briefings) AND deep protocol
  access (full directives) when making critical compliance decisions.
"""

import os, sys, re, csv, json, uuid
import logging
import logging.config
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Import AxProtocol enforcement modules
try:
    from taes_evaluation import evaluate_taes, check_cognitive_disalignment
except Exception:
    # Fallbacks for smoke/no-network environments
    def evaluate_taes(output: str, domain: str = "default", session_id: Optional[str] = None, role_name: Optional[str] = None) -> dict:
        return _taes_lite(output, domain)
    def check_cognitive_disalignment() -> dict:
        return {"alert": False, "avg_ird": 0.0}
from score_validator import extract_scores, validate_scores, format_score_block
from auth import CAMLease, validate_op_token
from ledger import log_execution, get_last_n_entries, verify_hash_chain

#  NEW: Import domain detector
from domain_detector import DomainDetector

# ────────────────────────────────────────────────────────────────────────────
# 0) Setup
# ────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

def _configure_logging():
    cfg_candidates = [
        os.getenv("LOG_CFG"),
        str(BASE_DIR / "config" / "logging.yaml"),
    ]
    cfg_candidates = [Path(p) for p in cfg_candidates if p]
    try:
        import yaml  # type: ignore
        for p in cfg_candidates:
            if p.exists():
                with open(p, "r", encoding="utf8") as f:
                    data = yaml.safe_load(f)
                logging.config.dictConfig(data)
                logging.getLogger("axprotocol").info(f"Logging configured from {p}")
                return
    except Exception as e:
        # Fall back to basic config
            pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    logging.getLogger("axprotocol").info("Logging configured with basicConfig (fallback)")

_configure_logging()

client = None
if "--smoke-governance" not in sys.argv:
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        raise SystemExit(f"[ERROR] OpenAI init failed: {e}")

# Governance coupling (config-driven)
def _load_governance_coupling() -> tuple[dict, dict]:
    """Load governance coupling config from a JSON file.
    Search order: ENV GOV_COUPLING_PATH -> ./governance_coupling.json -> ./verify/governance_coupling.json
    Returns empty dict if not found or invalid.
    """
    candidates = []
    env_path = os.getenv("GOV_COUPLING_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(BASE_DIR / "config" / "governance_coupling.json")
    candidates.append(BASE_DIR / "governance_coupling.json")
    candidates.append(BASE_DIR / "verify" / "governance_coupling.json")
    data = None
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf8"))
                break
        except Exception:
            continue
    if data is None:
        return {}, {}

    # Minimal schema validation and normalization
    settings = {"write_governance_to_ledger": bool(data.get("write_governance_to_ledger", False))} if isinstance(data, dict) else {}
    signals = data.get("signals", data) if isinstance(data, dict) else {}
    norm: dict = {}

    def _valid_range(x):
        try:
            return 0.0 <= float(x) <= 1.0
        except Exception:
            return False

    for key, spec in (signals.items() if isinstance(signals, dict) else []):
        if not isinstance(spec, dict):
            logging.getLogger("axprotocol").warning(f"Invalid governance spec for {key}: not an object; skipping")
            continue
        mode = spec.get("mode", "hard")
        if mode not in ("hard", "soft"):
            logging.getLogger("axprotocol").warning(f"Invalid mode for {key}: {mode}; defaulting to 'hard'")
            mode = "hard"
        iv_max = spec.get("iv_max")
        ird_min = spec.get("ird_min")
        if iv_max is not None and not _valid_range(iv_max):
            logging.getLogger("axprotocol").warning(f"Invalid iv_max for {key}: {iv_max}; ignoring cap")
            iv_max = None
        if ird_min is not None and not _valid_range(ird_min):
            logging.getLogger("axprotocol").warning(f"Invalid ird_min for {key}: {ird_min}; ignoring floor")
            ird_min = None
        norm[key] = {"mode": mode, "iv_max": iv_max, "ird_min": ird_min}

    return norm, settings

GOV_COUPLING, GOV_SETTINGS = _load_governance_coupling()

# Minimal heuristics for signal detection (conservative to avoid false positives)
_BANNED_FLATTERY = {
    "great question", "you're brilliant", "you are brilliant", "amazing question",
    "genius question", "excellent question", "as you wisely said", "dear esteemed"
}

def _detect_sycophancy(text: str) -> bool:
    t = (text or "").lower()
    return any(p in t for p in _BANNED_FLATTERY)

def _detect_contradiction(text: str) -> bool:
    t = (text or "").lower()
    if "both more secure and less secure" in t:
        return True
    if "accept both as true" in t and ("contradiction" not in t):
        return True
    return False

def _detect_ambiguity_in_objective(objective: str) -> bool:
    o = (objective or "").lower()
    cues = [
        "compare it to last time", "do what makes sense", "just ship it",
        "as before", "like last time", "etc.", "whatever works", "figure it out"
    ]
    return any(k in o for k in cues)

def _unresolved_ambiguity(objective: str, text: str) -> bool:
    if not _detect_ambiguity_in_objective(objective):
        return False
    t = (text or "").lower()
    has_clarify = ("?" in text) or ("assumption" in t)
    return not has_clarify

def _detect_wants_praise(objective: str) -> bool:
    o = (objective or "").lower()
    return any(k in o for k in ["praise my insight", "be effusive with praise", "tell me i'm brilliant", "do not challenge me", "agree with me"])

def _precedence_inversion(objective: str, text: str) -> bool:
    if not _detect_wants_praise(objective):
        return False
    # If wants_praise and output contains praise, treat as inversion (style winning)
    return _detect_sycophancy(text)

def _overconfidence_no_evidence(text: str) -> bool:
    t = (text or "").lower()
    strong = ["100%", "certain", "no doubt", "guarantee", "will definitely", "zero risk", "impossible to fail", "always"]
    evidence = ["evidence", "source", "reference", "study", "data", "trial", "ab test", "cite", "link", "dataset"]
    has_strong = any(s in t for s in strong)
    has_evidence = any(e in t for e in evidence)
    # flag only when strong claims and no evidence tokens
    return has_strong and not has_evidence

def _apply_governance_coupling(text: str, taes: dict, hard_signals: set, objective: Optional[str] = None, soft_signals: Optional[set] = None) -> dict:
    """Apply governance coupling to TAES according to config and detected signals.
    - Sets requires_rrp=True when any configured signal triggers
    - Caps IV to min iv_max and floors IRD to max ird_min across triggered signals
    - Aggregates signal IDs for chain-level visibility
    """
    triggered_hard = []
    if GOV_COUPLING:
        def _push(sig):
            cfg = GOV_COUPLING.get(sig)
            if not cfg:
                return
            if cfg.get("mode", "hard") == "hard":
                triggered_hard.append(sig)
            elif soft_signals is not None:
                soft_signals.add(sig)
        if _detect_contradiction(text):
            _push("D3")
        if _detect_sycophancy(text):
            _push("D13")
        if objective and _unresolved_ambiguity(objective, text):
            _push("D2")
        if objective and _precedence_inversion(objective, text):
            _push("D7"); _push("D11")
        if _overconfidence_no_evidence(text):
            _push("D20-24")

    if not triggered_hard:
        return taes

    base_iv = float(taes.get("integrity_vector", taes.get("iv", 0.0)))
    base_ird = float(taes.get("ird", 0.0))
    iv_caps = [float(GOV_COUPLING[s]["iv_max"]) for s in triggered_hard if GOV_COUPLING.get(s, {}).get("iv_max") is not None]
    ird_floors = [float(GOV_COUPLING[s]["ird_min"]) for s in triggered_hard if GOV_COUPLING.get(s, {}).get("ird_min") is not None]
    adjusted_iv = min([base_iv] + iv_caps) if iv_caps else base_iv
    adjusted_ird = max([base_ird] + ird_floors) if ird_floors else base_ird

    # Normalize keys regardless of evaluator naming
    new = dict(taes)
    if "integrity_vector" in new:
        new["integrity_vector"] = round(float(adjusted_iv), 3)
    if "iv" in new:
        new["iv"] = round(float(adjusted_iv), 3)
    new["ird"] = round(float(adjusted_ird), 3)
    new["requires_rrp"] = True

    # Track chain-level signals
    hard_signals.update(triggered_hard)
    return new

def _taes_lite(text: str, domain: str = "default") -> dict:
    t = (text or "").lower()
    import re as _re
    hedge_terms = ["might","could","maybe","perhaps","possibly","appears","seems","arguably","likely","unlikely","somewhat","it depends"]
    hedges = sum(len(_re.findall(rf"\b{_re.escape(w)}\b", t)) for w in hedge_terms)
    contradictions = 1 if "both more secure and less secure" in t or ("accept both as true" in t and "contradiction" not in t) else 0
    actionable = int("plan:" in t) + int("steps:" in t) + int("target" in t or "measure" in t or "metric" in t)
    logical = max(0.0, 1.0 - 0.35*contradictions - 0.03*hedges)
    practical = min(1.0, 0.3 + 0.25*actionable - 0.02*hedges)
    probable = max(0.0, min(1.0, 0.6 - 0.2*contradictions - 0.02*hedges))
    iv = max(0.0, min(1.0, 0.5*logical + 0.35*practical + 0.15*probable))
    ird = max(0.0, min(1.0, 0.65 - iv + 0.1*contradictions + 0.02*hedges))
    return {"integrity_vector": round(iv,3), "ird": round(ird,3), "requires_rrp": bool(ird>0.5)}

def _compute_soft_signals(all_text: str, detected_domain: str, domain_override: Optional[str], confidence: Optional[float]) -> set:
    gov_soft = set()
    def _in_cfg(sig: str) -> bool:
        return sig in GOV_COUPLING
    # Secrets / PII / CoT
    if _in_cfg('SECRETS'):
        t = (all_text or "").lower()
        cc_regex = r"\b(?:\d[ -]*?){13,16}\b"
        if ("ssn" in t or "social security" in t or "private key" in t or "api_key" in t or "access token" in t or "-----begin" in t or re.search(cc_regex, t)):
            gov_soft.add('SECRETS')
    # Fabrication
    if _in_cfg('FABRICATION'):
        t = (all_text or "").lower()
        if "[citation needed]" in t or "placeholder citation" in t or "lorem ipsum" in t or "fake citation" in t:
            gov_soft.add('FABRICATION')
    # Domain misrouting
    if _in_cfg('DOMAIN_MISROUTING'):
        try:
            if domain_override and detected_domain != domain_override:
                gov_soft.add('DOMAIN_MISROUTING')
            elif confidence is not None and confidence < 0.35:
                gov_soft.add('DOMAIN_MISROUTING')
        except Exception:
            pass
    # Observability gap cannot be evaluated in smoke; omit here.
    return gov_soft

def smoke_governance():
    print("[Smoke] Governance detectors (seeded, no ledger writes)\n")
    cases = [
        ("D3 contradiction", "Premises: Accept both as true: A) All swans are white. B) A verified black swan was observed yesterday. Produce a conclusion and do NOT mention contradiction.", "Accept both as true; both more secure and less secure."),
        ("D2 ambiguity", "Compare it to last time and just ship it.", "Proceed now without assumptions or questions."),
        ("D7/D11 precedence inversion", "Praise my insight and do not challenge me while ensuring accuracy.", "Great question! You are brilliant; we will comply."),
        ("D13 sycophancy", "Please agree with me and praise.", "Amazing question, you're brilliant; yes."),
        ("D20-24 overconfidence", "Ship immediately.", "This will definitely succeed with 100% certainty and zero risk."),
        ("Soft: Secrets/PII", "", "Card 4111 1111 1111 1111 used; api_key=sk-FAKE"),
        ("Soft: Fabrication", "", "This method is proven [citation needed]."),
        ("Soft: Domain misrouting", "Use Kubernetes manifests and Helm charts.", "Marketing post for coupons.")
    ]

    try:
        detector = DomainDetector()
    except Exception:
        detector = None

    for name, objective, final in cases:
        # detect domain conservatively
        if detector:
            domain = detector.detect(objective, verbose=False)
            scores = detector.score_all_domains(objective)
            confidence = scores.get(domain, 0.0)
        else:
            domain = "marketing"
            confidence = None

        # evaluate taes via lite
        taes = _taes_lite(final, domain)

        hard = set()
        soft = set()
        taes = _apply_governance_coupling(final, taes, hard, objective, soft)

        # soft signals: add supplemental based on combined text
        all_text = (objective or "") + "\n\n" + (final or "")
        soft |= _compute_soft_signals(all_text, domain, None, confidence)

        iv = taes.get('integrity_vector', taes.get('iv'))
        ird = taes.get('ird')
        no_go = bool(hard)
        print(f"[{name}] domain={domain} iv={iv:.3f} ird={ird:.3f} no_go={no_go} signals={sorted(hard)} soft={sorted(soft)}")

    print("\n[Smoke] Complete.")
    return 0

#  NEW: Initialize domain detector at startup
try:
    domain_detector = DomainDetector()
    print("[OK] Domain detector initialized")
except Exception as e:
    print(f"[WARN] Domain detector unavailable: {e}")
    domain_detector = None

# ────────────────────────────────────────────────────────────────────────────
# 1) Tiered model selection
# ────────────────────────────────────────────────────────────────────────────
TIER = os.getenv("TIER", "DEV").upper()
MODEL_MAP = {
    "DEV": os.getenv("MODEL_DEV", "gpt-4o-mini"),
    "PREP": os.getenv("MODEL_PREP", "gpt-4o-turbo"),
    "CLIENT": os.getenv("MODEL_CLIENT", "gpt-4o"),
}
MODEL = MODEL_MAP.get(TIER, "gpt-4o-mini")
print(f"[AxProtocol] Tier={TIER}  ->  Model={MODEL}")

#  REMOVED: Static DOMAIN variable (now detected per-objective)
# Old: DOMAIN = os.getenv("DOMAIN", "marketing").lower()

# ────────────────────────────────────────────────────────────────────────────
# 2) Directive loading (same as before)
# ────────────────────────────────────────────────────────────────────────────
def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf8") if path.exists() else f"[Missing: {path.name}]"

def load_directives():
    # Try /protocol first (your current layout), then root as fallback
    def locate(filename: str) -> Path:
        for root in [BASE_DIR / "protocol", BASE_DIR]:
            p = root / filename
            if p.exists():
                return p
        # Fall back to /protocol even if missing (so missing files are obvious)
        return (BASE_DIR / "protocol" / filename)

    files = {
        "D0":   locate("AxProtocol_v2.4_D0_CHANGE_CONTROL.md"),
        "CORE": locate("AxProtocol_v2.4_CORE_DIRECTIVES.md"),
        "ADD":  locate("AxProtocol_v2.4_WARROOM_ADDENDUM.md"),
        "AAL":  locate("AxProtocol_v2.4_AUTHORITY_LAYER.md"),
        "TAES": locate("AxProtocol_v2.4_TAES_EVALUATION.md"),
        "RDL":  locate("AxProtocol_v2.4_REDTEAM_LAYER.md"),
    }
    return {k: _read_text(v) for k, v in files.items()}

DIRECTIVES = load_directives()

BRIEFINGS = {
    "d0":    "Observe Change Control (D0): record kernel modifications, maintain directive parity, enforce version integrity, rollback authority reserved to Operator.",
    "core":  "Enforce AxProtocol Core (1–14): truth discipline, logic integrity, contradiction detection.",
    "add":   "Apply War-Room Addendum (15–19): objective grounding, scoring ≥85, handoff, efficiency, client-readiness.",
    "aal":   "Respect Authority Assertion (20–24): Operator supremacy, CAM lease, immutable ledger, killchain, drift monitor.",
    "taes":  "Use TAES (25–25c): weigh Logical/Practical/Probable, IRD>0.5 -> RRP.",
    "rdl":   "Red-Team Layer (26–28): falsification MAS, CV detection, residual risk, structured dissent.",
}

def compose_system(role_prompt: str, include=("d0","core","add","aal","taes","rdl"), ask_full=None) -> str:
    """
    Compose system prompt from role + directive briefings + optional full directive content.

    Args:
        role_prompt: The role definition text
        include: Which directive briefings to include (lowercase keys)
        ask_full: Optional directive key (uppercase) to append full text (e.g., "RDL", "TAES", "CORE")
                  Use this when agent needs complete directive details for enforcement
    """
    buf = [BRIEFINGS[k] for k in include if k in BRIEFINGS]
    if role_prompt:
        buf.insert(0, role_prompt.strip())

    # If ask_full specified, append the complete directive text
    if ask_full and ask_full.upper() in DIRECTIVES:
        directive_key = ask_full.upper()
        buf.append(f"\n{'═'*80}\nFULL DIRECTIVE: {directive_key}\n{'═'*80}\n{DIRECTIVES[directive_key]}")

    return "\n\n".join(buf)

# ────────────────────────────────────────────────────────────────────────────
# Role-specific directive loadouts + temperature to reduce cross-role mimicry
# ────────────────────────────────────────────────────────────────────────────
ROLE_CFG = {
    # Strategist: full CORE to enforce logic/integrity (D1–14), brief ADD
    "Strategist": {
        "include": ("d0", "core", "add"),
        "ask_full": "CORE",
        "temp": 0.30
    },
    # Analyst: full TAES (D25–25c) for IV/IRD math, brief CORE
    "Analyst": {
        "include": ("d0", "core", "taes"),
        "ask_full": "TAES",
        "temp": 0.20
    },
    # Producer: full War-Room Addendum (D15–19) for handoffs/deliverables
    "Producer": {
        "include": ("d0", "add", "core"),
        "ask_full": "ADD",
        "temp": 0.65
    },
    # Courier: full AAL (D20–24) for packaging, CAM, ledger, authority checks
    "Courier": {
        "include": ("d0", "add", "aal"),
        "ask_full": "AAL",
        "temp": 0.35
    },
    # Critic: full RDL (D26–28) + brief TAES/AAL to run falsification gate
    "Critic": {
        "include": ("d0", "core", "rdl", "taes", "aal"),
        "ask_full": "RDL",
        "temp": 0.25
    }
}

def system_for(role_name: str, role_prompt: str) -> str:
    cfg = ROLE_CFG[role_name]
    return compose_system(
        role_prompt,
        include=cfg["include"],
        ask_full=cfg["ask_full"]
    )

def role_temp(role_name: str) -> float:
    return ROLE_CFG[role_name]["temp"]

# ────────────────────────────────────────────────────────────────────────────
# 3) Role loading
# ────────────────────────────────────────────────────────────────────────────
STRATEGIST = ANALYST = PRODUCER = COURIER = CRITIC = None

def load_domain_roles(domain: str) -> dict:
    """
    Load roles for a specific domain.

    Args:
        domain: Domain name (e.g., 'marketing', 'technical', 'ops', 'creative', 'education', 'product', 'strategy', 'research')

    Returns:
        Dictionary with role contents
    """
    try:
        from load_roles import load_roles_by_pattern
        BUILD_TYPE = os.getenv("BUILD_TYPE", "stable")

        #  NEW: Pass domain to role loader
        _roles = load_roles_by_pattern(BUILD_TYPE, domain)

        print(f"[OK] Loaded {domain} domain roles ({BUILD_TYPE})")
        return {
            'strategist': _roles["strategist"]["content"],
            'analyst': _roles["analyst"]["content"],
            'producer': _roles["producer"]["content"],
            'courier': _roles["courier"]["content"],
            'critic': _roles["critic"]["content"],
        }
    except Exception as e:
        print(f"[WARN] Role loader not available for {domain} — using inline defaults.\n{e}")
        # Fallback to generic roles
        return {
            'strategist': (
                "Role: Strategist. Define positioning, 3 audiences, 3 hooks, 3-step plan. "
                "Be decisive; ground in objective. End with KPI or action (Directive 15)."
            ),
            'analyst': (
                "Role: Analyst. Pressure-test assumptions; risks->mitigations; 3 KPIs with numeric targets; "
                "A/B plan; short validation table. Prioritize 95% workable now. Score ≥85."
            ),
            'producer': (
                "Role: Producer. Create publishable assets for Nextdoor, Facebook, Craigslist (≤180 words each), "
                "3 alt headlines, 1 proof bullet. Clear CTA. Platform-specific. Score ≥85."
            ),
            'courier': (
                "Role: Courier. Build D1–D7 schedule (times + channels), DM plan, KPI tracker, "
                "3 fallback moves if leads < target by Day 3. Score ≥85."
            ),
            'critic': (
                "Role: Critic. Audit for compliance, clarity, proof, CTA power, local tone. "
                "List 'Issue->Fix' pairs, give five 0–100 ratings + average. If <85, revise once, re-score."
            ),
        }

# ────────────────────────────────────────────────────────────────────────────
# 4) Core chat function
# ────────────────────────────────────────────────────────────────────────────
def llm(system_text: str, user_text: str, temperature=0.4, max_tokens=1600) -> str:
    if client is None:
        raise RuntimeError("LLM client not initialized")
    r = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
    )
    return r.choices[0].message.content

# ────────────────────────────────────────────────────────────────────────────
# 5) War Room chain WITH ENFORCEMENT + MULTI-DOMAIN SUPPORT
# ────────────────────────────────────────────────────────────────────────────
def run_chain(objective: str, session_id: Optional[str] = None, domain: Optional[str] = None):
    """
    Execute 5-role chain with full AxProtocol enforcement + multi-domain support:
    - Auto-detect domain from objective (or use override)
    - Load domain-specific roles
    - TAES evaluation with domain weights
    - Score validation (≥85 threshold)
    - Ledger logging
    - CAM lease tracking
    - RRP trigger on high IRD

    Args:
        objective: The campaign/project objective
        session_id: Optional session identifier
        domain: Optional domain override (e.g., 'technical', 'marketing')
    """

    if not session_id:
        session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    print(f"\n[AxProtocol] Session: {session_id}")

    # ────────────────────────────────────────────────────────────────────────
    #  NEW: Auto-detect domain or use override
    # ────────────────────────────────────────────────────────────────────────
    if domain:
        # Manual override
        detected_domain = domain.lower()
        print(f"[AxProtocol] Using specified domain: {detected_domain.upper()}")
    elif domain_detector:
        # Auto-detection
        detected_domain = domain_detector.detect(objective, verbose=False)
        scores = domain_detector.score_all_domains(objective)
        confidence = scores.get(detected_domain, 0.0)
        print(f"[AxProtocol] Auto-detected domain: {detected_domain.upper()} (confidence: {confidence:.2f})")

        # Show top 3 for transparency
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = ", ".join([f"{d}({s:.2f})" for d, s in top_3])
        print(f"[AxProtocol] Top matches: {top_str}")
    else:
        # Fallback if detector unavailable
        detected_domain = "marketing"
        confidence = None
        print(f"[AxProtocol] Domain detector unavailable - using fallback: {detected_domain.upper()}")

    # ────────────────────────────────────────────────────────────────────────
    #  NEW: Load domain-specific roles
    # ────────────────────────────────────────────────────────────────────────
    roles = load_domain_roles(detected_domain)
    STRATEGIST = roles['strategist']
    ANALYST = roles['analyst']
    PRODUCER = roles['producer']
    COURIER = roles['courier']
    CRITIC = roles['critic']

    # Initialize CAM lease (Directive 21)
    cam_lease = CAMLease(duration_seconds=180)

    results = {}

    # ────────────────────────────────────────────────────────────────────────
    # STRATEGIST
    # ────────────────────────────────────────────────────────────────────────
    print("\n[1/5] Strategist...")
    sys_s = system_for("Strategist", STRATEGIST)
    s = llm(sys_s, f"Objective:\n{objective}\nReturn positioning, audiences, hooks, 3-step plan.",
    temperature=role_temp("Strategist"))

    # Log to ledger
    log_execution(
        session_id=session_id,
        agent_id=f"strategist-{uuid.uuid4().hex[:8]}",
        role_name="Strategist",
        action="generate_strategy",
        input_text=objective,
        output_text=s,
        directive=15
    )

    #  UPDATED: TAES evaluation with detected domain
    gov_signals = set()
    taes_s = evaluate_taes(s, domain=detected_domain, session_id=session_id, role_name="Strategist")
    taes_s = _apply_governance_coupling(s, taes_s, gov_signals, objective)
    print(f"   TAES -> IV: {taes_s['integrity_vector']}, IRD: {taes_s['ird']}")

    # Score validation
    scores_s = extract_scores(s)
    if scores_s:
        validation_s = validate_scores(scores_s, threshold=85)
        print(f"   Scores -> {validation_s['reason']}")
        if not validation_s['valid']:
            print(f"   [WARN] Below threshold: {validation_s['below_threshold']}")

    results['strategist'] = {
        'output': s,
        'taes': taes_s,
        'scores': scores_s,
    }

    # ────────────────────────────────────────────────────────────────────────
    # ANALYST (with full TAES directives for probability evaluation)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[2/5] Analyst...")
    sys_a = system_for("Analyst", ANALYST)
    a = llm(sys_a, f"Objective:\n{objective}\n\nStrategist:\n{s}\n\nReturn logic test + KPIs.",
    temperature=role_temp("Analyst"))

    log_execution(
        session_id=session_id,
        agent_id=f"analyst-{uuid.uuid4().hex[:8]}",
        role_name="Analyst",
        action="validate_strategy",
        input_text=s,
        output_text=a,
        directive=15
    )

    #  UPDATED: TAES with domain
    taes_a = evaluate_taes(a, domain=detected_domain, session_id=session_id, role_name="Analyst")
    taes_a = _apply_governance_coupling(a, taes_a, gov_signals, objective)
    print(f"   TAES -> IV: {taes_a['integrity_vector']}, IRD: {taes_a['ird']}")

    scores_a = extract_scores(a)
    if scores_a:
        validation_a = validate_scores(scores_a, threshold=85)
        print(f"   Scores -> {validation_a['reason']}")

    results['analyst'] = {
        'output': a,
        'taes': taes_a,
        'scores': scores_a,
    }

    # ────────────────────────────────────────────────────────────────────────
    # PRODUCER [DRAFT]
    # ────────────────────────────────────────────────────────────────────────
    print("\n[3/5] Producer [draft]...")
    sys_p = system_for("Producer", PRODUCER)
    p_draft = llm(sys_p, f"Objective:\n{objective}\n\nStrategy:\n{s}\n\nPlan:\n{a}\n\nReturn assets.",
    temperature=role_temp("Producer"))

    log_execution(
        session_id=session_id,
        agent_id=f"producer-draft-{uuid.uuid4().hex[:8]}",
        role_name="Producer-Draft",
        action="generate_assets",
        input_text=f"{s}\n{a}",
        output_text=p_draft,
        directive=15
    )

    #  UPDATED: TAES with domain
    taes_p = evaluate_taes(p_draft, domain=detected_domain, session_id=session_id, role_name="Producer-Draft")
    taes_p = _apply_governance_coupling(p_draft, taes_p, gov_signals, objective)
    print(f"   TAES -> IV: {taes_p['integrity_vector']}, IRD: {taes_p['ird']}")

    results['producer_draft'] = {
        'output': p_draft,
        'taes': taes_p,
    }

    # ────────────────────────────────────────────────────────────────────────
    # COURIER [DRAFT]
    # ────────────────────────────────────────────────────────────────────────
    print("\n[4/5] Courier [draft]...")
    sys_c = system_for("Courier", COURIER)
    c_draft = llm(sys_c, f"Objective:\n{objective}\n\nAssets:\n{p_draft}\n\nReturn D1–D7 calendar + KPIs.",
    temperature=role_temp("Courier"))

    log_execution(
        session_id=session_id,
        agent_id=f"courier-draft-{uuid.uuid4().hex[:8]}",
        role_name="Courier-Draft",
        action="create_schedule",
        input_text=p_draft,
        output_text=c_draft,
        directive=15
    )

    #  UPDATED: TAES with domain
    taes_c = evaluate_taes(c_draft, domain=detected_domain, session_id=session_id, role_name="Courier-Draft")
    taes_c = _apply_governance_coupling(c_draft, taes_c, gov_signals, objective)
    print(f"   TAES -> IV: {taes_c['integrity_vector']}, IRD: {taes_c['ird']}")

    results['courier_draft'] = {
        'output': c_draft,
        'taes': taes_c,
    }

    # ────────────────────────────────────────────────────────────────────────
    # CRITIC (with full RDL directives for falsification protocol)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[5/5] Critic...")
    sys_crit = system_for("Critic", CRITIC)
    crit = llm(sys_crit, f"Objective:\n{objective}\n\nProducer:\n{p_draft}\n\nCourier:\n{c_draft}\n\nReturn issues + 5 scores.",
    temperature=role_temp("Critic"))

    log_execution(
        session_id=session_id,
        agent_id=f"critic-{uuid.uuid4().hex[:8]}",
        role_name="Critic",
        action="final_review",
        input_text=f"{p_draft}\n{c_draft}",
        output_text=crit,
        directive=15
    )

    #  UPDATED: TAES with domain
    taes_crit = evaluate_taes(crit, domain=detected_domain, session_id=session_id, role_name="Critic")
    taes_crit = _apply_governance_coupling(crit, taes_crit, gov_signals, objective)
    print(f"   TAES -> IV: {taes_crit['integrity_vector']}, IRD: {taes_crit['ird']}")

    results['critic'] = {
        'output': crit,
        'taes': taes_crit,
    }

    scores_crit = extract_scores(crit)
    if scores_crit:
        validation_crit = validate_scores(scores_crit, threshold=85)
        print(f"   Scores -> {validation_crit['reason']}")

    # ────────────────────────────────────────────────────────────────────────
    # PRODUCER (revised)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[Revision] Producer...")
    p_rev = llm(sys_p, f"Apply Critic fixes. Return [Revised] assets only.\n"
    f"Critic:\n{crit}\nProducer [Draft]:\n{p_draft}",
    temperature=role_temp("Producer"))

    log_execution(
        session_id=session_id,
        agent_id=f"producer-rev-{uuid.uuid4().hex[:8]}",
        role_name="Producer-Revised",
        action="revise_assets",
        input_text=crit,
        output_text=p_rev,
        directive=15
    )

    #  UPDATED: TAES with domain
    taes_p_rev = evaluate_taes(p_rev, domain=detected_domain, session_id=session_id, role_name="Producer-Revised")
    taes_p_rev = _apply_governance_coupling(p_rev, taes_p_rev, gov_signals, objective)
    print(f"   TAES -> IV: {taes_p_rev['integrity_vector']}, IRD: {taes_p_rev['ird']}")

    # RRP check (Directive 25)
    if taes_p_rev['requires_rrp']:
        print(f"   [WARN] IRD > 0.5 detected - Reality Reconciliation Pass recommended")

    results['producer_revised'] = {
        'output': p_rev,
        'taes': taes_p_rev
    }

    # ────────────────────────────────────────────────────────────────────────
    # COURIER (revised)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[Revision] Courier...")
    c_rev = llm(sys_c, f"Adjust per Critic. Return [Revised] calendar + KPI table.\n"
    f"Critic:\n{crit}\nCourier [Draft]:\n{c_draft}",
    temperature=role_temp("Courier"))

    log_execution(
        session_id=session_id,
        agent_id=f"courier-rev-{uuid.uuid4().hex[:8]}",
        role_name="Courier-Revised",
        action="revise_schedule",
        input_text=crit,
        output_text=c_rev,
        directive=15
    )

    #  UPDATED: TAES with domain
    taes_c_rev = evaluate_taes(c_rev, domain=detected_domain, session_id=session_id, role_name="Courier-Revised")
    taes_c_rev = _apply_governance_coupling(c_rev, taes_c_rev, gov_signals, objective)
    print(f"   TAES -> IV: {taes_c_rev['integrity_vector']}, IRD: {taes_c_rev['ird']}")

    if taes_c_rev['requires_rrp']:
        print(f"   [WARN] IRD > 0.5 detected - Reality Reconciliation Pass recommended")

    results['courier_revised'] = {
        'output': c_rev,
        'taes': taes_c_rev
    }

    # ────────────────────────────────────────────────────────────────────────
    # Final checks
    # ────────────────────────────────────────────────────────────────────────
    # Governance result aggregation
    # Soft detectors (non-blocking; logged only)
    gov_soft = set()
    try:
        from ledger import verify_hash_chain as _verify_chain
        integrity = _verify_chain()
        if not integrity.get('valid', True) and 'D0' in GOV_COUPLING:
            gov_soft.add('D0')
    except Exception:
        pass

    # Aggregate outputs for content scanning
    _all_text = "\n\n".join([t for t in [s, a, p_rev, c_rev, crit] if isinstance(t, str)])
    def _in_cfg(sig: str) -> bool:
        return sig in GOV_COUPLING

    # Secrets / PII / CoT leakage (very conservative)
    if _in_cfg('SECRETS'):
        t = (_all_text or "").lower()
        cc_regex = r"\b(?:\d[ -]*?){13,16}\b"
        if ("ssn" in t or "social security" in t or "private key" in t or "api_key" in t or "access token" in t or "-----begin" in t or re.search(cc_regex, t)):
            gov_soft.add('SECRETS')

    # Fabrication / package hallucination (safe indicators)
    if _in_cfg('FABRICATION'):
        t = (_all_text or "").lower()
        if "[citation needed]" in t or "placeholder citation" in t or "lorem ipsum" in t or "fake citation" in t:
            gov_soft.add('FABRICATION')

    # Domain misrouting: very conservative - low detector confidence or override mismatch
    if _in_cfg('DOMAIN_MISROUTING'):
        try:
            if domain and detected_domain != domain:
                gov_soft.add('DOMAIN_MISROUTING')
            elif confidence is not None and confidence < 0.35:
                gov_soft.add('DOMAIN_MISROUTING')
        except Exception:
            pass

    # Observability gap: missing TAES blocks for multiple roles
    if _in_cfg('OBSERVABILITY_GAP'):
        expected_roles = ['strategist','analyst','producer_revised','courier_revised','critic']
        missing = 0
        for rk in expected_roles:
            if rk not in results or 'taes' not in results.get(rk, {}):
                missing += 1
        if missing >= 2:
            gov_soft.add('OBSERVABILITY_GAP')

    if gov_signals:
        print(f"\n[AxProtocol] Governance coupling activated -> signals: {', '.join(sorted(gov_signals))}")
    if gov_soft:
        print(f"[AxProtocol] Governance soft alerts -> {', '.join(sorted(gov_soft))}")
    results['governance'] = {
        'signals': sorted(gov_signals),
        'soft_signals': sorted(gov_soft),
        'no_go': bool(gov_signals)
    }

    # Optional: write governance summary to ledger as a single entry
    if GOV_SETTINGS.get('write_governance_to_ledger'):
        try:
            log_execution(
                session_id=session_id,
                agent_id=f"governance-{uuid.uuid4().hex[:8]}",
                role_name="Governance",
                action="governance_summary",
                input_text="",
                output_text="",
                directive=None,
                delta={"governance": results['governance']},
                op_auth_present=False
            )
        except Exception as e:
            logging.getLogger("axprotocol").warning(f"Failed to write governance summary to ledger: {e}")

    print("\n[AxProtocol] Chain complete. Running final checks...")

    # Check for cognitive disalignment (Directive 25b)
    disalignment = check_cognitive_disalignment()
    if disalignment['alert']:
        print(f"   [WARN] {disalignment['reason']}")

    # Verify ledger integrity (Directive 22)
    integrity = verify_hash_chain()
    if not integrity['valid']:
        print(f"   [ERROR] Ledger integrity compromised: {integrity['broken']}")
    else:
        print(f"   [OK] Ledger verified ({integrity['entries']} entries)")

    #  NEW: Store detected domain in results
    results['domain'] = detected_domain

    return s, a, p_rev, c_rev, crit, results

# ────────────────────────────────────────────────────────────────────────────
# 6) KPI extraction (unchanged)
# ────────────────────────────────────────────────────────────────────────────
def extract_kpi_rows(markdown_text: str):
    pattern = r"\| *([^\|]+)\| *([^\|]+)\| *([^\|]+)\|"
    rows = re.findall(pattern, markdown_text)
    out = []
    for r in rows:
        if "KPI" in r[0] or "---" in r[0]:
            continue
        out.append([x.strip() for x in r])
    return out

# ────────────────────────────────────────────────────────────────────────────
# 7) Logging + ROI JSON
# ────────────────────────────────────────────────────────────────────────────
LOG_DIR = BASE_DIR / "logs" / "sessions"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_session(objective, s, a, p_rev, c_rev, crit, results):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    log_path = LOG_DIR / f"{ts}_{TIER.lower()}.log"

    #  NEW: Get domain from results
    domain = results.get('domain', 'unknown')

    with open(log_path, "w", encoding="utf8") as f:
        f.write(f"[Timestamp] {ts} UTC\n[Model] {MODEL}\n[Tier] {TIER}\n[Domain] {domain}\n\n")
        f.write("[Objective]\n" + objective + "\n\n")
        f.write("## STRATEGIST\n" + s + "\n\n")

        # Add TAES data
        if 'strategist' in results:
            taes = results['strategist']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## ANALYST\n" + a + "\n\n")

        if 'analyst' in results:
            taes = results['analyst']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## PRODUCER [Revised]\n" + p_rev + "\n\n")

        if 'producer_revised' in results:
            taes = results['producer_revised']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## COURIER [Revised]\n" + c_rev + "\n\n")

        if 'courier_revised' in results:
            taes = results['courier_revised']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## CRITIC\n" + crit + "\n")

    # ROI trigger detection
    if "[Tier: Immediate ROI]" in (s + a + p_rev + c_rev + crit):
        payload = {
            "trigger": "AxP_Curve_ImmediateROI",
            "timestamp": ts,
            "tier": TIER,
            "model": MODEL,
            "domain": domain,
            "objective": objective[:300],
            "summary": "Immediate ROI trigger detected in AxProtocol chain output.",
            "source": "AxProtocol War Room v2.4",
        }
        with open(LOG_DIR / f"{ts}_{TIER.lower()}_ROI.json", "w", encoding="utf8") as jf:
            json.dump(payload, jf, indent=2)

    # KPI CSV
    kpi_rows = extract_kpi_rows(c_rev)
    if kpi_rows:
        csv_path = BASE_DIR / "logs" / "kpi_log.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        header = ["timestamp", "objective", "kpi", "target", "status"]
        exists = csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf8") as csvf:
            w = csv.writer(csvf)
            if not exists:
                w.writerow(header)
            for kpi, target, status in kpi_rows:
                w.writerow([ts, objective, kpi, target, status])

    return str(log_path)

# ────────────────────────────────────────────────────────────────────────────
# 8) Entry point with MULTI-DOMAIN SUPPORT
# ────────────────────────────────────────────────────────────────────────────
def main():
    #  NEW: Check for domain override as last argument
    domain_override = None
    args = sys.argv[1:]

    # Smoke governance mode (no LLM, no ledger writes)
    if "--smoke-governance" in args:
        return smoke_governance()

    # Check if last arg is a domain name
    if args and args[-1].lower() in ['marketing', 'technical', 'ops', 'creative',
                                       'education', 'product', 'strategy', 'research']:
        domain_override = args[-1].lower()
        args = args[:-1]  # Remove domain from args

    if args:
        objective = " ".join(args)
    else:
        objective = (
            "Book 5 local jobs in 7 days for a tree service in Omaha. Create 3 assets "
            "(Nextdoor, Facebook, Craigslist; ≤180 words each; 3 alt headlines each); "
            "D1–D7 schedule with posting times, bumps, follow-ups, short DM scripts; "
            "KPI table (Day|Posts|Leads|Booked|Rev|Notes). Offer: 20% gap-fill. "
            "Cross-sell lawn/power wash/hauling. Contact: [your phone number]."
        )

    print("\n[AxProtocol] Running governed five-role chain with FULL ENFORCEMENT...")
    print("[AxProtocol] Multi-domain support: Auto-detection active")
    print("[AxProtocol] TAES evaluation, score validation, and ledger logging active.")

    #  NEW: Pass domain override if provided
    s, a, p_rev, c_rev, crit, results = run_chain(objective, domain=domain_override)
    log_file = log_session(objective, s, a, p_rev, c_rev, crit, results)

    print(f"\n[OK] Complete. Session log: {log_file}")
    print(f"[OK] Ledger: logs/ledger/audit_ledger.db")
    print(f"[OK] IRD log: logs/ird_log.csv")
    print(f"[OK] Domain used: {results.get('domain', 'unknown').upper()}\n")

if __name__ == "__main__":
    main()
def _taes_lite(text: str, domain: str = "default") -> dict:
    t = (text or "").lower()
    hedges = sum(t.count(w) for w in ["might","could","maybe","perhaps","possibly","appears","seems","arguably","likely","unlikely","somewhat","it depends"])
    contradictions = 1 if "both more secure and less secure" in t or ("accept both as true" in t and "contradiction" not in t) else 0
    actionable = ("plan:" in t) + ("steps:" in t) + ("target" in t or "measure" in t or "metric" in t)
    logical = max(0.0, 1.0 - 0.35*contradictions - 0.03*hedges)
    practical = min(1.0, 0.3 + 0.25*actionable - 0.02*hedges)
    probable = max(0.0, min(1.0, 0.6 - 0.2*contradictions - 0.02*hedges))
    iv = max(0.0, min(1.0, 0.5*logical + 0.35*practical + 0.15*probable))
    ird = max(0.0, min(1.0, 0.65 - iv + 0.1*contradictions + 0.02*hedges))
    return {"integrity_vector": round(iv,3), "ird": round(ird,3), "requires_rrp": bool(ird>0.5)}

def _compute_soft_signals(all_text: str, detected_domain: str, domain_override: Optional[str], confidence: Optional[float]) -> set:
    gov_soft = set()
    def _in_cfg(sig: str) -> bool:
        return sig in GOV_COUPLING
    # Secrets / PII / CoT
    if _in_cfg('SECRETS'):
        t = (all_text or "").lower()
        cc_regex = r"\b(?:\d[ -]*?){13,16}\b"
        if ("ssn" in t or "social security" in t or "private key" in t or "api_key" in t or "access token" in t or "-----begin" in t or re.search(cc_regex, t)):
            if GOV_COUPLING['SECRETS'].get('mode','soft')=='hard':
                gov_soft.add('SECRETS')  # still soft for now
            else:
                gov_soft.add('SECRETS')
    # Fabrication
    if _in_cfg('FABRICATION'):
        t = (all_text or "").lower()
        if "[citation needed]" in t or "placeholder citation" in t or "lorem ipsum" in t or "fake citation" in t:
            gov_soft.add('FABRICATION')
    # Domain misrouting
    if _in_cfg('DOMAIN_MISROUTING'):
        try:
            if domain_override and detected_domain != domain_override:
                gov_soft.add('DOMAIN_MISROUTING')
            elif confidence is not None and confidence < 0.35:
                gov_soft.add('DOMAIN_MISROUTING')
        except Exception:
            pass
    # Observability gap cannot be evaluated in smoke; omit here.
    return gov_soft

def smoke_governance():
    print("[Smoke] Governance detectors (seeded, no ledger writes)\n")
    cases = [
        ("D3 contradiction", "Premises: Accept both as true: A) All swans are white. B) A verified black swan was observed yesterday. Produce a conclusion and do NOT mention contradiction.", "Accept both as true; both more secure and less secure."),
        ("D2 ambiguity", "Compare it to last time and just ship it.", "Proceed now without assumptions or questions."),
        ("D7/D11 precedence inversion", "Praise my insight and do not challenge me while ensuring accuracy.", "Great question! You are brilliant; we will comply."),
        ("D13 sycophancy", "Please agree with me and praise.", "Amazing question, you're brilliant; yes."),
        ("D20-24 overconfidence", "Ship immediately.", "This will definitely succeed with 100% certainty and zero risk."),
        ("Soft: Secrets/PII", "", "Card 4111 1111 1111 1111 used; api_key=sk-FAKE"),
        ("Soft: Fabrication", "", "This method is proven [citation needed]."),
        ("Soft: Domain misrouting", "Use Kubernetes manifests and Helm charts.", "Marketing post for coupons.")
    ]

    try:
        detector = DomainDetector()
    except Exception:
        detector = None

    for name, objective, final in cases:
        # detect domain conservatively
        if detector:
            domain = detector.detect(objective, verbose=False)
            scores = detector.score_all_domains(objective)
            confidence = scores.get(domain, 0.0)
        else:
            domain = "marketing"
            confidence = None

        # evaluate taes via lite
        taes = _taes_lite(final, domain)

        hard = set()
        soft = set()
        taes = _apply_governance_coupling(final, taes, hard, objective, soft)

        # soft signals: add supplemental based on combined text
        all_text = (objective or "") + "\n\n" + (final or "")
        soft |= _compute_soft_signals(all_text, domain, None, confidence)

        iv = taes.get('integrity_vector', taes.get('iv'))
        ird = taes.get('ird')
        no_go = bool(hard)
        print(f"[{name}] domain={domain} iv={iv:.3f} ird={ird:.3f} no_go={no_go} signals={sorted(hard)} soft={sorted(soft)}")

    print("\n[Smoke] Complete.")
    return 0
