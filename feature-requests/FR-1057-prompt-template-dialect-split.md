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
line. Two prompts in the repo are shipping this today:

- [projects/ninchat_voice/prompts/ninchat_mediator.yaml](../projects/ninchat_voice/prompts/ninchat_mediator.yaml)
  — `{user_message}` and `{bot_response}` never substituted
- [examples/demos/novel_generator/prompts/synopsis/evolve.yaml](../examples/demos/novel_generator/prompts/synopsis/evolve.yaml)
  — `{synopsis}` never substituted

W024 exists to catch this and did not, because it scans the file rather
than the message.

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

### Step 1 — one dialect decision, one granularity (fixes D1, corrects W024)

Extract the discriminator into `yamlgraph/utils/template.py`:

```python
def is_jinja(text: str) -> bool:
    """The single source of truth for which engine renders a message."""
    return "{{" in text or "{%" in text
```

Call it from `format_prompt`, from validation, and from W024. Change
`prepare_messages` to validate **per message** — the same list of strings it
is about to render — instead of `system_template + prompt_config["user"]`.
Change W024 to iterate message contents rather than `f.read()`.

### Step 2 — gate the two silent/loud classes at lint time (blocks D2, D3, D4)

Two new checks in `checks_prompts.py`, both `severity="error"` because each
names a defect that is certain at run time, not a smell:

- **E013** — a message with no Jinja marker containing a `{` that is not a
  valid `{identifier}`. Fix text names both escapes: rewrite the shape in
  prose, or wrap it in `{% raw %}…{% endraw %}`.
- **E014** — a Jinja message containing a `{var}` that will never be
  substituted. This is the silent class; W024 stays as the warning for
  stylistic mixing that is *not* unsubstitutable.

Then fix the two live D4 instances listed above.

### Deferred — render everything through Jinja

Not in scope. Rejected **for now**, with the reason recorded so a future FR
must answer it: Jinja is not a superset of current behaviour. It does not
substitute `{var}`; it passes it through silently. The census below counts
164 messages across 158 files that would become silent no-ops on the day
that change landed — the D4 failure mode, mass-produced, with no exception
to catch it. If it is ever revisited it needs (a) a mechanical
`{var}` → `{{ var }}` migration and (b) a validator that *errors* on a
residual `{var}` in a Jinja template, so the migration cannot fail quietly.
Steps 1 and 2 are not throwaway work under that future: (b) is E014.

## Acceptance Criteria

- [ ] **AC-01** `is_jinja()` exists in `utils/template.py` and is the only
      place the `{{`/`{%` discriminator appears; a test asserts no other
      module contains that literal check.
- [ ] **AC-02** RED test: the D1 prompt (system Jinja, user literal brace)
      raises `KeyError` before the fix and renders correctly after.
- [ ] **AC-03** `prepare_messages` validates per message. A test asserts a
      variable used only in `user:` is still demanded, i.e. per-message
      validation did not lose coverage.
- [ ] **AC-04** E013 fires on `Return {"chapters": []} for {topic}` and does
      not fire on `Return {"chapters": []} for {{ topic }}`.
- [ ] **AC-05** E014 fires on both live instances named in D4, by path.
- [ ] **AC-06** Both live instances are fixed; a test renders each through
      the real `format_prompt` and asserts no `{` survives in the output.
- [ ] **AC-07** W024 scans message content, not file text. A prompt whose
      `description:` contains `{foo}` no longer triggers it.
- [ ] **AC-08** `yamlgraph graph lint` over every graph in `examples/` and
      `graphs/` reports zero E013/E014 after the fixes — i.e. the gate is
      turned on against the existing corpus, not just against new files.
- [ ] **AC-09** Tests tagged `@pytest.mark.req("REQ-YG-685")`;
      `capabilities/CAP-274-prompt-template-dialect.yaml` added;
      `python scripts/req_coverage.py --strict` exits 0.
- [ ] **AC-10** `reference/prompt-yaml.md` documents the per-message rule
      and both escapes. The `{% raw %}` escape is currently undocumented.
- [ ] **AC-11** Changelog fragment, `type: fix`, `scope: prompts`.

## Alternatives Considered

Census executed against this checkout at `432ce1b4`. Every prompt message
in the repo (`rglob("*.yaml")`, excluding `.venv/`, `build/`, `tmp/`,
`htmlcov/`, `node_modules/`) classified by dialect:

```
 384  no placeholders
 327  jinja only
 164  str.format only    <- would break under "Jinja everywhere" (158 files)
   2  MIXED              <- already silently broken today
```

| Alternative | Probe result | Disposition |
|---|---|---|
| Do nothing; keep the house-style rule "describe JSON in prose" | The rule is written in 3 authoring briefs and was still violated in FR-499 and in the 2 live D4 instances | **Rejected** — `audit_as_ritual`: guidance repeated in prose, zero gates, 6+ incidents |
| Lint only (Step 2), skip Step 1 | Leaves D1: validation still blesses what rendering rejects | **Rejected** — a gate over a known-inconsistent engine |
| Fix validation only (Step 1), skip Step 2 | D2/D3/D4 still ship; D4 is silent and already live twice | **Rejected** — the silent class is the one that needs the gate |
| Render everything through Jinja | `format_prompt("Hello {name}", {"name":"Sam"})` under Jinja returns `'Hello {name}'` — no error. 164 messages / 158 files affected | **Deferred**, see above |
| Escape braces automatically before `str.format` | Cannot distinguish a literal `{"a"}` from an intended `{a}` without parsing; and `{` is far more common than `{{` in prompt text | **Rejected** — guessing at the boundary, `plausible_wrong_answer` |
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
