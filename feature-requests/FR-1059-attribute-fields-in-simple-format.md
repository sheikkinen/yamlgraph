# Feature Request: FR-1059 Attribute-tailed fields never render in simple-format prompts

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-23
**First consumer / first event:** `examples/codegen/impl-agent.yaml`, at its
`plan_discovery` node — the second LLM node of the codegen agent. Every run of
that graph raises `AttributeError` there today. The first event is the next
`yamlgraph graph run examples/codegen/impl-agent.yaml`.
**Research:** in-body dispositioned alternatives table (FR-889 style), see
§Alternatives Considered — every row carries a number or a transcript produced
by an executed probe on this worktree (`432ce1b4`, v0.5.26).
**Prior art:**
- [FR-1057-prompt-template-dialect-split.md](FR-1057-prompt-template-dialect-split.md)
  — direct parent, currently Enforced-unpushed. It split the dialect decision
  per message and added E013 (unrenderable simple message) / E014 (simple field
  in a Jinja message). Both fire on *syntax*. `{a.b}` is **valid** simple-format
  syntax, so FR-1057's checks are correctly silent on it; FR-1057 §"Out of
  scope, found and deliberately left (C-6)" names this defect as a follow-up.
  This FR is that follow-up. No overlap in code or in lint code space.
- [FR-631-variable-string-interpolation.md](FR-631-variable-string-interpolation.md)
  — Implemented. Taught the **graph** layer (`resolve_template` /
  `resolve_node_variables`) to walk dotted paths like `{state.drafted_page.id}`
  through dicts. It is the reason the asymmetry below exists: the graph layer
  got dict-aware dot paths, the prompt layer never did. This FR does not touch
  `resolve_node_variables`; it makes the prompt renderer agree with it.
- [FR-252-python-node-variables.md](FR-252-python-node-variables.md) — added the
  `{state.X}` expression form consumed by `variables:`. Same layer as FR-631,
  same disposition: producer of the asymmetry, not the subject of this FR.
- [FR-110-lint-state-variable-expressions.md](FR-110-lint-state-variable-expressions.md)
  — Enforced. Promoted W014→E007, validating that a `{state.X}` expression names
  a declared state key. It validates the **root** at the graph layer; it says
  nothing about what happens to a `.tail` inside a prompt message.
- [FR-319-lint-unanchored-prompt-variables.md](FR-319-lint-unanchored-prompt-variables.md)
  — Implemented. Warns when a node declares a variable the prompt never uses.
  The inverse direction, and it is satisfied here: `parsed_request` *is*
  declared and *is* referenced. The bug is invisible to it.
- [FR-645-lint-map-subnode-prompt-variables.md](FR-645-lint-map-subnode-prompt-variables.md)
  — Proposed, not implemented. Extends E002 to map/pipeline sub-node *scope*.
  Orthogonal: a scoping question, not a field-grammar question. Not blocked by
  or blocking this FR.
- [FR-430-linter-mixed-template-syntax.md](FR-430-linter-mixed-template-syntax.md)
  — its W024 was **retired** by FR-1057. Cited so the retirement is not
  re-proposed: this FR adds no lint code and does not resurrect W024.
- [FR-214-fix-extract-variables-nested-set.md](FR-214-fix-extract-variables-nested-set.md)
  — fixed `extract_variables` returning a nested set. Same function family,
  different defect (return shape vs. field grammar); superseded in the dotted
  case by FR-1057's `scan_simple_fields`.

## Summary

In a prompt message that uses the **simple** (`str.format`) dialect, a field
with an attribute tail — `{parsed_request.change_type}` — is resolved by
`str.format` with `getattr`. Every value that reaches a prompt from an upstream
`llm` node is a **dict** (`model_dump()`), so the render always raises
`AttributeError`. The template is syntactically valid, so no lint check sees it;
the graph simply dies at runtime.

The same dotted syntax **works** one layer up, in `variables:`, where FR-631
made it dict-aware. One YAML file, two layers, two incompatible meanings for
`.`.

## Value Statement

Graph authors who write `{parsed_request.change_type}` in a prompt get the value
they asked for — the same thing `{state.parsed_request.change_type}` gives them
three lines above in the same file — instead of an `AttributeError` at the first
live run.

## Problem

### The failure, verbatim

Probe run on this worktree (`432ce1b4`):

```python
from yamlgraph.executor_base import prepare_messages
prepare_messages(
    "examples/codegen/plan_discovery",
    {"story": "s", "scope": "x",
     "parsed_request": {"change_type": "feat", "file_patterns": [], "key_terms": []}},
    prompts_dir=Path("."),
)
```

```
AttributeError: 'dict' object has no attribute 'change_type'
```

### The asymmetry, verbatim

Same worktree, one script:

```
graph layer   resolve_node_variables({"ct": "{state.parsed_request.change_type}"}, state)
              -> {'ct': 'feat'}                       # FR-631, dict-aware

prompt layer  format_prompt("{pr.change_type}", {"pr": {"change_type": "feat"}})
              -> AttributeError 'dict' object has no attribute 'change_type'

prompt layer  format_prompt("{pr[change_type]}", ...)   -> 'feat'
prompt layer  format_prompt("{{ pr.change_type }}", ...) -> 'feat'
```

The `.` is dict-aware in `variables:` and object-only in the message body. Two
of the four rows work; an author has no way to know which two without running it.

### The producer

`examples/codegen/impl-agent.yaml` (lines 174-190) — an `llm` node feeding a
second `llm` node:

```yaml
nodes:
  parse_story:
    type: llm
    prompt: examples/codegen/parse_story
    variables:
      story: "{state.story}"
    state_key: parsed_request        # llm_nodes.py:292 -> result.model_dump()

  plan_discovery:
    type: llm
    prompt: examples/codegen/plan_discovery
    variables:
      story: "{state.story}"
      scope: "{state.scope}"
      parsed_request: "{state.parsed_request}"   # a dict, always
    state_key: discovery_plan
    requires: [parsed_request]
```

`examples/codegen/prompts/plan_discovery.yaml`, `user` message, 3 sites:

```
Change type: {parsed_request.change_type}
Key terms: {parsed_request.key_terms}
File patterns: {parsed_request.file_patterns}
```

`yamlgraph/node_factory/llm_nodes.py:292` returns `result.model_dump()`. The
dict is the *deliberate* state shape — the checkpointers serialise it. So the
dict is not the defect; the renderer's disagreement with it is.

### Census

Classifier: `is_jinja(text)` to select simple-dialect messages, then
`string.Formatter().parse(text)` keeping fields with `spec == "" and conv is
None` (FR-1057's `bare_roots` rule — a field with a format spec may be prose,
as `{pred: alive, ...}` in `examples/plot_modeller/prompts/extract_goals.yaml`
proved), then `"." in field_name or "[" in field_name`. Messages read:
`system`, `user`, `template`, list items' `content`, `system_segments[i].content`.

Run on this worktree over `git ls-files '*.yaml' '*.yml'`:

```
prompt files scanned: 363
  examples/codegen/prompts/plan_discovery.yaml           user  parsed_request.change_type
  examples/codegen/prompts/plan_discovery.yaml           user  parsed_request.file_patterns
  examples/codegen/prompts/plan_discovery.yaml           user  parsed_request.key_terms
  examples/demos/novel_generator/.../prose/generate_beat.yaml  user  synopsis.protagonist
  examples/demos/novel_generator/.../prose/generate_beat.yaml  user  synopsis.title
  examples/demos/novel_generator/.../timeline/construct.yaml   user  synopsis.antagonist
  examples/demos/novel_generator/.../timeline/construct.yaml   user  synopsis.protagonist
  examples/demos/novel_generator/.../timeline/construct.yaml   user  synopsis.synopsis
  examples/demos/novel_generator/.../timeline/construct.yaml   user  synopsis.title
sites: 9 files: 3
```

Zero index-tailed (`{a[0]}`) sites. **After FR-1057 merges** the
`novel_generator` demo is retired, leaving **3 sites in 1 file**. Both numbers
are stated because FR-1057 is not yet pushed; the count this FR must clear is 3.

The census grammar is stated explicitly because FR-1057's own census used the
regex `\{(\w+)\}` — the very grammar its defect D2 was about — and undercounted
6 findings as 1. `census-grammar-must-be-the-new-parser`.

## Ideal Result

A `.` inside `{...}` means the same thing everywhere in a YAMLGraph prompt file:
*walk into this value*. `{state.a.b}` in `variables:` and `{a.b}` in the message
body resolve identically, through dicts and through objects alike, so an author
who has learned one layer has learned both. Nothing new to configure, no new
lint code to learn, no rewrite of the 3 live sites — the templates that were
always obviously *intended* to work simply do.

## Proposed Solution

Make the simple-dialect renderer walk an attribute tail through a mapping before
falling back to `getattr` — one `string.Formatter` subclass in
`yamlgraph/utils/template.py`, consumed by `format_prompt`.

```python
class _PathFormatter(string.Formatter):
    """Attribute tails traverse mappings before objects (FR-1059).

    Matches resolve_node_variables (FR-631): a `.` means "walk into this
    value", whether the value is a dict or an object.
    """

    def get_field(self, field_name, args, kwargs):
        first, rest = _string.formatter_field_name_split(field_name)
        obj = self.get_value(first, args, kwargs)
        for is_attr, key in rest:
            if is_attr and isinstance(obj, Mapping):
                obj = obj[key]
            elif is_attr:
                obj = getattr(obj, key)
            else:
                obj = obj[key]
        return obj, first
```

Probe of exactly this logic, on this worktree:

```
"{pr.change_type} / {pr.key_terms} / {plain}" -> "feat / ['a'] / x"   # dict tail
"{o.b}" with a plain object                   -> "objval"             # object tail intact
"{pr.missing}" with pr={"a": 1}               -> KeyError 'missing'
```

Notes that belong in the change, not left implicit:

- `_string.formatter_field_name_split` is CPython's own C helper backing
  `str.format`. The first probe attempt used `str._formatter_field_name_split`
  and failed on 3.12 (`AttributeError: 'str' object has no attribute
  '_formatter_field_name_split'`) — recorded so the implementer does not repeat
  it. If the private-module dependency is judged unacceptable, the tail can be
  parsed with the field grammar FR-1057 already owns in `template.py`; that is
  a mechanical substitution, not a different design.
- A missing key raises `KeyError`, matching the existing behaviour for a missing
  root variable. Nothing becomes silent. Commandment 6.
- The changed behaviour is strictly a subset of today's: every template that
  renders today renders identically; only templates that raise `AttributeError`
  today change outcome.

No new lint code. E002's root check already covers the root identifier after
FR-1057 (`scan_simple_fields().bare_roots` sees `parsed_request` in
`{parsed_request.change_type}`; the pre-FR-1057 regex did not).

## Acceptance Criteria

All tests tagged `@pytest.mark.req("REQ-YG-686")` (id provisional — reallocate
at enforce time by scanning `capabilities/`, not `.chaplain/id-registry.yaml`;
`cap-req-id-allocation-race`).

- [ ] **AC-1 (RED first)** A test asserts `format_prompt("{a.b}", {"a": {"b": "v"}}) == "v"` and fails with `AttributeError` on the parent commit. Committed as a separate RED commit before the fix.
- [ ] **AC-2** `format_prompt` resolves an attribute tail through a `Mapping`.
- [ ] **AC-3** `format_prompt` still resolves an attribute tail through a plain object (`getattr` route unbroken).
- [ ] **AC-4** A nested tail (`{a.b.c}`) resolves through two mappings.
- [ ] **AC-5** A mixed tail (`{a.b[0].c}`) resolves; index tails unchanged.
- [ ] **AC-6** A missing tail key raises `KeyError`, not a silent empty string. No `on_error` change.
- [ ] **AC-7** `extract_variables` still reports the **root** only (`{"a"}` for `{a.b}`) — no regression of FR-1057's `bare_roots` contract.
- [ ] **AC-8 (live witness, not a fixture)** `prepare_messages("examples/codegen/plan_discovery", {...}, prompts_dir=...)` returns rendered messages containing `feat`. The exact call that produced the `AttributeError` above, with the same inputs, now green. Transcript pasted into the Implementation Record.
- [ ] **AC-9 (corpus)** `yamlgraph graph lint` over every tracked graph-shaped YAML: **0 crashes, 0 new findings** vs. the pre-change baseline, captured to a log and cited by path.
- [ ] **AC-10 (census closed)** The §Problem census re-run after the change reports the same 3 sites, and each renders. The residual count is stated, not assumed zero.
- [ ] **AC-11** Full unit suite green; `ruff check yamlgraph/` clean; `python scripts/req_coverage.py --strict` exits 0.
- [ ] **AC-12** `capabilities/CAP-275-prompt-attribute-path-resolution.yaml` added with `REQ-YG-686`; `ARCHITECTURE.md` **regenerated** via `python scripts/aggregate_capabilities.py` (never hand-edited).
- [ ] **AC-13** `reference/prompt-yaml.md` §"Template Dialect (per message)" (added by FR-1057) gains one paragraph: `.` walks dicts and objects alike in both dialects and at both layers.
- [ ] **AC-14** Changelog fragment `changelog/unreleased/fr-1059-attribute-fields-in-simple-format.md`, `type: fix`, `scope: prompts`, `req: REQ-YG-686`.
- [ ] **AC-15** Diary Distill entry in `docs/diary/` naming the trap and planting a **Seed:**.

## Alternatives Considered

Each row carries a number or transcript from an executed probe on this worktree.
No row is a paragraph written from priors (`alternatives-as-probes`).

| # | Alternative | Probe executed | Disposition |
|---|---|---|---|
| A1 | **Do nothing — call `{a.b}` a house-style error.** | The rule is written nowhere: `grep -n "getattr\|attribute" reference/prompt-yaml.md` at the time of writing returns no such guidance, and `examples/codegen` shipped 3 sites of it. | **Rejected.** An unwritten rule that an author cannot discover, cannot lint, and only learns by crashing is not a rule. |
| A2 | **Rewrite the 3 sites to `{a[b]}`.** | `format_prompt("{pr[change_type]}", ...)` → `'feat'`. Works today, zero framework change. | **Rejected as the whole fix, kept as the fallback.** It repairs the instances and leaves the trap armed for site 4 — `partial_remediation`. Retained as the contingency if A5 is judged too invasive. |
| A3 | **Rewrite the 3 sites to Jinja (`{{ a.b }}`).** | `format_prompt("{{ pr.change_type }}", ...)` → `'feat'`. | **Rejected.** Same `partial_remediation`, plus it flips a whole message to Jinja to fix one field — the exact "dialect chosen by accident" that FR-1057 was filed against. |
| A4 | **New lint code (E015) rejecting attribute tails in simple messages.** | Free codes on this base: E009, E015+ (E013/E014 reserved by FR-1057; `grep -rhoE 'code="[EW][0-9]{3}"' yamlgraph/linter/`). But: deciding whether a root is a dict needs graph-level knowledge — the prompt checks are handed a prompt file, not a graph. Proving "dict" requires resolving `variables:` → `state_key` → producing node type, which no prompt check does today. | **Rejected.** Would ship a check that either over-fires (bans a legitimate object tail) or needs a new graph↔prompt join to be correct. It also enforces the wrong answer: it makes the author's obvious intent illegal rather than working. |
| A5 | **Dict-aware attribute traversal in `format_prompt`.** | Probed above: `"feat / ['a'] / x"`, `'objval'`, `KeyError 'missing'`. ~12 lines. | **Selected.** Minimal path back from the Ideal Result; makes the prompt layer agree with `resolve_node_variables`, an in-repo pattern (Commandment 4), rather than inventing one. |
| A6 | **Keep the Pydantic object in state instead of `model_dump()`ing it.** | `llm_nodes.py:292` returns `result.model_dump()`; state is serialised by the SQLite/Redis checkpointers, which cannot carry arbitrary models. | **Rejected.** The dict is the checkpoint boundary's required shape. Changing it to serve prompt rendering inverts the dependency and blasts every node type. |
| A7 | **Render every message through Jinja; delete the simple dialect.** | FR-1057 considered and **deferred** this; its census showed simple-dialect messages across the corpus. | **Rejected here, not re-litigated.** If A7 ever lands, A5's ~12 lines are deleted with the dialect. A5 does not make A7 harder. |

## Is this a graph?

No. `yamlgraph graph list` offers no graph for "patch a resolver function and
add unit tests" — this is a single-function code change with a unit test, not a
per-item LLM pass, multi-stage pipeline, or fan-out. The one corpus-wide step
(AC-9 lint, AC-10 census) is a deterministic scan, not an LLM map. The
`is_this_a_graph` question is answered and closed.

## Related

- `yamlgraph/utils/template.py` — dialect + field grammar (FR-1057)
- `yamlgraph/executor_base.py` — `format_prompt`, `prepare_messages`
- `yamlgraph/utils/expressions.py:241` — `resolve_node_variables` (FR-631)
- `yamlgraph/node_factory/llm_nodes.py:292` — `result.model_dump()`, the dict boundary
- `examples/codegen/impl-agent.yaml`, `examples/codegen/prompts/plan_discovery.yaml` — the live instance
- No LangSmith trace: the failure is pre-invocation, in message preparation. No LLM call is made.
