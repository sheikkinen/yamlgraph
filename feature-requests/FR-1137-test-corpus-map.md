# Feature Request: Test Corpus Map — per-test description, target, and type

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged 2026-09-28 — APPROVED WITH REVISIONS
([judgement](FR-1137-test-corpus-map.judgement.md)); R-1..R-6 and the Q4
model/spend decision are not yet folded, and enforcement is gated on
them (C-1)
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
  - "read 10 raw test functions end-to-end before authority (R-1), 3+ with directory-vs-classification mismatch"
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
3. **Partition (tool).** One item per file. If a file goes over a token
   budget (for example `test_graph_commands.py`, 1,442 lines), split it into
   chunks of whole test functions, each carrying the file's import block.
   Item count must stay within the map cap, so batch items if the partition
   exceeds `max_items`.
4. **Map (LLM, bounded).** Each prompt gets the file path, the imports, and
   the chunk's tests, and must return
   `records: list[{nodeid, description, target, test_type}]`. The inline
   schema uses enum-constrained `target` and `test_type`. No `provider:` or
   `model:` is pinned, so the default resolution applies (`PROVIDER` env,
   then `DEFAULT_MODELS`), with optional `--var provider/model` overrides in
   the corpus_census style. `on_error` must be explicit.
5. **Reconcile (tool, no LLM).** Join LLM records to AST rows on `nodeid`.
   Rules:
   - A missing record becomes a fail-closed row
     (`target: other, test_type: other, description: null, error: <reason>`).
     The row is demoted, never dropped.
   - An unknown or duplicate nodeid is a batch-fatal error.
   - `description` must be one sentence: non-empty, and it must not contain
     a sentence break followed by more text. A row that fails is demoted
     with a reason and keeps the raw text.
   - Final check: count of AST test functions == count of JSON rows.
6. **Canary (tool).** A small fixed set of tests with known classification:
   at least one each of core, linter, examples, scripts, and docs, plus one
   known subprocess or integration test in `tests/unit/`. They live in a
   fixture file in the demo directory. If any canary is misclassified the
   run fails visibly, and the artifacts are written as `*.REJECTED.*`.
7. **Render (tool, no LLM).** Write `test-map.json`:
   `{provenance: {sha, provider, model, run_at, files, tests, failed_rows, token_usage}, rows: [...]}`.
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

- `target` is decided by what the test *exercises*, not by where it sits:
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

- [ ] AC-01: The graph exists at `examples/demos/test_map/graph.yaml` with
  prompts under `prompts/`. It was authored through `scripts/author.sh`, and
  the draft authoring report is committed as evidence.
  `yamlgraph graph lint` passes.
- [ ] AC-02: Extraction reuses the `req_coverage` marker extractor
  (import, not copy). A unit test proves that `reqs` for a fixture file
  equals what `req_coverage` reports for it.
- [ ] AC-03: The map prompt pins no provider or model. A unit test proves
  that the effective provider and model recorded in provenance come from
  default resolution when no vars are set.
- [ ] AC-04: Reconciliation unit tests cover:
  - missing record → demoted row with reason;
  - unknown nodeid → batch-fatal;
  - duplicate nodeid → batch-fatal;
  - out-of-enum value → rejected by the schema, then demoted;
  - multi-sentence description → demoted with raw text kept;
  - AST count ≠ row count → fatal.
- [ ] AC-05: Chunking unit test: a synthetic file over the token budget is
  split only at test-function boundaries, every chunk carries the import
  block, and the union of chunk nodeids equals the file's nodeids.
- [ ] AC-06: Both artifacts are produced from one record set. A unit test
  renders Markdown from a fixture JSON and checks that per-target counts in
  the table equal counts in the JSON, and that every JSON nodeid appears in
  the Markdown.
- [ ] AC-07: The canary fixture exists, and a unit test proves that a
  misclassified canary makes the run fail and write `*.REJECTED.*`.
- [ ] AC-08: A real run over the full framework test scope at a pinned SHA
  completes with `tests` in provenance equal to the AST count. A run log is
  committed as `examples/demos/test_map/demo-output.log`, produced by this
  graph (`proof_by_placement`).
- [ ] AC-09: Raw read before aggregates (`read_raw_output_first`). Before
  the count table is quoted anywhere, the FR records at least 10 raw rows,
  each with one concrete observation. At least 3 must come from files whose
  directory suggests a different target or type.
- [ ] AC-10: New CAP and REQ allocated at enforce time, not reserved now
  (FR-180). Every new test carries its `req` marker.
  `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: A changelog fragment in `changelog/unreleased/`, a README in the
  demo directory, and a diary entry with a **Seed:**.

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
