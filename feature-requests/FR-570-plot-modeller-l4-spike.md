# Feature Request: FR-570 Plot Modeller — L4 kind-classification spike

**Priority:** HIGH
**Type:** Feature
**Status:** Enforced — GO (optimistic); 28/35 (0.80) overall, blind-corpus re-test pending (2026-06-23)
**Effort:** 1–2 days
**Requested:** 2026-06-23
**Plan:** [`plan-v5-yaml-native-planner.md`](../examples/dungeon_master/docs/plan-v5-yaml-native-planner.md) §8b, §12 step 1
**Predecessor:** FR-560–565 (v3 plot model, all enforced)
**Blocks:** Full v5 pipeline build (the spike's pass/fail determines whether to proceed)

## Summary

Build a standalone YAMLGraph example (`examples/plot_modeller`) that runs the v5
planner's Layer 4 (classify prose glosses into the 16-kind Propp-derived alphabet)
against four genre synopses using a small model, evaluates accuracy against
hand-authored ground truth, and produces a go/no-go verdict for the full pipeline.

## Value statement

The v5 planner plan specifies a 7-layer pipeline but has zero running code.
Three plan iterations (v3→v4→v5) have been written without testing the pipeline's
central bet: can a small model classify prose into 16 structural categories?
This FR produces the first falsifiable evidence — a measured accuracy number
across 4 genres — before committing to 17 nodes and 7 prompts.

YAMLGraph gains a non-trivial example demonstrating: LLM nodes with YAML output,
Python validation tools, conditional retry edges, and structured evaluation
against a ground-truth corpus.

## Problem

The v5 pipeline's Layer 4 asks a Haiku-class model to map a one-sentence gloss
(e.g., "Hagen's hired men abduct Witness Pell from the court safe house") to one
of 16 closed categories (→ `villainy`). This is the first layer that isn't a
solved NLP task (L1–L3 are entity extraction and sentence decomposition). If L4
fails, the vocabulary needs shrinking, the prompt needs restructuring, or the
pipeline architecture changes — and none of the downstream layers matter.

There is no empirical evidence that this works. The claim rests on intuition and
the v4 plan's rhetoric. The diary heuristic says: *review the claim at its own
layer.*

## Proposed solution

### 1. Example structure

```
examples/plot_modeller/
├── graphs/
│   └── classify_kinds.yaml        # L4 graph (LLM + validator + retry)
├── prompts/
│   └── classify_kinds.yaml        # L4 prompt (16-kind vocab in-prompt)
├── nodes/
│   ├── __init__.py
│   └── tools.py                   # validate_kinds, load_glosses, load_synopsis
├── fixtures/
│   ├── synopses/                  # 4 prose synopses (.txt)
│   └── ground-truth/              # 4 hand-authored YAML plans
├── results/                       # Pipeline output (gitignored)
├── tests/
│   ├── __init__.py
│   └── test_evaluate.py           # Evaluation + regression
├── evaluate.py                    # CLI: compare results to ground truth
└── README.md
```

### 2. The L4 graph (`graphs/classify_kinds.yaml`)

Minimal YAMLGraph graph: one LLM node, one Python validator, conditional retry.

```yaml
metadata:
  name: classify-kinds
  description: >
    L4 spike: classify prose glosses into the 16-kind Propp alphabet.
  # No hardcoded provider/model — resolved from PROVIDER env var (or the
  # prompt's own metadata). Run with PROVIDER=anthropic for Haiku-class cost;
  # the spike's model choice is a run-time decision, not a graph constant.

state:
  glosses:
    type: list
    description: "Input: beat glosses with id, gloss, chapter"
  kinds_raw:
    type: str
    description: "Raw LLM YAML text (classify node output, default parse_json: false)"
  kinds:
    type: list
    description: "Output: parsed+validated kinds (written by validator on success)"
  validation:
    type: dict
    description: Validator result

nodes:
  classify:
    type: llm
    prompt: prompts/classify_kinds.yaml
    state_key: kinds_raw     # J1: raw text lands here, not in `kinds`

  validate:
    type: python
    tool: validate_kinds

edges:
  - from: START
    to: classify
  - from: classify
    to: validate
  - from: validate
    to: classify
    condition: "validation.ok == false"
  - from: validate
    to: END
    condition: "validation.ok == true"

loop_limits:
  classify: 3

loop_exits:
  classify: END
```

The LLM outputs YAML text into `kinds_raw`. The Python validator parses it
(`yaml.safe_load`), checks valid kinds, subject present, all glosses covered,
and — only on success — writes the parsed list to `kinds`. On failure it writes
**only** `validation`, leaving `kinds` absent (J1). The LLM retries with the
error in prompt (Jinja2 conditional block). Max 3 attempts.

**Note:** The framework lacks `parse_yaml`. The LLM node outputs raw text
(`parse_json: false`, the default); the validator does `yaml.safe_load()` as its
first step. This is the OQ1 workaround from the v5 plan — functional today, no
framework changes needed.

### 3. The L4 prompt (`prompts/classify_kinds.yaml`)

One task. 16 kinds enumerated with one-line definitions. Concrete YAML output
example. Jinja2 conditional for retry errors. ~300 tokens of instruction + glosses.

See v5 plan §6d for the full prompt sketch.

### 4. Validator (`nodes/tools.py`)

Reads `kinds_raw` (J1). On success writes the parsed list to `kinds`; on failure
writes **only** `validation`, leaving `kinds` absent so a later read never sees a
raw string where a list is expected.

```python
VALID_KINDS = {
    "villainy", "lack", "departure", "donor_test", "provision",
    "struggle", "victory", "liquidation", "return", "pursuit",
    "rescue", "recognition", "exposure", "punishment",
    "reconciliation", "death",
}

def validate_kinds(state: dict) -> dict:
    raw = state.get("kinds_raw", "")       # J1: read the raw-text key
    try:
        items = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return {"validation": {"ok": False, "flaws": [f"YAML parse error: {e}"]}}
    if not isinstance(items, list):        # None (empty) or scalar → invalid
        return {"validation": {"ok": False, "flaws": ["expected a YAML list of items"]}}
    flaws = []
    for item in items:
        if item.get("kind") not in VALID_KINDS:
            flaws.append(f"{item.get('id', '?')}: unknown kind '{item.get('kind')}'")
        if not item.get("subject"):
            flaws.append(f"{item.get('id', '?')}: missing subject")
    expected = {g["id"] for g in state.get("glosses", [])}
    got = {item.get("id") for item in items}
    missing = expected - got
    if missing:
        flaws.append(f"missing: {', '.join(sorted(missing))}")
    if flaws:
        return {"validation": {"ok": False, "flaws": flaws}}  # J1: do NOT write `kinds`
    return {
        "kinds": items,
        "validation": {"ok": True, "flaws": []},
    }
```

### 5. Evaluator (`evaluate.py`)

CLI tool: reads results and ground truth, computes per-function comparison,
writes evaluation YAML.

**Metrics:**

| Metric | Target | What it tells us |
|--------|--------|-----------------|
| Kind accuracy (overall) | ≥ 75% | Can the model classify? |
| Kind accuracy (per genre) | ≥ 60% | Does the vocab fit all genres? |
| Subject accuracy | ≥ 90% | Can the model identify actors? |
| Validation pass rate | ≥ 75% | Can the model produce valid YAML? |

Thresholds are **triggers**, not the verdict (J3). Per-genre n = 7–12, so one
item swings a percentage 8–14 points; the REVISE-vs-KILL call rests on the
confusion analysis, not the bare number. `evaluate.py` reports per-genre results
as **fractions alongside percentages** (`kind_correct: 5/7 (71%)`) so the
coarseness is visible. There is **no per-kind accuracy table** — several kinds
have n=1 (`exposure`; `recognition` nearly so), where a rate is noise (J4).

**Self-derived corpus ceiling (J2):** the synopses were reverse-derived from the
same plots whose `kind` fields are the ground truth, and each gloss was authored
knowing its label. The measured accuracy is therefore an **upper bound** —
"recover the author's label from prose the author wrote knowing it," not
"classify naturalistic prose." `evaluate.py` stamps every evaluation file and the
summary verdict with `corpus: self-derived (upper-bound)`, and any **GO** is
marked *optimistic, pending a blind-corpus re-test*.

**Exhausted-retry handling (J6):** when `loop_limits: classify: 3` exhausts and
`loop_exits` routes to `END`, `kinds` may be absent or unparseable. `evaluate.py`
treats an absent/unparseable `kinds` for a genre as **all-wrong** (0 correct over
that genre's function count) — never crash, never skip. A genre the model could
not produce valid YAML for is a classification failure, not missing data.

**Confusion analysis:** For each misclassification, record expected vs predicted.
Key pairs to watch: `lack`/`pursuit`, `donor_test`/`struggle`,
`recognition`/`exposure`, `reconciliation`/`victory`.

**Output format:**

```yaml
# results/evaluation/detective-thriller-eval.yaml
meta:
  synopsis: detective-thriller
  provider: anthropic            # captured at run time, not pinned in the graph
  model: claude-haiku-4-5        # whatever PROVIDER resolved to
  corpus: self-derived (upper-bound)   # J2
summary:
  total: 8
  kind_correct: 7
  kind_accuracy: "7/8 (0.875)"    # J3: fraction + percentage
  subject_correct: 8
  subject_accuracy: "8/8 (1.0)"
  produced_valid_yaml: true       # J6: false → kind_correct forced to 0
per_function:
  - id: F1
    expected_kind: villainy
    predicted_kind: villainy
    kind_match: true
    expected_subject: Hagen
    predicted_subject: Hagen
    subject_match: true
  # ...
confusions:
  - expected: lack
    predicted: pursuit
    function: F2
```

### 6. Two execution modes

**Mode 1 — Ground-truth glosses (isolates L4):**
Extract glosses from `fixtures/ground-truth/*.yaml`, strip kind labels, feed to
`classify_kinds.yaml`. Tests classification in isolation.

**Mode 2 — Full L3→L4 (future, not in this FR):**
Run `extract_glosses.yaml` on raw synopsis first, then classify model-generated
glosses. Tests the pipeline end-to-end. Deferred to a follow-up FR.

### 7. Test corpus

| Synopsis | Functions | Kinds exercised |
|----------|-----------|----------------|
| Detective thriller | 8 | villainy, lack, pursuit, donor_test, provision, exposure, recognition, punishment |
| Quest adventure | 8 | lack, departure, donor_test, provision, struggle, victory, return, liquidation |
| Horror survival | 7 | villainy, departure, pursuit, death, struggle, rescue, return |
| Sci-fi hybrid | 12 | villainy, lack, departure, donor_test, provision, pursuit, recognition, struggle, reconciliation, death, return, liquidation |

**35 glosses** covering **15 of 16 kinds** (only `exposure` has a single example).
Kinds with n=1 (`exposure`; `recognition` nearly so) are reported in confusions
but excluded from any per-kind rate — a single sample is noise (J4).

## Acceptance criteria

1. `graphs/classify_kinds.yaml` passes `yamlgraph graph lint`
2. `validate_kinds` catches invalid kinds, missing subjects, YAML parse errors,
   and non-list output; reads `kinds_raw` and writes `kinds` only on success (J1)
3. Pipeline runs against all 4 synopses without crashing
4. Evaluation YAML files produced for all 4 synopses, each stamped with the
   self-derived corpus ceiling (J2) and run-time provider/model
5. `test_evaluate.py` has ≥1 golden test (known input → known output) **and** a
   regression test reproducing the J1 crash (raw text in the validated key) —
   RED before the fix, GREEN after
6. `evaluate.py` scores an absent/unparseable `kinds` as all-wrong for that genre,
   never crashing (J6)

## Go/no-go gate (the point of this FR)

After execution, one of three outcomes. Thresholds are **triggers**; the
confusion analysis carries the REVISE-vs-KILL decision (J3), and any GO is
optimistic given the self-derived corpus (J2).

| Outcome | Kind accuracy | Action |
|---------|--------------|--------|
| **GO** (optimistic) | ≥ 75% overall, ≥ 60% per genre | Proceed to full v5 pipeline (FR-571+) **only after** a blind-corpus re-test confirms the number (J2) |
| **REVISE** | 50–75% overall, or confusions concentrate in known pairs | Analyze confusions; revise prompt or merge confused kind pairs; re-run |
| **KILL** | < 50% overall or any genre < 40% | The small-model approach doesn't work; redesign (larger model, two-step classification, or abandon layered pipeline) |

The evaluation YAML files are the evidence. The verdict is documented in the
`results/` folder and referenced by the follow-up FR.

## Deliverables

| File | Purpose |
|------|---------|
| `examples/plot_modeller/README.md` | Example documentation |
| `examples/plot_modeller/graphs/classify_kinds.yaml` | L4 YAMLGraph graph |
| `examples/plot_modeller/prompts/classify_kinds.yaml` | L4 prompt |
| `examples/plot_modeller/nodes/tools.py` | Validator + gloss extraction |
| `examples/plot_modeller/evaluate.py` | CLI evaluator |
| `examples/plot_modeller/tests/test_evaluate.py` | Evaluation tests |
| `examples/plot_modeller/fixtures/` | Synopses + ground-truth, **snapshot-copied** from the pinned sources below (J5) |
| `examples/plot_modeller/fixtures/README.md` | Source paths + commit SHA of the corpus snapshot (J5) |
| `examples/plot_modeller/results/` | Pipeline + evaluation output (gitignored) |

**Pinned fixture sources (J5)** — copy as a frozen snapshot, do not reference:
- synopses → `examples/dungeon_master/docs/v5/*.txt`
- ground-truth → `examples/dungeon_master/docs/v5/genre-plots/*.yaml`

Record the source paths and the commit SHA in `fixtures/README.md` so the spike
corpus stays reproducible and frozen against later DM-docs edits.

## What this FR does NOT do

- Does not build L1–L3 (extraction layers) — deferred to follow-up
- Does not build the merge node or final SAT validator — deferred
- Does not modify `schema.py` or any DM code — standalone example
- Does not modify `examples/dungeon_master/` — the plot_modeller is independent
- Does not add `parse_yaml` to the framework — uses Python-node workaround

---

## Judgement (2026-06-23)

*Verified against `graph_schema.py`, `llm_nodes.py`, `python_tool.py`,
`edge_compiler.py`, and the live corpus at `docs/v5/`. Claims graded ✓ are
checked against source; defects cite the deciding line.*

**Verdict: Authority GRANTED, conditional on J1.** The bet is the right one to
test, the scope is clean (standalone example, no `schema.py` or DM mutation —
strangler-clean ✓), and the acceptance criteria are falsifiable. One fatal
mechanical contradiction (J1) must be fixed before the example will run; J2 and
J5 must be named in the deliverables; J3/J4/J6 are refinements folded into
`evaluate.py` and the results writeup. Scope is frozen at the four corrections
below — no new layers, no framework changes.

### J1 — FATAL: the validator reads a key nothing writes (must fix)

The `classify` node declares `state_key: kinds` with `parse_json` unset
(default `False` — `graph_schema.py:213`). A non-JSON LLM node writes the **raw
response string** to its state key (`llm_nodes.py:367,375` → `cfg.state_key:
result`). So after `classify`, `state["kinds"]` holds raw YAML *text*.

But `validate_kinds` (§4) reads `state.get("kinds_raw", "")` — a key no node
ever writes. `yaml.safe_load("")` returns `None`, then `for item in items`
raises `TypeError: 'NoneType' object is not iterable`. The graph crashes on the
first validation, violating **AC#3** (runs without crashing).

**Prescribed fix (frozen):** separate the raw and parsed keys.
- `classify` node: `state_key: kinds_raw` (raw text lands here).
- `validate_kinds`: read `state["kinds_raw"]`; on success write the parsed list
  to `kinds` plus `validation`; on failure write **only** `validation` (do not
  write `kinds`). This also removes the §4 read-back bug where the failure
  branch returns `state.get("kinds", [])` — which at that point is a raw string,
  not a list. After the fix, `kinds` is always a parsed list or absent.

### J2 — Validity ceiling: the corpus is self-derived (must name)

The synopses (`docs/v5/*.txt`) were reverse-derived from the same plots
(`docs/v5/genre-plots/*.yaml`) whose `kind` fields are the ground truth, and
each `gloss` was authored alongside the label it must now be classified into
(verified: ✓ glosses carry `kind`+`subject`+`gloss`, 8/7/8/12 = 35 functions).
A gloss like "Hagen's men abduct Pell" → `villainy` is near-tautological when
the author wrote the gloss knowing the kind.

Consequence: the measured accuracy is an **upper bound** — "can the model
recover the author's label from prose the author wrote knowing it," not "can the
model classify naturalistic prose." This does not block the spike (a KILL on
self-derived data is doubly damning, and a GO is still necessary-if-not-
sufficient evidence). **Required:** the `results/` writeup must state this
ceiling explicitly, and any **GO** verdict must be marked *optimistic, pending a
blind-corpus re-test* (a synopsis authored without seeing the target kinds).

### J3 — Statistical power vs. threshold precision (refine)

Per-genre n = 7–12. At n=7, the ≥60% cutoff sits between 4/7 (57%, fail) and
5/7 (71%, pass) — one item swings the verdict 14 points. The four-cutpoint
gate (75/60/50/40) asserts more precision than 35 samples support.
**Refine, do not block:** keep the cutoffs as *triggers*, but require the
confusion analysis — not the bare percentage — to carry a REVISE-vs-KILL
decision. `evaluate.py` must report per-genre results as fractions (`5/7`)
alongside percentages so the coarseness is visible.

### J4 — Thin kinds make per-kind rates meaningless (refine)

Several kinds have a single example (`exposure`, and `recognition` is nearly so
per §7's own note). Per-kind accuracy at n=1 is noise. The verdict must rest on
the well-populated kinds and the named confusion pairs (`lack`/`pursuit`,
`donor_test`/`struggle`, `recognition`/`exposure`, `reconciliation`/`victory`),
not on a per-kind table that implies precision it cannot have.

### J5 — Pin the fixture source (must pin)

"Copied from DM docs" is ambiguous; the corpus moved during planning. The
frozen sources are:
- synopses → `examples/dungeon_master/docs/v5/*.txt`
- ground-truth → `examples/dungeon_master/docs/v5/genre-plots/*.yaml`

**Copy** (snapshot) into `fixtures/`, do not reference — the spike corpus must
be frozen against later edits to the DM docs. State the source path and commit
SHA in `fixtures/README.md` for reproducibility.

### J6 — Define the exhausted-retry output (refine)

After `loop_limits: classify: 3` exhausts, `loop_exits: classify: END` routes
out with `kinds` possibly unwritten or invalid. `evaluate.py` must treat an
absent/unparseable `kinds` for a genre as **all-wrong** (0 correct) for that
genre's score — never crash, never skip. A genre the model could not produce
valid YAML for is a classification failure, not missing data.

### Affirmed as sound (no change)

- `loop_limits` / `loop_exits` are correctly **top-level maps keyed by the
  re-entered LLM node** — the v4-review defect is not repeated. ✓
  (`edge_compiler.py:271`, FR-172 pattern; linter E008/E009 will pass.)
- `model: claude-haiku-4-5` is a valid in-repo model string. ✓
- The `parse_yaml` workaround (LLM emits text, Python validator `safe_load`s) is
  legitimate and needs no framework change. ✓
- AC#1 (lint) and AC#5 (golden test) are falsifiable and well-formed. ✓

### Conditions on the grant (all folded into the spec above)

1. **J1** \u2014 folded: §2 graph uses `state_key: kinds_raw`; §4 validator reads
   `kinds_raw`, writes `kinds` only on success; AC#2/AC#5 carry the crash
   regression test.
2. **J2** \u2014 folded: §5 stamps every evaluation file `corpus: self-derived
   (upper-bound)`; the gate marks GO *optimistic, pending blind-corpus re-test*.
3. **J5** \u2014 folded: deliverables pin the `docs/v5/` sources and require
   `fixtures/README.md` with source paths + commit SHA.
4. **J3/J4/J6** \u2014 folded: §5 reports fractions + percentages, drops the per-kind
   table, and scores absent/unparseable `kinds` as all-wrong; §7 excludes n=1
   kinds from rates; AC#6 codifies the no-crash rule.
5. Scope frozen: still no L1–L3, no merge node, no `schema.py`, no `parse_yaml`,
   and **no hardcoded provider/model** in the graph (resolved from `PROVIDER`).

With these folded, the spike produces exactly what three plan iterations have
lacked — a measured, falsifiable number — and the corpus's self-derived nature
is declared rather than hidden. Proceed to Enforce: RED first (validator test
that reproduces the J1 crash, then the fix), then the run.

---

## Implementation status (2026-06-23, Enforced)

**Verdict: GO (optimistic)** — overall kind accuracy **28/35 (0.80)**, every
genre ≥ 0.60. Proceed to the full v5 pipeline (FR-571+) only after the two
conditions below are met.

### Built

| Deliverable | Path | Note |
|-------------|------|------|
| L4 graph | `examples/plot_modeller/graphs/classify_kinds.yaml` | lint clean (AC#1); no hardcoded provider/model |
| L4 prompt | `examples/plot_modeller/prompts/classify_kinds.yaml` | 16-kind glossary + Jinja2 retry block |
| Validator + loaders | `examples/plot_modeller/nodes/tools.py` | J1 contract: reads `kinds_raw`, writes `kinds` only on success |
| Evaluator | `examples/plot_modeller/evaluate.py` | J2 ceiling stamp, J3 fractions, J6 all-wrong scoring |
| Runner | `examples/plot_modeller/run.py` | Mode-1 (isolate L4) across 4 synopses |
| Tests | `examples/plot_modeller/tests/test_evaluate.py` | 13 tests; J1 crash regression (RED→GREEN) + J6 scoring |
| Fixtures | `examples/plot_modeller/fixtures/` | snapshot-copied from `docs/v5/` at SHA `d93f446` (J5) |

### Results (anthropic / claude-haiku-4-5, Mode 1, 35 functions)

| Genre | Kind accuracy |
|-------|---------------|
| Detective thriller | 7/8 (0.88) |
| Quest adventure | 8/8 (1.00) |
| Horror survival | 5/7 (0.71) |
| Sci-fi hybrid | 8/12 (0.67) |
| **Overall** | **28/35 (0.80)** |

Subject accuracy 24/35 (0.69) — below the 0.90 aspiration; flagged for the
role-assignment layer, not blocking the L4 verdict.

### Confusion analysis (J3 — carries the verdict)

The 7 errors are **not** in the warned vocabulary pairs. They cluster around
**cause-vs-outcome**: `death → villainy`, `death → victory`, `liquidation →
villainy`, `rescue → provision`. A coherent, addressable failure mode, not a
sign the vocabulary is the wrong shape.

### Conditions on the GO

1. **Blind-corpus re-test** (J2): this is an upper bound on self-derived data.
2. **Add cause-vs-outcome disambiguation** to the L4 prompt before the re-test.

### Deviations from the frozen spec

- **Tool registration uses `module:` (dotted import), not `path:`.** The
  `path:`-relative resolver anchors at the graph's own directory and rejects
  paths that escape it (`python_tool.py:_resolve_python_tool_path`), so
  `nodes/tools.py` (a sibling of `graphs/`) was unreachable by path. The
  established example convention (`examples.diary_digest.nodes.*`) is `module:`,
  which routes through Python's import system. Added `examples/plot_modeller/__init__.py`.
- **`validate` node is left out of `loop_limits`/`loop_exits`.** Adding it (to
  silence lint W012) wrapped the conditional router's `END` target and broke
  LangGraph compilation (`unknown target 'END'`). The loop is correctly bounded
  on the re-entered `classify` node; W012 on `validate` is an accepted advisory
  warning (lint still reports 0 errors, AC#1 satisfied).
