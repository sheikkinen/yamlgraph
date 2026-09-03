# The Ledger Files Where the Pain Is, Not Where the Cause Lives

**Date:** 2026-09-03
**Trigger:** operator: "reflect - csap & the 400+ line fsm & grading
of statemachine-engine" — after a four-repo complexity evaluation
(voice_runtime → statemachine-engine → yamlgraph → csap) graded by
incident density.

## What I did

I ranked the stack by FR-files-per-k-LOC and crowned
statemachine-engine "the control group": 44k LOC, 24 FRs, 0.24:1
test ratio — "conventional software whose code tells the truth."
csap (33 FR/k-LOC) and yamlgraph (47) got the density laurels.

## The two errors the operator's pointer exposes

### 1. Incident ledgers are repo-scoped; incidents are not

FRs file where pain *manifests* — the consumer's ledger — not where
the cause *lives*. csap's 625 NCs include the composition-bug canon
(NC-141, NC-289: correct parts, wrong seams) and FSM-behavior arcs
(FR-371 preemption races) whose causal surface is engine semantics.
The engine's ledger is thin partly because its lessons are stored in
its consumer's ledger. Grading a library "truthful" from its own
ledger commits the same proxy error as line-counting — I upgraded
the proxy (LOC → incident density) but kept the wrong integration
boundary (per-repo). Scripture already names the genus:
`inventory_by_visibility`, and the `evaluation` boundary entry —
"method determines conclusion" — was minted from a csap arc
(NC-414). I re-fired the trap one abstraction level up.

The dependency arrow inverts the verdict: a library consumed by an
incident-dense platform inherits *suspicion* from that density, not
absolution from its own quiet ledger. 0.5 FR/k-LOC upstream of 33
FR/k-LOC is not serenity; it is unattributed liability.

### 2. The census counted Python; the program is YAML

My prod-LOC table counted `.py` only. csap's `config/` holds exactly
ONE FSM yaml — the 462-line navigator — and it is the platform's
entire live control program (verified: `find config -name '*.yaml'`
returns one file). The thing I called "the invisible UI" in the
onboarding guide, the artifact where composition bugs actually
express, appeared in my complexity evaluation as *zero lines of
code*. Config-as-code cuts both ways: if logic lives in YAML, the
census must count it as source or the highest-risk artifact becomes
invisible — the same blind spot that makes yamlgraph's graphs
"60-80% of the workflow" yet absent from any LOC metric.

Corollary, stated with calibrated uncertainty: yamlgraph doctrine
splits Python modules at 400 lines; the navigator sits at 462 with
no decomposition mechanism evident in engine core (grep for
subgraph/hierarchical constructs surfaced action_loader and parallel
machines, not composition). If the engine cannot decompose an FSM,
the consumer's config *must* bloat — a missing library feature
manifesting as consumer-side mass, which then files consumer-side
incidents. Both errors are the same error: **complexity exported
across a repo boundary is invisible to any per-repo metric.**

## The heuristic

`ledger_boundary_check`: before grading a component by its incident
ledger, ask where its failures would file. For libraries, grep the
CONSUMER's ledger for the library's nouns (states, events, actions,
marks) and re-attribute. A quiet ledger upstream of a loud one is a
hypothesis about attribution, not a conclusion about quality.

And its census twin: count the program where it lives — a complexity
census that skips config-as-code will always flatter the repo whose
logic is declarative.

## What survives from the original evaluation

The gradient finding stands — process density tracks uncertainty
class, not mass. What falls is the per-repo attribution: the engine
is not the "control group", it is the *unmeasured* group, and the
462-line YAML is not zero LOC, it is the densest program in the
fleet per line of blast radius.

**Seed:** a cross-repo incident attribution pass — map csap's 625
NCs onto the four-repo stack by causal surface (engine semantics /
voice physics / LLM nondeterminism / platform seams). Finite corpus,
enumerable, one classification per NC: the corpus-map-reduce shape
(FR-965's cure) fits exactly. Would the engine's re-attributed
density still read 0.5/k-LOC, or does it converge toward its
consumers'?
