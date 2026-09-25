# Judgement: FR-1065 Resumable map investigation

**Prior art:** `FR-1065-resumable-map-investigation.md` is the FR this judgement governs. FR-956 (map timeout lifecycle) is a sibling investigation kept separate under the FR-936 split. FR-798 and FR-922 match only on "investigation"; they cover test-suite failures and recap latency.

**Verdict:** APPROVED WITH REVISIONS — the investigation has substantive alternative classes and a real first consumer; authority to run scoped probes activates only after the revisions below are folded.

**Reviewed against:** `feature-requests/FR-1065-resumable-map-investigation.md`; `feature-requests/FR-1031-census-extract-cache-dir.judgement.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `docs/issues-2026-09-24.md`; `docs/plan-web-toolkit.md` (component D, cited by the FR); `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The plan's prior-art inventory separates checkpoint continuation from cross-run item reuse (plan sections 5.1 and 6.4). FR-1065:76-87 correctly poses two unresolved, cost-dominating questions instead of presenting an untested store as a solution. Five solution classes with dissent for graph-owned reuse, cited precedents and an `is_this_a_graph` answer are present (FR-1065:145-175); this meets the in-body research alternative permitted by doctrine. Classification: investigation of a framework primitive with more than three named reuse consumers (FR-1065:37-42, 147-169), not permission to build the primitive.

## Required revisions

### R-1: Replace fix-shaped acceptance with investigation witnesses

FR-1065:128-139 requires a two-run fixture, `--refresh`, node-version invalidation and a ledger even though the FR is investigation-only and those interfaces do not exist. Rewrite ACs to require executable *probes* for store concurrency, checkpoint size, batch composition and killed-process recovery on minimal LangGraph fixtures; tests may run RED against the existing map only when the current map has the relevant interface. Put new runtime fields and two-run assertions in the successor fix FR, not here. Record probe output and precise limitations in a committed report.

### R-2: Treat proposed storage semantics as hypotheses

FR-1065:93-109 calls the cache selection, node-version derivation, permanent-failure retention and JSONL locking "Decided" before its own store and scheduling experiments. Label these candidate contracts, and make the report select or reject each with a witness. Verify persistence across two processes and check `kill -9` versus graceful interrupt separately; do not assume a LangGraph cache API is a result store with durable single-copy guarantees (plan section 6.3).

### R-3: Fence dependencies and human cost decisions

The investigation's probes may use minimal stand-alone fixtures before FR-1064/FR-955/FR-939 exist; production integration must wait for independently judged successors (FR-1065:180-183). Ask the human explicitly: **May the 26 state-collect consumers change to store reads, or must existing `collect` semantics remain available?** Report checkpoint bytes and migration counts for both choices before seeking an implementation verdict (FR-1065:77-85, 119-124). Name the pilot's acceptable spend/storage budget in that report or leave the choice to human review.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Minimal stand-alone LangGraph probe tests for store concurrency and chunked Send behavior |
| D-2 | Reproducible checkpoint-size and killed-process resume measurements |
| D-3 | Committed investigation report and a separately judged fix FR |
| D-4 | Status correction to `feature-requests/032-node-level-caching.md`, after its no-backend witness |

Not authorized: new map `cache:`, `ledger:`, `version:`, `node_version:`, `--refresh`, store integration, consumer migration or permanent-failure retention in production. Do not change `yamlgraph/compile/` under this investigation.

## Revised acceptance criteria

- [ ] AC-01: Probe concurrent SQLite-cache reads/writes from branches and two processes; report collisions, latency and persistence with executable commands.
- [ ] AC-02: Compare serialized checkpoint size for 10k results in state and a store-only result; report the cost of the 26 collect consumers under both contracts.
- [ ] AC-03: A bounded-batch fixture demonstrates scheduling and join behavior at 10k items, with memory measured and FR-944/FR-1064 join compatibility recorded as tested or blocked.
- [ ] AC-04: A controlled killed-process fixture reports exactly which successful items rerun; distinguish thread checkpoint resume from cross-run result reuse.
- [ ] AC-05: A committed report selects or rejects candidate key/version/retention/locking semantics with evidence, records the human consumer-contract decision, and links a new fix FR; no implementation is claimed by the investigation.
- [ ] AC-06: FR-032's cache claim is corrected only after a probe confirms whether `compile(cache=...)` is passed by any runtime route.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into FR-1065 before running or committing the investigation probes. | GATE |
| C-2 | Human decides store-read versus state-collect consumer contract before any fix FR gains implementation authority. | GATE |
| C-3 | No production runtime, schema, cache or ledger change under this investigation. | GATE |

Authority granted: after revisions are folded, conduct only the bounded investigation and file its evidence-backed successor FR.
