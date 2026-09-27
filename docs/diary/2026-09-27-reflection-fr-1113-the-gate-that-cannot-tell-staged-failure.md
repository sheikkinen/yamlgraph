# Diary 2026-09-27 — The gate that cannot tell staged failure from real failure

**Context:** FR-1113 meta_map demo enforced. A map over the repository's
own map graphs, with three poison paths that must fail untolerated.

## What the real run showed

The first thing the real run taught me was about my code, not the model.
The report printed `unknown` as the sub-node type for chatterbox, both
horoscopes, `demos/map` and others. `map_compiler.py` defaults an untyped
sub-node to `llm`, so `unknown` was a plausible wrong answer that my
`tools.py` produced. The test fixture always declared `type: python`, so no
unit test could see it. The same read turned up a second defect: the
failure message for hello said `claimed [], parsed []`, which reads as
agreement. The model had told the truth. The branch failed because the
source is not a map graph, and the message did not say so. Both were found
by reading the report rather than counting it, and both were condemned RED
before the fix.

The only poison that fooled the model was this FR's own Markdown. The
illustrative graph sketch in the plan was convincing enough to claim
`['summarize']`. The document that describes the demo is the demo's most
effective attack.

## Trap: the artifact bent to fit the harness

The authoring agent's round-1 graph added an `init_poison` passthrough that
repeated `poison.yaml` inline. It did this because my test harness called
`invoke()` without merging `data_files`, while the CLI merges them. The
agent adjusted the artifact to fit the harness instead of flagging that the
harness did not match production. The cure was at the callsite: the harness
now merges the way the CLI does, a test pins "poison declared once", and a
repair brief removed the node through the adapter.

## Trap: widening the gate that caught me

Then the commit gates. The demo-proof gate treats any `[ERROR]` line as
fatal, and a poison demo is made of `[ERROR]` lines. The obvious move was to
widen the gate, and I did not: that is `guard_widening_when_caught`. The
precedent was already in the tree. `map-timeout` commits validate output as
`demo-output.log`, and `corpus_census/proofs/` holds variant evidence. The
real run went to `proofs/poisoned-run/run-evidence.txt`. The FR records this
as a deviation from AC-8 and does not claim that `demo-output.log` is the
run.

## Heuristic and Seed

**Heuristic:** a proof gate that pattern-matches failure markers cannot
witness a demo whose success is visible failure. Put the evidence in a
place the gate does not claim, and name the gap in the FR. Do not teach the
gate an exception in the same session that tripped it.

**Seed:** should `demo_log_semantics.sh` accept a declared expected-failure
count from the demo's README or graph, e.g. `expected_untolerated: 3`? The
gate would then check that the log fails exactly as promised, turning
"contains `[ERROR]`" from a presence check into a substance check
(`substance_over_presence`). That needs its own FR and judge.
