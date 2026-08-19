# Judgement: FR-824 HVA Weekly Governance and Procurement Bulletin — New Repository

**Verdict:** APPROVED WITH REVISIONS — the new-repo bulletin direction is sound, but authority activates only after R-1 through R-3 are folded into the FR.

**Reviewed against:** `feature-requests/FR-824-hva-weekly-bulletin-new-repo.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/FR-821-weekly-recap-automation-pr.md`; `../control-plane/docs/github-runner-weekly-recap-research.md`; `../control-plane/docs/information-landscape.md`; `../control-plane/docs/hva-probe-architecture-plan.md`; `../control-plane/scripts/hva-probe-orchestrator.sh`; `../control-plane/scripts/hva-procurement-bulletin.sh`.

**Prior art:** FR-819 is reused for separate-repo committed-state publication;
FR-821 is reused for weekly no-op and cron-evidence semantics; FR-046 and
FR-782 concern different digest/self-portrait consumers and do not overlap the
HVA governance/procurement bulletin. FR-824 is the judged target, not precedent.

## What is sound

The FR names a real first consumer and event: the operator reading `bulletins/<ISO-week>.md` on Monday instead of running `control-plane` or polling sources manually. It correctly chooses a separate public repository boundary to avoid mixing public OSINT automation with `control-plane` device and personal-data probes, matching the research warning that root-level glob-running probes would be a privacy defect.

The core architecture follows the evidence: collect daily, persist compact state/events, synthesize weekly, and organize by lifecycle threads rather than source inventory. The FR also preserves strong boundaries: Pydantic normalization before persistence, deterministic IDs/hashes before model synthesis, no removal inference from bounded indexes, and topical similarity as candidate-only linking. Those choices align with repo doctrine to normalize at the boundary and distrust plausible model links.

The prior-art disposition is adequate. FR-819 proves an unprotected public repo with PyPI YAMLGraph, committed state, direct `GITHUB_TOKEN` commits, no-op behavior, and governed graph authoring evidence. FR-821 proves scheduled weekly publication, substantive no-op detection, PAT/PR behavior for protected repos, and separate cron evidence. FR-824 distinguishes both and intentionally chooses the FR-819 direct-commit model for the new unprotected publication repo.

Strategic classification: **Contrib/example consumer deployment**, not a framework primitive. The FR consumes YAMLGraph from PyPI and explicitly avoids YAMLGraph package, CAP/REQ, graph, prompt, example, or `control-plane` source changes. It has one concrete consumer and one deployment product, so it does not justify a YAMLGraph core abstraction.

## Required revisions

### R-1: Persist source-health observations in a committed, bounded contract

Fold a concrete `source_health/<YYYY-Www>.jsonl` or equivalent committed state/event contract into the repository layout, workflow staging rules, and acceptance criteria. The FR says every collection produces a typed census and that the weekly bulletin cannot claim healthy coverage when endpoints failed during its window, but the proposed staged paths originally omitted a persisted health ledger. Without one, a Monday bulletin cannot mechanically know that a Wednesday HVA endpoint failed if no source item changed.

The revision must specify the health schema fields, deterministic/noise-free update rules, retention path, and scoped staging. Health records may not force a commit solely because durations or timestamps changed unless the FR explicitly defines that as meaningful operational truth.

### R-2: Freeze a mechanically testable materiality and ordering policy

Add a bounded policy for how the main bulletin selects, orders, and caps narrative entries before the full event-ledger appendix. The FR says the graph will select and summarize the most material changes and the renderer includes capped narrative sections plus a complete event ledger, but no original acceptance criterion proved what "material" meant. The cited research leaves this as an open question: money, deadline, lifecycle transition, cross-organization recurrence, or a scored combination.

Fold a deterministic materiality contract into the FR, such as priority tiers for disputes, lifecycle transitions, deadline proximity, value, cross-HVA recurrence, and source-health degradation. Add a fixture-backed AC proving ordering/capping behavior and proving that capped-out events still appear in the appendix.

### R-3: Correct the normalized model contract and make copied examples non-authoritative

Fix the `SourceItem` example so it is valid Python/Pydantic and cannot be copied into the new repo broken. The `source_urls` field was over-indented inside the code block. Fold the corrected field shape into the FR and add an AC that the model module imports and the example schema is exercised by unit tests, not merely described in prose.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | New public `sheikkinen/hva-weekly-bulletin` repository outside YAMLGraph and `control-plane` |
| D-2 | Public-only source adapters for `ktweb`, `dynasty`, `casem`, `hilma`, `ted`, and `mao` |
| D-3 | Pydantic models for source items, events, threads, bulletin output, and source health |
| D-4 | Durable compact state, weekly event ledger, and source-health ledger |
| D-5 | Daily `collect.yml` workflow with scoped permissions, allowlist, concurrency, no-op, pull/rebase, and scoped staging |
| D-6 | Monday `bulletin.yml` workflow with exact seven-day UTC window, scoped secret exposure, no-op behavior, and scoped staging |
| D-7 | Governed `graph.yaml` and `prompts/*.yaml` authoring evidence for weekly synthesis only |
| D-8 | README, fixture tests, dispatch evidence, cron-observation notes, FR implementation notes, and diary evidence |

Not authorized: YAMLGraph package/CAP/REQ changes; `control-plane` behavior changes; nested repos, submodules, vendored trees, or runtime checkouts inside YAMLGraph or `control-plane`; device/local profile probes; sources beyond HVA governance, Hilma/TED, and MAO; removal inference; branch-protection/ruleset changes; admin PATs or protection-bypassing credentials; GitHub Pages, RSS, Slack, email, hosted APIs, subscriptions, dashboards, or generalized probe-framework work.

## Revised acceptance criteria

- [ ] AC-01: Public `sheikkinen/hva-weekly-bulletin` exists outside both YAMLGraph and `control-plane`; neither source repo contains it as nested repo, submodule, vendor tree, generated artifact, or runtime checkout.
- [ ] AC-02: The new repo contains no device probe, local `~/Library` path, Safari/Messages/WhatsApp/Biome/Apple Intelligence extraction, personal profile output, or personal-data secret.
- [ ] AC-03: Fixture-backed unit tests validate all six normalized source values (`ktweb`, `dynasty`, `casem`, `hilma`, `ted`, `mao`) through Pydantic and reject missing stable IDs, titles, organizations, or source URL maps.
- [ ] AC-04: The model module imports cleanly; the corrected `SourceItem`, `SourceEvent`, thread, bulletin, and source-health contracts are exercised by unit tests.
- [ ] AC-05: First collection seeds state and emits zero events; second changed fixture emits exactly one deterministic event; third identical run emits zero events and changes no tracked state/event/health file except as explicitly allowed by the health contract.
- [ ] AC-06: Hash tests prove fetch timestamp, ordering, whitespace, duration, and observation-only noise do not emit `updated`; a substantive deadline/status/value/title change emits `updated` with exact `changed_fields`.
- [ ] AC-07: Hilma/TED fixtures sharing a publication ID normalize to one procurement item retaining both source URLs; no fuzzy match is needed.
- [ ] AC-08: The canonical configuration enumerates exactly 22 HVAs and maps every one to a supported governance adapter; workflow census attempts all configured entries and exposes every failure.
- [ ] AC-09: No source adapter or delta code emits `removed`; a fixture absent from a bounded follow-up index remains state, not a fabricated withdrawal.
- [ ] AC-10: Confirmed thread tests cover exact docket, explicit prior handling, and Hilma/TED publication-ID edges; topical similarity alone remains a candidate and cannot merge threads.
- [ ] AC-11: A fixture seven-day event window renders all frozen bulletin sections, source links, event IDs, link bases, source-health status, and complete event-ledger appendix; no section claims healthy coverage when committed health records contain errors.
- [ ] AC-12: Materiality fixture tests prove deterministic ordering/capping of the narrative sections and prove capped-out events remain present in the event-ledger appendix.
- [ ] AC-13: An empty seven-day event window exits 0, writes no bulletin, and the workflow logs a distinct no-op without committing.
- [ ] AC-14: `collect.yml` has daily cron, dispatch, contents-write permission, hard adapter allowlist, shared non-cancelling concurrency, scoped staging for state/events/health only, safe pull/rebase, and explicit no-op behavior.
- [ ] AC-15: `bulletin.yml` has Monday 06:00 UTC cron, dispatch, the same concurrency group, exact seven-day UTC window, scoped secret exposure, scoped staging for `bulletins/` only, safe pull/rebase, and no-op behavior.
- [ ] AC-16: A dispatched baseline collector run completes green; a later dispatched run proves durable cross-run delta/no-op behavior, with run URLs and commit SHAs recorded in Implementation Notes.
- [ ] AC-17: A dispatched bulletin run publishes one non-empty real-source bulletin; a repeated unchanged dispatch produces no duplicate bulletin or event, with evidence recorded.
- [ ] AC-18: The first real scheduled collector and Monday bulletin runs are observed and recorded; until both occur, status explicitly carries "cron observation pending" — dispatch evidence is not cron evidence.
- [ ] AC-19: `graph.yaml` and prompts are authored/adapted through `scripts/author.sh`; retained report records lint and smoke results. The graph consumes typed events, confirmed thread edges, source-health records, and the frozen materiality contract; it does not perform source fetching, delta, deterministic linking, health persistence, or Markdown serialization.
- [ ] AC-20: README documents consumer, source coverage, cadence, state/event/health contracts, privacy boundary, materiality policy, source-health semantics, local fixture test, manual dispatch, and the direct-commit security model.
- [ ] AC-21: YAMLGraph repository changes for enforcement are limited to this FR's status/implementation notes and required diary evidence; no package, CAP/REQ, graph, prompt, example, or `control-plane` source change is smuggled into this FR.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-3 must be folded into the FR before implementation authority activates. | GATE |
| C-2 | The enforcer must not re-run the judge; this judgement is advisory until human-reviewed. | GATE |
| C-3 | Any `graph.yaml` or `prompts/*.yaml` creation/adaptation must use the governed graph-authoring route and retain the authoring report, lint, and smoke evidence. | GATE |
| C-4 | Repository boundary is load-bearing: no nested repo, submodule, vendored tree, generated subtree, or runtime checkout inside YAMLGraph or `control-plane`. | GATE |
| C-5 | Public-data boundary is load-bearing: no device/local-profile probe, personal-data source, unbounded raw response body, or secret value may enter the public repo. | GATE |
| C-6 | Human review is required before relying on any public-repo secret or permission beyond `ANTHROPIC_API_KEY` and the scoped default `GITHUB_TOKEN`. | GATE |
| C-7 | Branch protection, PAT automation PRs, admin credentials, or repository ruleset changes are separate scope. | GATE |
| C-8 | The FR is not complete until both dispatch evidence and first real scheduled cron observations are recorded; dispatch evidence must not be represented as cron evidence. | GATE |

Authority granted: after R-1 through R-3 are folded and human-reviewed, the enforcer may build the separate `hva-weekly-bulletin` publication repository and record only the required YAMLGraph FR, judgement, implementation-note, and diary evidence in this repository.
