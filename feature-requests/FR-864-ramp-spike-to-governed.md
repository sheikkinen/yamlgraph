# Feature Request: Ramp — Bootstrapping a Repo from Spike to Governed

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed
**Effort:** 1.5 days
**Requested:** 2026-08-23
**First consumer / first event:** `sheikkinen/deviant-daily`, today. It
crossed into production on 2026-08-19 (commits `71e80b9` first public
publish, `eeca704` cron enabled) and has run four days unattended with
**zero** pre-commit hooks, **zero** CI running its 14 test files, and no
doctrine file. It produced four production failures in two hours this
morning. The first event is `scripts/ramp.sh ~/Documents/src/deviant-daily --tier 2`.

**Prior art:** **FR-207** (`scripture-dev`) is the failed attempt and
must be dispositioned, not repeated: template repo + `render.sh`
placeholder substitution, status *Implemented*, last commit
2026-03-29, 16 hooks against yamlgraph's current 45, its own
`scripture.yaml` still reading `project_name: my-minesweeper`, consumers
= two toy repos, contributions back = zero. This FR **supersedes its
mechanism and proposes its retirement** (§5). **FR-748** (`fr_atlas`) is
the reusable precedent — "render *any* project's feature-requests/
corpus", chunked map + merge judgement + count-in == count-out — and two
of the four graphs below are that shape. **FR-826/862/863** are the
target repo's history and its founding incident record. Not prior art
but decisive evidence: `customer-service-agent-platform` replicated the
same apparatus successfully (23 hooks, 8 skills, both adapter routes,
985 requirement tags) and contributed four traps *back* into yamlgraph's
Scripture (NC-141, NC-203, NC-414, FR-371). No REJECTED prior art
occupies this territory.

## Summary

A ramp that installs the process into a repo that has outgrown its
spike: a mechanical installer for the copyable assets, four YAMLGraph
graphs for the parts that require judgement, and a tier system keyed to
the event that triggered the ramp. Salvage `scripture-dev` in the same
pass and retire it.

## Value Statement

A repo that goes live acquires its gates in minutes instead of never,
and the parts that cannot be copied — doctrine, requirements, incident
record — are derived from the target repo rather than pasted from
someone else's.

## Problem

Three findings from today, each documented in `docs/diary/`:

1. **Nothing detects the spike ending.** deviant-daily's transition is
   written in its log with a timestamp and nothing noticed for four
   days (`diary-2026-08-23-the-spike-ends-at-a-commit.md`).
2. **Templating does not transfer a process.** `scripture-dev` shipped
   artifacts and froze; csap practised and stayed current
   (`diary-2026-08-23-process-transfers-by-practice.md`).
3. **Absent enforcement is silent.** Ten commits in deviant-daily ran
   with an empty `.git/hooks/` and none said so
   (`diary-2026-08-23-nothing-announces-the-absent-guard.md`).

The ramp addresses (2). (1) and (3) are separate FRs — the detector and
the warning — and this FR must not absorb them.

## Ideal Result

The operator types one command against a repo that has gone live. Ten
minutes later that repo has the gates appropriate to its tier, an
`AGENTS.md` written *about it* rather than copied at it, a requirement
registry derived from the tests it already has, and an incident record
containing its own four failures instead of someone else's forty. The
assets came from a repo that runs them daily, so nothing was stale. What
could not be derived was left undone and named, rather than filled with
plausible boilerplate.

## Proposed Solution

### 1. Where the assets live: the working repo, not a template repo

`scripture-dev` failed because a distributor that is not a consumer has
nothing forcing it to stay true. The ramp therefore ships **from
yamlgraph**, whose hooks fire on every commit here:

```
scripts/ramp.sh <target-repo-path> --tier {1|2|3} [--dry-run]
```

Mechanical, no LLM, idempotent, reversible (writes only files that do
not exist unless `--force`). It copies the domain-free assets and
records what it did in `<target>/docs/ramp-manifest.md`.

### 2. Tiers keyed to the triggering event

| Tier | Trigger | Installs |
|---|---|---|
| 1 live | `schedule:` / secret / first external write | pre-commit basics (ruff, file-size, whitespace, merge-conflict, private-key, `--no-verify` block, forbidden phrases), CI job running the suite, `.github/hooks/` Copilot guard set, `AGENTS.md` |
| 2 governed | second contributor, or first incident costing money or reputation | + FR/judgement/diary templates, `scripts/judge.sh` + `scripts/review.sh` routes, diary gate, changelog gate, requirement IDs |
| 3 regulated | IEC 62304 / MDR context | + registry (`capabilities/*.yaml` shape), `req_coverage.py --strict` gate, RTM document |

deviant-daily is **Tier 2** by the money-or-reputation clause. The RTM
the operator asked for is Tier 3 and is included for it explicitly —
note that csap, the successful replicant, is the *weaker* model here:
985 `@pytest.mark.req` tags with no registry and no coverage gate, so
nothing detects a requirement losing its last witness. deviant-daily
inherits yamlgraph's shape, not csap's.

### 3. The cognitive steps are graphs, not scripts

Four steps cannot be copied because they must be *about* the target
repo. Each is an LLM pipeline over a corpus with a fan-out and a merge —
the native map-reduce shape — so each is a graph, authored through the
governed route and run via `yamlgraph graph run`.

| Graph | Task shape | Why not a script |
|---|---|---|
| `ramp_doctrine` | python node inventories the target (languages, entry points, external effects, existing gates) → **map** over the parent Scripture's traps/cures/questions, each classified *applicable / not applicable / applicable-if-tailored* with a one-line reason → merge → render `AGENTS.md` | Requires reading the target's code to decide whether `streaming` or `provider` boundaries even exist there. A copy produces a document nobody owns. |
| `ramp_rtm` | **map** over the target's test files and source modules → propose `{req_id, statement, witness_tests}` → merge → dedupe → emit registry YAML + gap list. `fr_atlas` precedent: count-in == count-out reconciliation | Deriving a requirement statement from a test's behaviour is judgement. deviant-daily has 14 test files and 145 tests — the exact N-items-times-LLM-call shape the map node exists for. |
| `ramp_incidents` | **map** over source-repo FRs and diary entries mentioning the target → extract `{date, defect, root cause, cure, witness}` → merge → render the target's `docs/incidents.md` | Repatriation, not copying: today's four failures are filed in yamlgraph and belong in deviant-daily. Selecting *which* of 1,238 entries concern the target is a relevance judgement. |
| `salvage_classify` | **map** over `scripture-dev`'s 16 hooks, 8 scripts, 3 templates, `render.sh` → verdict `{duplicate-of-yamlgraph, lift, obsolete}` + rationale + target path | 27 artifacts × "does yamlgraph already have this, better?" is a classification fan-out. Doing it by hand is what has not happened for five months. |

All four write drafts to `tmp/` for human review before landing —
same contract as the judge and authoring adapters. None auto-commits.

### 4. What is copied, tailored, left

Sorting rule: **an asset is copyable exactly to the degree that it
encodes no local incident.**

- **Copy verbatim:** Copilot hook set (`pre-command-guard.sh` fired
  twice today from a foreign cwd — it contains no yamlgraph), pre-commit
  basics, CI gates, FR/judgement/diary templates, `judge.sh`/`review.sh`.
- **Tailor (via graphs):** doctrine file — inherit traps, cures,
  questions; **witness citations start empty**. Requirement prefix and
  registry. Thresholds (coverage %, file size, complexity) are policy.
- **Leave out:** the chaplain FSM runtime (needs its own operator), the
  226 capability *entries*, and the 45-hook set wholesale — deviant-daily
  needs roughly twelve. A ramp that installs everything gets reverted.

### 5. Salvage and retire `scripture-dev`

`salvage_classify` produces the disposition list; anything marked *lift*
moves into yamlgraph's ramp assets with attribution; then the repo is
**archived** (GitHub archive, not deleted — it holds FR-207's record).
Retiring it is the point: leaving a stale, unconsumed distributor in
place is how the next agent finds the wrong upstream.

## Acceptance Criteria

- [ ] AC-01: `scripts/ramp.sh <target> --tier 1 --dry-run` prints every
      file it would write and writes nothing; exit 0.
- [ ] AC-02: `--tier N` is idempotent — a second run makes no changes
      and reports "already installed" per asset.
- [ ] AC-03: ramp never overwrites an existing file without `--force`;
      test asserts a pre-existing `AGENTS.md` survives.
- [ ] AC-04: after `--tier 1` on a scratch repo, `pre-commit run --all`
      executes and `.git/hooks/pre-commit` exists.
- [ ] AC-05: `<target>/docs/ramp-manifest.md` lists every installed
      asset with its source path and the yamlgraph commit SHA
      (`artifact_carries_code_identity`).
- [ ] AC-06: all four graphs pass `yamlgraph graph lint` and were
      authored through the governed authoring route, with reports
      retained.
- [ ] AC-07: `ramp_doctrine` on deviant-daily emits an `AGENTS.md` whose
      trap list is a **strict subset** of the parent's, contains zero
      witness citations from other repos, and names at least one
      target-specific boundary (DA API, Replicate, vision payload).
- [ ] AC-08: `ramp_rtm` on deviant-daily emits ≥ 10 requirement
      candidates, each citing ≥ 1 existing test by name; count-in ==
      count-out over test files is asserted and reported.
- [ ] AC-09: `ramp_incidents` on deviant-daily emits an incident record
      containing all four of 2026-08-23's failures (vision payload
      ceiling, DA title cap, degenerate corpus key, guard-flag hedging),
      each with root cause and cure.
- [ ] AC-10: `salvage_classify` classifies **all 27** `scripture-dev`
      assets with no "unknown"; the lift list is non-empty or the FR
      records that nothing is worth lifting.
- [ ] AC-11: deviant-daily is ramped to Tier 2 + RTM, its CI runs the
      145 tests on push, and a deliberately failing commit is blocked —
      witnessed by run id.
- [ ] AC-12: `scripture-dev` is archived, with its disposition recorded
      in FR-207.
- [ ] AC-13: tests added before implementation (RED/GREEN commits).
- [ ] AC-14: no graph auto-commits; all four write to `tmp/` only.

## Risks

**The ramp becomes the thing that needs a ramp.** Four graphs plus an
installer is itself a subsystem in yamlgraph, subject to the same gates
(`infrastructure_self_exempt`). Mitigated by keeping `ramp.sh`
mechanical and dumb — every judgement lives in a graph, every graph
writes a draft a human reads.

**Derived requirements read as authoritative.** `ramp_rtm` proposes
requirement statements from test behaviour; a plausible-but-wrong
statement is worse than a gap, because it will be traced against
forever. Mitigation: output is a *candidate* file with an explicit
`status: proposed` per entry, and AC-08 requires each to cite the test
it came from.

**Tier 3 on a 14-test repo may be theatre.** The RTM was requested
explicitly, so it is in scope — but if `ramp_rtm` yields fewer than 10
defensible requirements, the honest outcome is to report that and stop,
not to pad.

**Scope adjacency.** The spike detector (`production_is_detected_not_declared`)
and the unenforced-repo warning (`silent_absence_of_enforcement`) are
the natural companions to this FR and are deliberately **excluded** —
they modify `pre-command-guard.sh`, which is enforcement infrastructure
and deserves its own judgement.

## Alternatives Considered

- **Revive `scripture-dev` as a `pre-commit` hook provider** (remote
  `repo:` + `rev:` pinning). This was my own first proposal and it is
  wrong as a primary: it fixes the decay problem `scripture-dev` had but
  does not create the condition csap has. csap has no `rev:` pin on
  anything and stays current because someone practises there. Retained
  as a possible *later* distribution refinement, not as the mechanism.
- **Copy csap's setup instead of yamlgraph's.** Rejected for the RTM
  specifically: csap's traceability is tag-only with no registry and no
  coverage gate.
- **Do the four cognitive steps as subagents or scripts.** Rejected:
  each is an N-items × one-LLM-call fan-out with a merge, which is the
  map node's native shape (`is_this_a_graph`). Scripts are the fallback,
  not the default.
- **Ramp deviant-daily by hand, once.** Tempting and cheaper today;
  rejected because the next repo starts tomorrow and hand-ramping is
  what has not happened since March.

## Related

- `feature-requests/FR-207-standalone-scripture-methodology-repo.md` — the failed mechanism; retirement proposed here
- `feature-requests/FR-748-*` / `examples/demos/fr-atlas/graph.yaml` — corpus map + merge + reconciliation precedent
- `feature-requests/FR-863-deviant-daily-publish-policy-boundary-mirroring.md` — the incidents to repatriate
- `docs/diary/diary-2026-08-23-the-spike-ends-at-a-commit.md`
- `docs/diary/diary-2026-08-23-process-transfers-by-practice.md`
- `docs/diary/diary-2026-08-23-nothing-announces-the-absent-guard.md`
- `customer-service-agent-platform` — the working replicant; not a dependency
