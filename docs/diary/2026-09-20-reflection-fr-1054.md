# The Bug That Was Fixed Four Times Without Being Found

*2026-09-20 — FR-1054, nested object schemas reach the provider*

## What happened

`build_pydantic_model_from_json_schema` read `items["type"]` and threw
away `items["properties"]`. An `output_schema` declaring array items with
`name`, `score` and `justification` became `list[dict]`. Pydantic emitted
`{"type": "array", "items": {"type": "object", "additionalProperties":
true}}`, the provider was asked for unconstrained objects, returned `{}`
per element, and `list[dict]` validated `[{}]` without complaint.

Fourteen sites across eleven shipped example prompts. Fifty-five declared
keys. Zero survivors.

## The trap: the loud symptom bought silence

The defect had been met four times and routed around every time.

**FR-458** hit it from the OpenAI side: strict mode rejected the schema
with `additionalProperties is required to be supplied and to be false`.
The conclusion recorded there was that *"the `list[dict]` type is valid
Python/Pydantic — the problem is OpenAI's strict mode requirement, not
the schema itself"*. A `method="function_calling"` fallback was added.
That fix worked, and in working it removed the only place the framework
raised its voice. **FR-466** abandoned structured output for an entire
example, demoting `output_schema` to "documentation". **FR-905** and
**FR-908** hand-wrote deterministic post-hoc validators to check item
shapes the schema should have enforced. **FR-904's judgement** listed
framework-side nested schema support as explicitly not authorized.

Four encounters, four local repairs, no diagnosis. Each one was correct
about its own symptom. The strict-mode error was the system's only alarm,
and silencing it was recorded as a fix.

## What actually surfaced it

Not a test. A downstream consumer with an artifact on disk. The
summarizer wrote every chunk's output to a file (FR-003), and the counts
were impossible to misread: `concepts` 114 items, 0 empty;
`speaker_positions` 6 items, 6 empty. Flat fields full, nested fields
hollow, in the same file, from the same call. The shape of the evidence
named the boundary.

This is `read_raw_output_first` arriving from an unplanned direction. The
artifact was not built to diagnose the framework. It was built so a human
could read what the map stage produced. Legibility for its own sake found
in one glance what four FRs had walked past.

## The confirmation nobody asked for

The first live-witness run resolved `yamlgraph` through the venv's
editable install — which points at the main checkout, not the worktree —
so it exercised the unfixed loader. It did not produce hollow items
quietly. It aborted: `2 validation errors for ChapterReview /
criteria.0.name / criteria.0.score / input_value={}`.

`examples/book_reviewer` is broken on `main` right now. Its hand-written
`CriterionScore` requires `name` and `score`, so the hollow items met a
strict model and died. Thirteen other sites have no such model and
absorbed them in silence. The accident of a wrong `PYTHONPATH` produced a
cleaner before/after than the witness I had designed.

I nearly filed that failure as noise. A reasoning guard stopped the
dismissal mid-sentence. It was right: the failure was the finding.

## The heuristic

**A fix that removes an error message without explaining it converts a
loud defect into a silent one.** When a provider rejects a generated
artifact, the rejection is evidence about the artifact. Adding a fallback
path answers the question "how do I stop seeing this?" — never "why is
this being generated?". The FR-458 fallback was the right code and the
wrong stopping point, and it bought six FRs' worth of silence.

Pairs with `downstream_fix` and `symptom_patch`, but it is not the same
animal. Those describe fixing at the wrong location. This one is about a
fix at the right location that also removes the instrument.

Proposed name: `fallback_silences_the_witness`. Recurrence so far is one
causal chain (FR-458 → 466 → 905 → 908 → 904 → 1054), which is one
incident with five downstream effects, not five incidents. Not a
Scripture graduation yet. Worth watching for a second chain.

## The cheaper check nobody ran

The corpus was eleven files. Enumerating what every shipped prompt
declared versus what Pydantic would send took one script and under a
second of runtime, and it produced the whole blast radius as a table.
That census was available at FR-458 and at every encounter after it. The
question "how many other prompts declare this?" was never asked, and it
was always affordable.

**Seed:** The framework has no assertion that a generated schema
preserves what was declared — the loader's output is only ever checked
against whether it parses, never against its own input. What would a
general declared-versus-generated conformance check look like, running
over every shipped prompt at CI time, and which other declarations
(`enum` values, `description` text, numeric bounds, `required` at depth)
are being dropped today with no one downstream strict enough to notice?
