# Judgement: FR-830 gitclaw Repository-Scoped Issue Ledger

**Verdict:** APPROVED — the live template witness proves a real idempotency
defect, and `(repository, issue)` is the smallest safe identity boundary.

**Route:** Canonical YAMLGraph judge adapter, `scripts/judge.sh`, model
`gpt-5.5`, run `01a01d75-20fa-7640-9640-fc4f67b4d5a2`, 2026-08-20.

**Prior art:** FR-827 supplies the frozen ledger FSM; FR-828 supplies the live
failing template witness; FR-829 is unrelated policy precedent. FR-243/CAP-106
concern inbox import, not repository-local issue identity.

## Finding

Current `_entries()` filters only by integer issue number, while GitHub template
creation copies committed state. The Oulu instance therefore inherited source
issue #1's terminal state and skipped its own issue #1. The defect is at the
external identity boundary, not in GitHub template behavior or the FSM.

## Scope Frozen

Authorized: explicit repository arguments in ledger domain functions;
fail-closed `GITCLAW_REPOSITORY` CLI boundary; job-level workflow injection;
mechanical canonical state provenance migration; direct tests; FR evidence.

Not authorized: state-machine changes, ledger deletion/truncation, placeholder
issues, failed-instance repair, prompts, policy, cron, permissions, secrets,
generated features, YAMLGraph runtime/core, or FR-828 retry.

## Conditions

1. Preserve RED before GREEN.
2. Missing/malformed repository identity fails closed.
3. Preserve terminal code 78, interrupted code 65, transitions, and remediation.
4. Migration changes only the added repository provenance field.
5. Human-review GREEN before any corrected template retry.

Authority granted within this frozen scope.

**Human review:** APPROVED by the operator after GREEN commit `fc5a844`, 55
local tests, migration-integrity proof, and remote CI run `32332787182` passed.
