# AxProtocol Multi-Domain Usage Guide

Complete guide to using AxProtocol across all domains.

---

## 🚀 Quick Start

### 1. Run Setup Script

```bash
cd implementations/war-room-v0.1b
./setup_multi_domain.sh
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Test Auto-Detection

```bash
# Let AxProtocol detect the domain automatically
python run.py "Launch a social media campaign for new product"
python run.py "Build a user authentication system"
python run.py "Create employee onboarding workflow"
python run.py "Design a brand identity"
python run.py "Develop an online course about Python"
```

---

## 🎯 Domain-Specific Usage

### Marketing Domain

**Keywords:** campaign, leads, ads, customers, promote, social media, content, brand

```bash
# Auto-detected as marketing
python run.py "Launch Instagram campaign for coffee shop"
python run.py "Create lead generation funnel for B2B SaaS"
python run.py "Book 10 local clients in 2 weeks"

# Force marketing domain
DOMAIN=marketing python run.py "Your objective"
```

**Expected Output:**

- Campaign positioning and audience targeting
- Platform-specific content assets (social, email, ads)
- Distribution schedule with posting times
- Lead generation KPIs
- Budget allocation recommendations

---

### Technical Domain

**Keywords:** build, code, implement, system, architecture, api, database, deploy

```bash
# Auto-detected as technical
python run.py "Build REST API for user authentication"
python run.py "Design microservices architecture for e-commerce"
python run.py "Implement CI/CD pipeline with monitoring"

# Force technical domain
DOMAIN=technical python run.py "Your objective"
```

**Expected Output:**

- System architecture diagram (described)
- Technology stack with rationale
- API contracts and database schemas
- Deployment strategy and monitoring plan
- Security and performance considerations

---

### Operations Domain

**Keywords:** workflow, process, automation, efficiency, sop, procedure, optimize

```bash
# Auto-detected as ops
python run.py "Design employee onboarding workflow"
python run.py "Optimize order fulfillment process"
python run.py "Create incident response procedure"

# Force ops domain
DOMAIN=ops python run.py "Your objective"
```

**Expected Output:**

- Process workflow diagram (described)
- Step-by-step SOPs
- RACI matrix (roles and responsibilities)
- Implementation timeline with training plan
- Efficiency metrics and KPIs

---

### Creative Domain

**Keywords:** creative, content, story, narrative, brand, design, video, blog

```bash
# Auto-detected as creative
python run.py "Design brand identity for eco-friendly startup"
python run.py "Create video content series for YouTube"
python run.py "Develop brand storytelling strategy"

# Force creative domain
DOMAIN=creative python run.py "Your objective"
```

**Expected Output:**

- Creative brief with brand voice
- Original content pieces across formats
- Visual/design direction
- Publishing and amplification strategy
- Engagement metrics

---

### Education Domain

**Keywords:** course, training, curriculum, education, teach, learn, lesson

```bash
# Auto-detected as education
python run.py "Create online course about Python programming"
python run.py "Design leadership training program"
python run.py "Develop certification curriculum"

# Force education domain
DOMAIN=education python run.py "Your objective"
```

**Expected Output:**

- Curriculum structure with learning objectives
- Lesson plans with activities
- Assessment strategy (quizzes, projects)
- Student engagement plan
- Instructor guide

---

## 🎛️ Advanced Usage

### Multi-Domain Detection Test

```bash
# Run detector in test mode
python domain_detector.py

# Or test from Python
python -c "from domain_detector import detect_domain; print(detect_domain('Build an API'))"
```

### Manual Domain Override

When auto-detection isn't picking the right domain:

```bash
# Force specific domain
DOMAIN=technical python run.py "Your objective"
DOMAIN=ops python run.py "Your objective"
DOMAIN=creative python run.py "Your objective"
```

### Tier Selection (Quality Levels)

```bash
# DEV tier (fast, gpt-4o-mini)
TIER=DEV python run.py "Your objective"

# PREP tier (mid-grade, gpt-4o-turbo)  
TIER=PREP python run.py "Your objective"

# CLIENT tier (full quality, gpt-4o)
TIER=CLIENT python run.py "Your objective"
```

### Combined Parameters

```bash
# Domain + Tier
DOMAIN=technical TIER=CLIENT python run.py "Build production API"

# Domain + Tier + Build Type
DOMAIN=ops TIER=PREP BUILD_TYPE=experimental python run.py "Design workflow"
```

---

## 📊 Understanding the Output

### Session Log Structure

```
logs/sessions/
└── 2025-10-26_14-30-15_dev_technical.log
    ├── Session metadata (timestamp, domain, model, tier)
    ├── Objective
    ├── Strategist output + TAES metrics
    ├── Analyst output + TAES metrics
    ├── Producer output + TAES metrics
    ├── Courier output + TAES metrics
    └── Critic output + ratings
```

### TAES Metrics Explained

- **IV (Integrity Vector):** Overall logic quality (0.0-1.0, higher is better)
- **IRD (Integrity-Reality Disalignment):** Gap between ideal logic and practical reality
  - < 0.3: Well-aligned
  - 0.3-0.5: Some tension
  - > 0.5: Requires Reality Reconciliation Pass (RRP)

### Console Output Example

```
[AxProtocol] Domain: TECHNICAL (auto-detected)
[AxProtocol] Model: gpt-4o-mini (DEV)
✅ Roles loaded: strategist, analyst, producer, courier, critic

[1/5] Strategist...
   TAES → IV: 0.89, IRD: 0.234

[2/5] Analyst...
   TAES → IV: 0.92, IRD: 0.156
   Scores → All scores above threshold (85+)

[3/5] Producer (draft)...
   TAES → IV: 0.88, IRD: 0.267

[4/5] Courier (draft)...
   TAES → IV: 0.91, IRD: 0.189

[5/5] Critic...
   TAES → IV: 0.93, IRD: 0.145
   Scores → Average: 88/100 (READY)

✅ AxProtocol chain complete [TECHNICAL]
📄 Session log: logs/sessions/2025-10-26_14-30-15_dev_technical.log
```

---

## 🧪 Testing Each Domain

### Test Script

Create `test_all_domains.sh`:

```bash
#!/bin/bash
echo "Testing all domains..."
echo ""

echo "1. Marketing..."
python run.py "Launch social media campaign for coffee shop"
echo ""

echo "2. Technical..."
DOMAIN=technical python run.py "Build REST API with authentication"
echo ""

echo "3. Operations..."
DOMAIN=ops python run.py "Design employee onboarding process"
echo ""

echo "4. Creative..."
DOMAIN=creative python run.py "Create brand identity for startup"
echo ""

echo "5. Education..."
DOMAIN=education python run.py "Develop Python programming course"
echo ""

echo "All domains tested!"
```

---

## 🔍 Troubleshooting

### Domain Detection Issues

**Problem:** Wrong domain detected

```bash
# Solution: Manual override
DOMAIN=technical python run.py "Your objective"
```

**Problem:** Low confidence detection

```
[Domain Detection]
   Selected: marketing (confidence: 0.58)
   ⚠️ Low confidence - using fallback domain
```

```bash
# Solution: Add more domain-specific keywords or override manually
DOMAIN=ops python run.py "Design process for customer support workflow automation"
```

### Missing Role Files

**Problem:** 

```
⚠️ Role file not found: roles/technical/strategist_stable.txt
⚠️ Using generic fallback roles
```

**Solution:**

1. Create the missing role file in the correct directory
2. Or let it use generic fallback (works but less optimized)

### Module Import Errors

**Problem:**

```
⚠️ Enforcement modules not available
⚠️ Running in basic mode without TAES/ledger/auth
```

**Solution:**

- This is expected if you haven't set up enforcement modules yet
- System will still work, just without TAES metrics
- Optional: Install enforcement modules for full functionality

---

## 📈 Optimization Tips

### Better Domain Detection

Add domain-specific keywords to your objective:

```bash
# Instead of:
python run.py "Make a website"

# Try:
python run.py "Build a web application with user authentication and database"  # → technical
python run.py "Create website content and marketing materials"                # → creative
python run.py "Design website update workflow and approval process"           # → ops
```

### Improve Output Quality

1. **Be specific in objectives:**
   
   - ❌ "Make a course"
   - ✅ "Create 6-week online course teaching Python to beginners with weekly projects"

2. **Include constraints:**
   
   - "Design onboarding workflow for 50+ new hires per month with 2-person HR team"

3. **Specify success criteria:**
   
   - "Launch campaign that generates 100 qualified leads in 30 days under $5k budget"

---

## 🎨 Customization

### Add New Domain

1. Create directory: `roles/my_domain/`
2. Add 5 role files: `strategist_stable.txt`, `analyst_stable.txt`, etc.
3. Update `DomainConfig.json`:
   
   ```json
   "my_domain": {
   "name": "My Domain",
   "description": "Domain description",
   "taes_weights": {"logical": 0.4, "practical": 0.4, "probable": 0.2},
   "keywords": ["keyword1", "keyword2", "keyword3"]
   }
   ```

### Modify Existing Roles

1. Navigate to: `roles/{domain}/{role}_stable.txt`
2. Edit the role definition
3. Test: `DOMAIN={domain} python run.py "Test objective"`

---

## 📚 Examples by Use Case

### Startup Launch

```bash
# Marketing campaign
python run.py "Launch pre-launch waitlist campaign for SaaS product"

# Product development  
DOMAIN=product python run.py "Design MVP feature set for project management tool"

# Technical implementation
DOMAIN=technical python run.py "Build landing page with email capture and analytics"

# Operations setup
DOMAIN=ops python run.py "Create customer onboarding workflow"
```

### Tree Service Business (Your Use Case!)

```bash
# Marketing
python run.py "Book 5 jobs in 7 days for tree service in Omaha"

# Operations
DOMAIN=ops python run.py "Design job scheduling and crew dispatch workflow"

# Technical
DOMAIN=technical python run.py "Build booking system with SMS notifications"

# Creative
DOMAIN=creative python run.py "Create brand identity and video content for tree service"
```

### Online Course Creation

```bash
# Education (primary)
python run.py "Create 8-week Python programming course for beginners"

# Marketing (promotion)
DOMAIN=marketing python run.py "Launch course with 500 student enrollments in 30 days"

# Technical (platform)
DOMAIN=technical python run.py "Build course delivery platform with video hosting"
```

---

## 🎯 Success Metrics

Track your domain usage effectiveness:

```bash
# Check session logs by domain
ls logs/sessions/ | grep "_technical"
ls logs/sessions/ | grep "_ops"
ls logs/sessions/ | grep "_marketing"

# Compare output quality across domains
# Look for average critic scores in log files
grep "Average score" logs/sessions/*.log
```

---

## 🚦 What's Next?

1. **Test auto-detection:** Run 5 different objectives and verify correct domain
2. **Review outputs:** Check if domain-specific roles produce better results
3. **Customize roles:** Tailor role definitions to your specific needs
4. **Add domains:** Create role sets for product, strategy, research
5. **Integrate with your workflow:** Build scripts that chain multiple domains

---

## 💡 Pro Tips

1. **Hybrid objectives work:** "Build and launch" will detect technical, but you can run ops and marketing separately
2. **Domain isn't always obvious:** "Create documentation" could be ops, technical, or education - be explicit!
3. **Start with DEV tier:** Test detection with fast model first, then use PREP/CLIENT for final output
4. **Save good outputs:** Session logs are your knowledge base - organize them by project
5. **Iterate:** If output isn't right, try different domain or refine objective wording

---

**Ready to build domain-agnostic reasoning? Start testing!** 🚀
