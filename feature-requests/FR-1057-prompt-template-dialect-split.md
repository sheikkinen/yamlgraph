# Feature Request: Prompt template dialect is decided at three different granularities

**Priority:** HIGH
**Type:** Bug
**Status:** Enforced
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

> **Correction (enforcement, 2026-09-23).** This section originally presented
> D1 as a constructed fixture with no committed instance. That was wrong.
> `examples/dungeon_master/prompts/author_plot_plan.yaml` is exactly this
> shape: a `system` message of literal JSON with no Jinja markers beside a
> `user` message that *is* Jinja. Proved on base code `432ce1b4`:
>
> ```
> system is jinja: False
> BASE CODE system render:      KeyError '\n  "agents"'
> BASE CODE prepare_messages:   KeyError '\n  "agents"'
> ```
>
> Both the `author_plan` and `repair_plan` nodes use that prompt, so the
> dungeon_master plot lane (FR-561/562/563) **could not run at all** and had
> not been able to since `9e1eaafa`. The concatenated validator blessed it
> every time. This is the FR's strongest witness and it was found by the
> corpus lint, not by reasoning.

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

- [x] **AC-01** `is_jinja(text)` is the sole production discriminator for
      prompt-message dialect selection; `format_prompt`, variable
      extraction/validation, E013 and E014 call it rather than repeating
      `{{`/`{%` checks.
- [x] **AC-02** A D1 fixture proves `system` is classified Jinja, `user`
      simple-format, and `yamlgraph graph lint` returns E013 for the user
      message before execution. No criterion claims the invalid literal is
      automatically repaired.
- [x] **AC-03** `prepare_messages` validates scalar `system`, list-form
      `system`, every `system_segments[*].content`, and `user` content
      independently; a variable used in only one message remains required.
- [x] **AC-04** Shared simple-field parsing uses `string.Formatter.parse()`
      and variable extraction returns root identifiers for `{name}`,
      `{analysis.grade}` and `{items[0]}`.
- [x] **AC-05** E013 fires for `Return {"chapters": []} for {topic}` and for
      unmatched braces, but not for runtime-valid `{topic}`,
      `{analysis.grade}` or `{items[0]}` fields.
- [x] **AC-06** E013 does not fire for `Return {"chapters": []} for {{ topic }}`
      because that message is Jinja text.
- [x] **AC-07** E014 fires for `{synopsis}`, `{analysis.grade}` and other
      simple-format fields inside a Jinja message; it does not fire for
      literal JSON text or for content inside a valid Jinja raw block.
- [x] **AC-08** W024 is removed from registration and its superseded tests
      are replaced by E014 tests.
- [x] **AC-09** The one retained live incident is a committed path, E014
      detects it before repair, and a real `format_prompt` regression test
      with brace-free fixture values proves each intended field is
      substituted after repair. (Not "no `{` survives": Jinja raw blocks
      render literal braces by design, and values may contain braces.)
- [x] **AC-10** A prompt whose metadata/`description` contains `{foo}`
      produces neither E013 nor E014 solely because of that non-message field.
- [x] **AC-11** Linting every graph under `examples/` and `graphs/` yields
      zero E013/E014 findings after the retained repair; the command and the
      complete graph count are recorded.
- [x] **AC-12** Tests tagged `@pytest.mark.req("REQ-YG-685")`;
      `capabilities/CAP-274-prompt-template-dialect.yaml` and the matching
      `ARCHITECTURE.md` entries exist; `python scripts/req_coverage.py
      --strict` exits 0.
- [x] **AC-13** `reference/prompt-yaml.md` states that dialect is selected
      per message, documents simple-format field rules, and shows both Jinja
      remedies for literal braces: a Jinja variable in that message, or
      `{% raw %}...{% endraw %}`.
- [x] **AC-14** The prompt repair was made through `scripts/author.sh`, and
      `tmp/draft-authoring-report.md` records precedent, lint, smoke/render
      witness, and any blocked validation honestly.
- [x] **AC-15** A `type: fix`, `scope: prompts` changelog fragment, an FR
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

> **Correction (enforcement, 2026-09-23) — the census undercounts.** The
> classifier above used `\{(\w+)\}` — *the very grammar defect D2 names*. It
> cannot see an attribute tail (`{synopsis.title}`) or a bare literal brace,
> so it could not see most of what this FR is about. Re-run with the shipped
> `scan_simple_fields` parser, lint over all 203 tracked graphs found **6
> findings across 4 defect sites in 3 files**, not 1. Second method
> correction in this FR after R-4: a census is only as good as its grammar,
> and measuring a grammar defect with the defective grammar undercounts by
> construction. AC-11's "zero findings" gate was, per
> `threshold_encodes_forecast`, encoding my forecast of one defect.

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

---

## Implementation Record (2026-09-23)

**Status: Enforced.** All 15 acceptance criteria met. Commits on
`feat/fr-1057-prompt-template-dialect-split`: `b83db9e0` (FR), `9c8418a2`
(judgement revisions), `fb25815e` (RED), GREEN following.

### What shipped (D-1..D-8)

| Deliverable | Where |
|---|---|
| D-1 `is_jinja`, `SimpleFieldScan`, `scan_simple_fields`, `strip_jinja_raw_blocks`; `extract_variables` rerouted off both brace regexes | `yamlgraph/utils/template.py` |
| D-2 per-message validation; `_extract_system_template_for_validation` deleted | `yamlgraph/executor_base.py` |
| D-3 E013 + E014; W024 retired (function, registration, `__all__`, tests) | `yamlgraph/linter/checks_prompts.py`, `graph_linter.py` |
| D-5 one prompt repair, authored via `scripts/author.sh` | `examples/dungeon_master/prompts/author_plot_plan.yaml` |
| D-6 dialect-per-message documentation | `reference/prompt-yaml.md` |
| D-7 CAP-274 / REQ-YG-685 | `capabilities/CAP-274-prompt-template-dialect.yaml`, `ARCHITECTURE.md` |
| D-8 changelog fragment, this record, diary Distill | `changelog/unreleased/fr-1057-prompt-template-dialect-split.md` |

### Deviations and corrections

1. **D1 had a live committed instance** (see the correction box in D1). The FR
   as judged asserted it did not. `examples/dungeon_master`'s plot lane was
   broken at runtime and is now fixed.
2. **The census undercounted** (see the correction box under Alternatives).
   The scope of the repair grew from 1 file to 3; the *code* scope did not.
3. **E014's grammar needed two narrowings the judgement did not anticipate**,
   both found by running the new check over the whole committed corpus rather
   than over fixtures:
   - *Format specs mark documentation.* `examples/plot_modeller/prompts/extract_goals.yaml`
     documents output as `{pred: alive, args: [<agent>], value: true}`.
     `string.Formatter` reads that as field `pred` with format spec
     ` alive, args…`. E014 fired wrongly — and worse, `extract_variables`
     began *requiring* a `pred` variable, a regression that would have broken
     that graph and was invisible to all 6907 unit tests. Cure: only
     `bare_roots` (no format spec, no conversion) count as substitutions.
   - *Raw blocks are literal.* `examples/yamlgraph_gen/prompts/assemble_graph.yaml`
     documents `{% raw %}{state.field}{% endraw %}`, which AC-07 already
     excluded. Cure: `strip_jinja_raw_blocks` before scanning. The test that
     was supposed to cover this had been passing for the wrong reason.

### Out of scope, found and deliberately left (C-6)

A **fifth** defect shape exists that this FR does not address:
`novel_generator`'s `prompts/timeline/construct.yaml` contains
`Title: {synopsis.title}` in a non-Jinja message. It is a syntactically
well-formed `str.format` field, so E013 correctly stays silent — but LLM
node outputs are always dicts (`llm_nodes.py` returns `result.model_dump()`),
and `str.format` does `getattr` on the attribute tail, so it can never render:
`'dict' object has no attribute 'title'`. Confirmed pre-existing by
`git stash` + re-run on base code. Candidate follow-up FR: a lint or runtime
rule for attribute access in simple-format messages.

### Operator decision — novel_generator retired from `examples/demos/`

The three `novel_generator` E014 repairs collided with
`scripts/check_demo_proof.sh`, which requires a staged successful
`demo-output.log` for any changed demo — unobtainable while defect 5 stands,
and defect 5 is out of scope. Surfaced as a decision; the operator chose
**"mv novel_generator to projects & remove from examples/demos"**. Executed:
the repaired tree was copied to the untracked private `projects/` directory
and `git rm`-ed from `examples/demos/novel_generator/` (14 files) along with
`tests/integration/test_novel_generator.py`. No CAP, `ARCHITECTURE.md` entry,
`README.md` line, or `examples/demos/demo.sh` entry referenced it, so the
retirement is self-contained. AC-09's witness is therefore the
dungeon_master D1 crash — a stronger witness than the evolve prompt, since it
was a real runtime failure rather than a silently dropped variable.

**Scope amendment to C-6 (2026-09-23, post-review).** PR #674's review raised
this retirement as blocking finding P1 — correctly by doctrine: an operator
decision recorded after judgement does not enlarge granted authority, and C-6
is a GATE against broadening this FR into unrelated prompt cleanup. The
operator was asked again, with the reviewer's objection stated, and chose to
**keep the retirement and amend the scope explicitly**. C-6 is therefore
amended here and in the judgement to permit exactly this one retirement, named
by path, and nothing else. The amendment is recorded rather than the finding
silently dismissed: the reviewer's reading of the frozen scope was right, and
the override is a human decision on the record, not an agent's.

### Correction 3 — the D4 cure was too broad (review P2)

The first `bare_roots` cure keyed on *"the field has a tail"*. That swallowed
the prose braces it was aimed at — and every real field carrying a format spec
or conversion with them. Reproduced by the reviewer and independently:

```
'Score: {score:.2f}'  extract_variables -> set()   render with {} -> KeyError 'score'
'Name: {name!r}'      extract_variables -> set()   render with {} -> KeyError 'name'
```

Lint stayed silent, validation required nothing, and the render then crashed —
re-creating at a new address exactly the validation/render disagreement that is
defect D1 and that C-3 requires to fail loudly. Corpus incidence was **0** (no
tracked non-Jinja message carries a spec-bearing field), so no test and no
corpus lint could have caught it; it was latent, and two independent
instruments — the outsider read of the PR body and the reviewer — named it
within minutes of each other.

Cure: `SimpleFieldScan.bare_roots` is replaced by `substitution_roots`, and the
discriminator is no longer "has a tail" but *"is the tail a format spec?"* —
`_FORMAT_SPEC`, transcribed from the mini-language's own definition, plus the
closed conversion set `r/s/a`. `{score:.2f}`, `{name!r}`, `{label:>10}`,
`{total:,}` and `{value:{width}}` are substitutions; `{pred: alive, args: []}`
is not. Nested specs are scanned recursively, because `{value:{width}}` cannot
render without `width`. The lesson is the general one: a cure aimed at a false
positive must be no wider than the false positive, or it buys silence with a
new blind spot.

### Correction 4 — the discriminator was a guess, and guessing was unsafe on one side (review P1)

Correction 3 was still wrong, and the second review found it in the same place.
`_FORMAT_SPEC` transcribes the *standard* format-spec grammar, but Python does
not own that grammar: `format()` hands the spec to the value's own
`__format__`. `{when:%Y-%m-%d}` is a perfectly valid field for a `datetime`,
and the regex says it is prose. Probed on the Correction-3 code:

```
"When: {when:%Y-%m-%d}"
  scan_simple_fields  -> roots={'when'}, substitution_roots=set()
  extract_variables   -> set()
  validate_variables(..., {}, "p")   -> PASSED        # should have raised
  format_prompt(..., {"when": datetime(2026,9,23)})   -> "When: 2026-09-23"
```

Validation requiring nothing while the render resolves `when` is defect D1
wearing a third costume. No regex can close this, because the grammar is open
by design.

Cure: stop asking the question where the answer must be right, and keep it only
where a wrong answer is cheap.

| message dialect | what an unresolvable field costs | set used |
| --- | --- | --- |
| `str.format` | `KeyError` at render | `roots` — **every** well-formed field |
| Jinja | nothing; the text renders literally | `substitution_roots` — the guess |

`extract_variables` now takes `roots` on the `str.format` branch. The
documentation-shape exemption survives only on the Jinja side, feeding E014,
which is advisory. A census of the whole prompt corpus confirms the exemption
is not needed anywhere else: of the messages containing a field whose tail is
not a format spec, **2 are Jinja and 0 are `str.format`**. The rule now reads
as one sentence per dialect: *in a `str.format` message every field is a
variable; in a Jinja message a field that cannot be a variable is left alone.*

`reference/prompt-yaml.md` and `CAP-274` carried the Correction-3 claim into
user-facing documentation and said a spec-bearing field is documentation; both
are corrected, and `ARCHITECTURE.md` regenerated.

### Witnesses

- `tests/unit/test_fr1057_prompt_template_dialect.py` — 22 tests
- `tests/unit/test_fr1057_prompt_repairs.py` — the dungeon_master D1 crash,
  rendering correctly after repair
- Full unit suite green (**7004 passed, 55 skipped, 1 xfailed**);
  `python scripts/req_coverage.py --strict` exits 0
- AC-11: `yamlgraph graph lint` over every tracked graph-shaped YAML
  (`git ls-files '*.yaml' '*.yml'` filtered on a top-level `nodes:` key —
  **242 graphs**) → **0 E013/E014 findings, 0 lint crashes**. Log:
  `logs/ac11e.log`. Re-run after Correction 4 over `examples/ graphs/
  projects/` (**202 graphs**) → **0 E013/E014, 0 crashes**
  (`logs/corpus-lint-p1.log`).
