# 2026-08-15 — FR-790: the dry-run heuristic paid out on its second use

**FR:** FR-790 (schema-extract step) — third of three remaining API
discovery steps; the orchestrator's dependencies are now complete.

## One diary entry old, already load-bearing

Yesterday's FR-789 entry planted the heuristic: *dry-run the brief's
validation premises before launching the route*. Applied here before
launch: one grep confirmed `type: tool_call` has committed precedent,
and one three-line Python call confirmed `parse_openapi` emits exactly
the `EndpointInfo` shape the judgement pins
(`method/path/description/parameters`). Cost: under a minute. Effect:
the FR-790 adapter run passed all three smokes in ONE route invocation —
no report-gate death, no second run. Contrast FR-789: same adapter, same
day, but an unverified premise (static server) cost a full 15-minute
route run plus diagnosis. The heuristic's second use was its first save;
per graduation process, one more recurrence makes it Scripture material.

## The adapter's repairs are converging on a taxonomy

FR-787's four repairs and FR-790's three overlap heavily: LLM returns
strings where objects belong, objects where arrays belong, and (new
here) success-shaped failure — the adapter added `on_error: fail` to all
llm nodes so schema drift stops the run instead of producing a plausible
wrong report. That last one is Commandment 6 verbatim ("no silent
fallbacks; a plausible wrong answer is harder to catch than a crash"),
discovered independently by the authoring agent inside its own repair
loop. The FR-787 Seed (defect-class taxonomy from repair histories) now
has three data points across two runs: shape-narrowing repairs are the
dominant class, and `on_error: fail` is the graph-level cure the step
templates should carry by default.

## Guard fail-closed on a read — correct behavior, noted

The FR-767 write-guard denied a read-only Python heredoc that mentioned
`prompts/*.yaml` paths — unrecognized write shape, fail closed. The
workaround (editor read tool) took seconds. This is the guard working as
designed: the cost of a false positive is one re-read; the cost of a
false negative is an ungoverned artifact. No change proposed.

**Seed:** all six step graphs now exist with per-prompt output_schema
blocks that repeat the same CapabilityReport/ReconResult/SniffResult
pinning idiom. When FR-791 wires the orchestrator, will schema drift
BETWEEN steps (orchestrator expecting one shape, step emitting another)
become the next composition_bug surface — and should the orchestrator FR
demand contract tests that validate each step manifest's output against
the orchestrator's input expectations?
