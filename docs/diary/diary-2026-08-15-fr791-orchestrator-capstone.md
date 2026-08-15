# 2026-08-15 — FR-791: the pipeline found its first real API, and lied about one step on the way

**FR:** FR-791 (orchestrator) — the arc's capstone: six step FRs composed
into one command.

## The composition_bug prediction fired within hours

This morning's FR-790 Seed asked whether schema drift BETWEEN steps would
be the next composition surface. It was — but the instance was subtler
than schema shape: the negative smoke's `steps_tried` claimed
`platform-confirm` ran when its wrapper was empty. Every component was
correct; the synthesize prompt simply let the model INFER the step list
from the route description instead of copying it from evidence. The
adapter's cure is the Scripture's own: treat the model's output as a
claim and reconcile it against the source of truth at the boundary — the
prompt now renders "Actual steps that ran" from non-empty wrappers and
requires `steps_tried` to copy those labels. Truthfulness mechanized, not
requested.

## The timeout was a budget composition failure, not a defect

Run 1 died at the copilot CLI's hard 900s ceiling — authoring plus two
full-pipeline live smokes (each spawning four child graphs with their own
LLM loops) cannot fit one budget. The report gate did exactly its job:
no report, no credit, exit 65. The cure was scope-splitting the resumed
brief: validation-only, explicit budget priority order, and permission to
record an honest partial ("one smoke + Blocked validation" beats a dead
run). Third data point for the brief-is-code heuristic: briefs now carry
BUDGETS as well as premises. A brief that requests more wall-clock than
the route's ceiling is defective the same way the FR-789 static-server
premise was.

## Watching the pipeline find statfin was the payoff artifact

The raw positive log shows the whole thesis working: candidates from a
one-line hint, curl probes returning live JSON, PXWeb confirmed, and a
terminal profile with fi/en/sv endpoints and genuine StatFin rows
(Adoptiot, Ajankäyttö…). The manual 10–30 min investigation is now
`yamlgraph graph run` + four variables. Also worth recording: edge
expressions cannot address into tool_call wrapper JSON strings, so the
platform-confirm skip keys on candidate-generation hints — a documented
deviation whose substance (no confirm without candidates, no extract
without confirmed success) is test-witnessed. The boundary between
"state the router can see" and "state only the LLM can see" is a real
design constraint for composed graphs; v2 should consider promoting step
outputs to parsed state.

**Seed:** three authoring-route failures/repairs today (FR-789 premise,
FR-791 budget, steps_tried inference) were all caught by gates and cured
by brief or prompt changes — zero manual authoring escapes. The
two_strike_split cure says mechanizable levels belong in code: should
`author.sh` grow a pre-flight that checks the brief for (a) validation
commands whose premises are locally verifiable and (b) estimated
wall-clock vs the CLI ceiling, before burning a 15-minute run?
