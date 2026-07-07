# The Inquisitor Prescribes Without Judgement

**Date:** 2026-07-07
**Context:** PR #458 (breakglass direct-push ledger gate) rejected by operator after a full
pipeline run: Inquisitor audit → auto-proposal → plan → judge APPROVE ("Authority granted") →
enforce → CI → PR — rejected at the last, most expensive gate. Third same-theme Inquisitor
proposal in one day (`inquisitor-pr-bypass-log`, `inquisitor-breakglass-missing`,
`inquisitor-main-bypass`).
**Trap:** detection authority conflated with prescription authority — an automated detector
was allowed to consume pipeline resources on a remedy nobody had judged.

## What Happened

The Inquisitor's finding was *correct*: direct pushes to main lacked break-glass documentation,
escalating across audits 252 → 255 → 256. Its `--propose` flag turned that finding into an
inbox topic. The pipeline Judge then did exactly what the Scripture already warns it does
(`unchallenged_premise`): it validated *execution*, not *intent* — the FR was clear, testable,
minimal, feasible, so it granted authority. The gate was built flawlessly. It failed only when
it met the operator, who rejected the *premise*: FR-662 mandates direct-to-main for the
single-developer manual lane, so a ledger-per-push policy taxes every routine commit, not just
emergencies. Detection was right; the prescription conflicted with sanctioned doctrine.

An autoimmune event: the immune system attacked the host's own sanctioned workflow. Three
times. And it will re-propose tomorrow, because nothing tells it the policy was rejected.

## The Asymmetry Nobody Noticed

The Philosopher — the *learning* system — has a built-in `challenge` node: a devil's-advocate
gate between pattern detection and proposal. The Inquisitor — the *immune* system — has none:
`--propose` writes to the inbox directly. Yet the immune system is precisely the component
prone to autoimmune responses, because its findings are always locally correct (a violation
*did* occur) while its remedies embed policy choices no one authorized. Human proposals carry
implicit human premise-judgement; Philosopher proposals pass a challenge gate; Inquisitor
proposals alone go from detector to executor unjudged.

The pipeline Judge cannot compensate: judging "is this FR well-formed?" is a different
cognitive act from "should this policy exist?" — and the Judge's prompt only mandates the
first. Today both were exercised end-to-end, and the gap between them cost a full pipeline
run, an ID collision (FR-697 race with FR-698), and a PR rejection.

## Heuristic

**Detection authority ≠ prescription authority.** Any automated proposer must pass a premise
challenge *before* consuming pipeline resources — either a devil's-advocate step (as the
Philosopher already has), an explicit Red Hat clause in the Judge's mandate for
detector-originated topics ("is the remedy compatible with sanctioned workflows?"), or a human
ack for proposals that would add enforcement gates. The cheapest place to kill a wrong policy
is before the plan, not after the CI run.

**Seed:** rejection memory — rejected FRs and closed PRs currently leave no trace the
Inquisitor can see, so the reject → re-propose treadmill is structural. Should the audit
prompt ingest a `decisions.md` ledger of standing operator verdicts ("direct-to-main is the
sanctioned single-dev lane, not a bypass incident"), so the Inquisitor cites precedent instead
of relitigating it — and how does one distinguish a standing decision from doctrine drift that
*should* be relitigated?
