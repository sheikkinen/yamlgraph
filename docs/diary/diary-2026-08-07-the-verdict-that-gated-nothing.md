# Diary — 2026-08-07 — The Verdict That Gated Nothing

**FR:** FR-779 (research-agent demo rot)

## What happened

A dogfood research run returned a confident OAuth2 report about a codebase
that contains no OAuth2. Two defects composed: bare `{query}` bindings fed
the model its own placeholder as the research question, and an
unconditional `validate_findings → synthesize_report` edge synthesized a
report from empty findings that validation had already, honestly, marked
low-confidence with three named gaps.

## The trap: validation as ornament

The second defect is the interesting one. The graph *had* a validation
node. It ran. It produced a correct verdict. And then the topology ignored
it — the verdict was stored in state and routed past. This is
`plausible_wrong_answer` in structural form: a validation stage whose
output gates nothing is not a safeguard, it is a *costume* of one. Worse
than absent, because a reader of the YAML sees "validate_findings" and
assumes the pipeline is guarded. The cure was not a better validation
prompt (two_strike_split: mechanizable levels defeat instruction text) but
two conditional edges — the verdict became load-bearing.

Generalization worth a grep someday: any graph with a node named
`validate_*`, `check_*`, or `verify_*` whose only outgoing edge is
unconditional has this defect by construction.

## Second trap: evidence admissibility

The judge (correctly) refused session-local `tmp/` and `logs/` artifacts
as evidence — R-1 forced the marker-run excerpts into the FR body itself.
Session evidence dies with the session; the FR is the only durable
courtroom. Cheap lesson: when filing a bug FR from a live debugging
session, embed the raw excerpts immediately, while they exist.

## Third trap: the whole-string anchor

The repo-wide sweep for bare `{var}` bindings initially matched
`security-cve-ignore`'s embedded `${{ github.workflow }}` — literal
GitHub Actions template text inside a variable *value*, not a binding at
all. Anchoring the regex to whole-string placeholders
(`^\{(?!state\.)[^{}]+\}$`) separated "this value IS a placeholder" from
"this value CONTAINS brace syntax". Syntactic similarity ≠ semantic
equivalence — `false_duplicate`, in regex form.

## Also live today

The adapter's own smoke run of the fixed graph hit the empty-findings
route and terminated without a report — the new terminal contract
witnessed itself during authoring, unprompted. Boring enforcement; the
Judgement was good.

**Seed:** Should the graph linter grow a W-class rule — "validation-shaped
node with only unconditional outgoing edges" — turning today's structural
insight into a mechanical sweep across all graphs, the way E007 already
catches undeclared state?
