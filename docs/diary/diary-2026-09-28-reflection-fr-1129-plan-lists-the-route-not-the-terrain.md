# Reflection: FR-1129 — the plan I wrote did not list the gates that stopped me

**Date:** 2026-09-28
**FR:** FR-1129 (Planned Operations section replaces Effort)

## What happened

The FR's measurement showed `Effort:` telling us almost nothing:
correlation 0.09 across 92 FRs, and 40 of them said "0.5 day". The
proposed replacement was a list of the operations the work will run. I
wrote that list for FR-1129 itself before enforcing it. Reconciling it
afterwards, all the planned delegations ran as written. The unplanned
rows were every pre-commit refusal:

- the prior-art gate fired on the judgement and evidence files;
- `ruff format` rewrote the RED test;
- capability validation wanted an `fr:` field;
- the PreToolUse guard refused a pytest `| tail`.

Also unplanned: my own witness test cut the skill's inline template at
the first `## ` *inside* the code fence, so GREEN failed on the test,
not the product.

## Trap

`plan_lists_the_route_not_the_terrain`: I planned the adapters
(research, judge, review) because they are the named route. I did not
plan the gates, because they feel like background. But in the
reconciliation the gates are most of the unplanned rows. This is
recurring, known behaviour, and nothing about it is a surprise. An
operations list that leaves out predictable hook refusals under-reports
the work for the same reason `Effort:` did: it records what the author
pictures, not what the repository does.

## Heuristic

When writing `## Planned Operations`, add one `probes` row per artifact
class you will create (FR sidecar, CAP, test, fragment) naming the gate
that validates it. Then the reconciliation finds those refusals in the
plan instead of in `Unplanned operations`.

## Seed

**Seed:** If the first ten reconciled FRs show the same gates in
`Unplanned operations`, is the missing artifact a per-artifact-class gate
map that the skill points to, rather than a longer sample?
