# Feature Request: Prompt template dialect is decided at three different granularities

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1-2 days
**Requested:** 2026-09-23
**First consumer / first event:** the next graph author who writes a JSON
shape into a prompt — concretely the `examples/dungeon_master` and
`yamlgraph-visual-novel` authors, who have each already been burned. First
event: `yamlgraph graph lint <graph.yaml>` on a prompt containing a literal
`{` , which today passes and then crashes at run time.
**Research:** in-body "Alternatives Considered" table below — an executed
census, not a prose lineup. Every row carries a number produced by a probe
run against this checkout at `432ce1b4`. `scripts/research.sh` was not run:
the question here is not "what do other systems do" but "what does our own
corpus actually contain", and that is answered by counting it.
<!-- R-4: the first census walked the FILESYSTEM via rglob and therefore
     counted gitignored trees (`projects/` is ignored at .gitignore:114).
     The judge caught it. All numbers below are now from `git ls-files
     '*.yaml'` — committed artifacts only. The original figures were
     164 messages / 158 files / 2 live instances; the honest figures are
     163 / 156 / 1. -->
**Prior art:**
- [FR-430-linter-mixed-template-syntax.md](FR-430-linter-mixed-template-syntax.md)
  — added W024 for mixed syntax. This FR shows W024 scans the whole prompt
  **file** and so both misses the harmful case and fires on harmless ones;
  it is corrected here, not duplicated.
- [FR-499-structured-world-state-ledger.md](FR-499-structured-world-state-ledger.md)
  — hit defect D2 live (`KeyError('"world_state"')`) and cured it by
  rewriting the prompt in prose. A workaround at the call site, not a fix.
- [FR-361-fix-executor-double-brace-output.md](FR-361-fix-executor-double-brace-output.md)
  — stripped doubled braces from LLM *output*; its own text labels this a
  `downstream_fix`. Different direction (output, not input), same family.
- [FR-783-api-discovery-leaf-tool-manifests.md](FR-783-api-discovery-leaf-tool-manifests.md)
  — same brace collision in `tools/shell.py`. Explicitly **out of scope**
  here: `shell.py` is pure `str.format` with no dialect sniffing, so its
  `{{` escape works. Named so a reader does not assume it is covered.
- [FR-795-endpoint-probe-schema-dialect-repair.md](FR-795-endpoint-probe-schema-dialect-repair.md)
  and [FR-1054-nested-object-schemas-reach-the-provider.md](FR-1054-nested-object-schemas-reach-the-provider.md)
  — both are `schema:`-vs-JSON-Schema **output** dialect defects in prompt
  YAML. Same family, different boundary: this FR is the **input template**
  dialect. No shared code path.
- Authoring briefs FR-789 / FR-790 / FR-791 each carry a line telling
  authors not to put literal JSON braces in prompts. Three copies of one
  instruction is the tell that the constraint belongs in a gate.

## Summary

Three layers of yamlgraph decide whether a prompt is a Jinja2 template or a
`str.format` template. All three use the same rule — "does it contain `{{`
or `{%`" — but each applies it to a **different string**. Rendering decides
per message; validation decides on system+user concatenated; the W024 lint
decides on the whole YAML file. Where the granularities disagree, prompts
pass validation and lint and then crash, or worse, silently ship
unsubstituted placeholders to the model.

## Value Statement

Graph authors can write a literal JSON shape in a prompt and find out at
lint time whether it will survive, instead of at minute nine of a live run
— or never, in the silent case.

## Problem

`format_prompt` ([yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L119))
is ground truth: it renders each message independently and picks the engine
from that message alone. Two other layers claim to reason about the same
property on different inputs:

| Layer | Decides dialect from | Correct? |
|---|---|---|
| `format_prompt` | the single message being rendered | ground truth |
| `prepare_messages` validation ([executor_base.py](../yamlgraph/executor_base.py#L239)) | `system_template + user` concatenated | **no** |
| `check_mixed_template_syntax` W024 ([checks_prompts.py](../yamlgraph/linter/checks_prompts.py#L134)) | the raw YAML file text, including `description:` and schema keys | **no** |

Four defect classes follow. All four were reproduced by probe against
`432ce1b4`; the transcripts are quoted verbatim.

### D1 — validation and rendering disagree about the engine

```yaml
system: You are a planner for {{ topic }}.
user:   Return {"chapters": []}
```
```
prepare_messages(...)  ->  KeyError: '"chapters"'
```
The concatenation contains `{{`, so validation runs as Jinja and treats the
braces as literal — correctly, for Jinja. The user message alone has no
marker, so it renders through `str.format` and `{"chapters"` becomes a
field name. The validator blesses exactly what the renderer rejects.

### D2 — the validator cannot see the hazard even when both agree

`extract_variables`'s non-Jinja pattern is `\{(\w+)\}`, narrower than
`str.format`'s field grammar. `{"chapters": []}` yields no variable, so
validation passes and `.format()` raises. Nothing in the linter covers it.

```
template : Return {"chapters": []} for {topic}
validate -> OK  (extract_variables -> {'topic'})
render   -> KeyError: '"chapters"'
```

### D3 — in `str.format` mode a literal brace is inexpressible

`{{`/`}}` is `str.format`'s only escape, and it is also the Jinja sigil, so
doubling flips the engine:

```
template : Return {{"chapters": []}} for {topic}
validate -> TemplateSyntaxError: expected token 'end of print statement', got ':'
```

There *is* a working escape — deliberately flipping that message to Jinja,
either by using `{{ var }}` for its variables or by wrapping the literal in
`{% raw %}…{% endraw %}` — because a single `{` is literal in Jinja. It is
undocumented, and it is per-message: a `{{ var }}` in `system:` does not
protect `user:`. That is precisely D1.

### D4 — mixed messages silently drop variables (2 live instances)

```
template : Hello {name}, topic is {{ topic }}
validation demands: {'name', 'topic'}
renders to        : 'Hello {name}, topic is AI'
```

Validation *forces the caller to supply* `name`, then the Jinja render
leaves `{name}` as literal text for the model to read. No exception, no log
line. **One committed prompt** is shipping this today:

- [examples/demos/novel_generator/prompts/synopsis/evolve.yaml](../examples/demos/novel_generator/prompts/synopsis/evolve.yaml)
  — `{synopsis}` never substituted

W024 exists to catch this and did not, because it scans the file rather
than the message.

> **Correction (R-4).** An earlier draft claimed two live instances. The
> second, `projects/ninchat_voice/prompts/ninchat_mediator.yaml`, is not a
> committed artifact — `projects/` is gitignored — so it cannot carry an
> acceptance criterion and is not counted. It is mentioned only to record
> that the defect also reaches untracked project trees.

### The message surface (R-5)

The shapes that carry renderable text, and which every layer must traverse
identically, verified against `prepare_messages`:

| Field | Rendered at |
|---|---|
| `system` (scalar) | [executor_base.py](../yamlgraph/executor_base.py#L280) |
| `system` (list of `{content, cache}`) | [executor_base.py](../yamlgraph/executor_base.py#L319) |
| `system_segments[*].content` | [executor_base.py](../yamlgraph/executor_base.py#L319) |
| `user` | [executor_base.py](../yamlgraph/executor_base.py#L240) |

There is no legacy `template:` message field; `grep` over `executor_base.py`
finds no other rendered field. This inventory is the frozen definition of
"per message".

## Ideal Result

Exactly one function answers "which engine renders this text", every layer
calls it with the same argument — one message — and any text that cannot be
rendered faithfully is rejected at `graph lint`, with the fix in the error
message. An author who writes a JSON shape into a prompt learns it in
seconds, from a gate, rather than from a live crash or from a house-style
line repeated in three authoring briefs.

## Proposed Solution

The minimal path back from that ideal is two changes. A third, larger one
is named and deferred below.

### Step 1 — one dialect decision, one granularity (removes the D1 disagreement)

Extract the discriminator into `yamlgraph/utils/template.py`:

```python
def is_jinja(text: str) -> bool:
    """The single source of truth for which engine renders a message."""
    return "{{" in text or "{%" in text
```

Call it from `format_prompt`, from validation, and from the lint checks.
Change `prepare_messages` to validate **per message** — over the surface
inventory above — instead of `system_template + prompt_config["user"]`.

**What Step 1 does and does not promise (R-1).** It does *not* make the D1
example render. Per-message validation still reaches `template.format()`,
which still raises on `{"chapters"` — correctly, because that text is not a
valid `str.format` template. What Step 1 removes is the *disagreement*: the
validator stops blessing text the renderer will reject. Step 2 is what moves
the failure from run time to lint time. A caller that bypasses lint is not
promised automatic brace repair, and this FR authorises no rewriting of
prompt content at run time.

### Step 2 — gate the classes at lint time (blocks D2, D3, D4)

**Grammar comes from the formatter, not from a second regex (R-2).** D2 *is*
the boundary mismatch between `\{(\w+)\}` and Python's real field grammar;
another regex would re-create it. Add a shared simple-field parser in
`utils/template.py` built on `string.Formatter.parse()`, used by both
variable extraction and the new checks. Verified behaviour:

```
'{name}'                              -> ['name']
'{analysis.grade}'                    -> ['analysis.grade']
'{items[0]}'                          -> ['items[0]']
'Return {"chapters": []} for {topic}'  -> ['"chapters"', 'topic']
'unmatched {'                         -> ValueError: Single '{' encountered
```

The parser extracts the **root identifier** from attribute/index fields and
reports (a) unmatched braces and (b) fields whose root is not an identifier
— which is exactly how `{"chapters"` is caught, without inventing grammar.

Two checks in `checks_prompts.py`, both `severity="error"` because each names
a defect certain at run time, not a smell:

- **E013** — a non-Jinja message whose formatter parse reports an unmatched
  brace or a non-identifier root. Fix text names both escapes: rewrite the
  shape in prose, or wrap it in `{% raw %}…{% endraw %}`.
- **E014** — a Jinja message containing any simple-format field with an
  identifier root (including attribute/index tails), which Jinja will never
  substitute. Literal JSON braces in a Jinja message are valid Jinja text and
  must **not** trigger E014.

**W024 is retired (R-3).** Within one message a simple-format field is
unsubstituted and belongs to E014; across separate messages differing
dialects are legitimate because rendering is per message. No third case
exists where W024 fires, E014 does not, and rendering stays faithful — so
retaining it would be dead policy. Its registration and tests are removed and
replaced by E014's.

Then fix the one committed live D4 instance, via `scripts/author.sh` (R-5),
since it is a governed `prompts/*.yaml` artifact.

### Deferred — render everything through Jinja

Not in scope. Rejected **for now**, with the reason recorded so a future FR
must answer it: Jinja is not a superset of current behaviour. It does not
substitute `{var}`; it passes it through silently. The census below counts
163 messages across 156 committed files that would become silent no-ops on
the day that change landed — the D4 failure mode, mass-produced, with no
exception to catch it. If it is ever revisited it needs (a) a mechanical
`{var}` → `{{ var }}` migration and (b) a validator that *errors* on a
residual `{var}` in a Jinja template, so the migration cannot fail quietly.
Steps 1 and 2 are not throwaway work under that future: (b) is E014.

## Acceptance Criteria

Replaced wholesale by the judgement's revised set (R-1 through R-5).

- [ ] **AC-01** `is_jinja(text)` is the sole production discriminator for
      prompt-message dialect selection; `format_prompt`, variable
      extraction/validation, E013 and E014 call it rather than repeating
      `{{`/`{%` checks.
- [ ] **AC-02** A D1 fixture proves `system` is classified Jinja, `user`
      simple-format, and `yamlgraph graph lint` returns E013 for the user
      message before execution. No criterion claims the invalid literal is
      automatically repaired.
- [ ] **AC-03** `prepare_messages` validates scalar `system`, list-form
      `system`, every `system_segments[*].content`, and `user` content
      independently; a variable used in only one message remains required.
- [ ] **AC-04** Shared simple-field parsing uses `string.Formatter.parse()`
      and variable extraction returns root identifiers for `{name}`,
      `{analysis.grade}` and `{items[0]}`.
- [ ] **AC-05** E013 fires for `Return {"chapters": []} for {topic}` and for
      unmatched braces, but not for runtime-valid `{topic}`,
      `{analysis.grade}` or `{items[0]}` fields.
- [ ] **AC-06** E013 does not fire for `Return {"chapters": []} for {{ topic }}`
      because that message is Jinja text.
- [ ] **AC-07** E014 fires for `{synopsis}`, `{analysis.grade}` and other
      simple-format fields inside a Jinja message; it does not fire for
      literal JSON text or for content inside a valid Jinja raw block.
- [ ] **AC-08** W024 is removed from registration and its superseded tests
      are replaced by E014 tests.
- [ ] **AC-09** The one retained live incident is a committed path, E014
      detects it before repair, and a real `format_prompt` regression test
      with brace-free fixture values proves each intended field is
      substituted after repair. (Not "no `{` survives": Jinja raw blocks
      render literal braces by design, and values may contain braces.)
- [ ] **AC-10** A prompt whose metadata/`description` contains `{foo}`
      produces neither E013 nor E014 solely because of that non-message field.
- [ ] **AC-11** Linting every graph under `examples/` and `graphs/` yields
      zero E013/E014 findings after the retained repair; the command and the
      complete graph count are recorded.
- [ ] **AC-12** Tests tagged `@pytest.mark.req("REQ-YG-685")`;
      `capabilities/CAP-274-prompt-template-dialect.yaml` and the matching
      `ARCHITECTURE.md` entries exist; `python scripts/req_coverage.py
      --strict` exits 0.
- [ ] **AC-13** `reference/prompt-yaml.md` states that dialect is selected
      per message, documents simple-format field rules, and shows both Jinja
      remedies for literal braces: a Jinja variable in that message, or
      `{% raw %}...{% endraw %}`.
- [ ] **AC-14** The prompt repair was made through `scripts/author.sh`, and
      `tmp/draft-authoring-report.md` records precedent, lint, smoke/render
      witness, and any blocked validation honestly.
- [ ] **AC-15** A `type: fix`, `scope: prompts` changelog fragment, an FR
      implementation record/status update, and a diary Distill entry with a
      **Seed:** are present.

## Alternatives Considered

Census executed against this checkout at `432ce1b4`, over **git-tracked**
YAML only (`git ls-files '*.yaml'`, 1064 files), classified by dialect:

```
 334  no placeholders
 225  jinja only
 163  str.format only    <- would break under "Jinja everywhere" (156 files)
   1  MIXED              <- already silently broken today
```

| Alternative | Probe result | Disposition |
|---|---|---|
| Do nothing; keep the house-style rule "describe JSON in prose" | The rule is written in 3 authoring briefs and was still violated in FR-499 and in the live D4 instance | **Rejected** — `audit_as_ritual`: guidance repeated in prose, zero gates, 6+ incidents |
| Lint only (Step 2), skip Step 1 | Leaves D1: validation still blesses what rendering rejects | **Rejected** — a gate over a known-inconsistent engine |
| Fix validation only (Step 1), skip Step 2 | D2/D3/D4 still ship; D4 is silent and already live | **Rejected** — the silent class is the one that needs the gate |
| Regex-based E013 grammar | `\{(\w+)\}` is narrower than the runtime's real grammar — that mismatch *is* D2 | **Rejected (R-2)** — reuse `string.Formatter.parse()` |
| Keep W024 alongside E014 | No fixture exists where W024 fires, E014 does not, and rendering stays faithful | **Rejected (R-3)** — dead policy |
| Render everything through Jinja | `format_prompt("Hello {name}", {"name":"Sam"})` under Jinja returns `'Hello {name}'` — no error. 163 messages / 156 files affected | **Deferred**, see above |
| Escape braces automatically before `str.format` | Cannot distinguish a literal `{"a"}` from an intended `{a}` without parsing; and `{` is far more common than `{{` in prompt text | **Rejected** — guessing at the boundary, `plausible_wrong_answer`; C-3 forbids it |
| Fix `tools/shell.py` in the same FR | `shell.py` has no dialect sniffing, so its `{{` escape works; FR-783 handled it | **Out of scope** — named so it is not assumed covered |

## Related

- Probe transcripts are reproduced verbatim in the Problem section above;
  every one is a two-line `python -` invocation against `432ce1b4`.
- [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L119) `format_prompt`
- [yamlgraph/executor_base.py](../yamlgraph/executor_base.py#L239) validation on concatenation
- [yamlgraph/utils/template.py](../yamlgraph/utils/template.py#L43) `extract_variables`
- [yamlgraph/linter/checks_prompts.py](../yamlgraph/linter/checks_prompts.py#L134) W024

### Is this a graph? (Scripture: `is_this_a_graph`)

No. There is no per-item LLM step, no multi-stage pipeline, and no parallel
fan-out. The census that produced the numbers above is a single `rglob` +
regex pass with no model in it, and the deliverable is Python in the linter
and the executor. `yamlgraph graph list` contains no matching graph, and
adding one would be `framework_costume`.

## Judgement (2026-09-23)

**Verdict:** APPROVED WITH REVISIONS — full text in
[FR-1057-prompt-template-dialect-split.judgement.md](FR-1057-prompt-template-dialect-split.judgement.md).
Classified a **framework primitive**. Authority activates only with R-1..R-5
folded, which they now are.

| # | Finding | Resolution (folded) |
|---|---|---|
| R-1 | AC-02 promised the D1 example would "render correctly after", which Step 1 cannot deliver — `str.format` still raises on `{"chapters"`. | Step 1 now states it removes the *disagreement*, not the crash; E013 moves the failure to lint time. AC-02 rewritten. |
| R-2 | E013's "a `{` that is not a valid `{identifier}`" would be a second narrow regex — re-creating the very mismatch D2 names. | Grammar now comes from `string.Formatter.parse()`, shared by extraction and both checks; verified transcript added. |
| R-3 | Retaining W024 beside E014 is dead policy — no fixture distinguishes them. | W024 retired; registration and tests replaced by E014's. |
| R-4 | `projects/ninchat_voice/...` is **not committed** (`projects/` is gitignored), so "2 live instances" and its ACs are unenforceable. | Census re-run over `git ls-files` only. Honest figures: 163/156/**1**, down from 164/158/2. Second instance demoted to a note. |
| R-5 | "Per message" was never pinned to a field inventory, and the prompt repair touches a governed artifact. | Message surface table added (scalar `system`, list `system`, `system_segments[*].content`, `user`; no legacy `template:`). Repair routed through `scripts/author.sh` (AC-14). |

**Scope frozen:** D-1..D-8 per the judgement. Not authorised: Jinja-only
migration, runtime brace rewriting, `tools/shell.py`, absent/external
artifacts, unrelated prompt cleanup, graph/provider/schema changes.

**Conditions:** C-1..C-6 GATE, all accepted.

### Questions for the human (as options)

None blocking. One judgement call already taken, flagged for visibility:
R-3 offered "retire W024" or "keep it plus a distinguishing fixture". I took
retirement, because I could not construct the fixture — if you know of a
mixing case that is stylistically wrong yet renders faithfully, say so and
W024 stays.
