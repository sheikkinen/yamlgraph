# Codebase Review — Refactoring & Summer Cleanup

**Date:** 2026-07-12
**Scope:** full `yamlgraph/` source + repo hygiene; v0.5.11 baseline
**Method:** radon cc/mi, vulture, jscpd, wc, import-linter (all green in
pre-commit), plus the Scripture's `incident_density_ranking` (diary
mentions ÷ source mass, not size alone) and `growth_as_default` (a mature
system benefits more from pruning claims than planting features).

## Snapshot

| Metric | Value | Verdict |
|---|---|---|
| Source | 23,118 lines / 122 modules | healthy for scope |
| Tests | 100,885 lines (4.4 : 1 test:src) | strong; watch witness rot |
| Duplication (jscpd) | 0.34 % tokens, 3 clones | excellent |
| Dead code (vulture) | 0 unreported | excellent |
| TODO/FIXME | 2 | excellent |
| noqa | 27, all confessed | healthy |
| Complexity ≥ C | 18 functions, worst C(20) | localized hotspots |
| Modules > 400 lines | 9 (gate is 450, 5 within 15 lines of it) | pressure building |
| CAP registry | 181 active-file CAPs, 23 `fr: legacy` | pruning due |
| FRs / diary entries | 695 / 1,042 | graduation sweep due |

The code is clean by every mechanical gate. The entropy is not in
functions — it lives in (a) dead scaffolding the gates don't scan,
(b) modules idling at 90–100 % of the size gate, (c) registries that grew
monotonically, and (d) two API-shape duplications the clone detector
only half-sees.

---

## P1 — Delete (dead scaffolding; zero-risk, one afternoon)

1. **`yamlgraph/cli/deprecation.py` is a dead shim.** `DeprecationError`
   and `deprecated_command` have **zero callers** outside their own
   module. A deprecation helper with no deprecated commands left is the
   exact "special faulty code" class FR-713 F13 named — the migration it
   served is complete. Delete module + its vulture-whitelist entries.
2. **`build/` and `langgraph_showcase.egg-info/` are tracked in git.**
   The egg-info carries the project's *previous name* — a fossil. Build
   artifacts in version control drift silently from source (the stale
   copy of `yamlgraph/` under `build/lib/` already disagrees with HEAD).
   `git rm -r`, add to `.gitignore`. Note: run the
   `boundary_inventory` check first (nested `.git`? untracked files?).
3. **Runtime droppings at repo root:** `outputs/` (horoscopes, image
   prompts), `vectorstore/`, `data/pipeline.db`, `dist/`. Two are
   git-tracked. Runtime state does not belong in the framework repo —
   ignore or relocate under `tmp/`.
4. **`docs-planning/` — 63 files, untouched since 2026-06.** Planning
   docs whose FRs shipped or died. Sweep: fold the ≤5 still-live ones
   into their FRs, delete the rest. The FR is the source of truth; a
   parallel planning tree is a second state that only decays.
5. **`graphs/` contains only `enforcement/`** yet README/CLAUDE.md
   examples still say `yamlgraph graph run graphs/showcase.yaml`.
   Either the docs lie or the directory does. Fix the docs (examples
   moved to `examples/`), keep `graphs/enforcement/` or move it under
   `.chaplain/`.

**Deletion ledger estimate:** ~1,200 tracked-file lines + 63 stale docs,
zero behavior change.

## P2 — Structural (the real refactoring; 1–2 days each, FR-worthy)

### P2.1 The 16-parameter signature, copied three times

`execute_prompt()` → `PromptExecutor.execute()` → `prepare_messages()`
thread the same ~12 kwargs by hand; jscpd flags the first pair (35
lines, the module's only real clone). Every new knob (max_tokens,
thinking_budget…) has been added in three places. **Fix:** one frozen
`PromptRequest` dataclass (mirrors the FR-223 `LLMNodeConfig` move that
already fixed this pattern in llm_nodes). Delete the duplicated
docstrings; the dataclass is the doc. This is the highest
knowledge-per-line refactor available — the signature is the framework's
front door.

### P2.2 Root-package sprawl: 27 modules, 6,097 lines, no seams

The three-layer architecture is enforced between layers but Layer 2 is a
flat bag. Natural sub-packages already visible in the names:

| Cluster | Modules | Lines |
|---|---|---|
| `a2a/` | a2a_server, a2a_message | 613 |
| `export/` | skill_export, skill_export_writer, mcp_server | 815 |
| `compile/` | node_compiler, edge_compiler, map_compiler, graph_loader, pipeline_template, verify_insert | ~1,800 |

Move, don't rewrite. Import-linter contracts gain three precise seams;
`reference/module-map.md` regenerates. Do **not** touch executor* in the
same PR (F9 lesson: one concern per commit).

### P2.3 Size-gate pressure: five modules within 15 lines of the cap

`graph_schema.py` (448), `checks_contracts.py` (441), `node_compiler.py`
(440), `state_builder.py` (438), `checks_semantic.py` (435),
`executor_async.py` (435). Each next feature triggers an unplanned
split under deadline pressure — the worst time to choose seams. Split
the two with obvious fault lines *now*:
- `graph_schema.py` → node-config models vs graph-level models.
- `executor_async.py``run_graph_streaming_native` is C(17) *and* in the
  fattest module — extract the event-translation loop; that one move
  fixes both a complexity and a size finding.

### P2.4 Complexity hotspots that are also incident-dense

Per `incident_density_ranking`, complexity only matters where incidents
concentrate. Cross-referencing radon ≥ C with diary/confession density:

| Function | CC | Why it matters |
|---|---|---|
| `edge_compiler._process_edge` | 20 | routing = core semantics; edge bugs are graph-wide |
| `edge_compiler._add_conditional_edges` | 18 | same organ |
| `executor_async.run_graph_streaming_native` | 17 | streaming = FR-057–060 scar tissue |
| `tools/python_tool.load_python_function` | 17 | boundary: user code enters here |

The other 14 C-grade functions (skill_export, a2a parse, mcp validate…)
are leaf conveniences — leave them; refactoring them is
`working_system_inertia` in reverse (busywork on low-incident code).

## P2.5 — Double-check addendum (2026-07-12, second pass)

The first pass ran radon/vulture/jscpd but **skipped bandit** — the
exact instrument the code-analysis skill lists with a "0 medium+"
target. Running it surfaced two findings the review missed, both of the
`detection_without_enforcement` class (Scripture: "lint without gate =
advisory → add CI block or remove claim"):

1. **Bandit is gated nowhere** (not in pre-commit, not in CI — the CI
   `security` job is pip-audit, dependencies only). Current findings:
   1 HIGH (B701 jinja2 `autoescape=False` in `utils/template.py`) +
   3 MEDIUM (2× B104 bind-`0.0.0.0` defaults in the a2a CLI, B108 `/tmp`
   FSM socket). Every one is already **ruff-confessed** (S701, S104,
   CONF-302) and judged acceptable for its context — prompt templates
   are not HTML, the socket prefix is deliberate — but bandit does not
   honor ruff `noqa`, so the skill's "0 medium+" claim is false as
   stated. Fix is one of: add bandit to pre-commit with `# nosec`
   mirrors of the existing confessions (~30 min), or delete the bandit
   target from the skill. A claim with no gate decays into a lie.
2. **Coverage gate drift:** CLAUDE.md documents "80% coverage threshold"
   for the CI `test` job; `pyproject.toml` enforces
   `--cov-fail-under=70`. The documented gate and the enforced gate
   disagree by 10 points — one of them lies
   (`gate_checks_shape_not_substance`, doc-claim variant). Align to the
   enforced number or raise the enforcement.

P2.1–P2.4 claims were re-verified against source in the same pass:
signatures, sizes, radon grades, and the dead-shim zero-caller claim all
hold as written.

## P3 — Registry pruning (the FR-465/466 arc, continued)

- **23 CAPs still `fr: legacy`** — each is a capability claim with no
  originating FR. Re-derive or retire; the changelog-req cross-gate
  cannot validate them (it skips `legacy`), so they are unguarded claims.
- **695 FR files, ~600 terminal (Completed/Rejected).** Move terminal FRs
  to `feature-requests/archive/` (keeps grep-ability, halves the
  directory listing the chaplain and humans scan). Mechanical script.
- **1,042 diary entries** — the graduation pipeline seed
  (`diary_graduation_pipeline`) is now overdue in the data: at this
  volume, recurring heuristics are statistically present but unfindable
  by eye. One `diary-index` graph run clustering by named trap would
  surface graduation candidates; three sibling-project heuristics
  already graduated this quarter prove the yield.

## P4 — Seams to watch (not yet refactors)

1. **`_PROVIDER_FINGERPRINT_VARS` duplicates constructor knowledge**
   (FR-713 Part B diary seed): each provider's env-reads are declared in
   `llm_factory` but *consumed* in `llm_providers`. A `reads_env`
   attribute on the constructor would make the fingerprint derived, not
   duplicated. Wait for the first drift bug before building it —
   but the moment a new provider ships with an unfingerprinted env var,
   this graduates to a fix FR.
2. **Sync/async mirrors** (`executor` / `executor_async`,
   `llm_factory` / `llm_factory_async`): the sync-first pattern is
   doctrine, but FR-713's own out-of-scope note names the end-state —
   async-first `run_graph` with sync CLI as thin wrapper, which would
   delete the bridge *and* half of executor_async. That is the next
   substrate promotion; do not partially converge before it.
3. **`logging.py` sets `propagate=False` at import** — three test files
   now carry the same `_propagate_yamlgraph_logs` fixture (FR-707/709/713
   cleanups). Normalize at the boundary: one autouse fixture in
   `tests/conftest.py`, delete the three copies. Five-minute fix, closes
   a recurring trap ("the witness that only passed in company").

## Recommended sequence

| # | Action | Size | Risk |
|---|---|---|---|
| 1 | P1 deletions + P4.3 conftest fixture | ½ day | none |
| 2 | P2.1 `PromptRequest` dataclass | 1 day | low (type-checked) |
| 3 | P3 FR archive + legacy-CAP triage | ½ day mechanical + judge pass | none |
| 4 | P2.3 split graph_schema + executor_async | 1 day | low |
| 5 | P2.2 root sub-packages (3 separate PRs) | 1–2 days | medium (import churn) |
| 6 | P2.4 edge_compiler decomposition | 1 day | medium (core semantics — TDD) |

Each lands as its own judged FR with a deletion ledger; per FR-713's
promotion test, **every one of these should net-delete or net-move —
none should add**.

## What NOT to do

- No new abstractions for the 14 leaf C-grade functions.
- No cache eviction, no connection pooling, no bridge sentinel — those
  wait on NC-367's measurement (rate-layer discipline: measure, then
  mitigate).
- No merging of linter check modules — 8 files of ~300 lines each with
  one concern apiece is the *goal* shape, not a problem.
- No touching `utils/fsm/` (915 lines, densest incident-to-code ratio in
  the codebase per the 2026-05-31 inventory) without its own research
  phase — that code is congealed production knowledge.

## Closing observation

The mechanical gates (ruff, vulture, jscpd, radon, size, import-linter)
have kept the *code* clean; nothing here is a fire. What accumulated
instead is **meta-entropy**: dead scaffolding below the gates' scan line,
registries that only ever grew, and one signature copied three times at
the front door. The cleanup priced above is ~5 days of net-negative-line
work — the summer haircut, not surgery.
