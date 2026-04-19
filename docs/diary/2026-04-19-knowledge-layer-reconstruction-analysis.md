# Knowledge Layer Reconstruction Analysis

**Date:** 2026-04-19
**Context:** Philosopher session — strategic analysis of YAMLGraph's documentation architecture
**Trigger:** After filing A2A refactoring FRs (#124–#126), examined which single artifact layer could reconstruct the project

## The Question

If you lost everything except one layer of YAMLGraph's knowledge — code, tests, FRs, capabilities, requirements, reference docs, diary — which one would you keep?

## The Inventory

| Layer | Files | Lines | What it encodes |
|-------|------:|------:|-----------------|
| Code (yamlgraph/) | 94 | 17,139 | The machine truth — what runs |
| Tests (tests/) | 239 | 64,621 | Behavioral contracts — what must hold |
| Feature Requests | 253 | 43,874 | Why decisions were made, how to implement, what was rejected |
| Diary | 456 | 15,253 | Cognitive traps, heuristics, seeds |
| Reference docs | 29 | 9,663 | User-facing how-to |
| Capabilities | 103 | 2,677 | Traceability index: CAP → REQ → module → FR |
| ARCHITECTURE.md | 1 | 1,584 | 257 requirements, capability table, design philosophy |

Total project prose: ~155K lines of non-code knowledge for 17K lines of code. A **9:1 documentation-to-code ratio**.

## Reconstruction Scores

| Layer | Reconstruction % | Strength | Weakness |
|-------|:-----------------:|----------|----------|
| Code | 100% (tautology) | It *is* the system | Zero rationale — no *why* |
| Feature Requests | ~85% | Intent + approach + rejected alternatives + acceptance criteria | Chronological, not structural; requires sequencing |
| Tests | ~75% | Observable behavioral contracts | No architecture, no rationale |
| ARCHITECTURE.md | ~60% | Requirements with increasing precision | No implementation approach, no alternatives |
| Diary | 0% code / 50% culture | Prevents repeat mistakes | Cannot reconstruct anything directly |
| Reference docs | ~30% | Teaches usage | Not implementation |
| Capabilities | ~20% | Shape of the system | Metadata about knowledge, not knowledge itself |

## The Verdict: Feature Requests

Feature requests are the **generative layer**. Everything else is derived:

- Code is the implementation of approved FRs
- Tests are the acceptance criteria of FRs made executable
- Capabilities are the index of completed FRs
- Requirements are the behavioral contracts extracted from FRs
- Reference docs are the user-facing distillation of FR outcomes
- Diary entries are the metacognitive residue of FR implementation

FRs are also the only artifact that would let you *disagree* with historic decisions. Code tells you what was done. FRs tell you what was considered and why. That's the difference between reconstruction and understanding.

## Observations

**Bimodal FR quality.** Early FRs (FR-005: "defer to documentation") carry less reconstruction value than recent ones (FR-208: phased implementation with error mapping tables and CLI commands). The layer's reconstruction power is concentrated in the recent 60%.

**The 9:1 ratio.** 155K lines of prose governing 17K lines of code is either profound discipline or documentation entropy. Diagnosis: **both**. The ceremony (capabilities, changelog fragments, diary gates) protects against drift but adds weight. The question isn't whether the ratio is too high — it's whether each layer *earns* its weight.

**Layers that don't earn their weight alone** but are force multipliers:
- Capabilities (2.7K lines) — worthless for reconstruction, essential for `req_coverage.py` and traceability gates
- Diary (15K lines) — worthless for reconstruction, essential for preventing the same trap twice

**The specification is larger than the implementation.** 253 FRs at 44K lines is 2.5x the 17K lines of code they govern. This is a feature, not a bug — the specification encodes decisions the code cannot express.

## Trap Identified

**documentation_as_substitute**: Measuring documentation health by volume, not by reconstruction power. A 2,677-line capability layer that scores 20% reconstruction is not 5x less valuable than tests — it serves a different purpose (traceability, not reconstruction). Confusing the purpose leads to either over-documenting (write more to close gaps) or under-documenting (this layer doesn't reconstruct, so why maintain it).

**Cure**: Each layer has a *primary purpose* independent of reconstruction:

| Layer | Primary Purpose |
|-------|----------------|
| Code | Execution |
| Tests | Regression detection |
| FRs | Decision archaeology |
| Capabilities | Traceability gates |
| Requirements | Behavioral contracts |
| Reference | User onboarding |
| Diary | Cognitive pattern library |

Evaluate each layer against its primary purpose, not against reconstruction. Reconstruction is a secondary benefit that only FRs happen to maximize.

## Seed

*If FRs are the generative layer, should the system be restructured to make FRs the primary interface for AI agents — generating code, tests, capabilities, and docs from approved FRs rather than the current manual pipeline? The Chaplain already does Plan → Judge → Enforce, but the enforce step writes code, not generates from FR spec. What would FR-as-source-code look like?*
