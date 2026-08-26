# Problem brief: parallel sessions corrupt the shared main checkout

<!-- FR-890 D-9 exemplar: the FR-888 problem as it stood PRE-solution,
     reconstructed from the incident record only. No solution content
     — this brief is the closed input for the research route. -->

## Problem statement

Multiple agent sessions run in parallel against one git checkout. They
corrupt each other's work through shared mutable state: one session's
staged files are swept into another session's commit under a foreign
message; working-tree edits are destroyed by another session's
checkout; enforcement documents and scripts on the default branch are
edited by sessions that should be isolated. The corruption is silent —
the harmed session discovers it only when its artifacts are missing or
its commit contains foreign files. Worktrees exist in the repo as an
isolation primitive but sessions do not reliably use them; nothing
denies a write to the shared checkout.

## Classification

enforcement/latency-critical

## Constraints

- Single-developer direct-push-to-main flow must be preserved; no PR
  ceremony for ordinary changes.
- Denial must happen at write time, before damage, not in post-hoc
  audit.
- No daemon or background watcher.
- The isolation primitive (git worktrees plus a helper script) already
  exists and must remain the sanctioned route.
- Agent sessions perform writes through editor tools and through
  arbitrary terminal commands; both surfaces exist.

## Witnessed incidents

- Two shared-index sweeps: one session's staged files were committed by
  a sibling session's `git add -A` / `git commit -a` on main under a
  foreign commit message.
- A mid-cycle sweep where an entire staged feature arc was pushed
  inside a sibling's unrelated commit.
- A session editing enforcement scripts directly in the main checkout
  while a sibling session owned uncommitted state in the same tree.
- Environment interference: a pip reinstall in one session deleted
  console scripts out from under a running sibling.
