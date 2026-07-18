# The Numbers Two Sessions Both Counted

**Date:** 2026-07-12
**FRs:** FR-714…FR-719 enforcement arc (six FRs, one day)
**Trap encountered:** one_session_one_repo, fourth strike — now in the
allocation layer; plus the gate that bit its own creator

## What happened

Six judged FRs enforced in sequence: gate-truth (bandit), PromptRequest,
module splits, SMT linter, package seams, edge-compiler decomposition.
Three observations survived the day.

**1. The allocator is shared state.** A parallel session worked the same
repo during the seams arc. It didn't touch my files — it touched my
*numbers*: REQ-YG-546, CAP-203, CONF-386 all double-allocated, plus its
test written against the pre-move `yamlgraph.graph_loader` path my
refactor retired mid-flight. The Scripture's one_session_one_repo names
the index, worktree, and environment as interleave surfaces; this adds a
fourth: **monotonic ID registries**. Cure applied: renumber mine (the
unpushed side yields), rewire their orphaned import, confess their four
unconfessed noqas — a red tree has one owner, whoever is standing in it.

**2. The gate bit its creator, twice, correctly.** FR-714's bandit hook
failed my own commit (bandit wasn't in .venv — the hook's interpreter,
not mine); FR-718's CC witness rejected my first decomposition when the
C(20) merely teleported into classify_edge as C(15), then C(11). Each
rejection was the gate doing exactly what the FR built it to do, before
the FR even closed. Enforcement infrastructure that inconveniences its
author on day one is the only kind worth shipping
(infrastructure_self_exempt, inverted into a feature).

**3. Line-number pins rot on every edit.** Perhaps a third of all hook
friction today was confessions/allowlists pinning file:line while lines
moved (noqa moved by a dataclass, FB001 shifted by 21 lines, B104 by 30).
The confession discipline is sound; its addressing scheme is brittle.

## Heuristic

Before an enforcement arc in a shared repo: `git pull --rebase` before
EVERY RED commit, and allocate IDs (REQ/CAP/CONF) at the last possible
moment — the longer an unpushed number lives, the higher the collision
odds. When the tree goes red after a rebase: enumerate what the OTHER
session allocated before assuming your own change broke it — but own the
fix regardless.

**Seed:** CONF/allowlist entries pin `file:line` and rot on every
unrelated edit. Could confessions pin a content anchor instead — the
suppressed line's text hash, or the enclosing symbol name — so that
moving code carries its confession with it and only *changing* the
sinful line demands re-confession?
