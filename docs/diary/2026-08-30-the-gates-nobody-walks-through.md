# 2026-08-30 — The Gates Nobody Walks Through

**Context:** operator reflection, verbatim calibration: the
research-plan-judge-enforce-pr-review-merge process is repeatable but slow
with variance. Chaplain and inquisitor automation are not running.
Plan-judge is never manually challenged — 900+ FRs have conditioned trust
in the researched, judged plan. Enforcement is supervised (because it is
slow) but seldom steered or stopped; hook-tweaking is the outlier class.
Merge acrobatics — the thing we have been fixing — is the major handicap:
time, LLM resources, money.

## Finding 1: the exercised process is not the documented process

| Stage | Doctrine gate | Exercised gate |
|---|---|---|
| Research | agent | agent (trusted) |
| Plan | FR authored | trusted |
| Judge | independent verdict; human may review | never manually challenged (900-FR track record) |
| Enforce | TDD + hooks, supervised | watched, ~zero interventions except hook-class FRs |
| PR review | review graph advisory + human decision | human pays merge *mechanics*, not judgment |
| Merge | CI gates | **the major cost center** |

The system spends its scarcest resources — operator attention and LLM
tokens — at the stage with the *least* decision content (merge mechanics)
and spends none at the stages with the *most* (plan-judge, where the human
rationally exited because the judge earned trust). Attention and decisions
have drifted apart.

## Finding 2: the causal chain runs through merge cost

Merge acrobatics → each FR is expensive → chaplain automation is
uneconomical → the pipeline is hand-cranked → the operator's attention is
consumed supervising mechanics → while the decision stages run unwatched
anyway. The chaplain didn't stop running because the FSM broke; it stopped
because every run pays the same merge toll a human session pays. Fixing
merge cost is not one improvement among several — it is the precondition
for reviving the automation the doctrine already describes.

## Finding 3: an unexercised gate is a claim awaiting disposition

A gate whose intervention rate is ~zero over a large sample is one of two
things: (a) proof the upstream earned trust — then *remove the attendance*
and record the trust as policy, or (b) theater — then *retire the gate*.
Plan-judge human review is (a): 900 FRs of track record is a measurement,
not negligence. Supervised enforcement is mostly (a) with a carve-out: the
one class that still draws interventions (enforcement-infrastructure /
hook FRs) is exactly the class the Scripture already flags for adversarial
review — so the carve-out is principled, not nostalgic. The
non-running chaplain/inquisitor are `detection_without_enforcement` at the
process level: the doctrine claims an automated pipeline that does not
execute. Either revive it (on the isolation rung where it needs no
supervision — yesterday's research) or prune the claim.

**Trap candidate — `unexercised_gate` (first witness):** a review gate
that never fires accumulates neither safety nor evidence; it accumulates
cost. Measure intervention rate per gate; a ~zero rate demands a
disposition (codify the trust or delete the gate), not continued
attendance. Related: `audit_as_ritual` (3+ audits without fix), but this
is the inverse — attendance without intervention.

## Priority ladder (fed back to the operator)

1. **Make merge boring.** §4d cure (always-reporting `test` contexts) is
   already on main via PR #505 — this diary PR is the AC-16 witness run:
   docs-only, `--auto` merge, no admin. Remaining acrobatics inventory:
   squash-history conflicts in long-lived lanes (cure: short-lived lanes;
   this very entry was eaten once by a `pull --rebase` replaying
   already-squashed commits — never rebase a squash-merged lane),
   gate surprises at commit time (prior-art, diary, changelog — cures
   exist as pre-flight checks), hook cascade re-runs.
2. **Codify the trust:** auto-merge (`gh pr merge --auto --squash`) as the
   default at PR creation for gate-passing PRs; human intervention becomes
   the exception it already is in practice. Attended mode remains for the
   hook/enforcement-infrastructure class.
3. **Revive chaplain unattended at rung 3+** (container / Copilot cloud
   agent) — economics restored by 1+2, supervision need removed by the
   isolation boundary. The inquisitor rides the same vehicle.
4. **Amend doctrine to match the exercised process:** the human gates are
   the merge decision and hook-class FRs. Recording this is not
   abdication; it is `substance_over_presence` applied to our own process.

**Seed:** the judge's 900-FR trust was conditioned, never measured. What
would a judge-error ledger look like — FRs where enforcement or production
later contradicted the judgement — and would its rate justify the trust,
or reveal that the merge gates have been silently catching what the judge
misses?
