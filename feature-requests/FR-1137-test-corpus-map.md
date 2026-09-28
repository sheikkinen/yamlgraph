# Feature Request: Test Corpus Map — per-test description, target, and type

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented — judged 2026-09-28 APPROVED WITH REVISIONS
([judgement](FR-1137-test-corpus-map.judgement.md)); R-2..R-6 and Q4
folded, R-1 overruled by the operator (see § Judgement fold); AC-06
amended by the operator (D6, 5% failed-partition allowance); full run
accepted (see § Implementation Status)
**Requested:** 2026-09-28
**First consumer / first event:** the operator, at the next test-retirement
or test-speed decision (live instance: FR-1134 retiring the FR knowledge
graph and FR-275 meta tests), filtering `test-map.json` by
`target != core` to see which tests guard the framework and which guard
examples, scripts, or docs. First event: one manual run over
`tests/unit` + `tests/integration` at a pinned SHA.
**Research:** in-body dispositioned alternatives table (§ Alternatives
Considered). `scripts/research.sh` not run; the Judge may require it.
**Prior art:**
- [FR-851](FR-851-requirement-witness-audit.md) — REQ-level LLM audit of
  whether tagged tests *witness* a requirement. This FR works at the test
  level and asks *what does the test do, what does it guard, what kind is
  it*. It reuses FR-851's REQ joins and makes no witness judgement.
- `scripts/req_coverage.py` (ADR-001, FR-145, FR-178, FR-436, FR-850) — the
  existing deterministic REQ ↔ test ↔ code mapping. This FR adds no second
  REQ source. It joins `req_coverage` AST marker extraction as a read-only
  input column.
- [FR-892](FR-892-corpus-census-pipeline-injected-adapters.md) /
  `examples/demos/corpus_census` — a reusable census that returns ONE
  normalized `judgement` label per item. This FR needs N typed records per
  item (one per test function, three fields each), so it cannot reuse the
  census envelope as-is (see A2).
- FR-1134 (retire FR knowledge graph and FR-275 meta tests; in flight on
  its own branch) — consumer, not precedent.
- `reference/patterns/corpus-map-reduce.md` — the contract this graph
  follows (freeze → partition → map → reconcile → canary → render).

## Summary

Build a corpus-map-reduce graph over the framework test files. Deterministic
Python enumerates every test function with AST. One bounded LLM call per test
file (or per chunk of a large file), using the default provider and model,
returns one record per test function:

| Field | Source | Values |
|---|---|---|
| `nodeid` | AST | `tests/unit/test_x.py::TestC::test_y` |
| `file`, `line` | AST | — |
| `reqs` | AST (`req_coverage` extractor) | `["REQ-YG-069", …]` or `[]` |
| `markers` | AST | e.g. `["slow"]` |
| `description` | LLM | exactly one sentence |
| `target` | LLM | `core` \| `linter` \| `examples` \| `scripts` \| `docs` \| `other` |
| `test_type` | LLM | `unit` \| `integration` \| `other` |

The graph writes **two artifacts** from the same reconciled record set:

- `test-map.json` is canonical and machine-readable. It holds the provenance
  header and one row per test.
- `test-map.md` is a human-readable rendering. Code renders it
  deterministically from the JSON; no LLM call writes it.

## Value Statement

The operator gets the first test-level inventory of 563 files and about 6,800
test functions, answering "what does this test guard, and is it really a unit
test?", for under a few dollars of cheap-model calls. Without it the answer
takes a manual read that never happens.

## Problem

The existing mapping answers **which requirement a test cites**
(`@pytest.mark.req`, `req_coverage.py --strict`). FR-851 answers **whether the
citation is substantive**. Neither answers:

1. **What does each test do?** Test names are the only index. About 6,800
   functions in 563 files (134,913 lines) cannot be read by hand.
2. **What does it guard?** `tests/unit/` mixes framework-core tests with
   linter, example-graph, script, hook, and doc-consistency tests. The
   directory hides this. FR-1134 had to find meta tests by hand.
3. **Is it the type its location claims?** Some `tests/unit/` files spawn
   subprocesses, run graphs end to end, or read the whole repo. That matters
   for test speed (CAP-126) and isolation (`one_session_one_repo`).

The corpus is finite and enumerable. Serial review is prohibitive, so this is
the corpus-map-reduce signal.

**Cost estimate (census before alternative, FR-965):**

- Input: about 135k lines at roughly 10 tokens per line is about 1.4M tokens,
  plus prompt overhead over about 600 calls.
- Output: about 6,800 records at roughly 50 tokens each is about 0.35M tokens.
- At mercury-2 list pricing (the current default via `PROVIDER=inception`)
  this is about $1. On claude-haiku-4-5 it is about $3–4.
- Treat these as estimates. The run records actual token usage.

## Ideal Result

At any pinned SHA, one command produces `test-map.json` and `test-map.md`.
They hold every AST-enumerated test function exactly once, with a
one-sentence description, a target, and a type. Code has checked that
nothing was dropped or invented, every enum value is valid, and a canary of
known classifications passed. Either artifact alone answers "which tests
guard `examples/`?" or "which `unit` tests are really integration?" with a
filter, not a reading session.

## Planned Operations

Added after the judge run (FR-1129 landed on main between the judge run and
the rebase); the judge did not read this block.

```yaml
probes:
  - "AST census of tests/unit + tests/integration at the pinned SHA — sets file, test, and partition counts and the max_map_items ceiling (judge counted 536 files / 6,890 top-level tests at edc1f173)"
  - "(struck: R-1 pre-authority raw read, overruled by the operator 2026-09-28)"
  - "import req_coverage.extract_req_markers from a demo tool — importable without sys.path hacks decides reuse vs blocker"
  - "largest test file token estimate vs per-payload ceiling — decides chunk split rule"
  - "census cost: payload count x per-payload tokens x Q4 model price, before any smaller alternative"
  - "read 10 raw model responses from tmp/test-map/ before any aggregate is quoted (R-1 post-run half)"
branches:
  - "partition count over max_map_items → preflight fails; raise declared ceiling in FR, never silent rebatch"
  - "any failed row, canary miss, or count mismatch → run rejected, no canonical test-map.* written"
  - "req_coverage extractor not importable as-is → stop; separate FR (C-6 forbids framework/script edits here)"
  - "token totals needed in JSON → refused; captured from CLI --token-usage into demo-output.log (R-4)"
  - "graph or prompt write → author.sh route, never manual"
delegations:
  - "judge.sh: 1 run done; 1 more if the R-1..R-6 fold is disputed"
  - "author.sh: 1 run for graph.yaml + map prompt"
  - "census: smoke on the canary fixture + 10 files, then 1 full-scope run"
  - "outsider.sh + review.sh: 1 run each on the enforcement PR"
waits:
  - "operator Q4 model/spend decision"
  - "judge"
  - "full census run"
  - "PR CI"
commands:
  - scripts/judge.sh
  - scripts/author.sh
  - yamlgraph graph lint examples/demos/test_map/graph.yaml
  - yamlgraph graph run examples/demos/test_map/graph.yaml --token-usage
  - python scripts/req_coverage.py --strict
  - scripts/outsider.sh
  - scripts/review.sh
```

## Judgement fold (2026-09-28)

| Revision | Disposition |
|---|---|
| R-1 pre-authority raw-input table | **Overruled by the operator** ("r-1 overruled. aint gonna happen. enforce"). No pre-authority table. The *post-run* raw-response read (revised AC-12) is a separate criterion and stays. |
| R-2 topology + ceilings | Folded: § Frozen ceilings; stage 3 below. One payload = one file or one chunk of whole test functions of one file; one LLM call per payload; overflow fails in the freeze tool before any LLM call. |
| Q4 model/spend | **(b) default resolution**, resolved by the agent from the original request ("analyze each test with default provider and model"); the operator did not answer Q4 separately. The map node pins no provider/model; `PROVIDER` env else `anthropic`, model from `DEFAULT_MODELS` (`{PROVIDER}_MODEL` env overrides). Quality and price follow the environment; this shell has `PROVIDER=inception` (mercury-2, ≈$1), a clean environment gets anthropic/claude-haiku-4-5 (≈$3–4). Temperature pinned to 0.0. Effective provider/model/temperature recorded in provenance. |
| R-3 reject on any defect | Folded: stage 5–6. Any defect ⇒ no `test-map.*`; only `tmp/test-map/test-map-rejected.json`. Stale canonical files are deleted first. |
| R-4 freeze + provenance | Folded: freeze rejects a dirty or untracked scope (`git status --porcelain --untracked-files=all -- <scope>`), then records path, SHA-256, bytes per file. `token_usage` is removed from the JSON; `--token-usage` output goes to `demo-output.log`. |
| R-5 extraction/classification | Folded: § Extraction contract, § Description validator, tie-break order in the classification guidance. |
| R-6 authoring/evidence | Folded: the authoring report is transient; committed proof is `examples/demos/test_map/proof.json`. |

The revised AC-01..AC-15 below are the judgement's, with AC-01's R-1 clause
removed by the overrule.

### Frozen ceilings

| Ceiling | Value | Enforced by |
|---|---|---|
| Source files | 700 | freeze tool, before any LLM call |
| Source bytes (total) | 6,000,000 | freeze tool |
| Estimated tokens per payload (chars / 4) | 8,000 | freeze tool; a single test over the budget fails, never truncates |
| Partitions = LLM calls = `max_items` / `max_map_items` | 900 | freeze tool, and the map node's `max_items` |
| Concurrency | 8 | graph `config.max_concurrency` |
| Per-call timeout | 180 s | map sub-node `timeout` |
| Wall-clock timeout | 3,600 s | graph `config.timeout` |

At main 977bf6e7 the scope is 538 test files, 4.8 MB.

### Extraction contract

- Files: `git ls-files` under each scope directory matching `test_*.py`.
- Tests: top-level `test*` functions (sync and async) and `test*` methods of
  top-level `Test*` classes. Nodeid: `<path>::<name>` or
  `<path>::<Class>::<name>`; parametrized tests appear once, unparametrized.
  `line` is the `def` line.
- `markers`: sorted unique `pytest.mark.<name>` names inherited from module
  `pytestmark`, class decorators, class-body `pytestmark`, and function
  decorators. **`req` is excluded** from `markers`; it is represented by
  `reqs`.
- `reqs`: exactly what `scripts/req_coverage.extract_req_markers` reports for
  the test, loaded by path (no copy, no `sys.path` edit). Module-level
  `pytestmark` req marks are therefore not in `reqs`, matching the existing
  mapping.

### Description validator

Valid iff: after stripping, non-empty; no newline; ends with exactly one of
`.` `!` `?`; and contains no earlier sentence break, where a sentence break
is `.`/`!`/`?` followed by whitespace and more text, except after the
abbreviations `e.g.`, `i.e.`, `etc.`, `vs.`, `cf.`. Dotted paths
(`yamlgraph.linter`, `graph.yaml`) contain no whitespace after the dot and
pass. The judgement's literal wording ("no earlier terminal punctuation
followed by non-whitespace") would reject every dotted path, which its own
abbreviation/path fixture requirement contradicts; this reading keeps the
fixture requirement.

## Proposed Solution

A new graph `examples/demos/test_map/graph.yaml`, authored through the sole
authoring route (`scripts/author.sh`, doctrine
`.github/skills/graph-authoring/doctrine.md`). It follows the six
corpus-map-reduce stages.

1. **Freeze (tool, no LLM).** Record the git SHA and list
   `tests/unit/**/test_*.py` and `tests/integration/**/test_*.py`. This is
   the `req_coverage` framework scope. `.github/hooks/tests` is left out,
   the same way FR-436 leaves it out; see Q1.
2. **Extract (tool, no LLM).** For each file, AST-enumerate test functions
   and methods: nodeid, line, decorators or markers, and `req` marks through
   the existing `req_coverage` extractor, imported rather than copied. Also
   capture the file's import block and each test's source.
3. **Partition (tool).** One payload per file. If a file goes over the
   per-payload token ceiling (for example `test_graph_commands.py`, 1,442
   lines), split it greedily into chunks of whole test functions, each
   carrying the file's import block and its collector-owned metadata
   (`partition_id`, `path`, `nodeids`). Files with no tests produce no
   payload. Any ceiling overflow raises before the first LLM call; there is
   no rebatching.
4. **Map (LLM, bounded).** Each prompt gets the file path, the imports, and
   the chunk's tests, and must return
   `records: list[{nodeid, description, target, test_type}]`. The inline
   schema uses enum-constrained `target` and `test_type`. No `provider:` or
   `model:` is pinned (Q4 b); the default resolution applies (`PROVIDER`
   env, then `DEFAULT_MODELS`); `{PROVIDER}_MODEL` env remains the override.
   Temperature 0.0. `on_error: skip` so failures reach the reconciler on the
   map's failures channel.
5. **Reconcile (tool, no LLM).** Join LLM records to AST rows on `nodeid`.
   Every one of these is a defect: map error; unusable or duplicate map
   index; a partition with no result; a malformed record; unknown nodeid;
   nodeid from another partition; duplicate nodeid; out-of-enum `target` or
   `test_type`; invalid description; an AST nodeid with no record. Any
   defect rejects the run: the reconciler deletes stale `test-map.*`, writes
   only `test-map-rejected.json` (defects with raw text, raw findings,
   counts), and raises.
6. **Canary (tool).** `examples/demos/test_map/canary.json` lists real
   corpus nodeids with expected `target` and `test_type`: at least one per
   target value and one `tests/unit` integration case. Only the reconciler
   reads it; it is never in model input. It runs after reconciliation and
   before rendering; a mismatch or an absent canary nodeid rejects the run
   as in stage 5.
7. **Render (tool, no LLM).** Write `raw-responses.jsonl` (the map
   results verbatim, with partition IDs), then `test-map.json`:
   `{provenance: {run_id, commit_sha, scope, ceilings, files: [{path, sha256, bytes, tests}], corpus_hash, artifact_hash, provider, model, temperature, counts: {files, tests, partitions}, calls: {estimated, actual}, reconciliation: {rows, failed_rows: 0, defects: 0}, canary}, rows: [...]}`.
   `artifact_hash` is the SHA-256 of the canonical rows serialization.
   Then render `test-map.md` from that JSON:
   - provenance head;
   - a `target × test_type` count table;
   - a per-directory, per-file table of `test | line | target | type | reqs | description`.

   Output paths come from caller vars (`--var json_path`, `--var md_path`).
   The defaults go under `tmp/test-map/`.

```bash
yamlgraph graph run examples/demos/test_map/graph.yaml \
  --var json_path=tmp/test-map/test-map.json \
  --var md_path=tmp/test-map/test-map.md
```

**Classification guidance (prompt, not code):**

- `target` is the single **primary exercised surface** — what the test
  exercises, not where it sits. When a test spans several surfaces, the
  tie-break order is `linter` > `examples` > `scripts` > `docs` > `core` >
  `other` (the most specific surface wins; `core` is what almost every test
  imports):
  - `core`: `yamlgraph/` runtime, excluding the linter;
  - `linter`: `yamlgraph/linter` and `graph lint`;
  - `examples`: `examples/**` graphs, tools, and demos;
  - `scripts`: `scripts/**` and `.github/hooks`;
  - `docs`: doc, FR, CAP, or changelog consistency;
  - `other`: anything else.
- `test_type`:
  - `unit`: in-process, mocked or no I/O beyond tmp_path;
  - `integration`: real subprocess, network or LLM, or a full graph run over
    repo files;
  - `other`: everything else.

## Acceptance Criteria

The judgement's revised criteria, verbatim except AC-01 (R-1 clause removed
by the operator overrule).

- [ ] AC-01: The committed FR records the resolved Q4 model/spend decision
  plus all numeric ceilings from R-2.
- [ ] AC-02: `examples/demos/test_map/graph.yaml` and its prompts are
  authored through `scripts/author.sh`; `tmp/draft-authoring-report.md` is
  present and substantive but uncommitted; graph lint and the narrow smoke
  are recorded honestly.
- [ ] AC-03: Freeze/extraction tests prove immutable-input handling,
  per-file path/SHA-256/bytes, path-qualified nodeid, line, sync/async and
  class test discovery, module/class/function marker inheritance, the
  declared `req`-marker policy, and equality with imported
  `req_coverage.extract_req_markers`.
- [ ] AC-04: Partition tests prove splits occur only between whole test
  functions, every payload carries the import block and collector-owned
  partition metadata, every nodeid belongs to exactly one payload, ordering
  is stable, and every configured source/byte/token/partition/call limit
  rejects before the first LLM call.
- [ ] AC-05: The map makes exactly one structured-output LLM call per
  file/chunk payload at the frozen concurrency and timeout. The schema
  requires `nodeid`, one-sentence `description`, enum-constrained `target`,
  and enum-constrained `test_type`; effective provider/model/temperature
  follow the recorded Q4 policy.
- [ ] AC-06: Reconciliation tests cover missing, unknown, duplicate,
  out-of-enum, malformed-description, wrong-partition, and map-error
  results. Every case produces diagnostic evidence and rejects acceptance;
  no failed row can appear in an accepted canonical map.
- [ ] AC-07: Classification tests cover every target and type, a
  multi-surface tie, a `tests/unit` subprocess/integration case, and the
  exact sentence-validation boundary, including abbreviations or dotted
  paths.
- [ ] AC-08: Markdown is rendered only from the accepted canonical JSON.
  Tests prove target-by-type counts equal JSON counts and every JSON nodeid
  appears exactly once in Markdown.
- [ ] AC-09: Withheld canary answers are never included in model input. A
  canary test covers every target family plus a unit-directory integration
  case; any mismatch rejects the run before `test-map.json` or
  `test-map.md` is written.
- [ ] AC-10: Accepted JSON provenance contains run ID, commit SHA, per-file
  hashes/bytes, corpus and artifact hashes, effective
  provider/model/temperature, source-file/test/partition counts, estimated
  and actual calls, reconciliation totals, and `failed_rows: 0`. Tests
  verify each field from deterministic inputs.
- [ ] AC-11: One real full-scope run at a pinned SHA succeeds with AST count
  == reconciled row count == unique nodeid count, every required invariant
  true, zero failed rows, and actual calls equal primary partitions.
  `demo-output.log` records the command, SHA, outcomes, and CLI
  `--token-usage` totals; `proof.json` records compact provenance and
  invariant results.
- [ ] AC-12: Before any aggregate table is quoted, at least ten raw model
  responses are read from `tmp/test-map/`; `proof.json` cites the
  corresponding nodeids and records one concrete observation per response,
  including at least three directory-versus-classification mismatches.
- [ ] AC-13: The full generated map and raw responses remain under
  `tmp/test-map/`; only `demo-output.log` and compact `proof.json` are
  committed as run evidence.
- [ ] AC-14: A new CAP and REQ are allocated at enforce time, every new test
  carries that REQ marker, and `python scripts/req_coverage.py --strict`
  passes.
- [ ] AC-15: The demo README documents scope, taxonomy, Q4 model policy,
  ceilings, rejection semantics, output locations, and the exact real-run
  command. A changelog fragment and diary entry with a **Seed:** are
  present.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| A1 | Extend `req_coverage.py` with heuristic target/type columns (imports → target, `subprocess` → integration) | **Rejected as sole mechanism.** Import heuristics cannot produce the one-sentence description and misfire on tests that import core only to drive examples (the `regex_fourth_exclusion` trap). Deterministic columns (`reqs`, `markers`) are kept as inputs. |
| A2 | Reuse `corpus_census` with new discover/extract adapters, item = one test function | **Rejected.** About 6,800 items against the census map cap of 200, and the census envelope is a single `judgement` label, not a three-field record. Item = file with one label loses per-test granularity. |
| A3 | Extend `corpus_census` to support multi-record findings | **Rejected for this FR.** It changes the FR-892/940/943 envelope contract that four adapter families depend on, which is scope creep. It can be revisited if a second multi-record census appears (graduation rule). |
| A4 | Map per test function (one call each) | **Rejected.** About 6,800 calls against about 600, with no quality gain: the file's imports and fixtures are shared context the model needs anyway. |
| A5 | LLM writes the Markdown | **Rejected.** The two artifacts could drift. Markdown is a deterministic rendering of the canonical JSON. |
| A6 | Commit the map as a maintained reference artifact | **Rejected by D2.** A committed map goes stale with every test change; nothing consumes it on a schedule. |

## Operator decisions (2026-09-28)

The operator accepted all three recommendations ("proceed as recommended"):

- **D1:** `.github/hooks/tests` is excluded (Q1 a), matching FR-436 scope.
- **D2:** artifacts are written to `tmp/test-map/` only; the committed
  evidence is `demo-output.log` plus an allowlisted proof (Q2 a).
- **D3:** the target enum stays at the six requested values (Q3).
- **D4 (enforce time):** R-1 overruled — "r-1 overruled. aint gonna
  happen. enforce".
- **D5 (enforce time):** Q4 = (b) default provider/model resolution. The
  operator did not answer Q4 separately; the agent resolved it from the
  original request ("analyze each test with default provider and model").
- **D6 (enforce time):** "allow 5% error rate" — amends AC-06 and R-3
  ("any defect rejects"). A partition whose map call fails, or whose
  records carry defects, is listed in `failed_partitions` with its nodeids
  and defects, and its tests are left unmapped. More than 5% failed
  partitions, any defect not attributable to one partition, or any canary
  miss still rejects. Canary entries inside a failed partition count as
  `skipped`, never `passed`. The map node retries twice with validation
  feedback (`on_error: retry`, `max_retries: 2`) and declares
  `min_success: 0.95`, so an exhausted retry still makes the CLI exit 3.

## Implementation Status

Branch `feat/fr1137-test-map-enforce`. RED/GREEN pairs: `edd370b2` /
`6cb62d87` (pipeline), `a9dcd9fb` / `3e2fc178` (`MapFailure` objects),
`8fb5dafd` / `b78d9fd8` (D6 allowance).

**Defect found by the first full run.** The map returns `failures` as typed
`MapFailure` objects (FR-1073), not dicts; `publish_map` crashed while
writing the rejection report. Fixed by normalising through
`MapFailure.model_validate(f).model_dump()`.

**Cause of the failed calls.** In that first run 3 of 545 calls failed
validation: mercury returned the `records` array without its
`{"records": ...}` wrapper. Answered here by the prompt line "never return
a bare array", the retry, and D6. The general fix belongs in the
structured-output boundary, not in this demo:
[FR-1140](FR-1140-bare-list-structured-output.md).

**Accepted full run** at `b78d9fd8` (inception/mercury-2.5, temperature
0.0), recorded in `examples/demos/test_map/demo-output.log` and
`examples/demos/test_map/proof.json`:

| Measure | Value |
|---|---|
| Files / tests / partitions | 538 / 6,891 / 546 |
| Calls estimated / actual | 546 / 546 (plus 2 retries, both bare-array) |
| Failed partitions / failed rows / defects | 0 / 0 / 0 |
| Canary | 7 checked, 7 passed, 0 skipped |
| Tokens | 1,817,104 in / 1,645,875 out |

The dry-run census at the earlier SHA gave 537 files / 6,903 tests / 545
partitions; the counts moved with main between runs, and each run's own
AST count equals its reconciled row count.

**Raw read (AC-12).** Twelve responses spread across the corpus were read
before any aggregate; observations are in `proof.json`. Four are
directory-versus-classification mismatches with one shared shape: the
model labels by the code a test *imports*, not by the artifact it
*guards* — this FR's own demo tests, pre-commit config tests, and
copilot-instructions tests all come out `core`. Aggregates after the read:
`core` 4,626 (67%), `examples` 1,090, `linter` 410, `scripts` 329, `other`
225, `docs` 211; `unit` 6,419, `integration` 472, `other` 0. Of the 296
rows in files named for examples or demos, 35 are labelled `core`. Read
the `core` share as an upper bound.

**Planned Operations reconciliation.** All probes ran; the req_coverage
extractor imported as-is; no ceiling was raised. Delegations: judge 1 run,
author.sh 3 runs (brief revisions 1–3; revision 3 for D6), smoke runs
plus 2 full-scope runs (the first hit the 3 bare-array failures and then
the `MapFailure` crash while writing its rejection; the second was
accepted). outsider.sh and review.sh run on the PR.

## Questions for the human (resolved — see Operator decisions)

- **Q1 — scope of `.github/hooks/tests`.** Options:
  - (a) exclude, matching `req_coverage` FR-436 scope;
  - (b) include, as target `scripts`.

  Recommended: **(a)** for the first run.
- **Q2 — where the artifacts live.** Options:
  - (a) `tmp/` only, with an allowlisted proof committed;
  - (b) commit `docs/test-map/test-map.{json,md}` stamped with SHA and
    regenerated on demand;
  - (c) a CI-regenerated artifact.

  Recommended: **(a)**. A committed map goes stale with every test change, and
  nothing yet consumes it on a schedule.
- **Q3 — target enum.** Should `hooks` be split out of `scripts`? Should
  `graphs` (for `graphs/**` YAML) be split out of `examples`? Recommended:
  keep the six requested values and let the model use `other` for edge cases.

## Related

- `scripts/req_coverage.py`, `ARCHITECTURE.md`, `capabilities/` — the
  existing REQ ↔ test mapping
- `reference/patterns/corpus-map-reduce.md`
- `examples/demos/corpus_census/`, `examples/demos/person_profile_census/`
- `yamlgraph/config.py` `DEFAULT_MODELS`; `yamlgraph/utils/llm_factory.py`
  provider resolution
