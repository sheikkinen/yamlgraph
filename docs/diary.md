# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-20.md](diary-2026-02-20.md) — 32 entries, 2026-02-19 to 2026-02-20.

---

## 2026-02-21: Six Hats — Concrete Viewpoint Implementations

**Context:** Yesterday's "Six Hats Chaplaincy" entry mapped de Bono's six modes to abstract agent roles. Today: what *concrete tools and techniques* could implement each viewpoint?

### ⚪ White Hat (Facts, Data) — **The Archaeologist**

Existing tools that could serve this viewpoint:
- `pytest --cov` → coverage per module, missing lines
- `radon cc` → cyclomatic complexity scores (already in pre-commit)
- `vulture` → dead code detection (already in pre-commit)
- `wc -l **/*.py` → line count trends over time
- `git log --shortstat` → commit velocity, churn hotspots
- `scripts/req_coverage.py` → requirement traceability gaps

**New capability:** A weekly `archaeologist.sh` that runs all of these and outputs a structured report:
```yaml
report_date: 2026-02-21
total_lines: 4090
coverage: 92%
complexity_hotspots:
  - yamlgraph/graph_loader.py: B
  - yamlgraph/tools/agent.py: B
dead_code_candidates: 12
req_coverage: 77/77 (100%)
```

### 🔴 Red Hat (Intuition, Emotion) — **The User Voice**

This is the hardest to automate — it's about *feelings*, not metrics. Approaches:

- **Simulated confusion:** Feed a diff to an LLM with prompt "You're a junior dev seeing this for the first time. What's confusing?"
- **Error message critique:** `grep -r "raise.*Error" yamlgraph/ | xargs -I{} copilot -p "Is this error message helpful to a user who doesn't know the codebase?"`
- **Config complexity:** Count YAML nesting depth, flag configs > 4 levels deep
- **Onboarding test:** Time how long it takes a fresh `copilot` session to complete `examples/demos/hello` from scratch

**The key insight:** Red Hat can't be fully automated — but it can be *prompted*. A scheduled "user voice" run asks the human: "Here are 3 recent changes. Rate each 1-5 for clarity."

### ⚫ Black Hat (Critical Judgment) — **The Judge**

Already implemented in `chaplain.sh`'s judge phase. Additional angles:

- **Security scan:** `bandit -r yamlgraph/` for common vulnerabilities
- **Dependency audit:** `pip-audit` for known CVEs
- **Breaking change detector:** Compare public API signatures between versions
- **Scripture compliance:** `grep -r "TODO\|FIXME\|HACK" yamlgraph/` (already in pre-commit)

### 🟡 Yellow Hat (Optimism, Benefits) — **The Opportunity Finder**

This is the inverse of Black — asking "what's the upside?" Techniques:

- **Feature extrapolation:** For each FR, ask "If this worked perfectly, what 3 things would it enable?"
- **Adjacent problem scan:** For each capability, search "langchain {capability} use cases" and extract patterns not yet in YAMLGraph
- **Simplification opportunities:** "Which 3 modules could be deleted if we changed assumptions?"
- **10x version:** "What would this feature look like if we had infinite compute/tokens?"

**Example prompt for diary_digest output:**
```
Read this week's LangChain ecosystem updates. For each announcement,
answer: "How could YAMLGraph benefit from this? What's the optimistic case?"
```

### 🟢 Green Hat (Creativity, Alternatives) — **The Wildcard**

Already partially in `chaplain.sh`'s planner. Additional creative techniques:

- **Constraint inversion:** "What if YAML was the minority and Python was the majority?"
- **Deletion brainstorm:** "If we could only keep 3 node types, which 3?"
- **Paradigm shift:** "How would this look in a functional/actor/dataflow paradigm?"
- **Cross-pollination:** "Name 3 patterns from React/Kubernetes/Terraform that could apply here"

**The Wildcard vs Planner distinction:** Planner writes structured FRs. Wildcard generates *uncomfortable* ideas that challenge assumptions. Planner is Green-within-bounds; Wildcard is Green-without-bounds.

### 🔵 Blue Hat (Process, Meta) — **The Compliance Auditor**

This is the conductor. Existing tools:

- Pre-commit hooks (already comprehensive)
- `scripts/req_coverage.py --strict` (already in CI)
- Diary rotation hook (already triggers on date change)

**New capability:** Process health dashboard
```yaml
process_health:
  diary_entries_this_week: 7
  frs_created: 2
  frs_judged: 2
  frs_rejected: 0
  coverage_trend: +1.2%
  avg_hook_runtime: 34s
  bypass_attempts: 1  # The --no-verify transgression
```

### The Orchestration Pattern

The insight from yesterday holds: **parallel viewpoints need a conductor.** The Blue Hat decides which viewpoint to invoke:

| Situation | Viewpoint to Invoke |
|-----------|---------------------|
| Starting new FR | 🟢 Green (creative options) then ⚫ Black (judge) |
| Bug reported | ⚫ Black (what broke?) then ⚪ White (trace data) |
| Weekly planning | 🟡 Yellow (opportunities) then 🔵 Blue (prioritize) |
| User confusion reported | 🔴 Red (empathize) then 🟢 Green (alternatives) |
| Post-mortem | ⚪ White (facts) then ⚫ Black (what failed) then 🟢 Green (prevention) |

**Heuristic:** *Match the hat to the phase.* Creative phases need Green/Yellow. Critical phases need Black/White. The Blue Hat's job is knowing which phase you're in.

**Seed:** Could the chaplain script accept `--hat white|red|black|yellow|green|blue` to run a single viewpoint? The human becomes the Blue Hat, selecting context-appropriate perspectives. `chaplain.sh subjects.md --hat yellow` runs only the Opportunity Finder.

---

---

## 2026-02-21: World Digest — Agent Orchestration & Observability Maturity

**LangGraph ecosystem momentum:** Five LangGraph releases (1.0.9, SDK 0.3.6–0.3.8, prebuilt 1.0.8) landed this period, signaling active stabilization of the core framework YAMLGraph depends on. The SDK increments suggest refinement of deployment and integration patterns.

**Agent architecture patterns crystallizing:** LangChain's recent content wave covers multi-agent orchestration (Cord, Deep Agents, Agent Builder templates), context management, and sandbox connection patterns. These represent the design space YAMLGraph must eventually support declaratively—moving from imperative LangGraph code to YAML-driven composition.

**Observability becoming table stakes:** LangSmith's Google Cloud Marketplace availability and the "Traces to Insights" piece signal that observability is no longer optional. YAMLGraph will need to emit structured traces by default, not as an afterthought. The Remote case study demonstrates LangGraph in production at scale, raising the bar for what "production-ready" means.

**Evaluation frameworks maturing:** The monday + LangSmith case study shows code-first evaluation strategies becoming standard practice. This connects to the recent Seed about whether bug reports should require minimal reproduction scripts—evaluation rigor is shifting left.

**Tension emerging:** Agent Builder's rapid feature expansion (chat, file uploads, tool registry) suggests the ecosystem is moving toward higher-level abstractions. YAMLGraph's bet on YAML-first configuration must prove it reduces cognitive load compared to code-first frameworks, not just add another layer.

**Seed:** As LangGraph stabilizes and Agent Builder abstracts further, should YAMLGraph's YAML schema explicitly model observability hooks (trace naming, span boundaries, evaluation gates) rather than treating them as post-hoc instrumentation — making evaluation-first design a first-class concern from graph definition?
---

## 2026-02-21: The Sandbox Trap — launchd vs. macOS Privacy

**Context:** `diary_digest` launchd job kept failing with `PermissionError: Operation not permitted: '.venv/pyvenv.cfg'`. Multiple iterations of "fix the script" before realizing the root cause.

**The Trap:** Debugging the symptom, not the system. I created a wrapper script, modified paths, checked file permissions — all while the actual problem was macOS sandbox blocking launchd's access to `~/Documents/` entirely.

**The Clue I Missed:** `getcwd: cannot access parent directories: Operation not permitted` — this wasn't a file permission issue, it was a directory *access* issue. The sandbox blocks the entire path traversal, not just individual files.

**Security Analysis Surfaced:**
- Full Disk Access to `/bin/bash` = every bash script gets access to Documents, Mail, Photos, iCloud
- Symlinks resolve to destination, so `~/bin/script → ~/Documents/...` still fails
- The "quick fix" was the wrong fix

**Options matrix:**

| Approach | Security | Effort | Maintenance |
|----------|----------|--------|-------------|
| FDA to `/bin/bash` | ⚠️ Risky | 10s | Low |
| FDA to isolated `/usr/local/bin/bash-launchd` | Acceptable | 2min | Medium |
| Move project to `~/Developer/` | ✅ Clean | 5min | Low |
| Isolated `~/scheduled-yamlgraphs/` | ✅ Best | 15min | Medium |

**Heuristic:** *When a permission error shows `getcwd` failing, suspect sandbox/TCC, not file permissions. Debug the access context, not the accessed file.*

**Seed:** Should scheduled automation live in a dedicated sandbox-friendly location by default? Could YAMLGraph's deployment docs include a "scheduled jobs" section that warns about macOS/Linux cron permission boundaries?
---

## 2026-02-21: The Impossible Recommendation — FDA to System Binaries

**Context:** Deeper reflection on recommending "Full Disk Access to `/bin/bash`" three times as a quick fix.

**The Failure:** Apple's System Integrity Protection (SIP) **blocks** granting FDA to system binaries like `/bin/bash`. The recommendation was:
1. A security antipattern
2. Physically impossible on modern macOS

I confidently recommended something that cannot be done.

**Count of recommendations:** 3 times before being prompted for security analysis.

**Cognitive Failure Analysis:**

| Trap | Mechanism |
|------|-----------|
| **Cached heuristic** | "FDA fixes permission errors" — pattern-matched without checking if it applies to protected binaries |
| **Quick fix bias** | Optimized for speed over correctness; offered fastest "solution" first |
| **Authority without verification** | Stated confidently without testing (`System.prefPane` or checking SIP logs would have revealed the block) |
| **Obstacle vs. boundary** | Framed the sandbox as something to bypass, not a security boundary to respect |
| **Omitting design intent** | Apple designed TCC to prevent exactly this. The block *is* the feature |

**The deeper error:** When the operating system blocks an action, the correct question is *"Why does Apple block this?"* not *"How do I bypass it?"* The sandbox exists to prevent the attack vector I later described in my own security analysis.

**The irony:** I eventually produced a correct security analysis — but only after being explicitly prompted. The knowledge was there; the instinct to apply it wasn't.

**Heuristic:** *When recommending a workaround to a system protection, first verify (1) it's possible, and (2) whether the protection exists for good reason. If the OS blocks it by design, that's information, not an obstacle.*

**Graduated heuristic candidate:** *Treat security boundaries as affordances, not obstacles. Ask "why is this blocked?" before "how do I unblock it?"*

**Seed:** Should the Scripture include a commandment about respecting platform security boundaries? "Thou shalt not bypass what the OS protects without first understanding why it protects."

## 2026-02-21: The Provider's Temperature Wall

**Context:** Running White Hat graphs after fixing scheduled diary_digest. `code-analysis` failed with `temperature=None` validation error for Gemini.

**Trap:** Schema declared `temperature: float | None = Field(default=None)`. Python's `dict.get("temperature", 0.7)` returns `None` when key exists with value `None` — it doesn't fall back. The None propagated through three layers before Gemini rejected it. Belt-and-suspenders fixes were added before identifying the root cause.

**Insight:** This is the same pattern as FR-059 (Provider's Lie): **normalization must happen at the boundary, not downstream**. The schema is the boundary. If a value is required by any provider, the schema should provide a real default, not `None`.

**Heuristic:** *Schema defaults should never require runtime null-coalescing. If downstream code needs a value, the schema must provide one.*

**Recurrence Check:** First instance of this pattern for temperature; similar to prior provider normalization issues.

**Seed:** Should Pydantic schemas distinguish "user explicitly set None" from "user omitted field"? If so, should YAMLGraph use `UNSET` sentinels for truly optional overrides — making intent explicit at the boundary?

---

## 2026-02-21: Git Report

Perfect! Now I have enough information to provide a comprehensive analysis. Let me summarize the development from the last 3 days:

## Git Repository Analysis: Last 3 Days

Based on the commit history, here's a **feature-level summary** of the development:

### **Active Development Period**
- **Timeframe**: February 20-21, 2026 (last 3 days)
- **Total Commits**: ~30 recent commits visible
- **Primary Developer**: Sami J P Heikkinen

---

### **Major Features & Work Items**

#### 1. **Streaming Error Resilience (FR-062)** ⭐ Major Feature
   - **Commit**: `01042bf` (Feb 20)
   - **Focus**: Implementing robust error handling for async streaming operations
   - **Changes**:
     - Added `StreamEvent` Pydantic model for typed error/interrupt signals
     - Wrapped `astream()` with try/except exception handling
     - Implemented asyncio timeout for stall detection
     - Added interrupt detection via `aget_state()`
     - Added `yield_events=False` flag for backward compatibility
   - **Testing**: 8 new unit tests with chaos fixtures
   - **Related Documentation**: Updated ARCHITECTURE.md and req_coverage.py

#### 2. **Schema Configuration Fix** 🔧 Bug Fix
   - **Commit**: `7f9419a` (Feb 21 - Most Recent)
   - **Issue**: Default temperature parameter causing Gemini provider failures
   - **Solution**: Changed `NodeConfig.temperature` default from `None` to `0.7`
   - **Safety**: Added guards in `llm_nodes.py`, `agent.py`, and `llm_factory.py`
   - **Impact**: Fixed "White Hat" graphs (system-status, code-analysis, diary_digest)

#### 3. **Diary Rotation Enhancement** 📅 Feature Addition
   - **Commit**: `40e49f6` (Feb 21)
   - **Enhancement**: Diary rotation now imports scheduled entries from `~/scheduled-yamlgraphs`
   - **Changes**: Expanded `diary_rotate.py` script with 72 lines of new functionality

---

### **Secondary Work**

#### 4. **Test Coverage Improvement**
   - `1debdaa`: MCP server error paths testing - improved coverage from 72% → 83%

---

## 2026-02-21: The Debugging Instinct — Fix at Source, Not Downstream

**Context:** Running White Hat graphs to verify temperature fix. `code-analysis` failed with `temperature=None` for Gemini.

**Trap:** I immediately added "belt-and-suspenders" fixes in three downstream locations (llm_nodes.py, agent.py, llm_factory.py) before tracing the root cause. The user had to redirect: *"wasn't the issue in graph_schema.py:59?"* — yes, the schema allowed `None` as default.

**The Pattern:** This is the same mistake as the Provider's Lie (FR-059). The instinct is to patch where the error *manifests*, not where it *originates*. Defensive code proliferates; the actual boundary (schema) remains leaky.

**Why it happens:**
1. Faster to add a guard than trace the call chain
2. Belt-and-suspenders *feels* safer (more protection = better, right?)
3. The symptom location is obvious; the cause requires archaeology

**The cost:** Three defensive guards that should never trigger. If the schema is correct, they're dead code. If the schema breaks again, they mask the symptom instead of failing fast.

**Heuristic graduated:** *Fix at the boundary, not downstream. If you find yourself adding defensive guards in multiple places, you haven't found the root cause yet.*

**Automation win:** Extended the diary automation loop. Now two scheduled jobs run nightly:
- `diary_digest` at 03:00 — World news synthesis
- `git_report` at 03:10 — 3-day rolling development summary

Both auto-import to diary on pre-commit. The human doesn't write scheduled entries; they accumulate automatically and get curated on commit.

**Seed:** Could a linter detect "defensive guard proliferation" — multiple `if x is None: x = default` guards for the same variable across files — and warn that a schema boundary fix might be missing?
