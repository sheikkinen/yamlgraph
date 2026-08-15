# 2026-08-15 — FR-787 recon: the adapter's repair loop is the argument for the route

**FR:** FR-787 (API discovery recon step) — first of the three remaining
step FRs (787 → 789 → 790) before the orchestrator.

## The sole route earned its keep in the repair history

The authoring adapter's report records four honest prompt repairs I would
each have hit interactively: evidence returned as nested objects instead
of strings; the agent exhausting its loop before final JSON synthesis; a
best-effort parse omitting required empty arrays; a literal JSON example
colliding with prompt-template braces. All four are LLM-boundary defects
of the exact class the Scripture's `two_strike_split` and
`tolerant_matching` entries describe — and the adapter burned them down
inside its own loop, delivering an artifact whose smoke passed before I
ever saw it. The route is not ceremony; it is where this defect class
goes to die without polluting the requesting session.

## Trap touched: argument order assumed, not read

My schema-builder witness called
`build_pydantic_model_from_json_schema("ReconResult", schema)` — name
first, like every other builder I'd seen today. The signature is
`(schema, model_name="DynamicOutput")`. One `AttributeError: 'str' object
has no attribute 'get'` later, the lesson restates itself: even for a
two-argument function, read the signature before writing the call. The
cheapest form of `ask_before_generate` is a five-second `grep -n "def "`.

## Reading the raw output validated more than the schema

The independent smoke didn't just satisfy AC-05's shape check — reading
it end-to-end (`read_raw_output_first`) showed the value statement's own
origin story reproduced live: the THL Sotkanet hidden REST endpoint
(`sotkanet.fi/rest/1.1/indicators`), found via rOpenGov and oskari-server
repos, with the no-auth User-Agent convention and JSON/CSV format hints,
every evidence string in the mandated `repo=; path=; url=; note=` form.
A shape check would have passed on plausible garbage; the read proved the
step does the thing the FR was written for.

**Seed:** the adapter's four-repair history is itself structured data —
each repair names a prompt-engineering defect class and its cure. Should
authoring reports feed a defect-class taxonomy (like the diary graduation
pipeline) so the third recurrence of "brace collision in literal JSON
examples" becomes a lint rule in the prompt loader instead of a repair?
