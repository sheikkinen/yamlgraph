# Judgement: FR-1057 Prompt template dialect is decided at three different granularities

**Verdict:** APPROVED WITH REVISIONS — the defect is real and the shared per-message boundary is the minimal framework fix, but authority activates only after R-1 through R-5 are folded into the FR.

**Reviewed against:** `feature-requests/FR-1057-prompt-template-dialect-split.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `ARCHITECTURE.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-430-linter-mixed-template-syntax.md`; `feature-requests/FR-499-structured-world-state-ledger.md`; `feature-requests/FR-361-fix-executor-double-brace-output.md`; `feature-requests/FR-783-api-discovery-leaf-tool-manifests.md`; `feature-requests/FR-789-api-discovery-browser-sniff-step.md`; `feature-requests/FR-790-api-discovery-schema-extract-step.md`; `feature-requests/FR-791-api-discovery-orchestrator.md`; `feature-requests/authoring-briefs/fr-789-authoring-brief.md`; `feature-requests/authoring-briefs/fr-790-authoring-brief.md`; `feature-requests/authoring-briefs/fr-791-authoring-brief.md`; `yamlgraph/executor_base.py`; `yamlgraph/utils/template.py`; `yamlgraph/linter/checks_prompts.py`; `yamlgraph/linter/graph_linter.py`; `examples/demos/novel_generator/prompts/synopsis/evolve.yaml`; `reference/prompt-yaml.md`; `tests/unit/test_format_prompt.py`; `tests/unit/test_template.py`. The FR-cited `projects/ninchat_voice/prompts/ninchat_mediator.yaml` was also checked but is absent from this committed checkout.

## What is sound

The problem is demonstrated at the actual seam. Rendering chooses a dialect for one message (`yamlgraph/executor_base.py:118-132`), validation currently concatenates system and user text (`yamlgraph/executor_base.py:227-232`), and W024 reads the entire YAML file (`yamlgraph/linter/checks_prompts.py:123-145`). The D1 transcript and explanation therefore match the implementation (`feature-requests/FR-1057-prompt-template-dialect-split.md:69-92`).

The research record has substance. It dispositions six genuine solution classes, records an executed corpus census, and explains why this is not a graph (`feature-requests/FR-1057-prompt-template-dialect-split.md:213-250`). The repeated author guidance is also committed evidence, not assertion: the FR-789, FR-790, and FR-791 briefs independently prohibit literal JSON braces (`feature-requests/authoring-briefs/fr-789-authoring-brief.md:74-75`; `feature-requests/authoring-briefs/fr-790-authoring-brief.md:67-68`; `feature-requests/authoring-briefs/fr-791-authoring-brief.md:95-100`).

Rubric assessment:

1. **Scope:** the shared discriminator, aligned message granularity, and lint gates are the smallest coherent correction; lint-only and validation-only alternatives each leave a demonstrated class open (`feature-requests/FR-1057-prompt-template-dialect-split.md:145-172,226-233`).
2. **Consistency:** the ideal and broad direction agree, but AC-02, W024's residual role, and the live-instance count contradict the proposed behavior; R-1, R-3, and R-4 resolve these (`feature-requests/FR-1057-prompt-template-dialect-split.md:131-170,191-200`).
3. **Measurability:** most criteria name files, diagnostics, commands, or assertions (`feature-requests/FR-1057-prompt-template-dialect-split.md:186-211`); the revised criteria below replace the impossible or stale assertions.
4. **Feasibility:** the relevant seams are small and already centralized enough to amend: dialect selection is two literal checks, validation has one call site, and prompt checks are registered in one linter pipeline (`yamlgraph/executor_base.py:118-132,227-240`; `yamlgraph/utils/template.py:42-65`; `yamlgraph/linter/graph_linter.py:132-141`).
5. **Architecture alignment:** moving shared template semantics into the existing template utility follows the repository's leaf-primitive pattern and runtime-safety goal (`ARCHITECTURE.md:5-17`; `yamlgraph/utils/template.py:1-20`).
6. **Single responsibility:** executor alignment, lint detection, incident repair, tests, and documentation all serve one responsibility: faithful per-message prompt rendering. `tools/shell.py` and a Jinja-only migration are explicitly excluded (`feature-requests/FR-1057-prompt-template-dialect-split.md:174-184,231-233`).
7. **Strategic classification:** **framework primitive**. It governs every prompt message, has more than three evidenced incidents/use sites, and replaces repeated local prohibitions with one framework boundary (`feature-requests/FR-1057-prompt-template-dialect-split.md:18-35,215-228`).
8. **Testability:** direct RED tests exist for dialect choice, formatter-field parsing, per-message validation, lint diagnostics, live prompt rendering, corpus lint, and traceability. Existing tests already expose the two rendering modes and extraction boundary (`tests/unit/test_format_prompt.py:8-89`; `tests/unit/test_template.py:6-73`).

## Required revisions

### R-1: Reconcile D1 with the authorized behavior

Replace the claim that Step 1 “fixes D1” and AC-02's “renders correctly after.” The proposed implementation does not rewrite `Return {"chapters": []}` and therefore cannot make a direct `prepare_messages()` call render it successfully: per-message validation still reaches `template.format()` and raises (`yamlgraph/executor_base.py:127-132`). State the exact contract instead:

- Step 1 removes the cross-message dialect disagreement by classifying and validating each rendered message independently.
- Step 2 makes the D1 user message fail `graph lint` with E013 before execution.
- A caller that bypasses lint is not promised automatic brace repair.

Rewrite AC-02 to assert the D1 fixture is classified Jinja for `system`, simple-format for `user`, and rejected by E013 at lint time. Preserve AC-03's proof that per-message validation still demands variables from every message.

### R-2: Define simple-format grammar with the formatter, not another narrow regex

Replace “a `{` that is not a valid `{identifier}`” with an implementable contract based on `string.Formatter.parse()`. The current extractor recognizes only `\w+` (`yamlgraph/utils/template.py:59-65`), while the runtime delegates to Python's formatter (`yamlgraph/executor_base.py:127-132`); another regex would preserve the same boundary mismatch named by D2.

Add a shared simple-field parser in `yamlgraph/utils/template.py` that:

- parses non-Jinja messages with `string.Formatter.parse()`;
- extracts the root identifier from supported attribute/index fields;
- reports unmatched braces and fields whose root is not an identifier, including the JSON key field in `{"chapters": []}`;
- preserves runtime-valid forms such as `{analysis.grade}` and `{items[0]}`;
- is used by variable extraction and E013 rather than duplicating formatter grammar.

Define E014 as a Jinja message containing any simple-format field with an identifier root, including attribute/index tails, not merely the exact `{var}` spelling. Literal JSON braces in a Jinja message are valid Jinja text and must not trigger E014.

### R-3: Retire W024 unless a distinct faithful fixture is specified

Remove the sentence that W024 remains “for stylistic mixing that is not unsubstitutable.” Within one Jinja-rendered message, a simple-format field is unsubstituted and belongs to E014; across separate messages, different dialects are valid because rendering is per message. The FR provides no third case where W024 is both distinct from E014 and useful.

The minimal authorized outcome is to remove W024's registration and tests while adding E014. If the author retains W024, the FR must instead add one concrete fixture where W024 fires, E014 does not, and rendering remains faithful; absent that fixture, retention is dead policy.

### R-4: Replace the absent live incident and repair assertions

The cited `projects/ninchat_voice/prompts/ninchat_mediator.yaml` does not exist in the committed checkout, so the “2 live instances” claim and AC-05/AC-06 cannot be enforced as written (`feature-requests/FR-1057-prompt-template-dialect-split.md:111-126,198-200`). Fold one of these exact resolutions:

1. cite a second committed, extant prompt and update the census/path evidence; or
2. change D4, the census, AC-05, and AC-06 to the one verified live instance at `examples/demos/novel_generator/prompts/synopsis/evolve.yaml`.

For each retained live prompt, assert that known fixture values replace every simple-format field that the prompt intends to interpolate. Do not assert that no `{` survives globally: Jinja raw blocks intentionally render literal braces, and variable values may themselves contain braces.

### R-5: Pin the message surface and authoring route

Define the exact message-bearing prompt shapes traversed by validation and lint: scalar `system`, list-form `system`, `system_segments[*].content`, and `user` (plus any actually rendered legacy `template` field, if supported). Tests must cover each retained shape so “per message” cannot regress into a different partial inventory.

Because enforcement modifies an existing `prompts/*.yaml` artifact, route that prompt repair through `scripts/author.sh` and require a substantive `tmp/draft-authoring-report.md`, as mandated by `.github/copilot-instructions.md:10-17`. Python, test, documentation, capability, changelog, FR-status, and diary edits remain ordinary enforcement work.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Shared `is_jinja()` and simple-format field parsing in `yamlgraph/utils/template.py` |
| D-2 | Per-message validation/render preparation in `yamlgraph/executor_base.py` |
| D-3 | E013/E014 and W024 retirement or revised distinct fixture in `yamlgraph/linter/checks_prompts.py` and `yamlgraph/linter/graph_linter.py` |
| D-4 | Focused unit/regression tests under `tests/unit/` |
| D-5 | Repair only the committed live D4 prompt paths retained after R-4 |
| D-6 | Per-message dialect and escape documentation in `reference/prompt-yaml.md` |
| D-7 | `capabilities/CAP-274-prompt-template-dialect.yaml`, REQ-YG-685 architecture registration, and tagged tests |
| D-8 | Fix changelog fragment, FR implementation record/status, graph-authoring report for prompt edits, and diary Distill entry |

Not authorized: rendering every prompt through Jinja; automatic brace rewriting; changes to `yamlgraph/tools/shell.py`; edits to absent/external `yamlgraph-visual-novel` or `projects/ninchat_voice` artifacts; unrelated prompt cleanup; new graph behavior; provider, schema, or LLM changes; new template dialects.

## Revised acceptance criteria

- [ ] AC-01: `is_jinja(text)` is the sole production discriminator for prompt-message dialect selection; `format_prompt`, variable extraction/validation, E013, and E014 call it rather than repeating `{{`/`{%` checks.
- [ ] AC-02: A D1 fixture proves `system` is classified as Jinja, `user` as simple-format, and `yamlgraph graph lint` returns E013 for the user message before execution; no criterion claims the invalid literal is automatically repaired.
- [ ] AC-03: `prepare_messages` validates scalar system, list-form system, every `system_segments[*].content`, and user content independently; a variable used in only one message remains required.
- [ ] AC-04: Shared simple-field parsing uses `string.Formatter.parse()` and variable extraction returns root identifiers for `{name}`, `{analysis.grade}`, and `{items[0]}`.
- [ ] AC-05: E013 fires for `Return {"chapters": []} for {topic}` and unmatched braces, but not for runtime-valid `{topic}`, `{analysis.grade}`, or `{items[0]}` fields.
- [ ] AC-06: E013 does not fire for `Return {"chapters": []} for {{ topic }}` because that message is Jinja text.
- [ ] AC-07: E014 fires for `{synopsis}`, `{analysis.grade}`, and other simple-format fields inside a Jinja message; it does not fire for literal JSON text or content inside a valid Jinja raw block.
- [ ] AC-08: W024 is removed from registration and its superseded tests are replaced by E014 tests, unless the folded FR supplies the distinct faithful fixture required by R-3.
- [ ] AC-09: Every live incident retained after R-4 is a committed path, E014 detects it before repair, and a real `format_prompt` regression test with brace-free fixture values proves each intended field is substituted after repair.
- [ ] AC-10: A prompt whose metadata/description contains `{foo}` produces neither E013, E014, nor W024 solely because of that non-message field.
- [ ] AC-11: Linting every graph under `examples/` and `graphs/` yields zero E013/E014 findings after the retained live repairs; the command and complete graph count are recorded.
- [ ] AC-12: Tests are tagged `@pytest.mark.req("REQ-YG-685")`; `capabilities/CAP-274-prompt-template-dialect.yaml` and the matching `ARCHITECTURE.md` requirement/capability entries exist; `python scripts/req_coverage.py --strict` exits 0.
- [ ] AC-13: `reference/prompt-yaml.md` states that dialect is selected per message, documents simple-format field rules, and shows both Jinja remedies for literal braces: a Jinja variable in that message or `{% raw %}...{% endraw %}`.
- [ ] AC-14: The retained prompt repairs were made through `scripts/author.sh`, and `tmp/draft-authoring-report.md` records precedent, lint, smoke/render witness, and blocked validation honestly.
- [ ] AC-15: A `type: fix`, `scope: prompts` changelog fragment, FR implementation record/status update, and diary Distill entry with a **Seed:** are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority activates only after R-1 through R-5 are folded into `feature-requests/FR-1057-prompt-template-dialect-split.md`. | GATE |
| C-2 | Do not modify any retained `prompts/*.yaml` incident file outside the graph-authoring route; accept the report's substance, not adapter exit code alone. | GATE |
| C-3 | Do not auto-escape or rewrite brace content at runtime; invalid simple-format text must fail explicitly at lint/validation boundaries. | GATE |
| C-4 | Do not retain W024 as an overlapping warning without the distinct faithful fixture required by R-3. | GATE |
| C-5 | Do not claim or test an absent prompt path; all incident-based acceptance evidence must resolve to committed artifacts. | GATE |
| C-6 | Do not broaden this FR into Jinja-only migration, shell formatting, unrelated prompt cleanup, or graph/provider changes. | GATE |

Authority granted: after the revisions are folded, implement the shared per-message prompt dialect primitive, formatter-grounded E013/E014 gates, the verified committed incident repair, and the frozen supporting tests, documentation, traceability, and release records.

---

## Author addendum — prior-art disposition (FR-738 gate)

Added by the FR author, not the judge; the gate requires the disposition to
appear in this artifact as well as in the FR.

**Prior art:**
- [FR-1057-prompt-template-dialect-split.md](FR-1057-prompt-template-dialect-split.md)
  — this judgement's own subject, not independent prior art.
- [FR-795-endpoint-probe-schema-dialect-repair.md](FR-795-endpoint-probe-schema-dialect-repair.md)
  [Enforced] — also a "two dialects, one field" defect inside a `prompts/*.yaml`
  file, and genuinely the same *family*. Different boundary: FR-795 is the
  **output schema** dialect (native `schema:` vs JSON-Schema `items:`), which
  fails loudly at graph compile. FR-1057 is the **input template** dialect
  (Jinja vs `str.format`), which fails at render or not at all. No overlap in
  code: FR-795 touched `schema_loader.py`, this touches `executor_base.py`,
  `utils/template.py` and `linter/checks_prompts.py`. Cited as corroboration
  that dialect confusion in prompt YAML is a recurring class, not a one-off.
- [FR-1054-nested-object-schemas-reach-the-provider.md](FR-1054-nested-object-schemas-reach-the-provider.md)
  [Judged] — same `schema:`-vs-JSON-Schema axis as FR-795, at the provider
  boundary. Distinct from this FR for the same reason: output schema, not
  input template. Its dialect-scoped fix is not inherited here.

Retrieval is filename-noun IDF ranked, so it found these by sharing the noun
"dialect" and missed the FRs that share the actual problem — FR-430, FR-499,
FR-361, FR-783 — which the FR's own **Prior art:** line dispositions.
