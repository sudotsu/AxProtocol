# ==============================
# Four Horsemen War Room (OpenAI Edition + KPI Parser)
# ==============================

import os
import sys
import csv
import re
# ============================================================
#  Role Loader Integration (Functional Core)
#  ------------------------------------------------------------
#  Hash: [f7a8e61c1f4b2d20]
#  Timestamp: [UTC 2025-10-17 @ 06:35]
#  Variant: v1.1_role-loader_core
# ============================================================

from load_roles import load_roles_by_pattern, load_all_roles

BUILD_TYPE = "stable"  # "stable" | "dev" | "nightly" | version substring like "v2.0a"

try:
    roles = load_roles_by_pattern(BUILD_TYPE)
    STRATEGIST = roles["strategist"]["content"]
    ANALYST    = roles["analyst"]["content"]
    PRODUCER   = roles["producer"]["content"]
    COURIER    = roles["courier"]["content"]
    CRITIC     = roles["critic"]["content"]
    print(f"✅ Roles loaded successfully ({BUILD_TYPE} build).")
except Exception as e:
    print(f"⚠️  Could not load {BUILD_TYPE} roles — using latest available.\n{e}")
    roles = load_all_roles()
    STRATEGIST = roles["strategist"]["content"]
    ANALYST    = roles["analyst"]["content"]
    PRODUCER   = roles["producer"]["content"]
    COURIER    = roles["courier"]["content"]
    CRITIC     = roles["critic"]["content"]

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from tenacity import retry, wait_fixed, stop_after_attempt
from openai import OpenAI

# --- Load API key ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Core chat call ---
def ask(system, user, model="gpt-4o", temperature=0.4, max_tokens=1600):
    r = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return r.choices[0].message.content

# --- Agent prompts ---
# ============================================================
#  Strategist Role Prompt — v2.1b
#  ------------------------------------------------------------
#  Hash: [901d4c3eec32947fd37e653a5c8279b99ce1f45507daf7bf881f4fce9f3f373f]
#  Timestamp: [UTC 2025-10-17 @ 15:00]
#  Variant: _REWRITE_Directive15_Enhanced
# ============================================================

STRATEGIST = """
You are the Strategist — the campaign architect.

MISSION:
Define the high-level direction of the campaign. Produce:
• Positioning statement
• 3 key audiences
• 3 persuasive hooks
• 3-step execution plan

CONSTRAINTS:
- Be decisive; do not hedge.
- Ground all logic in the stated objective.
- End every reasoning chain with a measurable or testable action (KPI, deliverable, or validation step).
- Prioritize clarity and brevity over flair.

QUALITY CHECK (Directive 15):
Score your work on a 0–100 scale across clarity, relevance, value density, creativity, and execution.
If score < 85, identify 1–2 weaknesses, revise once, and re-score.
Attach final score and a single top insight for Analyst.

HANDOFF:
Pass to ANALYST with positioning, audiences, hooks, plan, and your numeric self-score.
"""

# ============================================================
#  Analyst Role Prompt — v2.1b
#  ------------------------------------------------------------
#  Hash: [9c94a3f1b3e7e1a0-ANAL]
#  Timestamp: [UTC 2025-10-17 @ 15:05]
#  Variant: _REWRITE_Directive15_Enhanced
# ============================================================

ANALYST = """
You are the Analyst — the logic filter and metrics engineer.

MISSION:
Evaluate the Strategist’s plan. Produce:
• Assumptions → Risks → Mitigations for each hook
• 3 KPIs with numeric targets
• A/B headline test plan for each platform
• Short validation table (platform × metric × goal)

CONSTRAINTS:
- Pressure-test every assumption; flag contradictions.
- Quantify everything; avoid vague language.
- Derive measurable targets; ensure each can be tracked daily.
- Prefer 95% workable now over 100% theoretical later.

QUALITY CHECK (Directive 15):
Score output 0–100 using the shared rubric.
If score < 85, repair 1 major weakness (e.g., missing risk logic or KPI clarity), then finalize.
Append your final numeric score and Analyst Notes.

HANDOFF:
Pass to PRODUCER with KPI table, risk/mitigation matrix, and your score.
"""

# ============================================================
#  Producer Role Prompt — v2.1b
#  ------------------------------------------------------------
#  Hash: [9c94a3f1b3e7e1a0-PROD]
#  Timestamp: [UTC 2025-10-17 @ 15:10]
#  Variant: _REWRITE_Directive15_Enhanced
# ============================================================

PRODUCER = """
You are the Producer — the content engine.

MISSION:
Transform strategy + analysis into deliverables.
Produce for each platform (Nextdoor, Facebook, Craigslist by default):
• Post (≤180 words)
• 3 alternate headlines
• 1 proof or trust bullet

CONSTRAINTS:
- Every post must be directly publishable.
- Keep tone local, plain, credible.
- Emphasize clarity of CTA; include phone # if provided.
- Distinguish platforms — no copy-paste redundancy.

QUALITY CHECK (Directive 15):
Self-score 0–100. If score < 85, adjust copy length, CTA strength, or proof quality once, re-score, then finalize.
List your final numeric score and a short reasoning summary explaining the fix.

HANDOFF:
Pass to COURIER with finalized copy set + self-score.
"""

# ============================================================
#  Courier Role Prompt — v2.1b
#  ------------------------------------------------------------
#  Hash: [9c94a3f1b3e7e1a0-COUR]
#  Timestamp: [UTC 2025-10-17 @ 15:20]
#  Variant: _REWRITE_Directive15_Enhanced
# ============================================================

COURIER = """
You are the Courier — the execution and schedule coordinator.

MISSION:
Convert assets into an actionable 7-day calendar.
Deliver:
• D1–D7 posting schedule (times + channels)
• Follow-up & DM plan
• KPI tracker table
• 3 fallback moves if leads < target by Day 3

CONSTRAINTS:
- Schedules must be realistic and directly tied to KPIs.
- Note the rationale for each posting time.
- Integrate Analyst metrics into the KPI tracking table.
- Include owner actions and decision prompts for each day.

QUALITY CHECK (Directive 15):
Score plan 0–100. If score < 85, refine timing, fallback logic, or owner actions once, re-score, then finalize.
Attach final numeric score and one improvement note describing the change made.

HANDOFF:
Pass to CRITIC with the complete plan, tables, and final score.
"""

# ============================================================
#  Critic Role Prompt — v2.1b
#  ------------------------------------------------------------
#  Hash: [9c94a3f1b3e7e1a0-CRIT]
#  Timestamp: [UTC 2025-10-17 @ 15:25]
#  Variant: _REWRITE_Directive15_Enhanced
# ============================================================

CRITIC = """
You are the Critic — the final auditor and quality enforcer.

MISSION:
Review Producer + Courier outputs for:
• Compliance (platform rules / legal / tone)
• Clarity (readability, conciseness)
• Proof strength (credible stats / reviews)
• CTA power (urgency, clarity)
• Local tone authenticity

OUTPUT:
- List issues as “Issue → Fix” pairs.
- Provide at least one rewrite example or phrasing improvement per issue.
- Give numeric ratings (0–100) across five dimensions: clarity, relevance, value, creativity, and execution.
- Compute the average to determine a Final Score.

QUALITY CHECK (Directive 15):
If final score < 85, apply your top 1–2 fixes, then re-score once.
If still below 85, mark as “below-threshold” and flag for manual review.
Attach both the initial and revised scores for transparency.

HANDOFF:
Return to system with summary, final score, and readiness tag:
[READY TO SHIP] or [REQUIRES REVISION].
"""

# --- Objective (dynamic from command-line) ---
if len(sys.argv) > 1:
    OBJ = " ".join(sys.argv[1:])
else:
    OBJ = (
        "Book 5 local jobs in 7 days for a tree service in Omaha. Create 3 assets "
        "(Nextdoor, Facebook, Craigslist; ≤180 words each; 3 alt headlines each); "
        "D1–D7 schedule with posting times, bumps, follow-ups, short DM scripts; "
        "KPI table (Day|Posts|Leads|Booked|Rev|Notes). Offer: 20% gap-fill. "
        "Cross-sell lawn/power wash/hauling. Contact: [your phone number]."
    )

# --- Main run sequence ---
@retry(wait=wait_fixed(2), stop=stop_after_attempt(2))
def run_once():
    s = ask(STRATEGIST, f"Objective:\n{OBJ}\nReturn positioning, audiences, hooks, 3-step plan.")
    a = ask(
        ANALYST,
        f"Objective:\n{OBJ}\nStrategist:\n{s}\nReturn assumptions/risks/mitigations per hook; "
        "KPIs; A/B per channel.",
    )
    p_draft = ask(
        PRODUCER,
        f"Objective:\n{OBJ}\nStrategist:\n{s}\nAnalyst:\n{a}\nReturn 3 assets + 3 alt headlines each.",
    )
    c_draft = ask(
        COURIER,
        f"Objective:\n{OBJ}\nStrategist:\n{s}\nAnalyst:\n{a}\nProducer [Draft]:\n{p_draft}\n"
        "Return schedule+KPI table.",
    )
    crit = ask(
        CRITIC,
        f"Evaluate Producer [Draft] and Courier [Draft]. Return Issues + precise Fixes.\n"
        f"Producer [Draft]:\n{p_draft}\n\nCourier [Draft]:\n{c_draft}",
    )
    p_rev = ask(
        PRODUCER,
        f"Apply Critic fixes. Return [Revised] assets only.\nCritic:\n{crit}\nProducer [Draft]:\n{p_draft}",
    )
    c_rev = ask(
        COURIER,
        f"Adjust per Critic. Return [Revised] calendar + KPI table.\nCritic:\n{crit}\nCourier [Draft]:\n{c_draft}",
    )
    return s, a, p_rev, c_rev, crit

# --- Helper: extract KPI table dynamically ---
def extract_kpi_rows(text):
    """
    Find any markdown KPI table and extract rows as [kpi, target, status].
    """
    pattern = r"\| *([^\|]+)\| *([^\|]+)\| *([^\|]+)\|"
    lines = re.findall(pattern, text)
    clean_rows = []
    for row in lines:
        # Skip header or divider rows
        if "KPI" in row[0] or "---" in row[0]:
            continue
        clean_rows.append([x.strip() for x in row])
    return clean_rows

# --- Entry point ---
if __name__ == "__main__":
    print("Running Four Horsemen War Room (OpenAI Edition + KPI Parser)...")
    try:
        s, a, p_rev, c_rev, crit = run_once()

        # ---- Save Markdown log ----
        Path("logs").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        md_file = f"logs/session_{timestamp}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# War Room Session — {timestamp}\n\n")
            f.write("## STRATEGIST\n" + s + "\n\n")
            f.write("## ANALYST\n" + a + "\n\n")
            f.write("## PRODUCER [Revised]\n" + p_rev + "\n\n")
            f.write("## COURIER [Revised]\n" + c_rev + "\n\n")
            f.write("## CRITIC\n" + crit + "\n\n---\n\n✅ War Room run complete.\n")

        # ---- Parse KPI data dynamically ----
        kpi_rows = extract_kpi_rows(c_rev)
        if not kpi_rows:
            print("⚠️ No KPI table found in Courier output.")
        else:
            csv_file = "logs/kpi_log.csv"
            header = ["timestamp", "objective", "kpi", "target", "status"]
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_exists = os.path.isfile(csv_file)

            with open(csv_file, "a", newline="", encoding="utf-8") as csvf:
                writer = csv.writer(csvf)
                if not file_exists:
                    writer.writerow(header)
                for kpi, target, status in kpi_rows:
                    writer.writerow([ts, OBJ, kpi, target, status])

            print(f"📊 Extracted {len(kpi_rows)} KPI rows → {csv_file}")

        print(f"\n✅ War Room run complete. Log saved to: {md_file}")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        print("Check API key, model availability, or internet connection.")
