# Priority Review Checklist

This guide helps you review the most important files in your optimized AxProtocol project.

## 🔴 Must Review First (Core Documents)

### 1. README.md
**Why:** Project overview and quick start guide  
**Action:** Read to understand the project structure  
**Time:** 5 minutes

### 2. OPTIMIZATION-SUMMARY.md
**Why:** Detailed explanation of all changes made  
**Action:** Review to understand what changed and why  
**Time:** 10 minutes

### 3. REORGANIZATION.md
**Why:** Complete migration guide  
**Action:** Follow if updating existing repository  
**Time:** 15 minutes

### 4. QUICKSTART.md
**Why:** Step-by-step setup instructions  
**Action:** Use to get War Room running  
**Time:** 5 minutes

## 🟡 Review Soon (Configuration & Setup)

### 5. implementations/war-room-v0.1b/.env.example
**Why:** Configuration template  
**Action:** Copy to `.env` and fill in your API keys  
**Priority:** Before first run

### 6. .gitignore (root)
**Why:** Version control exclusions  
**Action:** Verify it matches your needs  
**Priority:** Before committing

### 7. CLAUDE.md
**Why:** Updated architecture documentation  
**Action:** Reference when working with Claude Code  
**Priority:** When developing

## 🟢 Review Later (Protocol & Implementation)

### 8. Protocol Files (7 files in protocol/)
**Location:** `protocol/v*.txt`  
**Why:** Constitutional directives  
**Action:** Read to understand governance framework  
**Order:**
1. v0-change-control.txt (change governance)
2. v2.1a-core-directives.txt (foundational rules)
3. v2.1b-war-room-integration.txt (integration layer)
4. v2.1c-authority-layer.txt (operator control)
5. v2.2-taes-evaluation.txt (evaluation metrics)
6. v2.3-red-team-layer.txt (adversarial review)
7. v2.3-consolidated.txt (complete protocol)

### 9. Role Definitions (5 files)
**Location:** `implementations/war-room-v0.1b/roles/*_stable.txt`  
**Files:**
- strategist_stable.txt
- analyst_stable.txt
- producer_stable.txt
- courier_stable.txt
- critic_stable.txt

**Action:** Review to understand each role's purpose  
**Priority:** Before customizing

### 10. Implementation Code (8 key Python files)
**Location:** `implementations/war-room-v0.1b/`

**Priority order:**
1. **run_axp.py** (main orchestrator)
2. **taes_evaluation.py** (evaluation engine)
3. **auth.py** (authorization system)
4. **ledger.py** (audit logging)
5. **score_validator.py** (score validation)
6. **load_roles.py** (role loader)
7. **app_axp.py** (Streamlit UI)
8. **fault_injection.py** (testing)

## 📊 Files by Category

### Documentation (Read First)
```
./README.md                    ← Start here
./QUICKSTART.md               ← Setup guide
./OPTIMIZATION-SUMMARY.md     ← What changed
./REORGANIZATION.md           ← Migration guide
./CLAUDE.md                   ← Architecture reference
./CHANGELOG.md                ← Change history
./FILE-LIST.txt               ← Complete file inventory
```

### Protocol (Read Second)
```
./protocol/
├── v0-change-control.txt                ← 1. Change governance
├── v2.1a-core-directives.txt           ← 2. Core rules
├── v2.1b-war-room-integration.txt      ← 3. Integration
├── v2.1c-authority-layer.txt           ← 4. Operator control
├── v2.2-taes-evaluation.txt            ← 5. Evaluation
├── v2.3-red-team-layer.txt             ← 6. Red team
└── v2.3-consolidated.txt               ← 7. Full protocol
```

### Implementation (Review Third)
```
./implementations/war-room-v0.1b/
├── .env.example              ← Copy to .env
├── requirements.txt          ← Dependencies
├── run_axp.py               ← Main entry point
├── app_axp.py               ← UI console
├── roles/                   ← Role definitions
│   ├── strategist_stable.txt
│   ├── analyst_stable.txt
│   ├── producer_stable.txt
│   ├── courier_stable.txt
│   └── critic_stable.txt
└── [other Python modules]
```

### Utilities & Docs
```
./docs/
├── operator-console.md       ← Console commands
└── deployment-validation.md  ← Deployment guide

./scripts/
└── sync_bridge.py           ← Git sync utility

./scouts/
└── gemini-first-test.md     ← Intelligence monitoring
```

## 🎯 Action Items by Role

### For Project Owner
- [ ] Read OPTIMIZATION-SUMMARY.md
- [ ] Review protocol files (understand governance)
- [ ] Verify .gitignore excludes sensitive files
- [ ] Update any external references to old paths

### For Developers
- [ ] Read QUICKSTART.md
- [ ] Setup War Room environment (.env)
- [ ] Run first test campaign
- [ ] Review role definitions
- [ ] Explore implementation code

### For Operators
- [ ] Read docs/operator-console.md
- [ ] Understand OP_AUTH commands
- [ ] Review TAES metrics
- [ ] Test operator override functions

### For Contributors
- [ ] Read README.md
- [ ] Follow QUICKSTART.md setup
- [ ] Review protocol/v0-change-control.txt
- [ ] Understand ratification process

## 🔍 What to Look For

### In Protocol Files
- **Directives:** Numbered rules (0-28)
- **Ratification:** Approval status
- **Thresholds:** Numeric targets (ACI≥90, etc.)
- **Authority:** Operator control mechanisms

### In Implementation Code
- **run_axp.py:** Flow of 5-role chain
- **taes_evaluation.py:** Scoring calculations
- **auth.py:** CAM lease and tokens
- **score_validator.py:** Threshold enforcement

### In Role Definitions
- **Purpose:** Each role's mission
- **Deliverables:** Expected outputs
- **Scoring:** Self-evaluation criteria
- **Transitions:** How roles connect

## ⚠️ Common Questions

### "Where are the log files?"
Logs are now .gitignored. They'll be created at runtime in:
- `implementations/war-room-v0.1b/logs/`
- `logs/` (root level)

### "Where's the .venv?"
Virtual environments are excluded (82MB saved!). Create yours:
```bash
cd implementations/war-room-v0.1b
python -m venv .venv
```

### "Which protocol file is authoritative?"
`protocol/v2.3-consolidated.txt` is the complete version.
Individual layer files are for reference.

### "Can I modify protocol files?"
Yes, but follow Directive 0 (Change Control):
1. Make changes
2. Get operator ratification
3. Update CHANGELOG.md
4. Add ratification block to file

### "How do I run the system?"
```bash
cd implementations/war-room-v0.1b
cp .env.example .env
# Edit .env with your API key
pip install -r requirements.txt
TIER=DEV python run_axp.py "Your objective"
```

## 📈 Progressive Review Plan

### Day 1: Get Running (30 min)
- Read QUICKSTART.md
- Setup environment
- Run first campaign
- ✅ System operational

### Day 2: Understand Structure (1 hour)
- Read README.md
- Review OPTIMIZATION-SUMMARY.md
- Explore directory structure
- ✅ Navigate confidently

### Day 3: Study Protocol (2 hours)
- Read v0-change-control.txt
- Read v2.1a-core-directives.txt
- Understand governance model
- ✅ Know the rules

### Week 1: Deep Dive (5 hours)
- Read all protocol files
- Study role definitions
- Review implementation code
- Run multiple campaigns
- ✅ Proficient user

### Month 1: Master Level
- Customize roles
- Modify protocol (with ratification)
- Extend functionality
- Contribute improvements
- ✅ Power user

## ✅ Completion Checklist

Mark off as you go:

**Setup**
- [ ] Downloaded optimized structure
- [ ] Read README.md
- [ ] Created .env file
- [ ] Installed dependencies
- [ ] Ran first campaign

**Understanding**
- [ ] Read OPTIMIZATION-SUMMARY.md
- [ ] Reviewed protocol v0 (Change Control)
- [ ] Reviewed protocol v2.1a (Core)
- [ ] Understand 5-role chain

**Proficiency**
- [ ] Read all protocol files
- [ ] Tested all TIER levels
- [ ] Used operator console
- [ ] Reviewed session logs

**Mastery**
- [ ] Modified role definitions
- [ ] Customized evaluation weights
- [ ] Contributed improvements
- [ ] Understand full architecture

---

**Recommended Path:** Start with README.md → QUICKSTART.md → Run first campaign → Study protocol files in order

**Total Review Time:** ~8 hours for complete understanding (but you can get started in 30 minutes!)
