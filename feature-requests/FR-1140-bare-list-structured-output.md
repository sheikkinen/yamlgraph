# Feature Request: Reconcile a bare list answer with a single-list-field output model

**Priority:** MEDIUM
**Type:** Bug
**Status:** Approved — judged 2026-09-28 APPROVED WITH REVISIONS
([judgement](FR-1140-bare-list-structured-output.judgement.md)); R-2..R-4
folded, R-1 folded into this FR's Alternatives table instead of the
frozen research record (see § Judgement fold)
**Requested:** 2026-09-28
**First consumer / first event:** `examples/demos/test_map` (FR-1137) — the
next full test-corpus map run at the default provider/model, where 3 of 545
classify calls answered `[{...}]` instead of `{"records": [...]}`.
**Research:** [FR-1140.research.md](FR-1140.research.md)
**Prior art:** [FR-998](FR-998-anthropic-constrained-structured-output.md) —
owns the structured-output policy module this FR extends; it prevents the
shape only for Anthropic (constrained decoding), this FR reconciles it for
the providers left on the library default.
[FR-464](FR-464-deepseek-structured-output-fallback.md) — JSON-extraction
fallback after a `response_format` rejection; it validates the extracted
value directly and fails on the same bare list, so it shares the new
reconciliation. [FR-933](FR-933-retry-cannot-recover-deterministic-rejection.md)
— retry with validation feedback; it spends a second call on a defect that
needs none, and stays the answer for every shape this FR does not cover.
[FR-678](FR-678-narrow-agent-structured-output-catch.md) — narrowed a bare
`except Exception` in the agent fallback; same discipline here: the catch is
one `ValidationError` shape, never broad.
[FR-449](FR-449-agent-structured-output-anthropic-bugfix.md) — agent
structured output crashing inside a broad catch at the Anthropic boundary;
different provider, different shape, same boundary. FR-779 (research-agent
demo rot), FR-488 (book-scope chapters), FR-922 (bare-repo recap test)
share only the words "bare"/"structured"/"output"; dismissed.
FR-059 (provider's type lie) — the_one_law applied to a field type; this FR
applies it to the root shape.

## Summary

When a prompt's output model has exactly one field and that field is a
list, and the provider answers with the list alone, reconcile the answer
into `{<field>: <list>}` at the structured-output boundary, validate it
against the model, and log one WARNING naming the model and field. Every
other validation failure propagates unchanged.

## Value Statement

Graph authors using list-returning schemas on non-Anthropic providers stop
losing map branches (or paying a retry) to a root-shape slip whose content
is valid.

## Problem

`invoke_structured` / `ainvoke_structured` (FR-998) bind the output model
with `with_structured_output`. For providers on the library default,
the model is asked for the object shape but not held to it. On
2026-09-28 the FR-1137 full run (inception / mercury-2.5, `ChatOpenAI`,
langchain-openai 1.6.2, temperature 0) lost 3 of 545 branches to
`1 validation error for ClassifyTestsOutput — Input should be an object
[type=model_type, input_type=list]`. The truncated inputs show records with
the expected keys. The consumer now retries twice and tolerates 5% failed
partitions (FR-1137 amendment), which bounds the damage for that consumer
only; every other graph with a single-list-field schema has the same
exposure.

The repair is unique only in the narrow case: one field, list-typed, list
answer. With several fields, a non-list field, or a non-list answer there
is no unique mapping, and reconciling would be a silent fallback
(Commandment 6).

## Ideal Result

A provider's bare-list answer to a single-list-field model validates as
the declared object on the primary structured calls (sync, native async)
and on every JSON-extraction fallback (executor FR-464, race FR-464, agent
tiers), without a second call, with one log line that says it happened;
every other shape fails exactly as today, and FR-998's second-attempt
errors are never touched.

## Planned Operations

```yaml
probes:
  - "reproduce with a fake chat model whose with_structured_output runnable raises the pydantic ValidationError seen in the run — decides whether the error reaches invoke_structured as ValidationError or wrapped (OutputParserException); the catch matches what arrives, no broader"
  - "grep every production caller of bind_structured_output / invoke_structured / ainvoke_structured / attempt_structured_invoke — the reconciliation must sit below all of them, once"
  - "confirm err.errors() carries type model_type, loc (), and the list as input for both validate-python and validate-json messages"
branches:
  - "error arrives wrapped → unwrap only the documented cause chain to the ValidationError; if the list is not recoverable from the error, stop and amend the FR (no re-parse of raw text)"
  - "a caller bypasses the policy module → route it through the module in the same PR, or record it as out of scope with the reason"
delegations:
  - "research.sh: 1 run (done; 2 invocations, the first failed the precedent check)"
  - "judge.sh: 1 run, 2 if revisions are disputed"
waits:
  - "judge"
  - "CI"
commands:
  - scripts/research.sh
  - scripts/judge.sh
  - "pytest tests/unit/ -q --no-cov -m 'not slow' -n auto"
  - "yamlgraph graph run examples/demos/test_map/graph.yaml"
```

## Judgement fold (2026-09-28)

| Revision | Disposition |
|---|---|
| R-1 research substance | **Folded here, not in the research record.** `FR-1140.research.md` is the promoted output of a completed research run and stays frozen; editing it by hand would make it a record of this author, not of the research. The four-to-six distinct solution classes, with precedent, effort/risk, and `is_this_a_graph`, are in § Alternatives Considered below; the subtractionist disagreement is kept there. AC-01 is re-pointed accordingly. The operator may overrule this and order a re-run. |
| R-2 exception contract | **Folded.** Probe result in § Exception contract (frozen). Direct `ValidationError`, no wrapper, no cause chain; the list is recoverable from `errors()[0]["input"]`. C-2 does not fire. |
| R-3 surfaces | **Folded.** § Surfaces matrix below; Ideal Result narrowed; FR-998 second-attempt errors excluded. |
| R-4 exactness + traceability | **Folded.** Acceptance criteria replaced by the judgement's AC-01..AC-15 (AC-01 re-pointed per R-1); CAP-164 extended, no new capability. |

### Exception contract (frozen)

Network-free probe, 2026-09-28: `ChatOpenAI` (langchain-openai 1.6.2,
openai 2.54.0, pydantic 2.13.5) over an `httpx.MockTransport` answering
`[{"nodeid": "a"}, {"nodeid": "b"}]`, output model
`Out(records: list[Rec])`, library-default method:

| Seam | Raised | `__cause__` / `__context__` | `errors()` |
|---|---|---|---|
| `with_structured_output(Out).invoke` | `pydantic_core.ValidationError` | None / None | 1 entry: `type=model_type`, `loc=()`, `input=` the list |
| `with_structured_output(Out).ainvoke` | `pydantic_core.ValidationError` | None / None | same |

The catch is `pydantic.ValidationError` only. No cause-chain traversal.
The probe becomes the AC-02 seam test at enforcement.

### Surfaces matrix

| # | Surface | Today | FR-1140 change |
|---|---|---|---|
| 1 | `invoke_structured` / `ainvoke_structured` primary attempt (`yamlgraph/utils/structured_output.py`) | `ValidationError` propagates | helper on `ValidationError` before the FR-998 second-attempt check; `None` re-raises the same object |
| 2 | `executor_base.attempt_structured_invoke` FR-464 extraction (sync executor + threaded async) | admits `dict \| list`, then `model_validate` fails on a list | validation goes through the helper |
| 3 | `race_node` native-async FR-464 extraction | admits only `dict` | a list is admitted and goes through the helper; run-ID and cancellation unchanged |
| 4 | `tools/agent.py` cheap extraction and plain-reinvoke validation | admit only `dict` | a list is admitted and goes through the helper; tier order unchanged |
| — | FR-998 forced-tool-call second attempt | error marked and propagated | **untouched**; never reconciled |

One helper; callers hold no field or error-shape logic of their own (C-4).

## Proposed Solution

One helper in `yamlgraph/utils/structured_output.py`:

```python
def reconcile_bare_list(output_model: type[BaseModel], err: ValidationError) -> BaseModel | None:
    """Return the model built from a bare-list answer, or None when the shape has no unique repair."""
```

It returns a model only when all hold: `output_model` has exactly one
field; that field's annotation is a `list[...]`; `err.errors()` has exactly
one entry, of type `model_type` at `loc == ()`, whose `input` is a `list`.
It then returns `output_model.model_validate({field: input})`. A failure
of that validation raises the new `ValidationError` and logs nothing. Only
after it succeeds, it logs one WARNING: `structured output: reconciled
bare list into <Model>.<field> (<n> items)`.

For the extraction surfaces (matrix rows 2–4), which hold a parsed value
rather than an error, a sibling entry point validates the value: a `dict`
takes today's `model_validate` path unchanged; a `list` is validated, and
its `ValidationError` handed to `reconcile_bare_list`, so the predicate
lives in one function. Call sites are the matrix above.

No configuration flag; no change for Anthropic under `json_schema`.

## Acceptance Criteria

The judgement's revised criteria, verbatim except AC-01 (re-pointed per
the R-1 disposition).

- [ ] AC-01: § Alternatives Considered in this FR contains four to six
  genuinely distinct, dispositioned solution classes, preserves the
  subtractionist disagreement, cites precedent for each class, and answers
  `is_this_a_graph`. `FR-1140.research.md` stays the unedited research
  output.
- [ ] AC-02: Committed network-free evidence records the exact exception
  delivered by the representative `with_structured_output(...).invoke` and
  `.ainvoke` seams and proves that the bare list is recoverable from the
  direct error or one named documented cause link.
- [ ] AC-03: RED tests prove the shared helper accepts only a one-field
  model whose field annotation has list origin plus exactly one root
  `model_type` error whose input is a list; two-field, scalar-field,
  non-list-input, multi-error, non-root, and unrelated validation failures
  return no repair.
- [ ] AC-04: Sync `invoke_structured` returns the validated model for the
  witnessed bare-list failure, makes no additional invocation, and
  preserves the original exception object for every non-qualifying
  failure.
- [ ] AC-05: Native `ainvoke_structured` satisfies AC-04 using `ainvoke`,
  with no thread substitution and no change to invocation config.
- [ ] AC-06: Executor/threaded-async FR-464 extraction reconciles a bare
  list through the shared helper; existing dict extraction behavior is
  unchanged.
- [ ] AC-07: Native-async race FR-464 extraction reconciles a bare list
  through the shared helper while preserving run-ID and cancellation
  behavior; existing dict extraction behavior is unchanged.
- [ ] AC-08: Agent cheap extraction and plain-reinvoke extraction
  reconcile a valid bare list without an extra model call at that tier;
  existing dict validation, lenient-construction, `function_calling`, and
  plain-reinvoke ordering remain unchanged.
- [ ] AC-09: A wrapped list whose items violate the declared item model
  raises the post-wrap `ValidationError`; it does not return a model, call
  the provider again, or emit the successful-reconciliation WARNING.
- [ ] AC-10: Every successful reconciliation emits exactly one WARNING
  containing the output-model name, field name, and item count; no
  rejected or non-qualifying attempt emits that WARNING.
- [ ] AC-11: An error from FR-998's forced-tool-call second attempt
  remains the same exception object and is never reconciled; the
  one-second-attempt limit remains intact.
- [ ] AC-12: Existing structured-output regression suites, including
  `tests/unit/test_fr998_structured_output.py`,
  `tests/unit/test_race_node.py`,
  `tests/unit/test_fr448_agent_structured_output.py`, and
  `tests/unit/test_fr678_narrow_structured_catch.py`, pass without
  weakened assertions.
- [ ] AC-13: CAP-164 gains one new FR-1140 requirement covering the exact
  predicate and all authorized surfaces; every new test carries its
  requirement marker; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-14: `reference/prompt-yaml.md` documents that YAMLGraph may
  reconcile only a bare list into an exactly one-list-field model and
  emits a WARNING; it does not promise repair for any other validation
  failure.
- [ ] AC-15: The RED commit precedes the GREEN commit; a `type: fix`
  changelog fragment, FR implementation-status record, and diary entry
  with a **Seed:** are present.

## Alternatives Considered

`is_this_a_graph`: no. The repair is one deterministic predicate at a
Python boundary with no "for each item, ask the model"; a graph would add
a model call to remove one.

| # | Class | Precedent | Effort / risk | Disposition |
|---|---|---|---|---|
| A1 | Narrow boundary reconciliation from the typed error (this FR) | FR-059 (normalise the provider's type lie at the boundary); FR-464 (extraction fallback in the same module family) | ~1 helper + 4 call sites; risk: a silent repair outside the predicate — bounded by C-3 and identity tests | **Chosen.** |
| A2 | Prompt guidance + `on_error: retry` only (subtractionist, research persona) | FR-933 (retry with validation feedback); FR-1137 (prompt line + 2 retries + 5% allowance) | zero core code; cost: one extra call per slip, and every consumer must re-learn it | **Kept for every other shape; rejected as the whole answer.** The subtractionist's case stands for multi-field and non-list shapes, where no unique repair exists. FR-1137's accepted run paid 2 retries for exactly this shape. |
| A3 | Per-consumer normalisation in demo Python | FR-1137 `reconcile.py` (consumer-side checks) | trivial per consumer; N copies | **Rejected.** `downstream_fix`: every graph repeats it. |
| A4 | Re-parse raw provider text (`include_raw=True`) | FR-464 (parses raw text only after a `response_format` rejection) | changes every structured call's return shape; risk: a second parser beside the library's | **Rejected.** The error already carries the parsed input (§ Exception contract). Not authorized by the judgement. |
| A5 | Constrained decoding (`json_schema` strict) for OpenAI-compatible providers | FR-998 (constrained decoding for Anthropic only, library default for the rest, by decision) | provider support varies per endpoint; risk: 400s on endpoints without strict mode | **Rejected here.** Reopens FR-998's provider policy; a separate FR if a provider's strict support is witnessed. |
| A6 | Loosen the schema (`records: list \| model`, or a root-list model) | FR-1123/FR-1125 (schemas refused rather than weakened) | touches every consumer schema; risk: accepts shapes the author never declared | **Rejected.** Schema weakening; not authorized. |

## Related

- `examples/demos/test_map/` (FR-1137), `yamlgraph/utils/structured_output.py`,
  `yamlgraph/executor_base.py`
- Research brief: `feature-requests/research-briefs/fr1140-bare-list-structured-output-brief.md`
