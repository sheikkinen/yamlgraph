# Feature Request: FR-1059 Attribute-tailed fields never render in simple-format prompts

**Priority:** MEDIUM
**Type:** Bug
**Status:** Judged — Authority GRANTED WITH REVISIONS (2026-09-23), not yet
activated: C-1 gates enforcement on FR-1057 being committed in the parent tree.
Judgement: [FR-1059-attribute-fields-in-simple-format.judgement.md](FR-1059-attribute-fields-in-simple-format.judgement.md)
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
- **Mapping-key precedence (judgement R-2).** While traversing a `Mapping`, a
  dotted component is **always** a key lookup — even when the name collides
  with a mapping method (`items`, `keys`, `values`, `get`, `copy`). `getattr`
  is used only when the current value is not a `Mapping`. The earlier draft
  claimed "every template that renders today renders identically"; that claim
  was **false and is withdrawn**. `{a.items}` with `a` a dict renders the bound
  method's repr today; after this change it resolves the key `"items"` or
  raises `KeyError`. This is the intended semantics — a prompt rendering
  `<built-in method items of dict...>` is a defect, not a contract — but it is
  a behaviour change and is covered by AC-03.
- **Terminal list presentation (judgement R-3).** `format_prompt`'s simple
  branch deliberately comma-joins top-level lists before formatting
  (`yamlgraph/executor_base.py:127-132`, verified: `", ".join(map(str, v)) if
  isinstance(v, list) else v`). A list reached *through* a path bypasses that
  normalisation — the probe above emitted `['a']`, not `a`. Two of the three
  live sites (`key_terms`, `file_patterns`) are lists, so this is not
  hypothetical. A path-terminal list must receive the same comma-joined
  presentation. Covered by AC-07.

No new lint code. E002's root check already covers the root identifier after
FR-1057 (`scan_simple_fields().bare_roots` sees `parsed_request` in
`{parsed_request.change_type}`; the pre-FR-1057 regex did not).

## Acceptance Criteria

Superseded by the judgement's revised set (R-1..R-5 folded). The capability and
requirement IDs are **not** fixed here: per R-4 they are allocated after the
rebase onto the committed FR-1057 parent, by scanning `capabilities/` — not
`.chaplain/id-registry.yaml`, which is stale (`cap-req-id-allocation-race`).
`CAP-275` / `REQ-YG-686` appear nowhere below; the FR is updated with the final
pair before RED begins.

- [ ] **AC-01** On the committed rebased parent, a separately committed RED test proves `format_prompt("{a.b}", {"a": {"b": "v"}})` raises `AttributeError`; the GREEN implementation returns `"v"`.
- [ ] **AC-02** Dotted traversal uses mapping keys for every `Mapping` and `getattr` only for non-mapping objects.
- [ ] **AC-03** A mapping key named `items` resolves that key; an absent `items` key raises `KeyError` rather than exposing `dict.items`.
- [ ] **AC-04** Plain-object attribute traversal remains functional.
- [ ] **AC-05** `{a.b.c}` traverses two mappings, and `{a.b[0].c}` traverses mixed mapping/index components.
- [ ] **AC-06** A missing mapping tail raises `KeyError`; no silent value, no `on_error` change.
- [ ] **AC-07** Terminal lists reached through paths retain comma-joined simple-format presentation; tests assert non-empty and empty lists exactly.
- [ ] **AC-08** On the rebased FR-1057 parent, `extract_variables("{a.b}") == {"a"}`.
- [ ] **AC-09** The live witness asserts all three rendered lines of `prepare_messages("examples/codegen/plan_discovery", ...)` — scalar `change_type`, comma-joined `key_terms`, comma-joined `file_patterns` — not merely that the output contains `feat`. Transcript recorded in the Implementation Record.
- [ ] **AC-10** The corpus lint command below is executed before and after; the post-change run has zero crashes and no findings absent from the recorded baseline, with both log paths cited.
- [ ] **AC-11** The census command below is executed and reports the same three surviving sites in `plan_discovery.yaml`. Rendering correctness is proven by AC-09, never inferred from this count.
- [ ] **AC-12** Full unit suite, `ruff check yamlgraph/`, and `python scripts/req_coverage.py --strict` all exit zero.
- [ ] **AC-13** A final free capability/requirement pair is allocated after rebase; the capability file is added and `ARCHITECTURE.md` is **regenerated** via `python scripts/aggregate_capabilities.py` (never hand-edited).
- [ ] **AC-14** `reference/prompt-yaml.md` documents mapping-key precedence, object fallback, missing-key failure, and path-terminal list presentation for the simple dialect, preserving FR-1057's per-message dialect contract.
- [ ] **AC-15** `changelog/unreleased/fr-1059-attribute-fields-in-simple-format.md` records a `fix` in `prompts` using the final requirement ID.
- [ ] **AC-16** The Implementation Record identifies the parent SHA, RED SHA, GREEN SHA, final IDs, commands, logs, results, and any deviation.
- [ ] **AC-17** A Distill entry in `docs/diary/` names the trap, extracts a heuristic, and includes a **Seed:**.

### Exact corpus commands (R-5)

Graph-shaped file selection and lint baseline — `tmp/fr1059-lint-before.log` on
the rebased parent, `tmp/fr1059-lint-after.log` after the change, compared with
`diff`:

```bash
for f in $(git ls-files '*.yaml' '*.yml'); do
  python - "$f" <<'PY' || continue
import sys, yaml, pathlib
d = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
sys.exit(0 if isinstance(d, dict) and "nodes" in d else 1)
PY
  echo "== $f"; yamlgraph graph lint "$f" 2>&1 || true
done > tmp/fr1059-lint-{before,after}.log
```

Attribute-tail census — the exact classifier from §Problem, using FR-1057's
`is_jinja` and `string.Formatter().parse`, filtered on `spec == "" and conv is
None`, over `system` / `user` / `template` / list-item `content` /
`system_segments[i].content`; written to `tmp/fr1059-census-after.log` and
asserted to contain exactly the three `plan_discovery.yaml` sites.

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

## Judgement (2026-09-23)

**Verdict:** APPROVED WITH REVISIONS. Full artifact:
[FR-1059-attribute-fields-in-simple-format.judgement.md](FR-1059-attribute-fields-in-simple-format.judgement.md)
(backend `copilot` / `gpt-5.6-sol`, run in this worktree at `d6faf6b5`).

| # | Finding | Resolution (binding) — folded |
|---|---------|-------------------------------|
| R-1 | FR-1057 is not in the committed parent tree; the judge could not consume it as evidence. Every `scan_simple_fields` / `bare_roots` / E013 / E014 / `reference/prompt-yaml.md §Template Dialect` reference is a forward claim. | **Accepted, gating.** Status downgraded to "authority not yet activated". Enforcement starts only after FR-1057 is merged; the FR is then rebased onto that SHA and the failure probe, census, and lint baseline are re-run on that tree. |
| R-2 | The claim "every template that renders today renders identically" is false: `{a.items}` on a dict currently resolves `dict.items`. | **Accepted.** Claim deleted and replaced by an explicit mapping-key-precedence rule in §Proposed Solution; AC-03 tests present and absent colliding keys. |
| R-3 | `format_prompt` comma-joins **top-level** lists (`executor_base.py:127-132`); a list reached through a path bypasses that and renders `['a']`. Two of the three live fields are lists. | **Accepted — the strongest finding.** Verified independently at `executor_base.py:127-132`. Path-terminal lists must inherit the comma-joined presentation; AC-07 asserts non-empty and empty lists exactly. AC-09 now asserts all three rendered lines, not "contains `feat`". |
| R-4 | AC-12 prescribed `CAP-275`/`REQ-YG-686` while the preamble called them provisional. | **Accepted.** Both IDs removed from the FR body; allocated after rebase by scanning `capabilities/`. |
| R-5 | AC-9/AC-10 named outcomes but no reproducible commands, and "each renders" is not established by a field-name census. | **Accepted.** Exact graph-shaped-selection + lint commands and census classifier added under §Exact corpus commands; rendering correctness moved entirely to the AC-09 witness. |

**Scope frozen:** D-1..D-7 of the judgement. Not authorised: graph-layer
expression resolution, Pydantic/state normalisation, checkpointers, Jinja
semantics, any linter code, rewriting the three `plan_discovery` placeholders,
retiring the simple dialect, or any CI/hook/judge/review infrastructure.

**Conditions:** C-1..C-6 of the judgement, all GATE. C-1 (FR-1057 committed in
the parent) is the blocking one and is **not yet satisfied**.

### Questions for the human

The judgement records none. One is raised by R-1 and needs a decision before
enforce:

- **Should FR-1059 wait for FR-1057 to merge, or rebase onto the FR-1057
  branch and stack the PRs?** Evidence: FR-1057 is committed at `4ef3b7ac` but
  unpushed and unreviewed; FR-1059's AC-08 depends on its `bare_roots`
  contract. **Recommended default: wait.** Stacking makes FR-1057's review
  diff and FR-1059's blast radius harder to read, for a 0.5-day change with no
  deadline.
