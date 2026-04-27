---

## 2026-04-26: Watcher2 Sweet Spot — Automation vs. Architecture

**Context:** After months of operating the plan→judge→enforce pipeline with pre-commit hooks and CI gates, a pattern has emerged about where automated enforcement excels and where it doesn't.

**Observation (human):** The watcher2 pipeline works nicely for small, incremental, feature-level additions — the kind where scope is clear, acceptance criteria are mechanical, and the change fits within existing patterns. One inbox item, one FR, one PR, one merge.

But bigger improvements have followed a different track entirely: architectural planning → implementation → complete rewrite → repeat. The cycle repeats until the design stabilizes, and only then does it make sense to switch to the automated watcher for incremental refinement. Trying to push architectural work through the watcher pipeline forces premature commitment to structure that hasn't been validated yet.

**Reflection (agent):** This maps precisely to the **framework_costume** trap and its inverse. The watcher pipeline is a production line — it excels when the shape of the output is known and the work is filling in details. Architectural work is exploration — the output shape is unknown, rewrites are signal not waste, and premature enforcement (changelog fragments, diary gates, acceptance tests) adds friction without value when the entire approach may be discarded tomorrow.

The evidence is in the session itself: watcher2's own evolution followed the human pattern, not the automated one. Phase 1 (basic loop), Phase 2 (copilot integration), Phase 3 (planning pipeline), Phase 4 (CI remediation) — each was a substantial rewrite, not an incremental feature. The FSM rewrite (gh-238/239/240) is the next iteration. Feeding these back through the watcher produced orphan worktrees, duplicate PRs, and confused branch state — the pipeline enforcing structure on work that was still finding its structure.

**Trap:** **working_system_inertia** — "It works blocks seeing it clearly." The watcher works for what it works for, and that success creates pressure to route everything through it. The cost is invisible: architectural decisions get flattened into feature-sized chunks that pass CI but miss the forest.

**Heuristic:** **Automate the last mile, not the first.** Use manual architectural iteration (plan → build → rewrite → stabilize) for structural changes. Switch to automated enforcement (watcher pipeline) only after the design has survived at least one rewrite and the remaining work is filling in known shapes. The boundary marker: if you can write acceptance tests that won't be thrown away, the work is ready for the pipeline.

**Seed:** Could the watcher itself detect when it's being asked to do architectural work? A signal might be: FR scope touches >3 files in different layers, or acceptance tests reference interfaces that don't exist yet, or the judge verdict keeps oscillating between approve/reject. An "architecture mode" that parks the item and flags it for human-led iteration instead of forcing it through the enforcement pipeline.

---

## Brainstorm: Two Pipelines — Enforcement vs. Exploration

### The two modes

| | Enforcement (watcher2) | Exploration (manual today) |
|---|---|---|
| **Input** | Scoped issue, clear pattern | Vague problem, no pattern |
| **Shape** | Known — fill in details | Unknown — discover through iteration |
| **Failure means** | Defect — fix and retry | Information — revise and rethink |
| **Output** | Merged PR | Stabilized architecture + revised plan |
| **Exit condition** | CI green, PR merged | Design survives a spike without structural change |
| **Gates** | Changelog, diary, tests, CI | None — spikes are disposable |

### The actual process today (clarified)

The current workflow is not pure manual exploration — it's a **phased hybrid**:

```
┌──────────────────────────────────────────────────────────────────┐
│              ARCHITECTURAL PLANNING (human)                       │
│                                                                  │
│  Problem → Architecture doc → Phased implementation plan         │
│                                                                  │
│  Phase 0: configs + validation                                   │
│  Phase 1: dispatcher skeleton                                    │
│  Phase 2: pipeline worker                                        │
│  Phase 3: integration + cutover                                  │
└──────────────────────┬───────────────────────────────────────────┘
                       │ split into FRs
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              PHASE EXECUTION (watcher)                            │
│                                                                  │
│  FR-1 → plan→judge→enforce→merge                                │
│  FR-2 → plan→judge→enforce→merge                                │
│  FR-3 → plan→judge→enforce→merge                                │
└──────────────────────┬───────────────────────────────────────────┘
                       │ phase complete
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              REVISION (human)                                     │
│                                                                  │
│  Review what the phase produced                                  │
│  Update architecture doc based on evidence                       │
│  Revise plan for next phase                                      │
│  Repeat until done                                               │
└──────────────────────────────────────────────────────────────────┘
```

This is already structured: the architecture plan provides the exploration, phases provide graduation boundaries, FRs within a phase are enforcement-ready work, and the post-phase revision closes the learning loop.

### What's working

- **Architecture doc is the exploration artifact.** It absorbs the learning. Each phase revision makes it more grounded in implementation reality.
- **Phases are natural graduation boundaries.** A phase contains FRs that share assumptions. If those assumptions hold, the watcher executes cleanly. If they break, the phase reveals it.
- **The watcher handles the mechanical work.** Within a stable phase, plan→judge→enforce is the right tool. It catches defects, enforces gates, produces auditable PRs.

### What's not working (where crashes happen)

- **Phase-level FRs that are too architectural for the watcher.** The FSM configs (gh-238/239/240) are design artifacts, not implementation tasks. The watcher tried to write acceptance tests for config files that don't have a runner yet — premature enforcement on exploration-stage work.
- **No routing signal.** The watcher treats every inbox item identically. It doesn't distinguish "implement this scoped change" from "design this new subsystem."
- **Phase boundaries are manual and implicit.** Nothing in the system tracks which phase we're in or triggers the revision step.

### Can the phased process be automated?

The phases themselves can't — they require architectural judgment about what to build next. But the **scaffolding around phases** can:

1. **Phase definition** — A phase manifest (YAML) listing the FRs, their dependency order, and the architecture doc they derive from. The watcher processes FRs in order within a phase.

2. **FR classification at intake** — When an inbox item arrives, a classifier checks: does it fit within the current phase (touches only files/interfaces already defined)? Or does it require new architecture (references abstractions that don't exist)?
   - **Phase-fit** → route to enforcement pipeline
   - **Architecture-needed** → park it, flag for human-led planning

3. **Phase completion trigger** — When all FRs in a phase manifest are merged, automatically generate a revision prompt: "Phase N complete. Here's what was built [diff summary]. Here's what the architecture doc predicted [doc excerpt]. Where do they diverge? What should change for Phase N+1?"

4. **Revision assist** — A copilot node that diffs the architecture doc against the merged code, highlights divergences, and drafts revision suggestions. The human decides, the automation highlights.

### Classification signals (for routing)

1. **No existing interface** — FR references types/modules that don't exist in the codebase → architecture work
2. **Cross-phase dependency** — FR needs output from a later phase → ordering problem, needs human rethink
3. **Pattern exists** — Similar node type, similar test pattern, similar graph structure already in codebase → enforcement-ready
4. **Config-only scope** — FR produces YAML/config without code that exercises it → design artifact, not implementation

### What this looks like concretely

```yaml
# .chaplain/config/phase-manifest.yaml
architecture_doc: docs/plan-watcher-fsm.md
current_phase: 0
phases:
  0:
    name: "Config + validation"
    frs: [gh-238, gh-239, gh-240]
    exit_criteria: "Both FSM configs pass statemachine-validate"
  1:
    name: "Dispatcher skeleton"
    frs: []  # generated after phase 0 revision
    exit_criteria: "Dispatcher polls inbox and spawns workers"
```

The watcher reads the manifest, processes FRs in the current phase, and triggers the revision prompt on phase completion. The revision produces the next phase's FRs.

The watcher's current plan→judge flow tries to get the architecture right on the first pass. That works when the pattern exists. When it doesn't, the plan is fiction — plausible-looking but untested. The spike→reflect→revise loop replaces planning confidence with implementation evidence.

### Practical next step

The exploration pipeline could be a YAMLGraph graph itself — a meta-graph that orchestrates spikes. Each spike is a subgraph invocation with relaxed gates. The reflect node reads the spike diff and produces structured learning. The revise node updates the architecture doc. The graduation check is a copilot node that compares spike diff against architecture and returns `stable` or `diverged`.

This would make YAMLGraph self-hosting for its own development process — eating the dog food at the meta level.
