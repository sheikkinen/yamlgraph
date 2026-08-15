# Diary — 2026-08-15 — FR-784 Playwright Network Sniff Utility

## What happened

Enforced FR-784: folded judgement revisions R-1..R-5 into the FR, then
RED (5 failing static-contract tests, 6 browser witnesses skipping on
the missing script) → GREEN (11/11, including six real-Chromium runs
against the committed local SPA fixture). Delivered `network-sniff.js`,
its FR-768 shell manifest with `parse: json`, a pinned
Playwright package boundary, and the fixture family (data + telemetry +
token + auth-wall + CAPTCHA + never-settling page).

## Cognitive observations

**The interleave hazard was the real work.** `now.py` showed five live
sessions and 43 staged files belonging to another session's FR-796
demo-relocation. The one_session_one_repo ritual held: explicit
pathspecs on every `git add` and path-limited `git commit -- <paths>`.
But the fr-board-check hook still blocked my docs commit — the OTHER
session's unstaged edit to FR-796.md gets stashed by pre-commit during
my commit, so the board regenerated inside the hook differs from the
board I regenerated in the shared working tree. The board is a
function of the WHOLE tree; a per-commit gate on a whole-tree artifact
is unsatisfiable while a sibling session holds unstaged FR edits. I
could not fix this by trying harder — only by sequencing (commit after
theirs lands). This is a fourth shape of parallel-session collision:
not index sweep, not branch switch, but *hook-input divergence via
stash*.

**Mock escape hatch resisted.** The judgement demanded the browser
tests exercise real Chromium against a committed fixture — the feature
exists because of a real phenomenon (client-side rendering hiding
APIs). Six real-browser witnesses at ~13s each felt expensive; they
are the only tests that prove anything. The `--package-lock-only` +
`npm ci` boundary made "real" reproducible.

**Ruff as boundary guard, not noise.** S105 flagged my `SECRET`
canary constant. The cure was renaming to `CANARY` — the variable is
not a credential, it is a leak detector. The linter was checking the
name, and the name was genuinely misleading.

## Heuristic

When a pre-commit gate validates a whole-tree derived artifact
(fr-board, aggregated registries), a parallel session's unstaged edits
make the gate non-deterministic from inside any one session. Detect it
by diffing the regenerated artifact twice a minute apart — if rows
flip between runs with no action of yours, a concurrent writer owns
the drift. Sequence, don't fight.

**Seed:** should fr-board-check regenerate from the *commit index*
(staged FR contents) instead of the working tree, making the gate a
pure function of the commit under judgement and immune to sibling
sessions' WIP?

## Addendum — live validation (same day)

The operator asked for a live-site check after enforcement. Five words;
two defects. The deterministic fixture proved the *mechanism* (params
named `token` get redacted) but encoded my own naming assumptions — the
wild immediately presented `x-algolia-api-key`, which exact-name
matching missed, and `telemetry.algolia.com`, which the domain denylist
missed. The fixture tests what you thought of; the live run tests what
vendors actually do. This is `read_raw_output_first` in network form:
one `cat` of real captured traffic exposed what no amount of fixture
elaboration would have. The cure was structural, not enumerative —
segment-based name matching plus *shape-based* value redaction, so the
next unlisted vendor prefix is caught by the value's own geometry.

Heuristic: for any boundary normalizer (redactor, classifier,
sanitizer), the acceptance suite proves the mechanism; ship it, then
immediately fire ONE live probe and diff reality against the fixture's
vocabulary. Deterministic tests keep the contract; the live probe
finds the vocabulary you didn't know you were missing. RED-first still
holds — the live findings became fixture canaries before the fix.

**Seed:** should the API-discovery family grow a standing
`live-vocabulary-probe` ritual — a manual, non-CI script that runs each
boundary tool against one rotating real site and diffs the
classification/redaction decisions against expectations — catching
vendor-vocabulary drift before consumers do?
