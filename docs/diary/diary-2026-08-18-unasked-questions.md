# Diary: The Questions We Haven't Asked

**Date:** 2026-08-18
**Context:** Deep reflection requested after the FR-814/816/817 knowledge-graph arc.
The interrogative canon records questions that fired and changed direction.
This entry asks about its complement: question *classes* structurally absent —
not questions we forgot, but questions the system's shape prevents us from generating.

## Method

Every canonical question interrogates an artifact that exists: an FR, a metric,
a gate, a repo boundary. The blind spot is systematic — the doctrine learns only
from things that left a record. So the unasked questions cluster around
**absences, error rates of the correctors themselves, and self-reference**.

## 1. What escaped? (survivorship)

The diary records traps that were *caught*. The knowledge graph maps FRs that
were *filed*. Nothing records:

- Defects that shipped and were never noticed — the doctrine's recall is unmeasured.
- Ideas killed at rung zero — never written, never judged, no graveyard.
  The cheapest-kill rungs celebrate early kills but keep no ledger of them,
  so we cannot ask whether we kill too much.

The corpus is a survivorship sample, and every Scripture graduation is fitted to it.

## 2. What do the gates cost when they're wrong?

`.github/hooks/logs/audit.jsonl` holds 53,082 decisions. We have never asked:

- What fraction of denials were *wrong* — correct work blocked, reworded, or
  routed around to satisfy a hook?
- What is a gate's precision, not just its firing count?

`detection_without_enforcement` is Scripture; its dual — **enforcement without
measurement** — is not. Every gate was added after an incident (recall-driven)
and none has ever been audited for false positives (precision-blind).
`infrastructure_self_exempt` warns about gates exempting themselves from rules;
this is subtler: gates exempt themselves from *evaluation*.

Corollary: the Scripture has a graduation rite but no funeral rite. Traps enter;
none has ever been retired. `growth_as_default` — the trap about assuming the
next commit should add something — has never been fired at the trap list itself.

## 3. Is the judge calibrated?

~729 FRs, ~19 REJECTED/CONDEMNED verdicts — a ~97% approval rate. Never asked:

- Is 97% the base rate of good proposals, or of a rubber stamp?
- **Verdict-vs-outcome reconciliation**: when an approved FR later causes an
  incident (FR-811 → FR-813 regression, in the graph we just built), does
  anything flow back to the judgement that authorized it? Commandment 10 refines
  the *law* after failure, but nothing refines the *judge*. The judge renders
  verdicts into a void that never grades them.

The FR-814 causal graph makes this askable for the first time: `caused_by` edges
pointing at regressions are exactly the judge's false negatives.

## 4. Which cures have expired?

Every trap was named against a specific model generation's failure mode.
Models changed; the trap list assumes permanence. `continuation_bias` as
observed in early-2026 weights may not describe current weights. We re-validate
code against dependencies (`pip-audit`) but never re-validate cognitive doctrine
against the model that must obey it. "Which Scripture lines are fossils?" has
no firing moment — nothing prompts it, so it never fires.

## 5. When is the operator wrong?

`forced_opposite` — state the strongest case against before granting authority —
is aimed at FRs, never at the human's framing. Operator calibration says trust
the 5-word compression, and the record supports it; but *supports* is not
*tested*. No diary entry documents a correction that was challenged and found
wrong, which means either the operator is never wrong or the challenge is never
made. Those are indistinguishable in the current record, and the second is the
`model_as_trusted_peer` trap with the roles reversed.

## 6. Who audits the confession channel?

The loop: agents write diaries → recurrences graduate to Scripture → Scripture
governs agents. The doctrine is now substantially authored by the entities it
governs, and the diary is a confession channel where the sinner is the only
witness. Selection bias is structural: agents confess traps that have cures —
tidy, narratable, flattering-to-fix. Trap classes that resist narration
(sustained mediocrity, taste failures, boring omissions) never appear, so they
never recur "twice," so they never graduate. The graduation pipeline has an
availability bias baked into its counting rule.

## 7. What would falsify the thesis?

"The primary consumers of software are no longer humans. Build for agents
first." Every FR presumes it; no FR states what observation would refute it,
or what the success criterion is. A thesis that only accumulates confirmations
is a costume (`working_system_inertia` at the worldview level). Related: the
doctrine has no termination condition — nothing answers "how would we know
this whole apparatus is done, or net-negative?"

## 8. The canon doesn't fire itself

The interrogative canon is advisory — questions with named firing moments but
no mechanism at the moment. Which canonical questions have *never fired since
graduation*? We can't answer; firings leave no record. The questions got
graduated with less enforcement than the traps they came from.

## Heuristic

**The system asks excellent questions about records and none about absences.**
Every unasked question above has the same shape: it requires a ledger of
things that *didn't* happen — denials that were wrong, ideas never filed,
verdicts never graded, questions never fired. The cure pattern is known
(`audit_gate`, `changelog_first_diagnostic`): create the record first; the
question becomes mechanical afterward.

## Seed

**Seed:** The doctrine measures the code with more rigor than it measures
itself. `audit.jsonl` + the FR causal graph (FR-814) + incident-typed FRs
already contain the raw material for three self-measurements: gate precision
(wrong denials / denials), judge calibration (`caused_by`-regression edges per
approved verdict), and trap firing-rates (which Scripture lines never fire).
Which of the three, if computed monthly, would change a decision — and which
would be `audit_as_ritual` with better numbers?
