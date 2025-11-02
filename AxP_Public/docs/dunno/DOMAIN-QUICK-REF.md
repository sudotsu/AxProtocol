# AxProtocol Multi-Domain Quick Reference

## One-Line Commands

### Auto-Detection (Recommended)

```bash
python run.py "Your objective here"
```

### Manual Domain Selection

```bash
DOMAIN=marketing python run.py "Your objective"
DOMAIN=technical python run.py "Your objective"
DOMAIN=ops python run.py "Your objective"
DOMAIN=creative python run.py "Your objective"
DOMAIN=education python run.py "Your objective"
```

### With Quality Tier

```bash
TIER=DEV python run.py "Your objective"      # Fast
TIER=PREP python run.py "Your objective"     # Balanced
TIER=CLIENT python run.py "Your objective"   # Best
```

---

## Domain Keywords Cheat Sheet

| Domain        | Trigger Keywords                                                    |
| ------------- | ------------------------------------------------------------------- |
| **Marketing** | campaign, leads, ads, promote, social, brand, customers, conversion |
| **Technical** | build, code, api, system, database, deploy, implement, architecture |
| **Ops**       | workflow, process, sop, automation, efficiency, onboard, procedure  |
| **Creative**  | content, story, brand, design, video, creative, narrative, visual   |
| **Education** | course, training, curriculum, teach, learn, lesson, pedagogy        |
| **Product**   | product, feature, roadmap, mvp, user, ux, prototype, sprint         |
| **Strategy**  | strategy, competitive, market, growth, vision, positioning          |
| **Research**  | research, study, data, analysis, survey, hypothesis, findings       |

---

## Output Checklist

Every AxProtocol run produces:

- ✅ **Strategist:** High-level plan
- ✅ **Analyst:** Validation + metrics
- ✅ **Producer:** Deliverables (draft)
- ✅ **Courier:** Implementation plan (draft)
- ✅ **Critic:** Quality audit
- ✅ **Producer (revised):** Final deliverables
- ✅ **Courier (revised):** Final implementation plan
- ✅ **Session Log:** Complete output saved

---

## Common Issues

| Problem        | Solution                            |
| -------------- | ----------------------------------- |
| Wrong domain   | Add `DOMAIN=` prefix                |
| Low quality    | Use `TIER=PREP` or `TIER=CLIENT`    |
| Generic roles  | Create domain-specific role files   |
| Slow execution | Use `TIER=DEV` for faster iteration |

---

## File Locations

```
roles/              ← Domain-specific role definitions
logs/sessions/      ← Session outputs
DomainConfig.json   ← Domain configurations
domain_detector.py  ← Auto-detection logic
run.py              ← Main orchestrator
```

---

## Test Commands

```bash
# Marketing test
python run.py "Launch Facebook ads campaign"

# Technical test  
python run.py "Build REST API with OAuth"

# Ops test
python run.py "Design hiring workflow"

# Creative test
python run.py "Create brand identity"

# Education test
python run.py "Develop Python course"
```

---

**Bookmark this page for quick reference!**
