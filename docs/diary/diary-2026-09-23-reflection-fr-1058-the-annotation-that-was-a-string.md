# The annotation that was a string

**Date**: 2026-09-23
**FR**: FR-1058 — subgraph RunnableConfig propagation and native `mode: direct`
**Context**: GitHub issue #474; three condemned defects, four root causes.

---

## The trap: a correct diagnosis that was incomplete

The FR named the cause of config suppression precisely: the OTel wrapper
declared `otel_wrapped(state)`, so LangGraph's arity inspection never injected
a `RunnableConfig`. The judgement accepted it. The RED witnesses condemned it.
I widened the signature to `(state, config)`.

Three tests stayed red.

The only evidence was a `UserWarning` that reads like a typo:

> The 'config' parameter should be typed as 'RunnableConfig' or
> 'RunnableConfig | None', not 'RunnableConfig | None'.

Both sides of "not" are identical — because one is a *type* and the other is
the *string* `"RunnableConfig | None"`. The module carried
`from __future__ import annotations`. LangGraph decides injection from arity
**and** annotation type; a stringified annotation matches nothing, so injection
is skipped in silence.

The diagnosis was right about the mechanism and wrong about the sufficiency.
Arity was *a* gate. There were two, and the FR had inventoried one.

## Why the witnesses caught it

AC-05 forbids asserting on `inspect.signature` and requires asserting on the
**payload the node actually received**. That clause is what saved this change.
A signature-based witness would have gone green the instant I widened the
parameter list, and config injection would have stayed broken in production
with a passing suite and a ticked acceptance criterion.

The AC was written to prevent a *lazy test*. It caught a *wrong fix*. Those
are not the same failure, and the same clause stopped both — which is the
argument for writing acceptance criteria about the observation method, not
only about the observed outcome.

## The second trap: the test that agreed with the code

My first AC-06 witness asserted that two parent threads produced two distinct
child thread ids. True, and insufficient — distinct ids are the mechanism; the
*claim* is that neither child can resume into the parent's checkpoint. I then
wrote a stronger version that imported `_PARENT_ROUTING_KEYS` from the module
under test and asserted the child config contained none of them. That test
cannot fail for the reason I care about: if someone shrinks the constant, the
implementation and the assertion shrink together. A test that imports the
contract from the code it is testing is a mirror, not a witness. The forbidden
keys are now spelled out literally in the test.

## The third trap: skip is not pass

Fourteen witnesses reported `skipped`, not `passed`, because the `otel` extra
was not installed. In `-q` output the two are a character apart. AC-03 and
AC-05(b)/(d) were one careless glance from being declared met without ever
having executed — a false green inside the very FR whose purpose is to stop a
silently-disabled code path. The instrument had the same disease as the
patient.

## The parallel suite that proved nothing

Two more defects surfaced *after* I declared this enforced, and both were
caught by instruments I had not run.

The PR review found AC-06 ticked on a witness that never resumed anything.
The criterion has two halves — distinct identity, and independent durable
resume — and my test covered the first. Worse, this FR *already contained*
the sentence explaining why the second was missing ("invoke children compile
without a checkpointer"), sitting a few hundred lines from the tick. I wrote
both. Writing an obstacle down is not the same as noticing it contradicts a
claim you are making elsewhere in the same document.

Then CI failed where 6935 local passes had not. My test module had copied the
OTel suite's private exporter and provider installer. OpenTelemetry's global
`TracerProvider` can be set once per process; both copies guarded with
`isinstance(get_tracer_provider(), TracerProvider)`, so whichever module ran
second short-circuited, never attached *its* exporter, and observed zero
spans. Mine-first broke twelve of theirs; theirs-first broke three of mine.

Every local run had used `-n auto`, which put the two modules on different
workers — one process each, no contention, green. The parallelism I adopted
for speed was also the thing concealing the bug. CI, running them together,
was the first honest observation.

## Heuristics

- **`downstream_sufficiency`**: a correct root cause is not automatically a
  complete one. When a fix targeting a confirmed cause leaves tests red, the
  default hypothesis is a *second gate on the same path*, not a bad fix.
- **`parallel_is_not_isolated`**: a green `-n auto` suite is evidence about
  correctness, not about isolation — xdist grants separate processes and
  hides every process-global collision. Before trusting a suite, run the
  suspect modules together in ONE process, in BOTH orders.
- **`copied_global_manager`**: duplicating a helper that manages
  process-global state is not DRY debt, it is a correctness bug — the
  "already installed?" guard turns the loser into a silent no-op. Such
  helpers need exactly one owner.
- **`own_document_rebuts_own_claim`**: an FR long enough to hold both a
  criterion and the observation that defeats it will hold them both happily.
  Before ticking an AC, search the document for the reason it cannot be true.
- **`warning_that_contradicts_itself`**: a message asserting `X is not X` is a
  type-versus-repr comparison. Read it as "one of these is a string."
- **`mirror_test`**: a witness that imports its expected values from the module
  under test cannot observe that module changing. Restate the contract
  literally in the test.
- **`skip_is_not_pass`**: before declaring any AC met, confirm the witness
  *ran*. Count passes, never absence of failures.

## Seed

**Seed:** AC-05's real power came from constraining the **observation method**
(assert on the received payload, never on `inspect.signature`), not the
outcome. Most of our ACs constrain outcomes. If method-constraining clauses
are what catch wrong fixes rather than lazy tests — could the judge be
required to add exactly one method clause to every AC set, naming the
instrument that would otherwise lie? What would that clause have said for the
FRs we later had to reopen?

**Seed:** Three defects here were each found by the *first* instrument of a
kind I had not yet used: the review (first reader denied my narrative), CI
(first single-process run), the outsider (first reader denied the context).
Each was cheap and each found something the previous ones structurally could
not. If an instrument's yield is highest on its first use, the scarce
resource is not effort but *variety of vantage*. What is the cheapest
unused vantage on a change about to be declared done — and should "name one"
be the last question of every enforce, the way **Distill** is the last task?
