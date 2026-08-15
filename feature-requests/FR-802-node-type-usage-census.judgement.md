# Judgement: FR-802 Node-Type Usage Census and Retirement Disposition

**Prior art:** FR-802-node-type-usage-census.md — the governing FR of this judgement (self-pair); substantive prior art dispositioned in R-5.

**Verdict:** APPROVED WITH REVISIONS - the census is a sound pattern-documentation evidence base for subtraction, but authority activates only after the FR closes source-root gaps, defines the incident-density method, and disambiguates its cited prior art.

**Reviewed against:** `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-802-node-type-usage-census.md`; `docs/diary/2026-08-15-market-research.md`; `feature-requests/FR-465-watcher2-test-cleanup.md`; `feature-requests/FR-465-llm-safety-settings.md`; `feature-requests/FR-466-cap-retirement-support.md`; `feature-requests/FR-466-dungeon-master-example.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md`; `feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.judgement.md`.

## What is sound

The problem is real and strategically aligned. The market research explicitly concludes that runtime investment should move toward subtraction and a smaller, boring runtime (`docs/diary/2026-08-15-market-research.md:33-38`), and its ninchat_voice cross-check says the largest production consumer exercises `interrupt`, `race`, checkpointer, and schema-templated prompts while not exercising `router`, `map`, or `subgraph` (`docs/diary/2026-08-15-market-research.md:39-59`). FR-802 uses that evidence for a measured keep/merge/retire inventory rather than a deletion-by-intuition argument (`feature-requests/FR-802-node-type-usage-census.md:18-32`).

The first consumer is named and concrete: the FR-466 CAP-retirement pipeline at the next retirement FR authoring event, plus the 2026-Q4 kill-risk review (`feature-requests/FR-802-node-type-usage-census.md:7-8`). The deliverable is also appropriately non-code: one document plus the FR table, with retirements reserved for follow-up FRs (`feature-requests/FR-802-node-type-usage-census.md:31-41`). That matches the CAP retirement precedent, where FR-466 creates retirement support while actual retirements happen in separate lifecycle work (`feature-requests/FR-466-cap-retirement-support.md:9-15`, `:118-127`; `feature-requests/FR-465-watcher2-test-cleanup.md:41-54`, `:76-79`).

The strategic classification is **Pattern documentation**. This FR does not create a framework primitive or a new example; it creates the evidence base future primitive-retirement FRs must cite. That is the right classification for a census whose value is governance and prioritization, not runtime behavior.

## Required revisions

### R-1: Replace the incomplete graph-source list with a mechanically complete source inventory

FR-802 claims coverage across every real consumer and demo (`feature-requests/FR-802-node-type-usage-census.md:10-12`), but the proposed command roots only name `projects/*/graphs/**/graph.yaml`, `examples/demos/*/graph.yaml`, `graphs/*.yaml`, and test fixtures (`feature-requests/FR-802-node-type-usage-census.md:26-32`). That omits committed non-demo examples evidenced by prior FRs, including `examples/dungeon_master/` delivered by FR-466 (`feature-requests/FR-466-dungeon-master-example.md:193-207`) and the NPC/eBook example lineage (`feature-requests/FR-466-dungeon-master-example.md:169-175`).

Fold this into the FR: the census must start from every committed YAML graph artifact discovered by structure, not from a hand-maintained path list. Define the graph-artifact predicate as "a YAML document with a `nodes:` mapping containing node entries with `type:` fields," classify each hit by root (`projects/`, `examples/demos/`, other `examples/`, root `graphs/`, `tests/fixtures` or equivalent), and include an exclusion appendix for any YAML file considered but not counted.

### R-2: Define a typed extraction method and raw evidence appendix

The current "grep `type:`" instruction (`feature-requests/FR-802-node-type-usage-census.md:28`) is too weak for a binding disposition table: it can count non-node YAML keys and cannot prove which node name produced a count. The acceptance criteria ask for reproducible command lines (`feature-requests/FR-802-node-type-usage-census.md:34-41`), but not for the raw hit list needed to audit the numbers.

Fold this into the FR: each census row must be backed by raw evidence listing at least `file`, `node name`, `node type`, and `consumer class`. The method must cross-check the observed type set against the node factory dispatch registry as required by AC-01 (`feature-requests/FR-802-node-type-usage-census.md:36`), and the document must show the exact no-network command(s) used to produce both the registry type list and the usage table. A temporary one-off parser is allowed during enforcement, but no permanent script or tooling is authorized by this FR.

### R-3: Specify the incident-density formula and false-positive handling

FR-802 requires an incident-density pass (`feature-requests/FR-802-node-type-usage-census.md:29`) and cites the `incident_density_ranking` cure (`.github/copilot-instructions.md:91-95`, `:112-115`), but it does not define the denominator, inclusion rule, or treatment for high-noise terms such as `map`, `tool`, or `agent`. A table of bare path counts would reproduce the `research_as_inventory` trap rather than producing analysis (`.github/copilot-instructions.md:91-94`).

Fold this into the FR: define `incident_count` as the number of cited FR/diary entries whose problem, fix, or judgement directly concerns that node type as a runtime primitive; define `usage_count` from the census; define `incident_density = incident_count / max(usage_count, 1)` unless the FR chooses a different explicit formula. Each included incident must cite the path and the reason it is node-type-specific. Ambiguous text hits must be excluded or listed separately as non-incidents.

### R-4: Bound the future-consumer sweep to committed evidence

The future-consumer pass says to sweep open FRs and project backlogs, with `subgraph` already known to have a ninchat_voice backlog-navigator plan (`feature-requests/FR-802-node-type-usage-census.md:30`). The cited support is secondary evidence in FR-797: it quotes `projects/ninchat_voice/backlog.txt:48-58` as a named forward demand while also stating current ninchat_voice usage is only top-level `interrupt` plus `Command(resume)` (`feature-requests/FR-797-subgraph-interrupt-propagation-langgraph-1x.md:7-10`).

Fold this into the FR: a future consumer must have a committed citation and a named first event. If the backing project backlog is outside this repository or not committed here, the census may cite the committed FR that quotes it, but the row must label the evidence as secondary. No row may be dispositioned `KEEP-with-consumer` from author memory, chat context, or an uncommitted backlog.

### R-5: Disambiguate FR-465 and FR-466 prior art by exact file path

The Related section cites "FR-465 / FR-466" as the CAP retirement lifecycle (`feature-requests/FR-802-node-type-usage-census.md:49-53`), but this repository contains duplicate FR IDs with unrelated subjects: `FR-465-watcher2-test-cleanup.md`, `FR-465-llm-safety-settings.md`, `FR-466-cap-retirement-support.md`, and `FR-466-dungeon-master-example.md`. A judge or enforcer cannot know which precedent is binding from the ID alone.

Fold this into the FR: replace ambiguous ID-only references with exact file paths and one-sentence dispositions. The relevant retirement lifecycle prior art is `feature-requests/FR-466-cap-retirement-support.md` plus `feature-requests/FR-465-watcher2-test-cleanup.md`; `FR-465-llm-safety-settings.md` is unrelated, and `FR-466-dungeon-master-example.md` is relevant only as evidence that non-demo `examples/` graph roots exist.

### R-6: State that disposition rows are evidence, not deletion authority

FR-802 calls the disposition table "binding" (`feature-requests/FR-802-node-type-usage-census.md:10-12`), while also saying actual retirements are separate FRs and zero production code changes are allowed (`feature-requests/FR-802-node-type-usage-census.md:31-41`). Preserve the useful binding effect but remove any chance that enforcement treats a `RETIRE` row as authority to delete code.

Fold this into the FR: the table is binding as the evidence source future add/retire-node FRs must cite or update; it does not authorize runtime code changes, graph artifact rewrites, test deletion, CAP retirement, or node removal in FR-802.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `docs/node-type-census-2026-08.md` containing source inventory, raw usage table, incident-density method and evidence, future-consumer citations, and keep/merge/retire disposition table |
| D-2 | `feature-requests/FR-802-node-type-usage-census.md` updated with folded revisions, final table summary, implementation status, and any deviations |
| D-3 | Reproducible command lines embedded in the census document; transient local scratch commands are allowed, but no committed tooling is authorized |

Not authorized: production/runtime code changes; node factory changes; compiler, linter, schema, hook, CI, or requirement-registry changes; graph or prompt artifact edits; test deletion; CAP retirement; node deprecation or removal; new permanent scripts; graph-authoring; running another judge.

## Revised acceptance criteria

- [ ] AC-01: FR-802 is amended with R-1 through R-6 before enforcement authority activates.
- [ ] AC-02: The census document lists the node factory dispatch registry source and includes one row for every registered node type; no row is sourced from a hand-written node-type list alone.
- [ ] AC-03: The census source inventory discovers committed graph artifacts by YAML structure, classifies every counted artifact by consumer class, and lists excluded candidate YAML files with reasons.
- [ ] AC-04: Each usage row cites raw evidence containing `file`, `node name`, `node type`, and `consumer class`, plus exact no-network command lines that reproduce the table.
- [ ] AC-05: Incident density is computed from an explicit formula; each included incident cites a diary or FR path and a node-type-specific reason; ambiguous text hits are excluded or listed as non-incidents.
- [ ] AC-06: Future-consumer claims cite committed evidence and a named first event; secondary evidence is labeled as such. The `subgraph` row is dispositioned against the FR-797 ninchat_voice backlog-navigator citation rather than current ninchat_voice runtime usage.
- [ ] AC-07: Every disposition is one of `KEEP`, `KEEP-with-consumer`, `MERGE`, or `RETIRE`; every `MERGE` row names the target type and migration note; every `RETIRE` row names the follow-up FR-466 lifecycle step.
- [ ] AC-08: The disposition table states explicitly that it is evidence for future FRs, not authority to change code or remove node types in FR-802.
- [ ] AC-09: Only `docs/node-type-census-2026-08.md` and `feature-requests/FR-802-node-type-usage-census.md` are changed by this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into FR-802 before implementation begins. | GATE |
| C-2 | Do not change runtime code, graph artifacts, prompts, tests, CAP files, CI, hooks, or permanent scripts under this FR. | GATE |
| C-3 | Do not treat a `RETIRE` or `MERGE` disposition as implementation authority; node removal or migration must re-enter the pipeline as a separate FR. | GATE |
| C-4 | Do not count future consumers from chat context or uncommitted external files; use committed citations only and label secondary evidence. | GATE |
| C-5 | If a complete census cannot be produced without new permanent tooling, stop and file a separate tooling FR rather than expanding this one. | GATE |

Authority granted: after the required revisions are folded into FR-802, enforcement may produce the node-type census document and update the FR summary/table, solely as a non-code evidence base for future retirement or merge proposals.
