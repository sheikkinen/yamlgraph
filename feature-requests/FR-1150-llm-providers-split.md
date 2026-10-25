# Feature Request: FR-1150 Split llm_providers.py under the size gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Round 2 judged (approved with revisions); R-1..R-5 folded, in enforcement
**Requested:** 2026-10-25
**First consumer / first event:** the next `.py` commit that touches
`yamlgraph/utils/llm_providers.py` (FR-1148's owed tests and the effort
setting, the two PRs queued after this one), which today rides on the
temporary `llm_providers.py: 473` BASELINE entry of FR-1149.
**Research:** in-body Alternatives Considered table (FR-889 style): solution
classes with precedent, and the preserved dissent; no `research.sh` run, the
change is a move of existing code with no behaviour change.
**Prior art:** [FR-1148-anthropic-thinking-off.md](FR-1148-anthropic-thinking-off.md)
— added the thinking-off rule that pushed the file to 473 lines and owes
this split (AC-08, R-6); this FR does that split only, not FR-1148's owed
tests and docs;
[FR-1149-size-gate-windows-paths.md](FR-1149-size-gate-windows-paths.md)
— added the temporary entry this FR removes, and parked the tautology this
FR repairs;
[FR-263-azure-openai-provider.md](FR-263-azure-openai-provider.md) — whose
change extracted `llm_providers.py` from `llm_factory.py` for the same gate
(the module docstring), the same kind of move;
[FR-998-anthropic-constrained-structured-output.md](FR-998-anthropic-constrained-structured-output.md)
— its review #599 P2 refused moving the provider-identity predicates out of
`llm_providers.py` ("source-of-truth drift", FR-998:159, :174) and froze them
there (AC-04); the cure it chose was to move *other* code out
(`llm_bounds.py`). This FR follows that precedent: the predicates stay;
[FR-1063-map-compiler-package-split.md](FR-1063-map-compiler-package-split.md)
— REJECTED: a move-only split for size pressure, refused for research of
four variants of one refactor without precedent or the graph-fit answer.
Same class as this FR; distinguished by (a) the target module is already
specified and judged under FR-1148 R-6/AC-08, so the chosen solution class
is not this FR's invention; (b) one contiguous 50-line region moves to one
module, with no typed return, no new record type and no consumer-signature
change, against FR-1063's five modules and shared normalisation; (c) FR-1063
judgement R-2's enumerate-importers duty is discharged under Proposed
Solution below.

## Summary

`yamlgraph/utils/llm_providers.py` is 473 lines against the 450-line gate,
held only by FR-1149's temporary BASELINE entry. This FR moves the Anthropic
thinking rule and the Anthropic factory that applies it into
`yamlgraph/utils/anthropic_thinking.py`, with no change in behaviour, names
or messages, removes the temporary entry, and repairs the size-gate test so
a stale entry like it can never stay unnoticed.

## Value Statement

Maintainers of `llm_providers.py` get the file back under the gate without
an exception, and the gate's own test catches a BASELINE entry that outlives
its reason.

## Problem

1. `wc -l yamlgraph/utils/llm_providers.py` is 473; `LIMIT` is 450.
2. `scripts/size_gate.py` holds it with `"yamlgraph/utils/llm_providers.py": 473`,
   a temporary entry (FR-1149, operator decision of 2026-10-25) that this
   split must remove.
3. `test_baseline_is_shrink_only_and_honest` would not notice if the entry
   stayed after the split. Its last clause,
   `assert actual > size_gate.LIMIT or allowed >= actual`, is always true
   once `actual <= allowed` has passed (FR-1149's parked note). A 425-line
   `llm_providers.py` with its 473 entry left in place passes the test.

## Ideal Result

`llm_providers.py` is under 450 lines with no BASELINE entry; every name and
message importable from it today is still importable from it and behaves the
same; and `test_baseline_is_shrink_only_and_honest` fails for any BASELINE
entry whose file is at or under `LIMIT`.

## Planned Operations

```yaml
probes:
  - "wc -l of both modules after the move"
  - "git diff --stat c1db2321..HEAD -- yamlgraph/utils/llm_providers.py before the move — empty is the precondition for the anchor (R-2)"
  - "byte-identity of the moved region against llm_providers.py:28-77 at c1db2321 (a script, output pasted)"
  - "python scripts/hedging_check.py yamlgraph scripts --strict before and after the move (R-3)"
  - "the repaired honesty test with the 473 entry left in place, after the move — must fail (RED witness)"
  - "pytest on the tests that reach the moved names, before and after"
branches:
  - "a moved name is imported or patched from llm_providers somewhere not listed below → keep it importable there and record the site"
  - "ruff F401 flags a same-name re-export → stop and report; no noqa"
  - "the anchor diff is non-empty → re-anchor AC-02 to the HEAD the move is made from, record both SHAs"
  - "a hedging finding exists in llm_providers.py after the move → re-key the ALLOWLIST entry and the CONF-352 anchor (FR-998:166); none → record it, touch neither"
delegations:
  - "judge.sh: round 2 (JUDGE_BACKEND=claude)"
waits:
  - "judge"
  - "CI"
  - "producer's reviewer, then merge"
commands:
  - JUDGE_BACKEND=claude bash scripts/judge.sh feature-requests/FR-1150-llm-providers-split.md
  - pytest -q --no-cov tests/unit/test_thinking_budget.py tests/unit/test_fr680_provider_registry.py tests/unit/test_fr708_client_timeout.py tests/unit/test_fr710_deadline_floors.py tests/unit/test_fr998_structured_output.py .github/hooks/tests/test_size_gate.py
  - pytest tests/unit/ -q --no-cov -m "not slow" -n auto
  - PYTHONUTF8=1 python scripts/size_gate.py
  - lint-imports
  - python scripts/req_coverage.py --strict
  - PYTHONUTF8=1 pre-commit run --files <changed files>
```

## Proposed Solution

One move and one repair. No logic, docstring meaning, name or message
changes in moved code.

1. **`yamlgraph/utils/anthropic_thinking.py`** (FR-1148 R-6 names this
   module): `yamlgraph/utils/llm_providers.py:28-77` at `c1db2321`, moved
   byte-identically — `_ANTHROPIC_THINKING_ALWAYS_ON`,
   `_anthropic_thinking_off` and `_create_anthropic_llm`. The factory moves
   with the rule because it is the rule's only caller
   (`llm_providers.py:68`) and the place the thinking setting reaches the
   request; the effort setting, two PRs later, lands in the same function,
   so the module that grows is this one, not `llm_providers.py`. The error
   text stays
   `"thinking_budget=0: thinking cannot be turned off on {model}; omit thinking_budget for this model"`.
   The new module imports `BaseChatModel` and `_bounded` at module level, as
   `llm_providers.py` does; `langchain_anthropic` stays imported inside the
   factory.
2. **`yamlgraph/utils/llm_providers.py`** imports the three names back:
   `_create_anthropic_llm` for `_PROVIDER_FACTORIES` (a real use), and
   `_anthropic_thinking_off` and `_ANTHROPIC_THINKING_ALWAYS_ON` in ruff's
   explicit re-export form (`from … import x as x`), so both stay importable
   from `llm_providers` (the producer's constraint, relayed: "keep the old
   names and error text"). Importers today: none outside `llm_providers.py`
   for any of the three (grep over `yamlgraph/`, `tests/`, `scripts/`);
   `_PROVIDER_FACTORIES["anthropic"]` is reached by
   `test_fr680_provider_registry.py`, `test_fr708_client_timeout.py` and
   `test_fr710_deadline_floors.py` through the registry, which keeps the same
   object. No test patches a name inside `llm_providers` that moves.
3. **The FR-998 predicates do not move** (FR-998 review #599 P2).
4. **`scripts/size_gate.py`**: the temporary entry and its comment removed.
   **`.github/hooks/tests/test_size_gate.py`**: the tautological disjunct
   `or allowed >= actual` goes; the final assertion becomes
   `assert actual > size_gate.LIMIT` with a message naming `rel` and
   `actual` and containing `stale baseline entry`, laid out as
   `ruff format` chooses.
   Every other entry's actual length is above `LIMIT` today: 807, 675, 549,
   615, 592, 589, 510, 501.
5. `llm_providers.py`'s module docstring says the Anthropic thinking rule and
   factory live in `anthropic_thinking.py`; `anthropic_thinking.py`'s
   docstring names FR-1148 as the rule's owner and FR-1150 as the move.

Arithmetic: 473 − 50 moved − 2 blank lines + 5 import lines ≈ 426.

**Commits, one concern each (R-6):**

1. `refactor(utils)`: the move, the re-exports, both docstrings, and the two
   identity tests (AC-03, AC-04). The size gate passes (the 473 entry is
   still present), and the old tautological test passes.
2. `test(hooks)` RED: the repaired assert alone, with the 473 entry still
   present. The test fails naming `llm_providers.py`; the output is pasted
   verbatim into Implementation status; `SKIP=pytest` with its reason in
   the PR body.
3. `chore(hooks)` GREEN: the 473 entry and its two comment lines removed.

**PR title (R-7):** `refactor(utils): FR-1150 split llm_providers.py under the size gate`.
No `changelog/unreleased/` fragment: the change is behaviour-free and the
changelog gate keys on `feat`/`fix` titles (`commitlint.yml:165-188`).

**FR-1148 hand-off (R-9.2):** a dated addendum in FR-1148, not an edit of its
Follow-up-owed paragraph (a committed written-before artifact is amended by
addendum only): FR-1150 performs the module move and removes FR-1149's
entry. Of FR-1148 AC-08 this closes the module holding the rule,
`llm_providers.py` ≤ 450, `lint-imports` and `pre-commit`; the
`_THINKING_OFF_UNSUPPORTED` rename and every test and doc clause of
AC-01..AC-07, AC-10 and AC-11 stay owed to FR-1148's next PR. FR-1150 adds
unit assertions of `_anthropic_thinking_off`'s three outcomes and of its
error text under `REQ-YG-083`; FR-1148's AC-01..AC-03 payload-level tests,
AC-06's 14-id table and AC-07's amendment remain owed and are not covered
by them.

## Alternatives Considered

**is_this_a_graph:** no — a mechanical code move with no per-item model
judgement.

| # | Solution class | Precedent | Disposition |
|---|---|---|---|
| A | **Extract the Anthropic thinking rule and its factory into `anthropic_thinking.py`** (chosen) | FR-263 extracted `llm_providers.py` from `llm_factory.py` for this gate; FR-998 P2 moved non-frozen code (`llm_bounds.py`) to make room; FR-1148 R-6 names the module | One region, one module, the module the next two PRs extend |
| A.1 | Rule only, no factory | — | Rejected: ≈ 453 lines, still over 450 |
| A.2 | Rule plus the FR-998 predicates to `anthropic_capability.py` (round 1's plan) | anti-precedent: FR-998 review #599 P2 refused the predicates leaving `llm_providers.py` | Rejected in round 2: repeats a refused move; its façade also made `test_predicates_live_in_llm_providers` pass by shape (round 1 R-2) |
| B | Keep one file, widen the gate (permanent entry or higher `LIMIT`) | FR-889 introduced the ratchet; anti-precedent `infrastructure_self_exempt` | Rejected: the gate exempts the file it exists to hold |
| C | Move the FR-998 predicates into `structured_output.py`, their only production consumer | anti-precedent: FR-998 P2 | Rejected: same refusal as A.2 |
| D | Split `llm_providers.py` by provider, one module per factory | anti-precedent: FR-1063's five-module split, REJECTED | Rejected: twelve modules for a 23-line overrun |
| E | Make `yamlgraph/utils/providers/` a package with a re-exporting `__init__` | anti-precedent: FR-1063 | Rejected: widest import surface; every registry test and patch target moves |
| F | Move the dispatch registry (`_PROVIDER_FACTORIES`, `_THINKING_PROVIDERS`, `dispatch_provider`) to its own module | — | Rejected: `llm_factory.py:17` and the import or patch sites in `test_fr230_google_vertex_thinking.py` (four `patch.dict` targets), `test_fr680_provider_registry.py`, `test_fr708_client_timeout.py` and `test_fr710_deadline_floors.py` would move or need re-exports |

**Preserved dissent:** the façade. Re-exporting the two thinking names from
`llm_providers` gives one object two import paths, against the spirit of
Commandment 8 (no shims). The other side: the producer requires the old
names importable from `llm_providers`, and no test or module needs the new
path. The re-export won on that requirement; if the operator drops it, the
fold is to delete the two `as` lines (nothing imports them from
`llm_providers` today).

## Acceptance Criteria

- [ ] AC-01: `wc -l yamlgraph/utils/llm_providers.py` ≤ 450 and `BASELINE`
  holds no `yamlgraph/utils/llm_providers.py` key;
  `PYTHONUTF8=1 python scripts/size_gate.py` exits 0 with no `✗` line
  (output pasted into Implementation status).
- [ ] AC-02: `yamlgraph/utils/anthropic_thinking.py` exists; its moved region
  is byte-identical to `llm_providers.py:28-77` at `c1db2321` (a script's
  output pasted); `git diff --stat c1db2321..HEAD -- yamlgraph/utils/llm_providers.py`
  was empty before the move (pasted, round 2 R-2); it has no module-level `langchain_anthropic` or
  `anthropic` import.
- [ ] AC-03: `_anthropic_thinking_off`, `_ANTHROPIC_THINKING_ALWAYS_ON` and
  `_create_anthropic_llm` import from `yamlgraph.utils.llm_providers` and are
  the same objects (`is`) as in `anthropic_thinking`;
  `_PROVIDER_FACTORIES["anthropic"] is anthropic_thinking._create_anthropic_llm`.
  Test in `tests/unit/test_thinking_budget.py`, `@pytest.mark.req("REQ-YG-083")`.
- [ ] AC-04: `_anthropic_thinking_off("claude-opus-5-5")` raises `ValueError`
  with exactly `thinking_budget=0: thinking cannot be turned off on claude-opus-5-5; omit thinking_budget for this model`;
  `_anthropic_thinking_off("claude-sonnet-5-5") == {"type": "between_tools"}`;
  `_anthropic_thinking_off("claude-haiku-5-5") == {"type": "disabled"}`.
  Same file and marker as AC-03.
- [ ] AC-05: `is_anthropic_chat_model` and
  `is_anthropic_unsupported_structured_output` are still defined in
  `llm_providers.py`; `test_fr998_structured_output.py` is unchanged and
  passes.
- [ ] AC-06: in `test_baseline_is_shrink_only_and_honest`, the loop body's
  final assertion is `assert actual > size_gate.LIMIT` with a message
  interpolating `rel` and `actual` and containing `stale baseline entry`;
  `or allowed >= actual` appears nowhere in the file;
  `ruff format --check .github/hooks/tests/test_size_gate.py` exits 0;
  `LIMIT`, `WARN`, `BYTE_CEILING` and every other `BASELINE` entry
  unchanged (round 2 R-1).
- [ ] AC-07: RED witness — at commit 2 (repaired assert, 473 entry present)
  `pytest .github/hooks/tests/test_size_gate.py -q --no-cov` fails naming
  `llm_providers.py`; the output is pasted verbatim; the three-commit order
  is visible in `git log`.
- [ ] AC-08: the targeted pytest command of Planned Operations passes at the
  final commit; the fast unit suite passes in CI.
- [ ] AC-09: `lint-imports` exits 0; `python scripts/req_coverage.py --strict`
  exits 0; `PYTHONUTF8=1 pre-commit run --files <changed files>` passes;
  `python scripts/hedging_check.py yamlgraph scripts --strict` before and
  after the move gives identical finding sets, both in Implementation
  status (round 2 R-3).
- [ ] AC-10: both module docstrings updated as Proposed Solution item 5 says.
- [ ] AC-11: the PR title is as stated above, with no changelog fragment.
- [ ] AC-12: FR-1148 carries the dated hand-off addendum, including which
  assertions FR-1150 adds and which of FR-1148's tests stay owed
  (round 2 R-4).
- [ ] AC-13: the ruff re-export probe's command and verbatim output are in
  the FR (round 2 R-5, below).
- [ ] AC-13a: no new `# noqa`; no `--no-verify`; no `Co-authored-by` trailer;
  every `SKIP=` recorded with its commit and reason in the PR body.
- [ ] AC-14: a `docs/diary/` reflection with a **Seed:**.

## Judgement fold (2026-10-25)

Round 1, `JUDGE_BACKEND=claude bash scripts/judge.sh`: APPROVED WITH
REVISIONS ([FR-1150-llm-providers-split.judgement.md](FR-1150-llm-providers-split.judgement.md)).

| # | Revision | Where folded |
|---|---|---|
| R-1 | Disposition FR-1063; `is_this_a_graph`; solution classes with precedent; dissent | Prior art; Alternatives Considered |
| R-2 | The FR-998 locality test would pass by re-export only | Moot: the predicates no longer move (redesign below); AC-05 |
| R-3 | Drop the `_ANTHROPIC_THINKING_ALWAYS_ON` re-export; drop the alias clause | Alias clause dropped. The re-export is **kept**, in ruff's `as` form: the producer's requirement that the old names stay importable from `llm_providers` decides it, and the form is not an F401 failure: `ruff check --config pyproject.toml` on a probe file flags `from os import sep` (unused-import) and not `from os.path import join as join` or `from os.path import _joinrealpath as _joinrealpath`. AC-09 runs ruff; AC-13 forbids `noqa` |
| R-4 | Line ranges, base SHA, arithmetic, importers | Proposed Solution 1–2; AC-02 |
| R-5 | Tests named, with markers | AC-03, AC-04 |
| R-6 | Three commits, RED witness verbatim | Proposed Solution, Commits; AC-07 |
| R-7 | PR title and changelog consequence | Proposed Solution; AC-11 |
| R-8 | Docstrings; lazy-import rule | Proposed Solution 5; AC-02, AC-10 |
| R-9 | Verification commands; FR-1148 hand-off | Planned Operations; AC-09; AC-12 (by dated addendum, not an edit of FR-1148's paragraph) |

**Redesign after round 1:** reading FR-998 for R-2 showed its review #599
P2 had already refused moving the predicates out of `llm_providers.py`. The
second move is now the Anthropic factory, not the predicates; solution class
A is unchanged, its sub-row changed. Round 1's frozen scope (D-2, D-6) no
longer applies, so this fold goes to a round-2 judgement before any code.

## Judgement fold, round 2 (2026-10-25)

Round 2, `JUDGE_BACKEND=claude bash scripts/judge.sh`: APPROVED WITH
REVISIONS, the fold needing no further round. Folded:

| # | Revision | Where folded |
|---|---|---|
| R-1 | AC-06 must not pin a line `ruff format` rewrites | Proposed Solution 4; AC-06 |
| R-2 | Prove the anchor `c1db2321` is the tree moved from | Planned Operations; AC-02; probe below |
| R-3 | Probe the line-keyed CONF-352 confession | Planned Operations; AC-09; probe below |
| R-4 | The FR-1148 addendum says what the new tests close | Proposed Solution, hand-off; AC-12 |
| R-5 | The ruff re-export probe as output | Probe below; AC-13 |

## Implementation status

**R-2 probe,** before the move, at `e1a253fd`:

```text
$ git diff --stat c1db2321..HEAD -- yamlgraph/utils/llm_providers.py
(no output)
```

The anchor holds: `c1db2321` is the file the move is made from.

**R-3 probe,** before the move:

```text
$ PYTHONUTF8=1 python scripts/hedging_check.py yamlgraph scripts --strict
No hedging patterns found.
exit 0
$ grep -c fallback yamlgraph/utils/llm_providers.py
0
```

No finding exists in `llm_providers.py`: CONF-352 (`hedging_check.py:81`,
`docs/confessions.md` `#L342`) already points at nothing. This FR touches
neither file. **Parked (not this FR):** the dead CONF-352 entry, and the
gap that `_validate_allowlist_for_scan` never checks an ALLOWLIST key still
has a finding, belong to a separate FR.

**R-5 probe,** the pinned hook (`ruff-pre-commit` `rev: v0.16.0`,
`.pre-commit-config.yaml:8`), on a probe file:

```text
$ cat tmp/rufftest/probe.py
from os.path import join as join
from os.path import _joinrealpath as _joinrealpath
from os import sep
$ PYTHONUTF8=1 pre-commit run --config .git/pre-commit-config.windows.yaml ruff-check --files tmp/rufftest/probe.py
ruff check...............................................................Failed
- hook id: ruff-check
- exit code: 1

Found 2 errors (2 fixed, 0 remaining).
$ cat tmp/rufftest/probe.py
from os.path import _joinrealpath as _joinrealpath
from os.path import join as join
```

The two errors are the unsorted block and the unused `from os import sep`;
`--fix` removed only that line and kept both same-name `as` imports.
