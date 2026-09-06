# Plan: Repo split — the library stays, the workflow leaves

**Date:** 2026-09-06 (revised the same day after the ramp review, §R)
**Status:** planning baseline, **parked** until the asset census numbers
exist (§Phase 1). Implementation authority remains in judged FRs. No
split FR filed. The first FR on the path is not new: it is FR-990, the
full capability census, awaiting judgement.
**Reader / moment:** whoever judges FR-990 and asks what the numbers
are for; whoever is asked "why is the doctrine no longer in this repo?"
if Phase 5 ever runs.
**Origin:** operator reflection 2026-09-06 — software generation is
near free; review and context are the bottleneck; the workflow is the
product. Sibling pattern precedent: FR-1001 (`yamlgraph-outsider`),
FR-819 (digest PoC repo), FR-827 (gitclaw).

## Ideal Result (stated first, per `ideal_result_backwards`)

Two repositories, each owning its own record.

- `sheikkinen/yamlgraph` holds the shipped package and everything a
  governed repository owns: `yamlgraph/`, its tests, `reference/`,
  `ARCHITECTURE.md`, the capability registry, changelog fragments, PyPI
  publishing, GitHub plumbing, **and its own `feature-requests/` and
  `docs/diary/` for library subjects**. An agent opening it loads dev
  commands and five critical rules. No Scripture in its context; the
  library's record is on disk for search, not loaded per session.
- The workflow repo (name to be decided; `yamlgraph-chaplain` is taken
  by the FR-1010 historical archive) holds the **engine**: the doctrine
  source, the four routes (author, judge, review, outsider), the ramp,
  the hook sources, the skills, the process scripts, and the record of
  the process itself (FR-864…869, FR-995, FR-1001 and their kin). It
  installs `yamlgraph` from PyPI at a pinned minimum and governs itself
  with its own assets.
- The library is the workflow repo's first daily consumer: it pulls the
  hooks at a pinned revision, runs them on every commit, and files
  breakage back. That pin is what `scripture-dev` never had (§R).
- Prose hooks the library wants (forbid-terms, hedging-check,
  block-ai-coauthor) arrive as a pre-commit remote hook source pinned by
  `rev:`. No copy, no shim.

## §R. Ramp review (2026-09-06) — what the first draft got wrong

The first draft of this plan (PR #616) moved the whole record, 1211 FRs
and 1367 diary entries, to the workflow repo (old D5) and gated library
merges from outside through a status check (old D1). Reading the ramp
plan (`docs/plan-ramp-spike-to-governed.md`, FR-864…869, judged with
authority; FR-865 enforced 2026-08-24 with one live consumer,
`deviant-daily`) exposed two errors.

1. **The record belongs with the code it governs.** The ramp's Tier 2
   installs the FR and diary templates *into* the target repo; Tier 3
   installs the capability registry and `req_coverage.py`. FR, CAP, REQ
   and test are one traceability spine and the product's own design
   keeps that spine inside the governed repository. The first draft
   severed it at the FR link. Corrected in D5.
2. **A distributor that is not a consumer has nothing forcing it to
   stay true** (FR-864 §1). `scripture-dev` (FR-207) froze at 16 hooks
   with no consumer contributing back. A standalone workflow repo is
   `scripture-dev` again unless a live repo pulls it daily at a pinned
   revision. The ramp's `curation-diffs.md` records how deep the
   co-location goes: every removed gate hardcodes this repo's scripts
   path, registry layout, doctrine files or venv path. The workflow was
   built assuming it sits inside the repo it governs. Corrected in D2
   and D4; named as the blocker for Phase 3.

Two deployment shapes are now on record. **Install into** is the ramp:
hooks, templates, judge and review scripts copied in; judged, enforced,
one consumer. **Run from outside** is
`docs/plan-github-chaplain-arbitrary-repo.md`: plan and judge post into
a foreign repo; a plan without authority. This plan uses the ramp shape
for the library and leaves the outside shape to foreign repos (D1).

The honest alternative is **no split**: the ramp is the product's
shipping form and this repo stays live distributor and consumer. It is
recorded here so the next reader does not have to rediscover it. The
lean is still toward the split, because a product that ships from
inside a library's repository will always be curated copies of
something else, and the curation drift the FR-865 judgement worried
about is exactly what a single pulled source removes.

## Prior art and its disposition

| Precedent | What it decided | Disposition here |
|---|---|---|
| Monorepo-split critical review, 2026-07-21 (cited in FR-755, FR-756) | **No split.** Core-test isolation buys "90% of the benefit of a repo split at ~0% of its cost." | Answered "is the shipped package green in isolation?"; FR-756 delivered that with the `process` marker and the `core-test` job. This plan asks whether the workflow can operate with the library as a dependency. FR-756 is Phase 1 groundwork already done, not a counter-verdict. |
| FR-754 / FR-755 (2026-07-21) | Removed the `.chaplain` path leak; ruled FSM ownership contrib-tier with an import-linter contract. | Inherited boundary cures; the reason the library's outbound dependency count is zero. |
| **Ramp** — FR-864 (split), FR-865 (installer, enforced 2026-08-24), FR-866…869 (judged) | The process is *installed into* the governed repo from the live repo that runs the same assets on every commit; a template repo without consumers fails (`scripture-dev`). | Binding on this plan: record stays with the governed repo (D5); the workflow repo must have a daily pinned consumer (D4); hooks that hardcode repo layout block extraction until made generic (Phase 3). See §R. |
| FR-1010 (judged 2026-09-06) | Archive `.chaplain/` to `sheikkinen/yamlgraph-chaplain` as a **source archive, not a runnable standalone** (R-3): scripts climb `../..` for the project root. | Same failure shape as the curation-diffs finding. Phase 3 inventories root-relative scripts before any move. |
| FR-1001 (2026-09-05) | First sibling repo produced through the authoring route; graph and prompt copied from a spike. | Proves a sibling can consume `yamlgraph` from pip and post to PRs cross-repo. Regeneration from an FR alone is parked (operator decision 2026-09-06). |
| `docs/plan-github-chaplain-arbitrary-repo.md` (2026-08-18) | Plan+judge for a repo that is not yamlgraph; "enforce does not ship." | The run-from-outside shape. Applies to foreign repos, not to this one (D1). |
| `docs/plan-gitclaw-modular-architecture.md` (2026-08-20) | GitClaw is a public integration demo, not the owner of the capabilities. | Same ownership rule: the workflow repo owns the process, the library owns the runtime, neither embeds the other. |

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
| Unit tests collected, by FR-756 marker | 2561 `process` / 4415 core (of 6976, 170 marked files; 1 collection error on Windows: a test importing the `fi_domain_crawl` example) |
| Unit test files whose source reads `examples/` | 74 (top fixtures: `demos/hello` 26, `demos/newdemo` 16, `demos/book-summary` 15) |
| Pre-commit hook ids | 45; local hook lines touching workflow paths: 45 |
| Doctrine loaded per agent session (`CLAUDE.md` + Scripture) | ~4400 words |

Two facts shape everything below. The library is clean **outbound**:
nothing in the package imports the workflow. The library is saturated
**inbound**: 182 files, 246 CAPs and 21 reference docs cite FR numbers.
Under D5 those pointers resolve locally, as today.

## The cut

| Stays in `yamlgraph` | Leaves to the workflow repo | Needs a decision (Phase 1) |
|---|---|---|
| `yamlgraph/`, `tests/integration/`, `tests/fixtures/`, core unit tests | `.github/copilot-instructions.md` (doctrine source), `.github/skills/`, `.github/hooks/` | `examples/` (1936 files; see D3) |
| `ARCHITECTURE.md`, `capabilities/` | `ramp/`, the four routes, `scripts/` process tooling, `scripts/tests/` | `reference/` (39 files; about 8 are process docs: `command-book`, `onepager-development-process`, `fr-knowledge-graph.*`, `audit-index`, `break-glass`, `impl-agent`, `contrib`) |
| **`feature-requests/` and `docs/diary/` for library subjects** (D5) | **`feature-requests/` and `docs/diary/` for process subjects** (the ramp family, the routes, the doctrine's own evolution) | Mixed-subject FRs — the hard rows of the FR census |
| `changelog/`, `CHANGELOG.md` generation, `pyproject.toml`, `LICENSE`, `README.md` | `docs/` plans, research, recaps, census runs, spikes, ebook; `constraints/`, `docs-planning/`, `outputs/`, `tmp/` | `docs/adr/`, `docs/confessions.md` (library-side by content; confirm) |
| `.github/workflows/workflow.yml`, `security.yml`, `commitlint.yml` | `.github/workflows/daily-digest.yml`, `weekly-recap.yml` | Process-marked tests whose REQ maps to a `core_runtime` CAP, and the reverse (§Phase 1) |
| Code-hygiene hooks: ruff, import-linter, vulture, jscpd, radon, bandit, file-size-gate, noqa-confession, req-coverage-strict, validate-capabilities, cap-architecture-sync, validate-id-registry, dependency-rationale, direct-import-scan, inline-llm-check, changelog-required, changelog-req-cross-check, changelog-release-sync, **feat-requires-fr, prior-art-gate, triage-gate, diary-\*** (they read the library's own record, which stays) | Route launchers: authoring-proof, demo-proof-check, final-summary, gitignore-boundary-guard | Prose hooks consumed from the remote source: forbid-terms, hedging-check, block-ai-coauthor |
| `CLAUDE.md`, trimmed to dev commands and the five critical rules; the `@.github/copilot-instructions.md` import line goes | `scripts/aggregate_changelog.py`, `scripts/req_coverage.py` and the other gate scripts the library's own hooks call **stay**; classify script by script | |

## Design decisions

**D1. Enforcement at the library's merge boundary — install into, not
run from outside.** The library keeps its record and the hooks that
read it (D5), so `feat-requires-fr`, prior-art and triage gates keep
running locally as today. The four routes run from the workflow repo
against a library PR and post their artifacts as PR comments, as the
outsider already does (FR-1001, FR-1004); they are advisory until the
human merge decision, as review doctrine already says. A required
cross-repo status check is the *foreign-repo* shape
(`plan-github-chaplain-arbitrary-repo.md`) and is not built for this
repo.

**D2. Hook distribution — the ramp's successor.** pre-commit supports
remote hook repos pinned by revision. The workflow repo publishes a
`.pre-commit-hooks.yaml`; the library's config lists it under `repo:`
with a `rev:`. This replaces the ramp's curated copies
(`ramp/assets/tier1/pre-commit-config.yaml`, whose curation record lists
every gate stripped because it hardcodes this repo's layout) with one
pulled source. Precondition, from the same record: the hooks must stop
hardcoding `.venv/bin/python`, `scripts/` and the registry layout.
Until they do, there is nothing generic to publish.

**D3. Examples.** The demos are the library's smoke corpus: 74 test
files read them, `discovery.py` globs them, the Quickstart runs
`examples/demos/hello`. Keep `examples/demos/` trimmed to what tests
and reference docs cite. Production examples (`dungeon_master`,
`novel_fandom`, `plot_modeller`, `yamlgraph_gen`, `api-discovery`,
`codegen`, `npc`, …) follow the sibling pattern, one FR each, in
Phase 6. `examples-dungeon-master` is a `pyproject.toml` extra and
leaves with its example. The FR-990 pilot's `example_only` rows and
`retire` dispositions are the first cut list.

**D4. Version coupling and the consumer test.** The workflow repo pins
`yamlgraph>=X`. The library pins the workflow repo's `rev:` for hooks.
A one-version lag in either direction is acceptable. The FR-864 axiom
is satisfied not by the workflow repo governing itself, which is weak,
but by the library pulling daily at a pinned revision and filing
breakage back. Cost: a route that needs a new library feature becomes a
two-PR loop (library PR, release, workflow PR). At roughly one library
commit per day the lag is tolerable and forces release discipline.

**D5. Each repo owns its record.** *Revised from the first draft.*
Library-subject FRs and diary entries stay here with the CAPs, REQs and
tests they justify; the traceability spine is never cut. Process-subject
FRs and diary entries move with the engine. Mixed-subject FRs are
classified in Phase 1, not guessed. "Who solved this before" is
preserved *per governed repo*, which is what the ramp installs anyway.

**D6. Naming.** The PyPI name `yamlgraph` stays with the library, so
the library keeps this repository and its history. The workflow repo is
new and receives the moved paths with history via `git filter-repo`.
`yamlgraph-chaplain` is taken (FR-1010 archive); pick another.

## Phases

1. **Census — with the instruments that exist.** The asset
   classification is the ground everyone agrees on, and it needs no new
   script. The corpus-map-reduce pattern
   (`reference/patterns/corpus-map-reduce.md`) has five census graphs
   under `examples/demos/`; the first draft of this plan reached for an
   ad-hoc classifier before consulting them, the exact moment the
   `is_this_a_graph` question is written for.
   - **Capabilities:** `examples/demos/cap_journey_census` already
     classifies each CAP with a `blast_kind` of `core_runtime`,
     `cli_surface`, `process_infra`, `tooling_integration`,
     `example_only`. FR-990 ran it three times over 30 of 246 CAPs
     (pilot: 11 example_only, 8 core_runtime, 6 process_infra,
     3 tooling_integration, 2 cli_surface; dispositions 25 keep,
     3 retire, 2 already retired). **FR-990 is Proposed and asks
     authority for the full run over the remaining 242. Judging it is
     the first step of this plan.**
   - **Tests:** already classified binary by the FR-756 marker and its
     collection-time scanner (2561 / 4415). The four-way class needs no
     marker change: every test carries a REQ mark, every REQ belongs to
     a CAP, and the full CAP run gives each CAP a `blast_kind`. Tests
     inherit their class through the spine. A test whose inherited class
     disagrees with its marker is a finding to record, not a census bug.
   - **REQs:** FR-851 audited all 412 witnesses on 2026-08-22. REQ class
     derives from its CAP; nothing to build. The hard output is the list
     of REQs whose CAP is `process_infra` but whose witness tests are
     unmarked, and the reverse.
   - **Scripts:** the one instrument gap. Precedent shape is
     `examples/demos/salvage_classify` (FR-868): mechanical caller
     evidence (pre-commit, CI, skills, other scripts, docs, none) plus
     one cheap judgement per item. 72 scripts; `ramp/manifest.yaml`
     already names four as curated assets. One small FR.
   - **FRs and diary:** subject classification (library / process /
     mixed) for D5. Same census graph, new rubric; FR-748 (FR Atlas)
     is the precedent run.
   - **Doctrine defect found on the way:** the `is_this_a_graph` entry
     says "consult `yamlgraph graph list`". That subcommand does not
     exist in the CLI at 0.5.24 (run, info, validate, lint, codegen,
     bench, export). Fix FR: restore the subcommand or repoint the
     question at `examples/demos/`.
2. **Rehearse in place.** Before moving anything, make the library
   green without the engine paths. `pytest tests/unit -m "not process"
   -q --no-cov` is already the `core-test` job; add exclusion of the
   census's *go* tests; run pre-commit with the route hooks disabled;
   run `req_coverage.py --strict` on the *stay* subset. Everything is
   reversible here. If the rehearsal is boring, the census was right
   (`boring_enforcement`).
3. **Make the hooks generic, then create the workflow repo.** The
   curation record (`ramp/curation-diffs.md`) and FR-1010 R-3 both name
   the blocker: scripts that hardcode `.venv/bin/python`, compute the
   repo root from their own location, or assume `feature-requests/` is
   beside them. Inventory and parameterise them first. Then
   `git filter-repo` the *go* paths out with history; `pip install
   yamlgraph` at the current release. Witness: all four routes run from
   the workflow repo against a library PR and post their artifacts.
4. **Wire the consumer.** Publish the hooks source (D2). Point the
   library's pre-commit at it with a `rev:`. Only then delete the
   duplicated hook definitions from the library's local config. Register
   the library in the ramp consumer table (`ramp/consumers.md`) as
   consumer number two, after `deviant-daily`.
5. **Delete and release.** Remove the *go* paths from the library. Trim
   `CLAUDE.md`. Cut a library release; bump the workflow repo's pin.
6. **Examples leave one at a time**, each under its own FR, each with a
   first consumer named (`would_you_use_this`).
7. **Distill.** Diary entry with a Seed, per the Sermon.

Phases 3 and 4 are POSIX work (filter-repo, hook rehearsal). Do them on
the mac.

## Risks

- **REQ orphaning.** If many of the 481 REQ IDs map to `process_infra`
  CAPs, `ARCHITECTURE.md` is partly a workflow document and needs its
  own split. The full FR-990 run answers this before anything moves.
- **Mixed-subject FRs.** Many FRs touch both the library and the
  process. The FR census will produce a long *mixed* column. If it
  dominates, D5 degrades to "the record stays here and the engine
  leaves without its history", which is honest but weaker.
- **Root-relative scripts.** FR-1010 R-3 and `curation-diffs.md` both
  found layout hardcoding. A moved script that still climbs is a
  defect, not a follow-up.
- **The consumer stops pulling.** If the library pins a `rev:` and never
  bumps it, the workflow repo is `scripture-dev` with a nicer name.
  Watch the pin age; a stale pin is the failure signal.
- **Two-PR loop fatigue.** If route work needs library changes weekly,
  D4's lag becomes friction. Watch the count for one quarter; if it
  hurts, the answer is a faster library release cadence, not merging the
  repos back.

## What is explicitly not in this plan

- Regenerating a sibling from its FR alone as a field test of
  "workflow + FR = code". Parked by operator decision 2026-09-06 as safe
  but insignificant under the premise that the workflow is the product.
- A cross-repo status check gating this repo's merges (first-draft D1),
  a cross-repo FR resolver, a governance "kernel" package, or any
  adapter layer.
- A new classification script. Phase 1 runs on the census graphs that
  exist.
- Moving `.chaplain/`. FR-1010 owns that and runs first.
