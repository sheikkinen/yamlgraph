# Diary — Reflection FR-892: The Skeleton Learns to Accept Guests

**Date:** 2026-08-26
**Context:** FR-892 enforced same day as its conception: operator
reflection → grounded brief → 5-persona research (operator's sketch as
withheld canary, rediscovered 4/5) → judgement (R-1..R-6) → worktree
enforcement. The pattern the mercury study spent eleven rounds naming is
now a shipped primitive: `slot: true` + `--tool SLOT=manifest.yaml`.

## What the day proved

The full doctrine loop ran three times in one day (FR-891, FR-892, plus
FR-890's own bootstrap) and each pass got cheaper. The corpus-census
pipeline's two proof configurations — PDF library and git timeline — ran
with ZERO new graph YAML: manifest pair + rubric each. The census
architecture priced at "weeks" in the product study is now priced at
"minutes per corpus." Ideal-result-backwards worked: the FR's first
consumer (P0a) executed before the FR closed.

## Traps witnessed

- **The demo run as truth-teller:** the binding-path bug (graph-relative
  instead of R-1's frozen CWD-relative) survived 13 unit tests and the
  authoring smoke — because both used paths that happened to work. The
  first REAL invocation from repo root caught it instantly. Unit tests
  witness the contract you remembered to freeze; a consumer run witnesses
  the contract you meant. (Cousin of FR-891's stale-code tripwire: the
  authoring agent had silently ADAPTED to the bug by using graph-relative
  paths — a passing smoke can encode a defect as convention.)
- **zsh word-splitting** bit again (`set -- $pair` does not split in
  zsh) — mangled manifest filenames, caught by ls. The shell-traps
  memory grows.
- **Line-pinned gates cascade** (3rd occurrence today): noqa confessions
  and hedging allowlists pin file:line; any insertion above them bounces
  commits. The line-number pin is itself a `gate_checks_shape_not_substance`
  smell — the gate checks WHERE, not WHAT.

## The architectural insight

The authoring agent discovered a real constraint no one had written down:
map sub-nodes cannot invoke shell tools — only python tools. The sole
authoring route surfaced this as a recorded repair instead of a silent
workaround, exactly what the route exists for. The constraint is now
documented in the slots reference section rather than embedded in one
graph's shape.

## Seed

**Seed:** The slot contract validates runtime type and shell placeholders
but duck-types python/graph args. When the first contract-mismatch defect
ships through a python-runtime manifest, the mechanical check should
extend to signature inspection at bind time (inspect.signature on the
loaded function) — is that worth an FR now, or wait for the witness?
Also: line-pinned gate references (confessions, hedging allowlist) could
anchor on content hashes or symbol names instead of line numbers — a
census of gate-anchor drift incidents would price the fix.
