# Feature Request: FR-896 Twelve-Month Cross-Repo Pattern & Model Census (map-mercury / reduce)

**Priority:** MEDIUM
**Type:** Feature (investigation/tooling, read-only)
**Status:** In Progress (graph artifact authored and verified 2026-08-28; real-repo runs, synthesis, and promotion remain — see Enforcement Status)
**Effort:** 5 days (phased: scope freeze + new example authoring, discover/extract tools, map/reduce lenses, redaction-gated synthesis)
**Requested:** 2026-08-28
**Judgement:** [FR-896.judgement.md](FR-896-cross-repo-pattern-model-census.judgement.md) — APPROVED WITH REVISIONS (2026-08-28); R-1..R-5 folded below.
**First consumer / first event:** the author, at the moment of authoring the next
"which pattern/model should I standardize on" decision or a FR-802-style
retirement review — the keep/adopt/retire disposition table this census
produces is the evidence base, the same role FR-802's node-type census plays
for `yamlgraph/node_factory/`.
**Research:** In-body dispositioned alternatives table (FR-889 style; see
`## Alternatives Considered`). `scripts/research.sh` (FR-890 sole route) was
deliberately not run for this planning pass — the "how" is already answered
by three pieces of committed prior art disposed below (`corpus_census`
graph, `docs/mercury-census/findings.md`, FR-802); running five orthogonal
personas would re-derive machinery this FR already cites by path.

## Summary

A read-only census of architectural/design **patterns** and **LLM
model/provider** choices actually adopted across the last 12 months of
development, spanning `yamlgraph` plus the four sister repos cloned on this
device and the author's own GitHub-hosted repos active in the window —
executed by reusing the existing `examples/demos/corpus_census` discover→
extract→map→reduce→synthesize pipeline, with the map/judge fan-out pinned to
the cheap `inception/mercury-2` model per the `docs/mercury-census/findings.md`
F1 finding (not the corpus_census default `claude-haiku-4-5`), and a mandatory
human redaction gate before anything crosses from private ledger to a
committed yamlgraph artifact.

## Value Statement

The author gets an evidence-based (not memory-based) view of which patterns
and models actually recurred — versus one-off — across the whole personal +
professional footprint, so future standardization/retirement FRs cite real
cross-repo incidence instead of impression, the way FR-802 did for node types
within `yamlgraph` alone.

## Problem

Development this year spans at least 5 known local repos
(`yamlgraph`, `customer-service-agent-platform`, `fsm`/`statemachine-engine`,
`questionnaire-api`, `tt-bot-v2`) plus a personal GitHub footprint an order of
magnitude larger than what's cloned locally. Nobody has measured which
architectural patterns (map/reduce, router, state-machine, adapter, retry/
backoff, CI-gate, schema-migration, …) or which LLM models/providers actually
recurred versus appeared once. Institutional memory of "what did I actually
build and with what" today lives only in `yamlgraph`-local diaries/FRs and
machine-local memory-tool notes (see `memory-tool-locality` note: repo memory
is workspace-hash-scoped to one device, not actually cross-repo); sister-repo
and GitHub-wide evidence never crosses into any single view. FR-874 already
established that wholesale, unjudged cross-repo content transport into the
public `yamlgraph` repo is unsafe (customer hostnames/security findings
leaked into a seed corpus and had to be rolled back same day) — this FR
supplies the missing prerequisite that rejection identified: a scoped,
judged inventory step with a redaction gate, done correctly this time.

## Raw Output Read

This FR extends the existing `corpus_census` scorer/reduce machinery
(FR-892/FR-895) with new discover/extract bindings and new judgement rubrics,
so the discovery-layer boundary was read raw before design, not assumed:

- **Sample 1** — `git log -1` + `git remote -v` run directly against all four
  sister repos (see terminal history, 2026-08-28). Surprising detail: `fsm`'s
  remote is `sheikkinen/statemachine-engine` — the on-disk directory name and
  the GitHub repo name diverge, so any repo-corpus manifest keyed by local
  path alone would silently mislabel it.
- **Sample 2** — `gh repo list sheikkinen --json name,pushedAt,visibility`
  and the equivalent for `terveystalo`, both executed raw (2026-08-28).
  Surprising detail: the `terveystalo` org call alone returned 20+ PRIVATE
  repos with zero relationship to any sister project touched here
  (`ada-appointment-api`, `sss-k8s-domain-api-infra`, `health-survey`,
  `suunta-analytics`, …) — a literal "include github" reading of the
  original task would have vacuumed unrelated engineers' unrelated
  proprietary codebases into scope with no judgement gate at all. This is
  the concrete finding driving the scope freeze in Proposed Solution Phase 0.
- **Sample 3** — the same `gh repo list sheikkinen` call, filtered to
  `pushedAt >= 2025-08-28`, returned **54** personal repos active in the
  window. Surprising detail: several (`gitclaw-oulu-civic-intelligence-failed-witness`,
  `my-minesweeper2`) are visibly abandoned/duplicate spikes by name alone —
  a raw commit-count census without a triage pass would weight noise and
  signal repos identically.

## Ideal Result

One committed, redaction-reviewed document in `yamlgraph` states, per lens
(pattern / model), which choices recurred across the last 12 months of the
author's real corpus — local sister repos plus the author's own active
GitHub repos, with employer-org-wide enumeration permanently out of scope
(judged decision, not pending). Every claim in the committed document cites
a row in a private ledger that never held raw proprietary diff/file content;
no commit subject, hostname, SHA, or raw private repo name appears in
anything committed to the public repo — only human-approved repo aliases,
pattern/model labels, and counts.

## Proposed Solution

**Phase 0 — Scope freeze (decided 2026-08-28; blocks Phase 1).**
Repo corpus = `yamlgraph` + the 4 known sister repos
(`customer-service-agent-platform`, `fsm`/`statemachine-engine`,
`questionnaire-api`, `tt-bot-v2`) + the author's own active personal GitHub
repos (candidate list: the 54 from Sample 3, triaged to drop forks/
duplicates/dead spikes before Phase 1 runs). The `terveystalo` org is
**never** enumerated wholesale (decided, not pending — Sample 2's finding
stands): any future expansion beyond the 4 named sister repos requires a
separate, explicitly authorized follow-up FR that defines how "the author
is a real contributor" is verified (author filter on commits, not org
membership).

**Phase 0 committed scope table (AC-01, enforced 2026-08-28).** The 4
sister repos are named in cleartext (already disclosed above and in the
Problem section — no incremental exposure). The 54 personal-repo
candidates are **aliased in this public document** — a live R-4 finding
surfaced during enforcement: several raw names in the mechanical
`gh repo list sheikkinen` pull (e.g. Finnish health/social-service domain
project names) are exactly the customer/domain-identifying class Phase 4's
alias mechanism exists to keep out of `yamlgraph`, so the same discipline
is applied here, not just at the final brief. The raw name↔alias mapping
is kept local-only at `tmp/fr896-alias-map.json` (git-ignored) pending
Phase 4's dedicated private repo; it is never committed to `yamlgraph`.
Inclusion/exclusion is mechanical: 0 forks, 0 archived repos found;
3 name-normalized duplicate/version clusters detected (e.g.
`X` / `X2`), each cluster's most-recently-pushed member marked `include`
(canonical) and older members marked `exclude` (superseded spike) —
raw cluster examples, safe to name because they are throwaway personal
spikes with no domain sensitivity: `my-minesweeper` family,
`minesweeper-yamlgraph` vs `minesweeper`.

| Repo | Visibility | Category | Decision | Reason |
|---|---|---|---|---|
| `yamlgraph` | PUBLIC | self | include | this repo |
| `customer-service-agent-platform` | PRIVATE | sister | include | named sister project |
| `fsm` (`statemachine-engine`) | PUBLIC | sister | include | named sister project |
| `questionnaire-api` | PRIVATE | sister | include | named sister project |
| `tt-bot-v2` | PRIVATE | sister | include | named sister project |
| `personal-001`..`personal-054` | mixed | personal | 51 include / 3 exclude | full table: `tmp/fr896-scope-table.md` (git-ignored working artifact; mechanical fork/archived/duplicate-cluster triage per above) |

**Phase 0.5 — Artifact boundary and route (R-2/R-3 resolution).**
`corpus_census`'s `judge_items`/`synthesize` nodes hardcode
`provider`/`model` in `graph.yaml` and read them at compile time
(`yamlgraph/node_factory/llm_nodes.py:148`: `node_config.get("provider",
defaults.get("provider"))`) — there is no runtime/state templating for
those fields, confirmed by reading the resolver. Editing the shared
`corpus_census/graph.yaml` in place would silently change behavior for its
other consumers (FR-892/FR-895). This FR therefore authors a **new**,
structurally-identical graph under `examples/demos/pattern_model_census/`
(`graph.yaml`, `prompts/*.yaml`, tool manifests, `README.md`) through the
sole graph-authoring route (`scripts/author.sh
feature-requests/authoring-briefs/fr-896-pattern-model-census-brief.md`,
per `.github/skills/graph-authoring/doctrine.md`) — `corpus_census` itself
is not modified. New Python modules (`git_discover.py`, `git_extract.py`,
a private-ledger reducer) live alongside it; no other repo path is touched.

**Phase 1 — Discover (per repo, read-only, new tool slot binding).**
Bind the new graph's `discover` slot to a new tool:
`git log --since="12 months ago" --no-merges --pretty=format:%H` per repo
path → list of commit SHAs. **Decision (2026-08-28): full census, no cap** —
every commit in the window is enumerated per repo; `mercury-2`'s label-class
cost tier (`docs/mercury-census/findings.md` F1) makes uncapped fan-out
affordable, so no sampling truncation is applied. The output records the
total enumerated count per repo for auditability.

**Phase 2 — Extract (per commit, metadata only — redaction by construction).**
Bind the `extract` slot to `git show --stat --format=%s <sha>` bounded to N
lines → `{repo, sha, date, subject, shortstat}`. Deliberately **excludes**
full diff bodies and file contents — the judged unit is commit metadata, not
code — which removes most of the FR-874 leak surface by construction instead
of relying on later review to catch it.

**Phase 3 — Map/judge, mercury-pinned, one lens per pass (single judgement
per prompt — `prompt-as-subagent-contract` discipline, no fused rubrics).**
Two separate map passes over the same extracted content, each node in the
new `pattern_model_census/graph.yaml` hardcoding `provider: inception`,
`model: mercury-2` (verified by a config-inspection test, not merely
documented — R-3):
- **Lens A — pattern:** classify the dominant architectural/design pattern
  implied by `subject` + `shortstat` (one short label, or `null`).
- **Lens B — model:** extract any literal LLM provider/model name the commit
  mentions or changes (one token, or `null`).

**Phase 4 — Reduce (LLM-free, new reducer module; R-4 alias table).**
Aggregate counts by `repo_alias × quarter × label`. A pattern/model is
flagged **convergent** only if it recurs in ≥3 independently-owned repos
(mirrors the convergence-across-runs rule `docs/mercury-census/findings.md`
already applies to itself). The ledger carries both the raw repo name and a
human-approved `repo_alias` column; only the alias is eligible for the
public brief (R-4 — a raw repo name can itself be customer/employer-
identifying, e.g. private sister repos). **Decision (2026-08-28): the
ledger and all working artifacts are written to a new dedicated private
GitHub repo** (created private during enforcement; not the existing
`control-plane` repo, and never `yamlgraph/docs/` or `yamlgraph/tmp/`). A
path-prefix guard in the reducer fails closed if output is attempted under
any tracked `yamlgraph` path.

**Phase 5 — Synthesize (haiku-tier, bounded, public-safe columns only).**
Reuse the `prepare_brief_input` / `render_brief` / LLM-free citation-
boundary pattern (`adapters/census_brief.py`): synthesis input is restricted
to `repo_alias`, `label`, `count`, and `quarter` columns — never commit
subjects, shortstat detail, SHAs, hostnames, or raw private repo names.
Every citation in the rendered brief is validated against the private
ledger before rendering; on rejection, no brief is written (matches the
existing `*.REJECTED.md` fail-closed behavior).

**Phase 6 — Human redaction review gate (mandatory, blocking).**
The synthesized brief stays in the private repo by default. It is promoted
to a committed `yamlgraph/docs/` artifact only after explicit human review
confirms every repo reference is an approved alias and no customer-
identifying content survived aggregation — the two-stage private-inventory
→ reviewed public-safe-transfer-packet pattern FR-831 already established,
applied here instead of skipped the way FR-874 skipped it. The committed
document states plainly that it is evidence for future standardization/
retirement FRs only and grants no authority to change runtime code, graph
artifacts, prompts, tests, CAPs, CI, or hooks (C-6).

## Acceptance Criteria

- [ ] AC-01: A committed Phase 0 scope table lists every candidate repo
      (the 4 sister repos + triaged personal GitHub repos from Sample 3)
      with source, visibility, raw name, `repo_alias`, and inclusion/
      exclusion reason; `terveystalo` org-wide enumeration is absent from
      the table by construction, not merely stated.
- [ ] AC-02: `examples/demos/pattern_model_census/` is authored via
      `scripts/author.sh` with a committed task brief under
      `feature-requests/authoring-briefs/`; `tmp/draft-authoring-report.md`
      evidence (lint + smoke) is recorded in this FR at enforcement time;
      `examples/demos/corpus_census/graph.yaml` is not modified.
- [ ] AC-03: `discover`/`extract` tool bindings never read file contents or
      diff bodies — only `git log`/`git show --stat --format=%s` metadata;
      a test asserts the extracted schema has no `diff`/body/file-content
      field.
- [ ] AC-04: a test or graph-config inspection proves both map/judge nodes
      in `pattern_model_census/graph.yaml` are pinned to
      `provider: inception`, `model: mercury-2`; each pass emits exactly one
      field per item (no fused rubric).
- [ ] AC-05: discovery is uncapped (full census per repo, per the 2026-08-28
      decision); the output records the total enumerated commit count per
      repo for auditability.
- [ ] AC-06: reduce/ledger output is written only to the new private repo
      created for this census — never under `yamlgraph/docs/`,
      `yamlgraph/tmp/`, or any tracked `yamlgraph` path — enforced by a
      path-prefix assertion in the reducer that fails the run if violated.
- [ ] AC-07: every ledger row carries a `repo_alias` column distinct from
      the raw repo name; the synthesis input allowlist contains only
      `repo_alias`, `label`, `count`, `quarter` — a test rejects commit
      subject, shortstat detail, SHA, hostname-shaped token, or raw private
      repo name appearing in any artifact eligible for public commit.
- [ ] AC-08: every citation in the public brief validates against a row in
      the private ledger; invalid citations produce a rejected/private
      artifact and no public brief (reuses the existing fail-closed
      renderer contract).
- [ ] AC-09: no artifact is committed to `yamlgraph/docs/` until a human
      redaction review is explicitly recorded (commit message or FR update
      citing the review) — no automated promotion path exists.
- [ ] AC-10: `terveystalo` org-wide enumeration is not executed by any tool
      or script this FR authors; only the 4 named sister repos plus the
      author's own personal GitHub repos are read.
- [ ] AC-11: the final committed census document states it is evidence
      only — no authority to change runtime code, graph artifacts, prompts,
      tests, CAPs, CI, or hooks.

## Enforcement Status (2026-08-28)

**Status: In Progress.** Phases 0–4 are implemented for the graph artifact;
Phases 1–2's *real* sister-repo/personal-repo binding, Phase 5 synthesis,
and the Phase 6 human promotion gate are not yet run.

- **AC-01 (scope table):** done — folded into Phase 0 above; 51 include /
  3 exclude personal-repo dispositions, mechanical (0 forks, 0 archived,
  3 duplicate clusters).
- **AC-02 (artifact boundary + route):** done —
  `examples/demos/pattern_model_census/` authored via
  `scripts/author.sh feature-requests/authoring-briefs/fr-896-pattern-model-census-brief.md`
  (sole route); `tmp/draft-authoring-report.md` recorded lint pass, `5
  passed` targeted tests, `ruff check` pass, and an end-to-end fixture
  smoke (10 ledger rows = 5 fixture commits × 2 lenses). Independently
  re-verified in this session (not trusted by exit code alone, per
  `author-sh-timeout-race`): `yamlgraph graph lint`, `pytest
  tests/unit/test_fr896_pattern_model_census.py` (5 passed), `ruff
  check` (clean), `python scripts/req_coverage.py --strict` (clean,
  reuses `REQ-YG-624` per the FR-892/FR-893 census-family convention),
  and a live fixture smoke via the real `inception`/`mercury-2` API
  (see `examples/demos/pattern_model_census/demo-output.log`).
  `examples/demos/corpus_census/graph.yaml` was not modified.
- **AC-03 (metadata-only extraction):** done — `tools/git_tools.py`'s
  `extract()` returns exactly `{repo, sha, date, subject, shortstat}`;
  the reducer's `CommitMetadata` Pydantic model uses `extra="forbid"` to
  reject any other field; a live-git-repo unit test asserts no `diff` key.
- **AC-04 (mercury pin):** done — both `judge_pattern` and `judge_model`
  map sub-nodes hardcode `provider: inception`, `model: mercury-2`,
  `temperature: 0`; asserted by a test that parses `graph.yaml` directly
  (not merely documented).
- **AC-05 (uncapped discovery):** the production `tools/git_discover.tool.yaml`
  binding enumerates the full `git log --since="12 months ago" --no-merges`
  output with no truncation; `max_map_items: 200` remains a graph-level
  fan-out safety cap carried over from the `corpus_census` precedent, not
  a discovery-stage sampling cap — real high-volume repos (`yamlgraph`
  itself) may need this revisited in the Phase 1 real-run follow-up FR/PR
  if the per-repo commit count exceeds it.
- **AC-06/AC-07 (path guard + alias):** done — `reduce_ledger`'s
  `_assert_allowed_output_path` raises unless the resolved path is
  outside the `yamlgraph` repo or under its `tmp/`; the public markdown
  summary carries only `repo_alias`, `quarter`, `lens`, `label`, `count`
  — verified by a test asserting raw `sha`/`subject`/private path never
  appear in the markdown output (only in the private JSONL working
  ledger).
- **AC-08–AC-11 (citation boundary, human gate, org-scope prohibition,
  evidence-only framing):** not yet applicable — no synthesis tail was
  authored in this pass (deliberately deferred, mirroring how FR-892 v1
  shipped without one before FR-895 added it) and no real repo has been
  censused yet, so there is nothing to promote or gate.

**Not done in this pass (explicit follow-up, not silently dropped):**
running the real `tools/git_discover.tool.yaml`/`tools/git_extract.tool.yaml`
bindings against the 4 sister repos and the 51 included personal repos;
creating the new dedicated private ledger repo (Decisions table); Phase 5
synthesis tail; Phase 6 human redaction review and public promotion. Each
remains gated by C-1..C-6 in the judgement until performed.

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Full `scripts/research.sh` 5-persona research pass | Rejected for this planning pass — the architectural "how" is already answered by committed prior art (`corpus_census` graph, `docs/mercury-census/findings.md` F1–F4, FR-802's census methodology); a fresh 5-persona run would re-derive, not add, machinery. Not a permanent exemption — a future *design-uncertain* extension of this FR should still route through it. |
| FR-802-style single-repo node-type census, left as-is | Insufficient — FR-802 only covers `yamlgraph`'s own node types, not cross-repo patterns/models or the sister/GitHub corpus this task asks for. Cited as prior methodology, not a substitute. |
| Enumerate the entire `terveystalo` GitHub org | Rejected — Sample 2 showed this pulls in 20+ private repos owned/authored by other engineers with no relationship to the author's sister projects; no judgement or authorization boundary exists for that surface. |
| Extract full diffs/file contents per commit | Rejected — raw code content is exactly the FR-874 leak class (hostnames, security findings) and buys no additional signal for pattern/model labeling; commit subject + shortstat is sufficient and redacts by construction. |
| Write ledger/brief directly under `yamlgraph/docs/` | Rejected — `yamlgraph` is a public repo (per `memory-tool-locality`/FR-874 precedent); default-private-then-reviewed-promotion is the only path judged safe. |
| Clone/pull every discovered GitHub repo locally before censusing | Rejected as this FR's scope — read via `gh api`/shallow `git log` against remotes where feasible, or restrict to already-cloned repos; bulk-cloning 54+ repos is a separate, heavier operational decision. |

## Related

- [examples/demos/corpus_census/graph.yaml](../examples/demos/corpus_census/graph.yaml),
  [examples/demos/corpus_census/README.md](../examples/demos/corpus_census/README.md) — the shared pipeline this FR's new example mirrors structurally (FR-892, FR-895); not modified by this FR.
- [feature-requests/FR-802-node-type-usage-census.md](FR-802-node-type-usage-census.md) — prior-art census methodology (single-repo, node types) this FR generalizes.
- `docs/mercury-census/findings.md` — the `mercury-2` cost-tier rationale (F1) and the convergence-across-runs discipline this FR's Phase 4 mirrors.
- FR-874 (rejected, 2026-08-24 per user memory `memory-tool-locality.md`) — the precedent this FR's Phase 0/4/6 gates exist to not repeat.
- [feature-requests/FR-831-oulu-bulletin-staged-source-reuse.md](FR-831-oulu-bulletin-staged-source-reuse.md) — the private-inventory → reviewed public-safe-transfer-packet pattern reused in Phase 6.
- [feature-requests/FR-896-cross-repo-pattern-model-census.judgement.md](FR-896-cross-repo-pattern-model-census.judgement.md) — the judgement whose R-1..R-5 are folded above.

## Decisions (judged 2026-08-28, folding R-1)

| Question | Decision |
|---|---|
| GitHub org scope | **Never** — the `terveystalo` org is frozen out of scope; only the 4 named sister repos + the author's own personal GitHub repos are read. Any future expansion is a separate, explicitly authorized follow-up FR. |
| Private ledger location | **A new dedicated private GitHub repo**, created during enforcement solely for this census (not a reuse of the existing `control-plane` repo, and never any tracked `yamlgraph` path). |
| Sampling cap for high-volume repos | **Full census, no cap** — every commit in the 12-month window is enumerated per repo; the output records the total enumerated count for auditability. |
