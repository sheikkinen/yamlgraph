# Plan: Repo split — the library stays, the workflow leaves

**Date:** 2026-09-06
**Status:** planning baseline; implementation authority remains in judged FRs.
No FR filed yet. Phase 1 (census) is the first FR to file.
**Reader / moment:** whoever files the census FR, and whoever is asked
"why is the doctrine no longer in this repo?" after Phase 5.
**Origin:** operator reflection 2026-09-06 — software generation is
near free; review and context are the bottleneck; the workflow is the
product. Sibling pattern precedent: FR-1001 (`yamlgraph-outsider`),
FR-819 (digest PoC repo), FR-827 (gitclaw).

## Ideal Result (stated first, per `ideal_result_backwards`)

Two repositories with one record.

- `sheikkinen/yamlgraph` holds the shipped package and nothing else:
  `yamlgraph/`, its tests, `reference/`, `ARCHITECTURE.md`, the
  capability registry, changelog fragments, PyPI publishing and GitHub
  plumbing. An agent opening it loads dev commands and five critical
  rules. No Scripture, no FRs, no diary in its context.
- The workflow repo (name to be decided; `yamlgraph-chaplain` is taken
  by the FR-1010 historical archive) holds the doctrine, the four
  routes (author, judge, review, outsider), the hooks, the skills, the
  scripts, and the whole record: 1211 FRs and 1367 diary entries. It
  installs `yamlgraph` from PyPI at a pinned minimum. It runs against
  the library repo's PRs and posts a required status check.
- Library merges still block on doctrine, because the workflow repo's
  status check is required by branch protection. Enforcement stays at
  the merge boundary (`enforcement_at_merge_boundary`), it just arrives
  from across the fence.
- Prose hooks the library still wants (forbid-terms, hedging-check,
  block-ai-coauthor) are pulled from the workflow repo as a pre-commit
  remote hook source pinned by `rev:`. No copy, no shim.

## Prior art and its disposition

| Precedent | What it decided | Why this plan is not the same question |
|---|---|---|
| Monorepo-split critical review, 2026-07-21 (cited in FR-755, FR-756) | **No split.** Core-test isolation buys "90% of the benefit of a repo split at ~0% of its cost." | That review answered "is the shipped package green in isolation?" and FR-756 answered it with the `process` marker and the `core-test` CI job. This plan answers a different question: can the workflow operate with the library as a dependency, and can the library be developed without the record in context? FR-756 is the first phase of this plan already done, not a counter-argument to it. |
| FR-754 / FR-755 (2026-07-21) | Removed the `.chaplain` path leak from `id_registry`; ruled FSM ownership contrib-tier with an import-linter contract. | Both are boundary cures this plan inherits. They are why the library's outbound dependency count is zero today. |
| FR-1010 (judged 2026-09-06) | Archive `.chaplain/` to `sheikkinen/yamlgraph-chaplain` as a **source archive, not a runnable standalone** (R-3): a raw subtree split does not run because scripts climb `../..` for the project root. | Direct warning for Phase 3: every script that assumes the current directory is the monorepo must be found before the move, not after. The research and outsider routes already take a workdir env var (`RESEARCH_WORKDIR`, `OUTSIDER_WORKDIR`); the rest must be inventoried. |
| FR-1001 (2026-09-05) | First sibling repo produced through the authoring route; graph and prompt copied from a spike. | Proves a sibling can consume `yamlgraph` from pip and post to PRs cross-repo. Does not prove regeneration from an FR alone; that field test is parked by operator decision (2026-09-06). |
| `docs/plan-github-chaplain-arbitrary-repo.md` (2026-08-18) | Plan+judge for a repo that is not yamlgraph; "enforce does not ship." | This is the same product pointed at its own library. Once the workflow repo exists, the library is simply its first arbitrary target. |
| `docs/plan-gitclaw-modular-architecture.md` (2026-08-20) | GitClaw is a public integration demo, not the owner of the capabilities. | Same ownership rule: the workflow repo owns the process; the library owns the runtime; neither embeds the other. |

## Measured state (2026-09-06)

| Measure | Value |
|---|---|
| Library `yamlgraph/` | 25.1k lines |
| Workflow layer `scripts/` + `.github/` | 30.8k lines |
| Commits touching `examples/` vs `yamlgraph/`, last 90 days | 328 vs 84 (of 1294) |
| Library imports from `scripts/` or `examples/` | 0 |
| Library string references to `graphs/`, `prompts/`, `examples/` | 15 (deprecation messages, discovery glob, doc examples) |
| Workflow scripts calling the `yamlgraph` runtime | 27, plus all four doctrine routes are graphs |
| Library files citing an FR number in comments | 182 |
| CAPs with an `fr:` list | 246 of 246 |
| REQ IDs in `ARCHITECTURE.md` | 481 |
| Unit test files, flat in `tests/unit/` | 496 |
| … carrying the `process` marker (FR-756) | 170 |
| … whose source reads `scripts/`, `feature-requests/`, `docs/diary`, `.github/`, `changelog/`, `capabilities/` | 111 |
| … whose source reads `examples/` | 74 (top fixtures: `demos/hello` 26, `demos/newdemo` 16, `demos/book-summary` 15) |
| Pre-commit hook ids | 45; local hook lines touching workflow paths: 45 |
| Doctrine loaded per agent session (`CLAUDE.md` + Scripture) | ~4400 words |

Two facts shape everything below. The library is clean **outbound**:
nothing in the package imports the workflow. The library is saturated
**inbound**: 182 files, 246 CAPs and 21 reference docs cite FR numbers.
Those are text pointers, not imports. They survive the split as long as
no gate inside the library verifies that an FR *file* exists.

## The cut

| Stays in `yamlgraph` | Leaves to the workflow repo | Needs a decision (Phase 1) |
|---|---|---|
| `yamlgraph/`, `tests/integration/`, `tests/fixtures/`, core unit tests | `.github/copilot-instructions.md`, `.github/skills/`, `.github/hooks/` | `examples/` (1936 files; see D3) |
| `ARCHITECTURE.md`, `capabilities/` | `feature-requests/`, `docs/diary/`, `docs/` plans, research, recaps, census, spikes, ebook | `reference/` (39 files; about 8 are process docs: `command-book`, `onepager-development-process`, `fr-knowledge-graph.*`, `audit-index`, `break-glass`, `impl-agent`, `contrib`) |
| `changelog/`, `CHANGELOG.md` generation, `pyproject.toml`, `LICENSE`, `README.md` | `scripts/` (most of 72), `scripts/tests/`, `ramp/`, `constraints/`, `docs-planning/`, `outputs/`, `tmp/` | Process-marked and workflow-reading tests (170 / 111 files; overlap unknown) |
| `.github/workflows/workflow.yml`, `security.yml`, `commitlint.yml` | `.github/workflows/daily-digest.yml`, `weekly-recap.yml` | `docs/adr/`, `docs/confessions.md` (library-side by content; confirm) |
| Code-hygiene hooks: ruff, import-linter, vulture, jscpd, radon, bandit, file-size-gate, noqa-confession, req-coverage-strict, validate-capabilities, cap-architecture-sync, validate-id-registry, dependency-rationale, direct-import-scan, inline-llm-check, changelog-required, changelog-req-cross-check, changelog-release-sync | Record hooks: authoring-proof, diary-rotate, diary-reflection-check, diary-filename-check, prior-art-gate, triage-gate, feat-requires-fr, demo-proof-check, gitignore-boundary-guard, final-summary | Prose hooks consumed from the remote source: forbid-terms, hedging-check, block-ai-coauthor |
| `CLAUDE.md`, trimmed to dev commands and the five critical rules; the `@.github/copilot-instructions.md` import line goes | `scripts/aggregate_changelog.py`, `scripts/req_coverage.py` and the other gate scripts the library's own hooks call **stay**; classify script by script | |

## Design decisions

**D1. Enforcement at the library's merge boundary.** The doctrine
requires every gate to block at PR merge, and after the split a library
PR cannot read FRs. Two routes: (a) library CI checks out the workflow
repo at a pinned tag and runs its gates locally; (b) the workflow repo
runs judge and review against the library PR and posts a required
status check. **Choose (b).** It is "the workflow runs in the workflow
repo" taken literally, the outsider already writes to PRs cross-repo
(FR-1001, FR-1004), and it keeps model-produced verdicts advisory until
the human merge decision, as review doctrine already says. The workflow
repo holds the token and becomes a privileged actor in the library's
merge path. It already is one today; the fence makes it visible
(`model_as_trusted_peer`).

**D2. Hook distribution.** pre-commit supports remote hook repos pinned
by revision. The workflow repo publishes a `.pre-commit-hooks.yaml`;
the library's config lists it under `repo:` with a `rev:`. This is the
governance kernel with a mechanism that already exists. No adapter, no
copied script.

**D3. Examples.** The demos are the library's smoke corpus: 74 test
files read them, `discovery.py` globs them, the Quickstart runs
`examples/demos/hello`. Keep `examples/demos/` trimmed to what tests
and reference docs cite; delete the rest of the demos. Production
examples (`dungeon_master`, `novel_fandom`, `plot_modeller`,
`yamlgraph_gen`, `api-discovery`, `codegen`, `npc`, …) follow the
sibling pattern, one FR each, in Phase 6. `examples-dungeon-master` is
a `pyproject.toml` extra and leaves with its example.

**D4. Version coupling.** The workflow repo pins `yamlgraph>=X`. The
library pins the workflow repo's `rev:` for hooks and its tag for the
status-check action. A one-version lag in either direction is
acceptable. Cost: a route that needs a new library feature becomes a
two-PR loop (library PR, release, workflow PR). At roughly one library
commit per day the lag is tolerable and forces release discipline.

**D5. The record does not split.** FRs and the diary live in the
workflow repo, all of them, including FRs about library internals.
Library PRs cite FR numbers as today; the `feat-requires-fr` check
moves to the status check (D1) where it can read the file. The
alternative, library FRs in the library repo, kills "who solved this
before" within a quarter (`constraint_over_code`).

**D6. Naming.** The PyPI name `yamlgraph` stays with the library, so
the library keeps this repository and its history. The workflow repo is
new and receives the moved paths with history via `git filter-repo`.
`yamlgraph-chaplain` is taken (FR-1010 archive); pick another.

## Phases

1. **Census (first FR).** Classify every unit test file, CAP, reference
   doc, script and hook as *stay*, *go*, or *split*. Reuse what exists:
   the `process` marker and its collection-time scanner (FR-756),
   `scripts/req_coverage.py`, the direct-import scan. The corpus is
   about 900 items; this is the corpus-map-reduce pattern
   (`reference/patterns/corpus-map-reduce.md`), not a reading job. The
   hard output is the list of REQ IDs whose **only** witness is a
   process-marked test: those are workflow claims in library costume and
   move with their tests, with their CAP entries. Deliverable: a
   manifest file, one row per path, that later phases execute
   mechanically.
2. **Rehearse in place.** Before moving anything, make the library
   green without the workflow paths. Run `pytest tests/unit -m "not
   process" -q --no-cov` (already the `core-test` job) plus exclusion of
   the manifest's *go* tests; run pre-commit with the record hooks
   disabled; run `req_coverage.py --strict` on the *stay* subset.
   Everything is reversible here. If the rehearsal is boring, the census
   was right (`boring_enforcement`).
3. **Create the workflow repo.** `git filter-repo` the *go* paths out
   with history. `pip install yamlgraph` at the current release.
   Inventory every script that computes the repo root from its own
   location or assumes `feature-requests/` is beside it (the FR-1010 R-3
   failure shape) and give each a target-repo parameter. Witness: all
   four routes run from the workflow repo against a library PR.
4. **Wire cross-repo enforcement.** Publish the hooks source (D2).
   Publish the status check (D1). Add it to the library's required
   contexts. Only then delete the record hooks from the library's local
   pre-commit config.
5. **Delete and release.** Remove the *go* paths from the library. Trim
   `CLAUDE.md`. Rewrite the 21 reference-doc FR paths to URLs or accept
   them as dangling pointers; record the choice. Cut a library release;
   bump the workflow repo's pin.
6. **Examples leave one at a time**, each under its own FR in the
   workflow repo, each with a first consumer named
   (`would_you_use_this`).
7. **Distill.** Diary entry with a Seed, per the Sermon.

Phases 3 and 4 are POSIX work (filter-repo, hook rehearsal). Do them on
the mac.

## Risks

- **REQ orphaning.** If many of the 481 REQ IDs have only process
  witnesses, `ARCHITECTURE.md` is partly a workflow document and needs
  its own split. Phase 1 answers this before anything moves.
- **Model in the gate.** A status check produced by a model in another
  repo gates library merges. Structural form of `model_as_trusted_peer`.
  Mitigation is the existing one: advisory until the human merge
  decision; the check asserts "a judged FR exists and review ran", not
  "the model approves".
- **Root-relative scripts.** FR-1010 R-3 found `../..` project-root
  climbing. Expect the same in `scripts/`. Phase 3 inventories before
  moving; a moved script that still climbs is a defect, not a
  follow-up.
- **Dangling FR pointers.** 182 library files cite FR numbers. They
  stay as text. A resolver is a convenience, not a requirement; do not
  build one before someone asks.
- **Two-PR loop fatigue.** If route work needs library changes weekly,
  D4's lag becomes friction. Watch the count for one quarter; if it
  hurts, the answer is a faster library release cadence, not merging the
  repos back.

## What is explicitly not in this plan

- Regenerating a sibling from its FR alone as a field test of
  "workflow + FR = code". Parked by operator decision 2026-09-06 as safe
  but insignificant under the premise that the workflow is the product.
- A cross-repo FR resolver, a governance "kernel" package, or any
  adapter layer. D1 and D2 use GitHub status checks and pre-commit
  remote repos as they exist.
- Moving `.chaplain/`. FR-1010 owns that and runs first.
