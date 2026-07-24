# 2026-07-24 — Route contract is not hook contract

**Context:** checked `.github/hooks` against the new `judge-fr` and
`review-pr` skill bundles. The skill wrappers and Scripture now say one
thing clearly: judge through `scripts/judge.sh`, review through
`scripts/review.sh`; the old VS Code prompt files are gone. The question
was whether the hook layer also enforces that contract.

**What the check found:** the wrappers enforce the live execution
boundary: OS lock, `JUDGE_EXECUTION` / `REVIEW_EXECUTION` recursion
sentinel, explicit yamlgraph executor resolution, and artifact contracts
for `tmp/draft-judgement.md` and `tmp/draft-review.md`. The hook layer
does not currently enforce the sole-route rule. `.github/hooks` contains
FR prior-art and triage reminders, generic command safety gates, and
post-edit checks, but no test or guard that blocks manual/subagent
judge or review execution. That is not automatically a defect: the old
prompt surfaces are absent, and a hook cannot block a bypass it cannot
observe.

**Implementation check:** the copied implementation itself is coherent at
the local surface. The adapter graphs are thin copilot-node wrappers with
`allow_all_paths`, `allow_all_tools`, and a pinned model; YAMLGraph's
copilot runtime consumes those flags and converts them to CLI arguments.
The wrapper scripts parse cleanly under `bash -n` and verify the artifact,
not the copilot exit code, which is the right boundary for the known
silent-write-denial failure. But the implementation is inherited, not
locally witnessed: searches found no `tests/` or `.github/hooks/tests/`
coverage for `scripts/judge.sh`, `scripts/review.sh`, the sentinels, or
the artifact contracts; no CAP/REQ/ARCHITECTURE traceability entry names
the new skill bundles; and the only local ledger is two changelog
fragments pointing back to csap precedent. This is the same category as
route-contract-vs-hook-contract: provenance is not proof. A mirror copy
needs a mirror witness if this repository is going to rely on it as a
governance boundary.

**The trap:** documentation can say "sole route" so loudly that the mind
mentally promotes it into a mechanical gate. But a route contract and a
hook contract are different things. The wrapper proves executions that
pass through it; hooks only prove the tool events they inspect. Treating
those as the same protection creates false confidence at exactly the
authority boundary.

**Heuristic:** when a process declares one legal execution route, name
the enforcement boundary explicitly: deleted surface, wrapper sentinel,
artifact contract, CI gate, or hook denial. If the boundary is only
documentation, call it advisory. If a hook is proposed, first name the
observable event it can actually catch; otherwise the hook becomes a
ceremonial reminder around an unobservable violation.

**Seed:** file a small FR for local wrapper contract tests and
traceability: stale-lock handling, recursion sentinel denial, executor
resolution order, artifact-required failure, and verdict-line shape for
`scripts/judge.sh` / `scripts/review.sh`. The test can mock the
`yamlgraph` executable; it does not need to run a real judge.
