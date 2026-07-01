# 2026-07-01 FR-628: Wiki Memory Gate — Boundary Normalization at Every Seam

## Context
Built a demo combining `data_files` glob (FR-629), `write_data_file` (FR-625),
and a Python gate node with conditional loop edges.

## Traps Encountered

### 1. Variable Interpolation Assumption
**Trap:** Assumed `{state.drafted_page.id}` would interpolate inside a string
like `wiki/{state.drafted_page.id}.yaml`. The variable resolver only handles
full `{state.X}` replacement, not string interpolation.

**Cure:** Moved path computation into the gate node (which already reads the
drafted page). Gate computes `save_path` as a string and persist reads it from
state. Callsite fix — don't extend the framework, use what exists.

### 2. Pydantic Serialization at Jinja2 Boundary
**Trap:** The `fix_refs.yaml` prompt used `{{ state.drafted_page | tojson }}`
but `drafted_page` was a Pydantic `WikiPage` model — not JSON serializable.

**Cure:** Gate node normalizes `drafted_page` to dict via `model_dump()` and
re-writes it to state. Normalize at the boundary (gate), not downstream (prompt).

### 3. LLM Instruction Following vs Demo Needs
**Trap:** When the draft prompt showed the wiki page list AND instructed
"only reference existing pages", Gemini 3.5 Flash obeyed perfectly. No gate
trigger — no demo of the correction loop.

**Cure:** Removed wiki visibility from draft prompt. The gate IS the enforcement
layer; the prompt shouldn't duplicate it. This produced cleaner architecture:
draft is creative, gate is mechanical.

### 4. loop_exits Target Must Be a Node
**Trap:** Used `loop_exits: gate: END` but `END` isn't a node the conditional
router knows about. Error: "unknown target 'END'".

**Cure:** Changed to `loop_exits: gate: persist` — route to the nearest real
node that leads to END.

## Heuristic
**Enforcement layer vs prompt constraint:** When a deterministic gate validates
a property, remove that same constraint from the LLM prompt. Redundant
constraints make the gate untestable and hide its value. Let the LLM be
creative; let the gate be strict.

## Framework Defects Surfaced

Three issues are framework bugs, not demo-local workarounds:

### 1. `loop_exits: node: END` crashes at runtime (BUG)
The linter (`checks_semantic.py:86`) explicitly accepts `"END"` as a valid
target. But `edge_compiler.py` adds it to `targets` as the string `"END"`,
then the route_mapping loop checks `t == END` (the `"__end__"` constant).
String `"END"` ≠ sentinel `END`, so it becomes an unmapped route and the
router crashes: "unknown target 'END'". Fix: normalize `"END"` → `END`
constant in `edge_compiler.py:275` before adding to targets.

### 2. Variable string interpolation unsupported
`resolve_template()` requires the ENTIRE string to be `{state.X}`. A mixed
string like `wiki/{state.drafted_page.id}.yaml` returns unchanged because
line 192 checks `startswith("{") and endswith("}")`. This forces graph
authors to compute paths in Python nodes. Fix: support f-string style
interpolation when a template contains `{state.` but also has surrounding
text.

### 3. Pydantic models not serializable in Jinja2 `tojson`
LLM structured outputs stay as BaseModel in state. When a Jinja2 prompt
uses `{{ state.field | tojson }}`, it crashes because `json.dumps()` can't
serialize Pydantic models. The framework should either:
(a) `model_dump()` at LLM output boundary (in `llm_nodes.py` before storing), or
(b) Register a custom Jinja2 `tojson` filter that handles BaseModel.

**Priority:** #1 is a clear bug (linter/runtime disagree). #2 and #3 are
feature gaps that push complexity into user Python code.

## Seed
Could the gate pattern generalize into a reusable `verification_gate` node type
in YAML (analogous to `verification-gate` demo) that auto-loops with a fixer
prompt? The YAML author would declare `gate_fn`, `fix_prompt`, and `max_retries`.
