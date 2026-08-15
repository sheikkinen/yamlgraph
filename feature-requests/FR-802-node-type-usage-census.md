# Feature Request: FR-802 Node-Type Usage Census and Retirement Disposition

**Priority:** MEDIUM
**Type:** Enhancement (subtractive)
**Status:** Judged — APPROVED WITH REVISIONS (2026-08-15, R-1..R-6 folded below)
**Effort:** 1 day (census + disposition doc; retirements are follow-up FRs)
**Requested:** 2026-08-15
**Prior art:** FR-802-node-type-usage-census.judgement.md — this FR's own judgement (self-pair). FR-708-llm-client-request-timeout.md, FR-777-shared-shell-toolbelt-manifests.md, FR-709-race-loser-teardown-integration.md, FR-713-persistent-bridge-loop.md — lexical noise on generic nouns (type/census); none concerns node-type inventory or retirement; unrelated. Substantive prior art (FR-465/FR-466 retirement lifecycle, FR-797) is dispositioned by exact path in Related below.
**First consumer / first event:** the FR-466 CAP-retirement pipeline, at the moment the next retirement FR is authored — the census's keep/merge/retire table is its evidence base. Second consumer: the 2026-Q4 kill-risk review (docs/diary/2026-08-15-market-research.md).

## Summary

Mechanical census of all 11+ node types (`llm`, `router`, `agent`, `tool`, `map`, `tool_call`, `race`, `interrupt`, `passthrough`, `copilot`, `subgraph`, nested `python`) across every real consumer and demo, ranked by incident density — producing a keep/merge/retire disposition per node type that future add/retire FRs must cite or update (evidence base, not deletion authority — R-6).

## Value Statement

The maintainer stops paying the langgraph-upgrade tax (FR-797 class) for node types no consumer exercises, and retirement FRs get a licensed evidence base instead of ad-hoc justification.

## Problem

The 2026-08-15 market research cross-check found the framework's most complex consumer (ninchat_voice: 11 graphs, 40+ prompts, production PSTN) uses only `interrupt`, `race`, `llm`, and checkpointer + inline schemas. `router`, `map`, and `subgraph` are unexercised by it, yet `subgraph` alone just consumed a full investigation + fix arc (FR-797) driven by a langgraph 1.x behavior change. Maintenance cost is distributed across all node types; consumer value is concentrated in a few. Nobody has measured the distribution — the census does not exist, so every retirement conversation restarts from zero (`growth_as_default`'s mirror: unmeasured accretion).

## Ideal Result

One committed document ranks every node type by (a) usage count per consumer class (production project / demo / test-only), (b) diary + FR incident density, (c) named future consumers — and states a keep/merge/retire disposition per type. Any future "add node type" or "retire node type" FR must cite it or update it. The runtime shrinks toward its proven primitives; nothing with a named consumer is touched.

## Proposed Solution

1. **Source inventory (R-1, structural discovery):** the census starts from every committed YAML graph artifact discovered by *structure*, not a hand-maintained path list. Graph-artifact predicate: a YAML document with a `nodes:` mapping whose entries carry `type:` fields. Classify each hit by root (`projects/`, `examples/demos/`, other `examples/` — e.g. `examples/dungeon_master/` from FR-466-dungeon-master, root `graphs/`, `tests/` fixtures). Include an exclusion appendix listing every candidate YAML considered but not counted, with reason.
2. **Typed extraction with raw evidence (R-2):** each census row is backed by raw evidence listing `file`, `node name`, `node type`, `consumer class`. The observed type set is cross-checked against the node factory dispatch registry (not a hand-list). The census document embeds the exact no-network command lines that reproduce both the registry type list and the usage table. A transient one-off parser is allowed during enforcement; no permanent script or tooling is authorized by this FR (C-5: if impossible without permanent tooling, stop and file a separate tooling FR).
3. **Incident-density pass (R-3, explicit formula):** `incident_count` = number of FR/diary entries whose problem, fix, or judgement directly concerns that node type *as a runtime primitive*; `usage_count` from the census; `incident_density = incident_count / max(usage_count, 1)`. Each included incident cites its path and the reason it is node-type-specific. Ambiguous text hits (high-noise terms: `map`, `tool`, `agent`) are excluded or listed separately as non-incidents.
4. **Future-consumer pass (R-4, committed evidence only):** a future consumer requires a committed citation and a named first event. Known: `subgraph` has the ninchat_voice backlog-navigator plan — cited via FR-797 (which quotes `projects/ninchat_voice/backlog.txt:48-58`); that is *secondary* evidence and the row must label it so. No row may be dispositioned `KEEP-with-consumer` from author memory, chat context, or an uncommitted backlog.
5. **Disposition table (R-6, evidence not authority):** per node type — KEEP (production consumer), KEEP-with-consumer (committed future-consumer citation), MERGE (target type + migration note), RETIRE (names the follow-up FR-466-lifecycle step). The table is binding as the evidence source future add/retire-node FRs must cite or update; it does NOT authorize runtime code changes, graph artifact rewrites, test deletion, CAP retirement, or node removal in FR-802.
6. Deliverables: `docs/node-type-census-2026-08.md` + this FR updated with the table. Only those two files change.

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: FR-802 amended with R-1..R-6 before enforcement (this revision)
- [ ] AC-02: census lists the node factory dispatch registry source; one row per registered node type; no hand-written type list
- [ ] AC-03: source inventory discovers committed graph artifacts by YAML structure, classifies every counted artifact by consumer class, lists excluded YAML candidates with reasons
- [ ] AC-04: each usage row cites raw evidence (`file`, `node name`, `node type`, `consumer class`) plus exact no-network reproduction commands
- [ ] AC-05: incident density computed from the explicit formula; each incident cites path + node-type-specific reason; ambiguous hits excluded or listed as non-incidents
- [ ] AC-06: future-consumer claims cite committed evidence + named first event; secondary evidence labeled; `subgraph` dispositioned against the FR-797 backlog-navigator citation, not current runtime usage
- [ ] AC-07: every disposition ∈ {KEEP, KEEP-with-consumer, MERGE, RETIRE}; MERGE names target + migration note; RETIRE names the FR-466 lifecycle step
- [ ] AC-08: table states explicitly it is evidence for future FRs, not authority to change code or remove node types
- [ ] AC-09: only `docs/node-type-census-2026-08.md` and this FR are changed

## Alternatives Considered

- **Retire by intuition (status quo):** each retirement argument restarts from zero; rejected — this is the problem.
- **Line-count ranking:** rejected by Scripture (`inventory_by_visibility` trap — the FSM bridge was 4% of source and 26% of diary).
- **Fold census into each retirement FR:** duplicates the measurement N times and invites inconsistent counts.

## Related (prior art dispositioned by exact path, R-5)

- docs/diary/2026-08-15-market-research.md — verdict licensing subtraction
- feature-requests/FR-466-cap-retirement-support.md — the CAP retirement lifecycle this census feeds (binding precedent)
- feature-requests/FR-465-watcher2-test-cleanup.md — retirement executed as separate lifecycle work (binding precedent)
- feature-requests/FR-465-llm-safety-settings.md — duplicate FR ID, unrelated subject; not prior art here
- feature-requests/FR-466-dungeon-master-example.md — duplicate FR ID; relevant only as evidence that non-demo `examples/` graph roots exist (R-1)
- feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md — maintenance-tax exhibit; secondary citation for the `subgraph` future consumer
- Scripture: `incident_density_ranking`, `growth_as_default`, `would_you_use_this`

## Judgement (2026-08-15)

**Verdict:** APPROVED WITH REVISIONS — see [FR-802-node-type-usage-census.judgement.md](FR-802-node-type-usage-census.judgement.md). R-1..R-6 folded above. Gates: C-1 fold-first (done), C-2 no runtime/graph/test/CI changes, C-3 dispositions are not implementation authority, C-4 committed citations only, C-5 no permanent tooling — file a separate FR if needed.
