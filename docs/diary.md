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
