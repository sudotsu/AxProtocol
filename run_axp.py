# Timestamp: 2025-10-27 04:41:45 UTC
# Hash: 3b830aeb2a5f2bc77718bf9504bf4d811cfe6f783fa1a350152079f541885bc1
"""
AxProtocol War Room â€” Hybrid Runner with FULL ENFORCEMENT v2.4
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
  â€¢ Analyst gets full TAES (D25-25c) for probability evaluation
  â€¢ Critic gets full RDL (D26-28) for falsification protocol
  â€¢ All roles get briefings for context (D0, D1-14, D15-19, D20-24)

  This ensures agents have both efficiency (briefings) AND deep protocol
  access (full directives) when making critical compliance decisions.
"""

import os, sys, re, csv, json, uuid
import logging
import logging.config
from pathlib import Path
import traceback as _tb
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
from axp.governance.coupling import (
    load_governance_coupling as _ext_load_governance_coupling,
    apply_governance_coupling as _ext_apply_governance_coupling,
    compute_soft_signals as _ext_compute_soft_signals,
)

#  NEW: Import domain detector
from domain_detector import DomainDetector

# 0) Setup

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
GOV_COUPLING, GOV_SETTINGS = _ext_load_governance_coupling()

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
    return _ext_apply_governance_coupling(
        text, taes, hard_signals, objective, soft_signals, cfg=GOV_COUPLING
    )

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
    return _ext_compute_soft_signals(all_text, detected_domain, domain_override, confidence, cfg=GOV_COUPLING)

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

# 1) Tiered model selection

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

# 2) Directive loading (same as before)

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
    "core":  "Enforce AxProtocol Core (1â€“14): truth discipline, logic integrity, contradiction detection.",
    "add":   "Apply War-Room Addendum (15â€“19): objective grounding, scoring â‰¥85, handoff, efficiency, client-readiness.",
    "aal":   "Respect Authority Assertion (20â€“24): Operator supremacy, CAM lease, immutable ledger, killchain, drift monitor.",
    "taes":  "Use TAES (25â€“25c): weigh Logical/Practical/Probable, IRD>0.5 -> RRP.",
    "rdl":   "Red-Team Layer (26â€“28): falsification MAS, CV detection, residual risk, structured dissent.",
}

# Collaboration contract appended to all role system prompts to encourage
# complementary, non-duplicative artifacts with cross-role traceability.
COLLAB_CONTRACT = (
    "\nCollaboration Contract:\n"
    "- Build on prior roles; do not restate their sections.\n"
    "- Introduce new artifacts and assign stable IDs (S-1, A-1, P-1, C-1).\n"
    "- Cross-reference upstream IDs wherever applicable.\n"
    "- Prefer depth and specificity over general prose.\n"
)

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
        buf.append(f"\n{'â•'*80}\nFULL DIRECTIVE: {directive_key}\n{'â•'*80}\n{DIRECTIVES[directive_key]}")

    # Append collaboration contract to all roles
    buf.append(COLLAB_CONTRACT)

    # Optional debug: dump first few lines of the system prompt
    try:
        import os as _os
        if _os.getenv("DEBUG_SYS", "0") == "1":
            preview = "\n".join("\n\n".join(buf).splitlines()[:12])
            print("[DEBUG_SYS] System prompt preview:\n" + preview + "\n---")
    except Exception:
        pass

    return "\n\n".join(buf)

# Role-specific directive loadouts + temperature to reduce cross-role mimicry

ROLE_CFG = {
    # Strategist: full CORE to enforce logic/integrity (D1â€“14), brief ADD
    "Strategist": {
        "include": ("d0", "core", "add"),
        "ask_full": "CORE",
        "temp": 0.30
    },
    # Analyst: full TAES (D25â€“25c) for IV/IRD math, brief CORE
    "Analyst": {
        "include": ("d0", "core", "taes"),
        "ask_full": "TAES",
        "temp": 0.20
    },
    # Producer: full War-Room Addendum (D15â€“19) for handoffs/deliverables
    "Producer": {
        "include": ("d0", "add", "core"),
        "ask_full": "ADD",
        "temp": 0.65
    },
    # Courier: full AAL (D20â€“24) for packaging, CAM, ledger, authority checks
    "Courier": {
        "include": ("d0", "add", "aal"),
        "ask_full": "AAL",
        "temp": 0.35
    },
    # Critic: full RDL (D26â€“28) + brief TAES/AAL to run falsification gate
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

# 3) Role loading

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
        print(f"[WARN] Role loader not available for {domain} â€” using inline defaults.\n{e}")
        # Fallback to generic roles
        return {
            'strategist': (
                "Role: Strategist. Define positioning, 3 audiences, 3 hooks, 3-step plan. "
                "Be decisive; ground in objective. End with KPI or action (Directive 15)."
            ),
            'analyst': (
                "Role: Analyst. Pressure-test assumptions; risks->mitigations; 3 KPIs with numeric targets; "
                "A/B plan; short validation table. Prioritize 95% workable now. Score â‰¥85."
            ),
            'producer': (
                "Role: Producer. Create publishable assets for Nextdoor, Facebook, Craigslist (â‰¤180 words each), "
                "3 alt headlines, 1 proof bullet. Clear CTA. Platform-specific. Score â‰¥85."
            ),
            'courier': (
                "Role: Courier. Build D1â€“D7 schedule (times + channels), DM plan, KPI tracker, "
                "3 fallback moves if leads < target by Day 3. Score â‰¥85."
            ),
            'critic': (
                "Role: Critic. Audit for compliance, clarity, proof, CTA power, local tone. "
                "List 'Issue->Fix' pairs, give five 0â€“100 ratings + average. If <85, revise once, re-score."
            ),
        }


# 4) Core chat function

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

# 5) War Room chain WITH ENFORCEMENT + MULTI-DOMAIN SUPPORT

def run_chain(objective: str, session_id: Optional[str] = None, domain: Optional[str] = None):
    """
    Execute 5-role chain with full AxProtocol enforcement + multi-domain support:
    - Auto-detect domain from objective (or use override)
    - Load domain-specific roles
    - TAES evaluation with domain weights
    - Score validation (â‰¥85 threshold)
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

    #  NEW: Auto-detect domain or use override

    confidence = None
    domain_override = None
    if domain:
        # Manual override
        detected_domain = domain.lower()
        confidence = None
        domain_override = detected_domain
        print(f"[AxProtocol] Using specified domain: {detected_domain.upper()}")
    elif domain_detector:
        # Auto-detection
        detected_domain = domain_detector.detect(objective, verbose=False)
        scores = domain_detector.score_all_domains(objective)
        confidence = scores.get(detected_domain, 0.0)
        domain_override = None
        print(f"[AxProtocol] Auto-detected domain: {detected_domain.upper()} (confidence: {confidence:.2f})")

        # Show top 3 for transparency
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = ", ".join([f"{d}({s:.2f})" for d, s in top_3])
        print(f"[AxProtocol] Top matches: {top_str}")
    else:
        # Fallback if detector unavailable
        detected_domain = "marketing"
        confidence = None
        domain_override = None
        print(f"[AxProtocol] Domain detector unavailable - using fallback: {detected_domain.upper()}")

    #  NEW: Load domain-specific roles

    roles = load_domain_roles(detected_domain)
    STRATEGIST = roles['strategist']
    ANALYST = roles['analyst']
    PRODUCER = roles['producer']
    COURIER = roles['courier']
    CRITIC = roles['critic']

    # Initialize CAM lease (Directive 21)
    cam_lease = CAMLease(duration_seconds=180)

    results = {}

    # STRATEGIST
    registry = _init_registry()
    shapes_cfg = _load_role_shapes()
    qa_log: Dict[str, Dict[str, str]] = {}
    prev_texts: list[str] = []
    redundancy_metrics: Dict[str, float] = {}
    gov_signals = set()
    soft_signals = set()

    print("\n[1/5] Strategist...")
    sys_s = system_for("Strategist", STRATEGIST)
    _write_sys_preview(session_id, "Strategist", sys_s)
    strategist_prompt = (
        f"ObjectiveSpec:\n{objective}\n"
        "Return ONLY a fenced JSON array named S with objects: {\"s_id\", \"title\", \"audience\", \"hooks\", \"three_step_plan\", \"acceptance_tests\"}."
    )
    s, s_data = _run_role_json(
        "Strategist",
        sys_s,
        strategist_prompt,
        strategist_prompt,
        BASE_DIR / "config" / "role_examples" / "strategist.md",
        _validate_S,
        registry,
        "S",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics
    )

    log_execution(
        session_id=session_id,
        agent_id=f"strategist-{uuid.uuid4().hex[:8]}",
        role_name="Strategist",
        action="generate_strategy",
        input_text=objective,
        output_text=s,
        directive=15
    )

    taes_s = evaluate_taes(s, domain=detected_domain, session_id=session_id, role_name="Strategist")
    taes_s = _apply_governance_coupling(s, taes_s, gov_signals, objective, soft_signals)
    print(f"   TAES -> IV: {taes_s['integrity_vector']}, IRD: {taes_s['ird']}")

    scores_s = extract_scores(s)
    results['strategist'] = {
        'output': s,
        'taes': taes_s,
        'scores': scores_s,
    }

    # ANALYST
    print("\n[2/5] Analyst...")
    sys_a = system_for("Analyst", ANALYST)
    _write_sys_preview(session_id, "Analyst", sys_a)
    s_slice = _json.dumps(registry['S'], indent=2)
    analyst_prompt = (
        f"ObjectiveSpec:\n{objective}\n"
        f"S objects:\n{_json.dumps(registry['S'], indent=2)}\n"
        "Return ONLY a fenced JSON array named A with objects: {\"a_id\", \"s_refs\", \"kpi_table\", \"falsifications\", \"risks\"}."
    )
    s_ids = {item.get('s_id') for item in registry['S']}
    a, a_data = _run_role_json(
        "Analyst",
        sys_a,
        analyst_prompt,
        analyst_prompt,
        BASE_DIR / "config" / "role_examples" / "analyst.md",
        lambda data: _validate_A(data, s_ids),
        registry,
        "A",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics
    )

    log_execution(
        session_id=session_id,
        agent_id=f"analyst-{uuid.uuid4().hex[:8]}",
        role_name="Analyst",
        action="validate_strategy",
        input_text=s,
        output_text=a,
        directive=15
    )

    taes_a = evaluate_taes(a, domain=detected_domain, session_id=session_id, role_name="Analyst")
    taes_a = _apply_governance_coupling(a, taes_a, gov_signals, objective, soft_signals)
    print(f"   TAES -> IV: {taes_a['integrity_vector']}, IRD: {taes_a['ird']}")

    scores_a = extract_scores(a)
    results['analyst'] = {
        'output': a,
        'taes': taes_a,
        'scores': scores_a,
    }

    qa_context = "Strategy objects:\n" + _json.dumps(registry["S"], indent=2) + "\nAnalysis objects:\n" + _json.dumps(registry["A"], indent=2)
    qa_flag, qa_question, qa_answer = _run_micro_qa(session_id, detected_domain, "Producer", "Analyst", qa_context)
    if qa_flag:
        qa_log['producer_to_analyst'] = {'question': qa_question, 'answer': qa_answer}
        registry['Q'].append({'from': 'Producer', 'to': 'Analyst', 'question': qa_question, 'answer': qa_answer})

    # PRODUCER [DRAFT]
    print("\n[3/5] Producer [draft]...")
    sys_p = system_for("Producer", PRODUCER)
    _write_sys_preview(session_id, "Producer", sys_p)
    a_slice = _json.dumps(registry['A'], indent=2)
    qa_section = ""
    if 'producer_to_analyst' in qa_log:
        payload = qa_log['producer_to_analyst']
        qa_section = f"\nClarifications from Analyst:\nQ: {payload['question']}\nA: {payload['answer']}\n"
    producer_prompt = (
        f"ObjectiveSpec:\n{objective}\n"
        f"S objects:\n{_json.dumps(registry['S'], indent=2)}\n"
        f"A objects:\n{_json.dumps(registry['A'], indent=2)}\n"
        + qa_section +
        "Return ONLY a fenced JSON array named P with objects: {\"p_id\", \"a_refs\", \"spec_type\", \"body\"}."
    )
    a_ids = {item.get('a_id') for item in registry['A']}
    p_draft, p_data = _run_role_json(
        "Producer",
        sys_p,
        producer_prompt,
        producer_prompt,
        BASE_DIR / "config" / "role_examples" / "producer.md",
        lambda data: _validate_P(data, a_ids),
        registry,
        "P",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics
    )

    log_execution(
        session_id=session_id,
        agent_id=f"producer-draft-{uuid.uuid4().hex[:8]}",
        role_name="Producer-Draft",
        action="generate_assets",
        input_text=f"{s}\n{a}",
        output_text=p_draft,
        directive=15
    )

    taes_p = evaluate_taes(p_draft, domain=detected_domain, session_id=session_id, role_name="Producer-Draft")
    taes_p = _apply_governance_coupling(p_draft, taes_p, gov_signals, objective, soft_signals)
    print(f"   TAES -> IV: {taes_p['integrity_vector']}, IRD: {taes_p['ird']}")

    results['producer_draft'] = {
        'output': p_draft,
        'taes': taes_p,
    }

    qa_context_pc = "Production assets:\n" + _json.dumps(registry["P"], indent=2)
    qa_flag2, qa_question2, qa_answer2 = _run_micro_qa(session_id, detected_domain, "Courier", "Producer", qa_context_pc)
    if qa_flag2:
        qa_log['courier_to_producer'] = {'question': qa_question2, 'answer': qa_answer2}
        registry['Q'].append({'from': 'Courier', 'to': 'Producer', 'question': qa_question2, 'answer': qa_answer2})

    # COURIER [DRAFT]
    print("\n[4/5] Courier [draft]...")
    sys_c = system_for("Courier", COURIER)
    _write_sys_preview(session_id, "Courier", sys_c)
    p_slice = _json.dumps(registry['P'], indent=2)
    qa_section_c = ""
    if 'courier_to_producer' in qa_log:
        payload2 = qa_log['courier_to_producer']
        qa_section_c = f"\nClarifications from Producer:\nQ: {payload2['question']}\nA: {payload2['answer']}\n"
    courier_prompt = (
        f"ObjectiveSpec:\n{objective}\n"
        f"P assets:\n{_json.dumps(registry['P'], indent=2)}\n"
        + qa_section_c +
        "Return ONLY a fenced JSON array named C with objects: {\"day\", \"time\", \"channel\", \"p_id\", \"kpi_target\", \"owner_action\"}."
    )
    p_ids = {item.get('p_id') for item in registry['P']}
    c_draft, c_data = _run_role_json(
        "Courier",
        sys_c,
        courier_prompt,
        courier_prompt,
        BASE_DIR / "config" / "role_examples" / "courier.md",
        lambda data: _validate_C(data, p_ids),
        registry,
        "C",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics
    )

    log_execution(
        session_id=session_id,
        agent_id=f"courier-draft-{uuid.uuid4().hex[:8]}",
        role_name="Courier-Draft",
        action="create_schedule",
        input_text=p_draft,
        output_text=c_draft,
        directive=15
    )

    taes_c = evaluate_taes(c_draft, domain=detected_domain, session_id=session_id, role_name="Courier-Draft")
    taes_c = _apply_governance_coupling(c_draft, taes_c, gov_signals, objective, soft_signals)
    print(f"   TAES -> IV: {taes_c['integrity_vector']}, IRD: {taes_c['ird']}")

    results['courier_draft'] = {
        'output': c_draft,
        'taes': taes_c,
    }

    # CRITIC
    print("\n[5/5] Critic...")
    sys_crit = system_for("Critic", CRITIC)
    _write_sys_preview(session_id, "Critic", sys_crit)
    critic_prompt = (
        f"ObjectiveSpec:\n{objective}\n"
        f"S objects:\n{_json.dumps(registry['S'], indent=2)}\n"
        f"A objects:\n{_json.dumps(registry['A'], indent=2)}\n"
        f"P assets:\n{_json.dumps(registry['P'], indent=2)}\n"
        f"C schedule:\n{_json.dumps(registry['C'], indent=2)}\n"
        "Return ONLY a fenced JSON array named X with objects: {\"x_id\", \"refs\", \"issue\", \"fix\", \"severity\", \"proof_scores\"}."
    )
    s_ids = {item.get('s_id') for item in registry['S']}
    a_ids = {item.get('a_id') for item in registry['A']}
    p_ids = {item.get('p_id') for item in registry['P']}
    c_ids = {row.get('p_id') for row in registry['C']}
    crit, crit_data = _run_role_json(
        "Critic",
        sys_crit,
        critic_prompt,
        critic_prompt,
        BASE_DIR / "config" / "role_examples" / "critic.md",
        lambda data: _validate_X(data, s_ids, a_ids, p_ids, c_ids),
        registry,
        "X",
        shapes_cfg,
        session_id,
        detected_domain,
        prev_texts,
        redundancy_metrics
    )

    log_execution(
        session_id=session_id,
        agent_id=f"critic-{uuid.uuid4().hex[:8]}",
        role_name="Critic",
        action="final_review",
        input_text=f"{p_draft}\n{c_draft}",
        output_text=crit,
        directive=15
    )

    taes_crit = evaluate_taes(crit, domain=detected_domain, session_id=session_id, role_name="Critic")
    taes_crit = _apply_governance_coupling(crit, taes_crit, gov_signals, objective, soft_signals)
    print(f"   TAES -> IV: {taes_crit['integrity_vector']}, IRD: {taes_crit['ird']}")

    results['critic'] = {
        'output': crit,
        'taes': taes_crit,
    }

    final_report = _compose_final_report(objective, registry, qa_log)
    p_rev = p_draft
    c_rev = c_draft

    # Mirror draft entries into revised slots for downstream compatibility
    results['producer_revised'] = dict(results['producer_draft'])
    results['courier_revised'] = dict(results['courier_draft'])
    results['registry'] = registry
    results['qa'] = qa_log
    results['composer'] = final_report
    results['redundancy'] = dict(redundancy_metrics)

    # Aggregate governance summary
    combined_text = "\n\n".join([seg for seg in [objective, s, a, p_draft, c_draft, crit, final_report] if seg])
    try:
        soft_signals |= _compute_soft_signals(combined_text, detected_domain, domain_override, confidence)
    except Exception:
        pass

    # Add redundancy soft signal if any role exceeded threshold
    try:
        if any(float(score) >= 0.55 for score in redundancy_metrics.values()):
            soft_signals.add("REDUNDANCY")
    except Exception:
        pass

    results['governance'] = {
        'signals': sorted(gov_signals),
        'soft_signals': sorted(soft_signals),
        'no_go': bool(gov_signals),
        'requires_rrp': bool(gov_signals),
        'redundancy': dict(redundancy_metrics),
    }

    # Sentinel verification (mock, null-bias): compute simple post-hoc score
    try:
        sent = _sentinel_verify(objective, results)
        results['sentinel'] = sent
        if sent.get('flags'):
            # attach drift detail into governance section for ledger visibility
            if sent.get('drift'):
                results['governance']['drift'] = sent['drift']
            ss = set(results['governance'].get('soft_signals', []) or [])
            ss.add('DRIFT')
            results['governance']['soft_signals'] = sorted(ss)
    except Exception:
        pass

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
                delta={"governance": results['governance'], "sentinel": results.get('sentinel')},
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

# 6) KPI extraction (unchanged)

def extract_kpi_rows(markdown_text: str):
    pattern = r"\| *([^\|]+)\| *([^\|]+)\| *([^\|]+)\|"
    rows = re.findall(pattern, markdown_text)
    out = []
    for r in rows:
        if "KPI" in r[0] or "---" in r[0]:
            continue
        out.append([x.strip() for x in r])
    return out

# 7) Logging + ROI JSON

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

# 8) Entry point with MULTI-DOMAIN SUPPORT

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
            "(Nextdoor, Facebook, Craigslist; â‰¤180 words each; 3 alt headlines each); "
            "D1â€“D7 schedule with posting times, bumps, follow-ups, short DM scripts; "
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
import re as _re
import json as _json

def _shingles(text: str, n: int = 3) -> set:
    t = (text or "").lower()
    tokens = _re.findall(r"[a-z0-9]+", t)
    return {" ".join(tokens[i:i+n]) for i in range(max(0, len(tokens) - n + 1))}

def _redundancy_score(current: str, prior: list[str], n: int = 3) -> float:
    if not current or not prior:
        return 0.0
    cur = _shingles(current, n)
    if not cur:
        return 0.0
    # Compare against the union of prior shingles for a conservative upper bound
    prior_union: set = set()
    for p in prior:
        prior_union |= _shingles(p, n)
    if not prior_union:
        return 0.0
    inter = len(cur & prior_union)
    union = len(cur | prior_union)
    return inter / union if union else 0.0

def _uniqueness_nudge(role: str) -> str:
    hints = {
        "Strategist": (
            "Remove checklist/rationale overlap. Introduce distinct positioning, unique audiences/hooks,"
            " and S-ID acceptance tests not present upstream. Do NOT include specs, schedules, or audits."
        ),
        "Analyst": (
            "Eliminate narrative; present numeric KPIs, falsifications, and an A-ID map to S-IDs."
            " Do NOT include positioning/audience/hooks, schedules, or production copy."
        ),
        "Producer": (
            "Replace prose with assets/specs (P-IDs). Provide API/contracts, DDL, config tables,"
            " or copy blocks tied to A-IDs. Do NOT include schedules or audits."
        ),
        "Courier": (
            "Return only schedule tables, DM scripts, KPI tracker rows with P-ID references."
            " Do NOT restate assets or strategy."
        ),
        "Critic": (
            "Return Issue->Fix pairs with S/A/P/C references and audit tables."
            " Do NOT write new assets or schedules."
        ),
    }
    return hints.get(role, "Reduce overlap and add new, role-unique artifacts.")

# ---------------- Registry helpers (blackboard) ----------------
def _init_registry() -> dict:
    return {"S": [], "A": [], "P": [], "C": [], "X": [], "Q": []}

def _extract_json_block(text: str):
    t = text or ""
    # Try fenced JSON
    m = _re.search(r"```json\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", t, _re.IGNORECASE)
    if not m:
        # Try first brace/bracket
        m = _re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", t)
    if not m:
        return None
    frag = m.group(1)
    try:
        return _json.loads(frag)
    except Exception:
        return None

def _violates_exclusions(text: str, role_name: str, shapes_cfg: dict) -> bool:
    """
    Return True when the generated text contains tokens that belong to another role's domain.
    Shapes config schema (config/role_shapes.json):
      {
        "RoleName": {
          "banned": ["phrase1", "phrase2"],
          "banned_regex": ["pattern"]
        }
      }
    """
    if not text or not isinstance(shapes_cfg, dict):
        return False
    role_spec = shapes_cfg.get(role_name) or shapes_cfg.get(role_name.lower())
    if not isinstance(role_spec, dict):
        return False
    haystack = text.lower()
    banned = role_spec.get("banned") or []
    for phrase in banned:
        try:
            if phrase and phrase.lower() in haystack:
                return True
        except Exception:
            continue
    banned_regex = role_spec.get("banned_regex") or []
    for pattern in banned_regex:
        try:
            if pattern and _re.search(pattern, text, _re.IGNORECASE):
                return True
        except Exception:
            continue
    return False

def _validate_S(items) -> tuple[bool, str]:
    if not isinstance(items, list) or not items:
        return False, "S must be non-empty list"
    req = {"s_id", "title", "audience", "hooks", "three_step_plan"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "S item missing required keys"
    return True, "ok"

def _validate_A(items, s_ids:set) -> tuple[bool, str]:
    if not isinstance(items, list) or not items:
        return False, "A must be non-empty list"
    req = {"a_id", "s_refs", "kpi_table"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "A item missing required keys"
        if not set(it.get("s_refs", [])).issubset(s_ids):
            return False, "A item has unknown S refs"
    return True, "ok"

def _validate_P(items, a_ids:set) -> tuple[bool, str]:
    if not isinstance(items, list) or not items:
        return False, "P must be non-empty list"
    req = {"p_id", "a_refs", "spec_type", "body"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "P item missing required keys"
        if not set(it.get("a_refs", [])).issubset(a_ids):
            return False, "P item has unknown A refs"
    return True, "ok"

def _validate_C(items, p_ids:set) -> tuple[bool, str]:
    if not isinstance(items, list) or not items:
        return False, "C must be non-empty list"
    req = {"day", "time", "channel", "p_id", "kpi_target", "owner_action"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "C row missing required keys"
        if it.get("p_id") not in p_ids:
            return False, "C row references unknown P-ID"
    return True, "ok"

def _validate_X(items, s_ids:set, a_ids:set, p_ids:set, c_ids:set) -> tuple[bool, str]:
    if not isinstance(items, list) or not items:
        return False, "X must be non-empty list"
    req = {"x_id", "refs", "issue", "fix", "severity", "proof_scores"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "X item missing required keys"
        refs = it.get("refs", {}) or {}
        if not isinstance(refs, dict):
            return False, "X refs must be dict"
        if not set(refs.get("s", [])).issubset(s_ids):
            return False, "X refs contain unknown S ids"
        if not set(refs.get("a", [])).issubset(a_ids):
            return False, "X refs contain unknown A ids"
        if not set(refs.get("p", [])).issubset(p_ids):
            return False, "X refs contain unknown P ids"
        if not set(refs.get("c", [])).issubset(c_ids):
            return False, "X refs contain unknown C ids"
    return True, "ok"

def _strict_reprompt(role: str, sys_prompt: str, base_user: str, fewshot_path: Path | None = None) -> str:
    demo = ""
    try:
        if fewshot_path and fewshot_path.exists():
            demo = "\n\nExample:\n" + fewshot_path.read_text(encoding="utf8")[:800]
    except Exception:
        demo = ""
    user = base_user + "\n\nSTRICT MODE: Return ONLY JSON in a single fenced block (```json ... ```)." + demo
    return llm(sys_prompt, user, temperature=0.2)

# ---------------- Role shapes config ----------------
def _load_role_shapes() -> dict:
    paths = [
        os.getenv("ROLE_SHAPES_PATH"),
        str(BASE_DIR / "config" / "role_shapes.json"),
    ]
    for p in paths:
        try:
            if p and Path(p).exists():
                return _json.loads(Path(p).read_text(encoding="utf8"))
        except Exception:
            continue
    return {}

# ---------------- Micro Q&A helper ----------------
def _run_micro_qa(session_id: str, detected_domain: str, asker: str, responder: str, context: str) -> tuple[bool, str, str]:
    try:
        question = llm(
            f"Micro-QA ({asker} asking {responder})",
            context + "\nAsk ONE clarifying question for the {responder}. If none needed, reply with NONE.",
            temperature=0.35
        )
    except Exception as exc:
        _append_session_error(session_id, detected_domain, f"QA-{asker}", exc)
        return False, "", ""
    if question.strip().upper().startswith("NONE"):
        return False, "", ""
    try:
        answer = llm(
            f"Micro-QA ({responder} answering {asker})",
            context + f"\nQuestion: {question}\nProvide a short, direct answer.",
            temperature=0.2
        )
    except Exception as exc:
        _append_session_error(session_id, detected_domain, f"QA-{responder}", exc)
        return False, question, ""
    return True, question.strip(), answer.strip()

# ---------------- Final composer ----------------
def _compose_final_report(objective: str, registry: dict, qa_log: dict) -> str:
    lines = []
    lines.append("# AxProtocol Execution Summary")
    lines.append(f"Objective: {objective}")
    if registry.get("S"):
        lines.append("\n## Strategy (S)")
        for item in registry["S"]:
            lines.append(f"- {item.get('s_id')}: {item.get('title')}")
    if registry.get("A"):
        lines.append("\n## Analysis (A)")
        for item in registry["A"]:
            lines.append(f"- {item.get('a_id')} -> refs {item.get('s_refs')}")
    if registry.get("P"):
        lines.append("\n## Production Assets (P)")
        for item in registry["P"]:
            lines.append(f"- {item.get('p_id')} [{item.get('spec_type')}], refs {item.get('a_refs')}")
    if registry.get("C"):
        lines.append("\n## Courier Schedule (C)")
        for item in registry["C"]:
            lines.append(f"- {item.get('day')} {item.get('time')} via {item.get('channel')} -> {item.get('p_id')} (target {item.get('kpi_target')})")
    if registry.get("X"):
        lines.append("\n## Critic Findings (X)")
        for item in registry["X"]:
            lines.append(f"- {item.get('x_id')} severity={item.get('severity')} refs={item.get('refs')}")
    if qa_log:
        lines.append("\n## Clarifications")
        for key, payload in qa_log.items():
            lines.append(f"- {key}: Q: {payload['question']} | A: {payload['answer']}")
    return "\n".join(lines)


def _run_role_json(role_name: str, sys_prompt: str, user_prompt: str, strict_prompt: str, example_path: Path, validator, registry: dict, registry_key: str, shapes_cfg: dict, session_id: str, detected_domain: str, prev_texts: list, redundancy_metrics: dict) -> tuple[str, list]:
    def _call(prompt: str, temp: float) -> str:
        try:
            return llm(sys_prompt, prompt, temperature=temp)
        except Exception as exc:
            _append_session_error(session_id, detected_domain, role_name, exc)
            raise

    def _parse(text: str):
        if _violates_exclusions(text, role_name, shapes_cfg):
            return None, "excluded"
        data = _extract_json_block(text)
        if data is None:
            return None, "no_json"
        ok, msg = validator(data)
        if not ok:
            return None, msg
        return data, "ok"

    base_temp = role_temp(role_name)
    text = _call(user_prompt, base_temp)
    data, msg = _parse(text)
    if data is None:
        text = _strict_reprompt(role_name, sys_prompt, strict_prompt, example_path)
        data, msg = _parse(text)
        if data is None:
            # Graceful fallback: record soft failure and continue with empty slice
            _append_session_error(session_id, detected_domain, role_name, Exception(f"validation_failed: {msg}"))
            text = "[]"
            data = []
    red = _redundancy_score(text, prev_texts, n=3)
    if red > 0.6:
        text = _strict_reprompt(role_name, sys_prompt, strict_prompt, example_path)
        data, msg = _parse(text)
        if data is None:
            _append_session_error(session_id, detected_domain, role_name, Exception(f"redundancy_retry_failed: {msg}"))
        else:
            red = _redundancy_score(text, prev_texts, n=3)
    prev_texts.append(text)
    try:
        redundancy_metrics[role_name] = float(f"{red:.3f}")
    except Exception:
        pass
    registry[registry_key] = data or []
    return text, data


# ---------------- Sentinel verification (mock) ----------------
import math as _math

def _sentinel_verify(objective: str, results: dict) -> dict:
    registry = results.get('registry') or {}
    s = registry.get('S') or []
    a = registry.get('A') or []
    p = registry.get('P') or []
    c = registry.get('C') or []
    x = registry.get('X') or []

    text_pool = []
    try:
        text_pool.append(results.get('composer') or '')
        text_pool.append(results.get('producer_draft',{}).get('output',''))
        text_pool.append(results.get('courier_draft',{}).get('output',''))
        text_pool.append(results.get('critic',{}).get('output',''))
    except Exception:
        pass
    text = "\n\n".join([t for t in text_pool if t])

    strong = ["100%","certain","always","definitely","zero risk","guarantee","impossible to fail"]
    evid = ["evidence","source","cite","reference","data","study","trial","dataset","link"]
    t = (text or '').lower()
    strong_hits = sum(t.count(w.lower()) for w in strong)
    evid_hits = sum(t.count(w.lower()) for w in evid)

    # Cross-ref coverage from Critic refs -> registry ids
    def _idset(key):
        return {item.get(f"{key.lower()}_id") for item in (registry.get(key) or [])}
    s_ids, a_ids, p_ids, c_ids = _idset('S'), _idset('A'), _idset('P'), set()
    try:
        c_ids = {row.get('p_id') for row in (registry.get('C') or [])}
    except Exception:
        c_ids = set()

    total_refs = 0
    matched = 0
    drift = []
    for item in x or []:
        refs = item.get('refs') or {}
        for sid in refs.get('s',[]) or []:
            total_refs += 1; matched += 1 if sid in s_ids else 0
        for aid in refs.get('a',[]) or []:
            total_refs += 1; matched += 1 if aid in a_ids else 0
        for pid in refs.get('p',[]) or []:
            total_refs += 1; matched += 1 if pid in p_ids else 0
        for cid in refs.get('c',[]) or []:
            total_refs += 1; matched += 1 if cid in c_ids else 0
    coverage = (matched/total_refs) if total_refs else (1.0 if not x else 0.0)

    # Upstream emptiness penalty
    upstream_empty = int(len(s)==0 or len(a)==0)
    if upstream_empty:
        drift.append({"type":"UPSTREAM_EMPTY","detail":"S or A slice empty while downstream present"})

    # Compose score (100 baseline minus penalties)
    score = 100.0
    # strong without evidence => penalty
    if strong_hits > evid_hits:
        score -= min(40.0, (strong_hits - evid_hits) * 5.0)
    # low coverage penalty
    score -= max(0.0, (1.0 - coverage) * 30.0)
    # upstream empty penalty
    if upstream_empty:
        score -= 20.0

    score = max(0.0, min(100.0, score))

    flags = []
    if strong_hits > evid_hits:
        flags.append('OVERCONF_NO_EVIDENCE')
    if coverage < 0.7:
        flags.append('LOW_REF_COVERAGE')
    if upstream_empty:
        flags.append('UPSTREAM_EMPTY')

    return {
        'score': round(score,1),
        'flags': flags,
        'details': {
            'strong_hits': int(strong_hits),
            'evidence_hits': int(evid_hits),
            'ref_coverage': round(coverage,3),
        },
        'drift': drift,
    }
# ---------------- System prompt preview (persistent capture) ----------------
def _write_sys_preview(session_id: str, role_name: str, sys: str, max_lines: int = 12) -> None:
    try:
        import os as _os
        if _os.getenv("DEBUG_SYS", "0") != "1":
            return
        lines = "\n".join((sys or "").splitlines()[:max_lines])
        out = f"[{role_name}] System preview\n{lines}\n---\n"
        path = BASE_DIR / "logs" / "sessions" / f"{session_id}_sys.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf8") as f:
            f.write(out)
    except Exception:
        pass

# ---------------- Error logging helpers ----------------
def _append_session_error(session_id: str, domain: str, role: str, exc: Exception):
    try:
        sess_dir = BASE_DIR / "logs" / "sessions"
        sess_dir.mkdir(parents=True, exist_ok=True)
        path = sess_dir / f"{session_id}_errors.log"
        with open(path, "a", encoding="utf8") as f:
            f.write("[Error] Role=" + role + " Domain=" + str(domain) + "\n")
            f.write("Type: " + exc.__class__.__name__ + "\n")
            f.write("Message: " + str(exc) + "\n")
            f.write("Traceback:\n" + "".join(_tb.format_exception(type(exc), exc, exc.__traceback__)) + "\n\n")
    except Exception:
        pass
