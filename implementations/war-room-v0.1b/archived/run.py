"""
AxProtocol War Room — Multi-Domain Orchestrator v2.3
====================================================
Five-role reasoning chain with intelligent domain detection and full enforcement.

MULTI-DOMAIN SUPPORT:
- Auto-detects domain from objective (marketing, ops, technical, creative, etc.)
- Loads domain-specific role definitions
- Applies domain-specific TAES weights
- Supports manual domain override via DOMAIN env var

Usage:
    python run.py "Your objective"                    # Auto-detect domain
    DOMAIN=technical python run.py "Your objective"   # Force specific domain
    DOMAIN=ops TIER=PREP python run.py "Your objective"
"""

import os
import sys
import re
import csv
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Import AxProtocol enforcement modules
try:
    from taes_evaluation import evaluate_taes, check_cognitive_disalignment
    from score_validator import extract_scores, validate_scores, format_score_block
    from auth import CAMLease, validate_op_token
    from ledger import log_execution, get_last_n_entries, verify_hash_chain
    ENFORCEMENT_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Enforcement modules not available: {e}")
    print("⚠️  Running in basic mode without TAES/ledger/auth")
    ENFORCEMENT_MODULES_AVAILABLE = False

# Import domain detection
try:
    from domain_detector import DomainDetector
    DOMAIN_DETECTION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Domain detection not available: {e}")
    print("⚠️  Falling back to manual domain selection")
    DOMAIN_DETECTION_AVAILABLE = False

# ────────────────────────────────────────────────────────────────────────────
# Setup & Configuration
# ────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
PROTOCOL_DIR = BASE_DIR.parent.parent / "protocol"

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    raise SystemExit(f"[ERROR] OpenAI initialization failed: {e}\n"
                    f"       Ensure OPENAI_API_KEY is set in .env file")

# ────────────────────────────────────────────────────────────────────────────
# Tiered Model Selection
# ────────────────────────────────────────────────────────────────────────────

TIER = os.getenv("TIER", "DEV").upper()
MODEL_MAP = {
    "DEV": os.getenv("MODEL_DEV", "gpt-4o-mini"),
    "PREP": os.getenv("MODEL_PREP", "gpt-4o-turbo"),
    "CLIENT": os.getenv("MODEL_CLIENT", "gpt-4o"),
}
MODEL = MODEL_MAP.get(TIER, "gpt-4o-mini")

# ────────────────────────────────────────────────────────────────────────────
# Domain Detection & Configuration
# ────────────────────────────────────────────────────────────────────────────

def detect_and_configure_domain(objective: str) -> str:
    """
    Detect domain from objective or use manual override.

    Priority:
        1. DOMAIN environment variable (manual override)
        2. Auto-detection from objective text
        3. Fallback to 'marketing'

    Args:
        objective: The campaign/project objective

    Returns:
        Domain name (e.g., 'marketing', 'technical', 'ops')
    """
    # Check for manual override
    manual_domain = os.getenv("DOMAIN", "").lower()

    if manual_domain:
        print(f"[AxProtocol] Domain: {manual_domain.upper()} (manual override)")
        return manual_domain

    # Auto-detect if available
    if DOMAIN_DETECTION_AVAILABLE:
        detector = DomainDetector()
        detected = detector.detect(objective, verbose=True)
        return detected

    # Fallback
    print(f"[AxProtocol] Domain: MARKETING (fallback - detection unavailable)")
    return "marketing"

# ────────────────────────────────────────────────────────────────────────────
# Protocol Directive Loading
# ────────────────────────────────────────────────────────────────────────────

def _read_text(path: Path) -> str:
    """Read text file with error handling"""
    if not path.exists():
        print(f"⚠️  Protocol file missing: {path}")
        return f"[Missing: {path.name}]"
    try:
        return path.read_text(encoding="utf8")
    except Exception as e:
        print(f"⚠️  Error reading {path.name}: {e}")
        return f"[Error reading: {path.name}]"

def load_directives() -> Dict[str, str]:
    """Load all AxProtocol directive files"""
    files = {
        "D0":   PROTOCOL_DIR / "v0-change-control.txt",
        "CORE": PROTOCOL_DIR / "v2.1a-core-directives.txt",
        "ADD":  PROTOCOL_DIR / "v2.1b-war-room-integration.txt",
        "AAL":  PROTOCOL_DIR / "v2.1c-authority-layer.txt",
        "TAES": PROTOCOL_DIR / "v2.2-taes-evaluation.txt",
        "RDL":  PROTOCOL_DIR / "v2.3-red-team-layer.txt",
    }

    loaded = {k: _read_text(v) for k, v in files.items()}

    missing = [k for k, v in loaded.items() if "[Missing:" in v or "[Error" in v]
    if not missing:
        print(f"✅ All protocol directives loaded")
    else:
        print(f"⚠️  Missing protocols: {', '.join(missing)}")

    return loaded

DIRECTIVES = load_directives()

# Directive briefings for system prompts
BRIEFINGS = {
    "core":  "Enforce AxProtocol Core (Directives 1-14): truth discipline, logic integrity, contradiction detection.",
    "add":   "Apply War Room (Directives 15-19): objective grounding, self-scoring ≥85/100, clean handoffs.",
    "aal":   "Respect Authority Layer (Directives 20-24): Operator supremacy, CAM lease, immutable ledger.",
    "taes":  "Use TAES (Directives 25-25c): balance Logical/Practical/Probable axes; trigger RRP when IRD > 0.5.",
    "rdl":   "Apply Red-Team (Directives 26-28): falsification MAS, CV detection, structured dissent.",
}

def compose_system(role_prompt: str, include=("core","add","aal","taes","rdl")) -> str:
    """Compose system prompt by combining role definition with directive briefings"""
    buf = [BRIEFINGS[k] for k in include if k in BRIEFINGS]
    if role_prompt:
        buf.insert(0, role_prompt.strip())
    return "\n\n".join(buf)

# ────────────────────────────────────────────────────────────────────────────
# Role Loading (Domain-Aware)
# ────────────────────────────────────────────────────────────────────────────

def load_domain_roles(domain: str, build_type: str = "stable") -> Dict[str, str]:
    """
    Load roles for specified domain.

    Args:
        domain: Domain name (marketing, ops, technical, etc.)
        build_type: Build type (stable, experimental, dev)

    Returns:
        Dictionary with role names as keys and role content as values
    """
    try:
        from load_roles import load_roles_by_pattern
        roles_dict = load_roles_by_pattern(build_type, domain)

        # Extract just the content
        return {
            "strategist": roles_dict["strategist"]["content"],
            "analyst": roles_dict["analyst"]["content"],
            "producer": roles_dict["producer"]["content"],
            "courier": roles_dict["courier"]["content"],
            "critic": roles_dict["critic"]["content"]
        }
    except Exception as e:
        print(f"⚠️  Could not load roles for domain '{domain}': {e}")
        print(f"⚠️  Using generic fallback roles")
        return get_generic_roles(domain)

def get_generic_roles(domain: str) -> Dict[str, str]:
    """Fallback generic roles when domain-specific roles unavailable"""

    domain_contexts = {
        "marketing": "campaign assets and lead generation",
        "ops": "process documentation and workflow design",
        "technical": "system architecture and code implementation",
        "creative": "original content and brand development",
        "education": "curriculum and learning materials",
        "product": "product specifications and user stories",
        "strategy": "strategic plans and business analysis",
        "research": "research design and data analysis"
    }

    context = domain_contexts.get(domain, "deliverables")

    return {
        "strategist": f"Role: Strategist. Define high-level strategy for {context}. Be decisive, ground in objective, include success criteria.",
        "analyst": f"Role: Analyst. Validate assumptions, identify risks for {context}. Provide measurable metrics, A/B alternatives, practical solutions.",
        "producer": f"Role: Producer. Create high-quality {context}. Focus on clarity, completeness, professional execution.",
        "courier": f"Role: Courier. Design implementation plan for {context}. Include timeline, dependencies, contingencies.",
        "critic": f"Role: Critic. Audit {context} for quality, completeness, alignment. Identify issues, provide fixes, rate readiness."
    }

# ────────────────────────────────────────────────────────────────────────────
# Core LLM Function
# ────────────────────────────────────────────────────────────────────────────

def llm(system_text: str, user_text: str, temperature=0.4, max_tokens=1600) -> str:
    """Call OpenAI API with system and user messages"""
    try:
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
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return f"[ERROR: LLM call failed - {str(e)}]"

# ────────────────────────────────────────────────────────────────────────────
# War Room Five-Role Chain (Domain-Aware)
# ────────────────────────────────────────────────────────────────────────────

def run_chain(objective: str, domain: str, roles: Dict[str, str],
              session_id: Optional[str] = None) -> tuple:
    """
    Execute five-role chain with domain-specific configuration.

    Args:
        objective: Campaign/project objective
        domain: Domain name (marketing, ops, technical, etc.)
        roles: Dictionary of role definitions
        session_id: Optional session identifier

    Returns:
        Tuple of (strategist, analyst, producer_rev, courier_rev, critic, results_dict)
    """

    if not session_id:
        session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*70}")
    print(f"[AxProtocol] Session: {session_id}")
    print(f"[AxProtocol] Domain: {domain.upper()}")
    print(f"[AxProtocol] Model: {MODEL} ({TIER})")
    print(f"[AxProtocol] Enforcement: {'ENABLED' if ENFORCEMENT_MODULES_AVAILABLE else 'DISABLED'}")
    print(f"{'='*70}")

    if ENFORCEMENT_MODULES_AVAILABLE:
        cam_lease = CAMLease(duration_seconds=180)

    results = {}

    # ────────────────────────────────────────────────────────────────────────
    # STRATEGIST
    # ────────────────────────────────────────────────────────────────────────
    print("\n[1/5] Strategist...")
    sys_s = compose_system(roles["strategist"])
    s = llm(sys_s, f"Objective:\n{objective}\n\nReturn: positioning, target audiences, hooks, execution plan.")

    if ENFORCEMENT_MODULES_AVAILABLE:
        log_execution(session_id=session_id, agent_id=f"strategist-{uuid.uuid4().hex[:8]}",
                     role_name="Strategist", action="generate_strategy",
                     input_text=objective, output_text=s, directive=15)

        taes_s = evaluate_taes(s, domain=domain, session_id=session_id, role_name="Strategist")
        print(f"   TAES → IV: {taes_s['integrity_vector']:.2f}, IRD: {taes_s['ird']:.3f}")

        scores_s = extract_scores(s)
        if scores_s:
            validation_s = validate_scores(scores_s, threshold=85)
            print(f"   Scores → {validation_s['reason']}")
        else:
            validation_s = None
    else:
        taes_s = scores_s = validation_s = None

    results['strategist'] = {'output': s, 'taes': taes_s, 'scores': scores_s, 'validation': validation_s}

    if ENFORCEMENT_MODULES_AVAILABLE and cam_lease.is_expired():
        print("   ⚠️  CAM lease expired - requesting OP_AUTH extension")

    # ────────────────────────────────────────────────────────────────────────
    # ANALYST
    # ────────────────────────────────────────────────────────────────────────
    print("\n[2/5] Analyst...")
    sys_a = compose_system(roles["analyst"])
    a = llm(sys_a, f"Objective:\n{objective}\n\nStrategist:\n{s}\n\n"
                   "Return: assumptions/risks/mitigations, measurable KPIs, A/B plan, validation.")

    if ENFORCEMENT_MODULES_AVAILABLE:
        log_execution(session_id=session_id, agent_id=f"analyst-{uuid.uuid4().hex[:8]}",
                     role_name="Analyst", action="analyze_strategy",
                     input_text=s, output_text=a, directive=16)

        taes_a = evaluate_taes(a, domain=domain, session_id=session_id, role_name="Analyst")
        print(f"   TAES → IV: {taes_a['integrity_vector']:.2f}, IRD: {taes_a['ird']:.3f}")

        scores_a = extract_scores(a)
        validation_a = validate_scores(scores_a, threshold=85) if scores_a else None
        if validation_a:
            print(f"   Scores → {validation_a['reason']}")
    else:
        taes_a = scores_a = validation_a = None

    results['analyst'] = {'output': a, 'taes': taes_a, 'scores': scores_a, 'validation': validation_a}

    # ────────────────────────────────────────────────────────────────────────
    # PRODUCER (draft)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[3/5] Producer (draft)...")
    sys_p = compose_system(roles["producer"])
    p_draft = llm(sys_p, f"Objective:\n{objective}\n\nStrategist:\n{s}\n\nAnalyst:\n{a}\n\n"
                         "Return: high-quality deliverables per domain requirements.")

    if ENFORCEMENT_MODULES_AVAILABLE:
        log_execution(session_id=session_id, agent_id=f"producer-{uuid.uuid4().hex[:8]}",
                     role_name="Producer", action="create_assets_draft",
                     input_text=f"{s}\n\n{a}", output_text=p_draft, directive=19)

        taes_p_draft = evaluate_taes(p_draft, domain=domain, session_id=session_id, role_name="Producer-Draft")
        print(f"   TAES → IV: {taes_p_draft['integrity_vector']:.2f}, IRD: {taes_p_draft['ird']:.3f}")
    else:
        taes_p_draft = None

    # ────────────────────────────────────────────────────────────────────────
    # COURIER (draft)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[4/5] Courier (draft)...")
    sys_c = compose_system(roles["courier"])
    c_draft = llm(sys_c, f"Objective:\n{objective}\n\nStrategist:\n{s}\n\nAnalyst:\n{a}\n\nProducer [Draft]:\n{p_draft}\n\n"
                         "Return: implementation plan with timeline, dependencies, contingencies.")

    if ENFORCEMENT_MODULES_AVAILABLE:
        log_execution(session_id=session_id, agent_id=f"courier-{uuid.uuid4().hex[:8]}",
                     role_name="Courier", action="build_schedule_draft",
                     input_text=p_draft, output_text=c_draft, directive=17)

        taes_c_draft = evaluate_taes(c_draft, domain=domain, session_id=session_id, role_name="Courier-Draft")
        print(f"   TAES → IV: {taes_c_draft['integrity_vector']:.2f}, IRD: {taes_c_draft['ird']:.3f}")
    else:
        taes_c_draft = None

    # ────────────────────────────────────────────────────────────────────────
    # CRITIC
    # ────────────────────────────────────────────────────────────────────────
    print("\n[5/5] Critic...")
    sys_crit = compose_system(roles["critic"])
    crit = llm(sys_crit, f"Evaluate Producer [Draft] and Courier [Draft].\n\n"
                         f"Producer [Draft]:\n{p_draft}\n\n"
                         f"Courier [Draft]:\n{c_draft}\n\n"
                         "Return: Issue→Fix pairs, ratings, readiness assessment.")

    if ENFORCEMENT_MODULES_AVAILABLE:
        log_execution(session_id=session_id, agent_id=f"critic-{uuid.uuid4().hex[:8]}",
                     role_name="Critic", action="audit_outputs",
                     input_text=f"{p_draft}\n\n{c_draft}", output_text=crit, directive=15)

        taes_crit = evaluate_taes(crit, domain=domain, session_id=session_id, role_name="Critic")
        print(f"   TAES → IV: {taes_crit['integrity_vector']:.2f}, IRD: {taes_crit['ird']:.3f}")

        scores_crit = extract_scores(crit)
        validation_crit = validate_scores(scores_crit, threshold=85) if scores_crit else None
        if validation_crit:
            print(f"   Scores → {validation_crit['reason']}")
    else:
        taes_crit = scores_crit = validation_crit = None

    # ────────────────────────────────────────────────────────────────────────
    # PRODUCER (revised)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[Revision] Producer...")
    p_rev = llm(sys_p, f"Apply Critic's fixes to Producer [Draft].\n\n"
                       f"Critic feedback:\n{crit}\n\nProducer [Draft]:\n{p_draft}\n\n"
                       "Return: [Revised] deliverables incorporating all fixes.")

    if ENFORCEMENT_MODULES_AVAILABLE:
        log_execution(session_id=session_id, agent_id=f"producer-rev-{uuid.uuid4().hex[:8]}",
                     role_name="Producer-Revised", action="revise_assets",
                     input_text=crit, output_text=p_rev, directive=15)

        taes_p_rev = evaluate_taes(p_rev, domain=domain, session_id=session_id, role_name="Producer-Revised")
        print(f"   TAES → IV: {taes_p_rev['integrity_vector']:.2f}, IRD: {taes_p_rev['ird']:.3f}")

        if taes_p_rev['requires_rrp']:
            print(f"   ⚠️  IRD > 0.5 detected - Reality Reconciliation Pass recommended")
    else:
        taes_p_rev = None

    results['producer_revised'] = {'output': p_rev, 'taes': taes_p_rev}

    # ────────────────────────────────────────────────────────────────────────
    # COURIER (revised)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[Revision] Courier...")
    c_rev = llm(sys_c, f"Adjust per Critic feedback.\n\n"
                       f"Critic:\n{crit}\n\nCourier [Draft]:\n{c_draft}\n\n"
                       "Return: [Revised] implementation plan.")

    if ENFORCEMENT_MODULES_AVAILABLE:
        log_execution(session_id=session_id, agent_id=f"courier-rev-{uuid.uuid4().hex[:8]}",
                     role_name="Courier-Revised", action="revise_schedule",
                     input_text=crit, output_text=c_rev, directive=15)

        taes_c_rev = evaluate_taes(c_rev, domain=domain, session_id=session_id, role_name="Courier-Revised")
        print(f"   TAES → IV: {taes_c_rev['integrity_vector']:.2f}, IRD: {taes_c_rev['ird']:.3f}")

        if taes_c_rev['requires_rrp']:
            print(f"   ⚠️  IRD > 0.5 detected - Reality Reconciliation Pass recommended")
    else:
        taes_c_rev = None

    results['courier_revised'] = {'output': c_rev, 'taes': taes_c_rev}

    # ────────────────────────────────────────────────────────────────────────
    # Final Enforcement Checks
    # ────────────────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("[AxProtocol] Chain complete. Running final checks...")
    print(f"{'='*70}")

    if ENFORCEMENT_MODULES_AVAILABLE:
        disalignment = check_cognitive_disalignment()
        if disalignment['alert']:
            print(f"   ⚠️  {disalignment['reason']}")

        integrity = verify_hash_chain()
        if not integrity['valid']:
            print(f"   ❌ Ledger integrity compromised at entry: {integrity['broken']}")
        else:
            print(f"   ✅ Ledger verified: {integrity['entries']} entries")

    return s, a, p_rev, c_rev, crit, results

# ────────────────────────────────────────────────────────────────────────────
# Session Logging
# ────────────────────────────────────────────────────────────────────────────

LOG_DIR = BASE_DIR / "logs" / "sessions"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_session(objective: str, domain: str, s: str, a: str, p_rev: str,
                c_rev: str, crit: str, results: Dict[str, Any]) -> str:
    """Write session log with all outputs and metrics"""

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    log_path = LOG_DIR / f"{ts}_{TIER.lower()}_{domain}.log"

    with open(log_path, "w", encoding="utf8") as f:
        f.write(f"[AxProtocol Multi-Domain War Room]\n")
        f.write(f"[Timestamp] {ts} UTC\n")
        f.write(f"[Domain] {domain.upper()}\n")
        f.write(f"[Model] {MODEL} ({TIER})\n")
        f.write(f"[Enforcement] {'ENABLED' if ENFORCEMENT_MODULES_AVAILABLE else 'DISABLED'}\n\n")
        f.write(f"{'='*70}\n\n")

        f.write(f"[OBJECTIVE]\n{objective}\n\n{'='*70}\n\n")
        f.write(f"## STRATEGIST\n\n{s}\n\n")

        if 'strategist' in results and results['strategist']['taes']:
            taes = results['strategist']['taes']
            f.write(f"TAES → IV: {taes['integrity_vector']:.2f}, IRD: {taes['ird']:.3f}\n\n")

        f.write(f"{'='*70}\n\n## ANALYST\n\n{a}\n\n")

        if 'analyst' in results and results['analyst']['taes']:
            taes = results['analyst']['taes']
            f.write(f"TAES → IV: {taes['integrity_vector']:.2f}, IRD: {taes['ird']:.3f}\n\n")

        f.write(f"{'='*70}\n\n## PRODUCER [Revised]\n\n{p_rev}\n\n")

        if 'producer_revised' in results and results['producer_revised']['taes']:
            taes = results['producer_revised']['taes']
            f.write(f"TAES → IV: {taes['integrity_vector']:.2f}, IRD: {taes['ird']:.3f}\n\n")

        f.write(f"{'='*70}\n\n## COURIER [Revised]\n\n{c_rev}\n\n")

        if 'courier_revised' in results and results['courier_revised']['taes']:
            taes = results['courier_revised']['taes']
            f.write(f"TAES → IV: {taes['integrity_vector']:.2f}, IRD: {taes['ird']:.3f}\n\n")

        f.write(f"{'='*70}\n\n## CRITIC\n\n{crit}\n")

    return str(log_path)

# ────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ────────────────────────────────────────────────────────────────────────────

def main():
    """Main entry point with multi-domain support"""

    if len(sys.argv) > 1:
        objective = " ".join(sys.argv[1:])
    else:
        objective = "Launch an online course about Python programming"
        print(f"\n⚠️  No objective provided, using default test objective")

    print(f"\n[AxProtocol] Multi-Domain War Room v2.3")
    print(f"[AxProtocol] Tier: {TIER} → Model: {MODEL}")
    print(f"[AxProtocol] Detection: {'ENABLED' if DOMAIN_DETECTION_AVAILABLE else 'DISABLED'}")

    # Detect domain
    domain = detect_and_configure_domain(objective)

    # Load domain-specific roles
    build_type = os.getenv("BUILD_TYPE", "stable")
    print(f"[AxProtocol] Loading {domain} roles (build_type: {build_type})...")
    roles = load_domain_roles(domain, build_type)
    print(f"✅ Roles loaded: {', '.join(roles.keys())}")

    # Execute chain
    s, a, p_rev, c_rev, crit, results = run_chain(objective, domain, roles)

    # Log session
    log_file = log_session(objective, domain, s, a, p_rev, c_rev, crit, results)

    # Final summary
    print(f"\n{'='*70}")
    print(f"✅ AxProtocol chain complete [{domain.upper()}]")
    print(f"{'='*70}")
    print(f"📄 Session log: {log_file}")
    if ENFORCEMENT_MODULES_AVAILABLE:
        print(f"🔐 Audit ledger: logs/ledger/audit_ledger.db")
        print(f"📊 TAES log: logs/ird_log.csv")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()