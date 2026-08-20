# 2026-08-20 — The Week's Repos Are the Acceptance Suite

Four public repos in three days: `yamlgraph-daily-digest` (daily cron
pipeline, hand-built), `hva-weekly-bulletin` (weekly, hand-built),
`deviant-daily` (daily + external publish + extra secret, FR-826),
then `gitclaw` (FR-827) — the factory. The arc is the classic one:
three hand-rolled instances, then the generalization. Rule of three,
observed in the wild at repo granularity.

**Trap: acceptance tests invented from imagination.** Asked "what
would make sense as gitclaw acceptance tests," the generative reflex
is to brainstorm scenarios. But the week already ran the experiment:
each sibling repo is a real, paid-for requirement that a human found
worth building by hand. The honest acceptance suite is "can gitclaw
regenerate this week's repos as features?" — precedent-harvested, not
imagined. This is `ask_before_generate` applied to test design: who
solved this before? I did, three times, this week.

**What the corpus grades:** the digest test (feature graphs using
tools) likely passes — the operator's static-gate revert made it
possible. The bulletin test fails: a weekly feature intentionally
emitting nothing six days out of seven is indistinguishable from a
failed feature (`extract_output → None → .failed.json`). The deviant
test fails: text-only outputs, no per-feature secrets. gitclaw v1
covers exactly one class — the daily text oracle — and the week's own
repos mark the next rungs.

**Insight: the generalization defines its own gaps by what it cannot
re-absorb.** A factory's acceptance suite is its own prehistory. If
gitclaw could ingest digest, bulletin, and deviant as issues, the
three sibling repos would become retireable — the additive-default
correction applied at repo scale.

**Seed:** should "intentional silence" be a first-class cron outcome
(`skipped_by_design`, no `.failed.json`, no exit 1)? The bulletin test
cannot pass without distinguishing "chose not to speak" from "failed
to speak" — the same distinction the ledger already makes between
`judged_rejected` (terminal, fine) and interrupted (needs human).
