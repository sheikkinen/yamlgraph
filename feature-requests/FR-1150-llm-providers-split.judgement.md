# Judgement: FR-1150 Split llm_providers.py under the size gate (round 2)

**Prior art:** [FR-1150-llm-providers-split.md](FR-1150-llm-providers-split.md) — the FR this judgement rules on, not precedent; dismissed. [FR-1063-map-compiler-package-split.md](FR-1063-map-compiler-package-split.md) — REJECTED move-only split; dispositioned in the FR's Prior art. [FR-1057-prompt-template-dialect-split.md](FR-1057-prompt-template-dialect-split.md) — splits a prompt dialect, not a provider module; dismissed. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `JUDGE_BACKEND=claude scripts/judge.sh`, 2026-10-25, round 2; round 1 is in this file's git history at e1a253fd.)

**Verdict:** APPROVED WITH REVISIONS — the round-1 redesign is correct and the chosen move is now anchored in evidence I independently reproduced (FR-998:159/:174 really do refuse moving the predicates; the three moved names have no importer outside `llm_providers.py`; the arithmetic lands at 426; the repaired assert is safe against all eight remaining BASELINE entries), but AC-06 pins a 105-character assert to a line number that `ruff format` will rewrite, the byte-identity anchor `c1db2321` is never shown to equal the tree the move is made from, and the move shifts `llm_providers.py`'s line-keyed hedging confession by 50 lines with no probe — authority activates the moment R-1..R-5 are folded, and the fold needs no further judgement round.

**Reviewed against:** `feature-requests/FR-1150-llm-providers-split.md`; `feature-requests/FR-1150-llm-providers-split.judgement.md` (round 1); `feature-requests/FR-1148-anthropic-thinking-off.md` (cited clauses: :149-157, :204-224, :258-266, :280, :333, :345-346); `feature-requests/FR-998-anthropic-constrained-structured-output.md` (cited lines :150-181); `yamlgraph/utils/llm_providers.py` (full); `yamlgraph/utils/llm_bounds.py` (imports); `yamlgraph/utils/llm_factory.py` (import site); `yamlgraph/utils/structured_output.py` (import site); `scripts/size_gate.py`; `scripts/hedging_check.py`; `docs/confessions.md` (CONF-352); `.github/hooks/tests/test_size_gate.py`; `tests/unit/test_fr998_structured_output.py:182-201`; `tests/unit/test_thinking_budget.py` (markers); `tests/unit/test_direct_import_scan.py:130-154`; repo-wide `*.py` grep for the three moved names and for `llm_providers`; line counts of `scripts/migrate_capabilities.py` (501), `scripts/vscode/now.py` (510), `.github/hooks/tests/test_main_write_guard.py` (549); `pyproject.toml`; `.pre-commit-config.yaml`; `.importlinter`; `.github/workflows/commitlint.yml`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

Round 2 for this FR file. `FR-1150-llm-providers-split.judgement.md` holds one `**Verdict:**` line today; promoting this draft makes two, which **arms the FR-1022 round sentinel**: every later `scripts/judge.sh` run against this file returns the fixed REJECTED without a model call. The revisions below are therefore written to be folded and enforced directly — none of them requires coming back.

Not consumed: no chat transcript, no working notes, no uncommitted artifact. `git` was unavailable in this session (Bash disabled), so SHA-level claims were checked against the working tree and the committed record only; R-2 exists because of exactly that gap.

## What is sound

- **The round-1 redesign is correct, and for the reason it states.** FR-998:159 records the review's refusal verbatim — the predicates in a new `llm_provider_identity.py` were "source-of-truth drift", and the cure was to move *other* code out (`llm_bounds.py`) — and FR-998:174 repeats it as P2. Round 1's plan A.2 would have repeated a refused move. Dropping it and moving the Anthropic factory instead is the right correction, and the FR says so openly (FR-1150:248-252) instead of quietly reshaping the table.
- **The moved region is exactly what the FR says it is.** `llm_providers.py:28-77` in the tree is the comment at :28, `_ANTHROPIC_THINKING_ALWAYS_ON` at :29, `_anthropic_thinking_off` at :32-47 and `_create_anthropic_llm` at :50-77 — 50 contiguous lines ending at the factory's closing paren, with nothing of another concern caught in the range.
- **The arithmetic checks out, which round 1's did not.** 473 − 50 moved = 423; the removal leaves four consecutive blanks between `llm_providers.py:25`'s section comment and `:80`'s next `def`, so two go (421); a five-line `from yamlgraph.utils.anthropic_thinking import (...)` block returns it to 426. "≈ 426" (FR-1150:140) is right.
- **The move is genuinely behaviour-free, including the parts the FR does not claim.** Lines 28-77 touch no module-level name of `llm_providers.py` except `BaseChatModel` (:14) and `_bounded` (:18) — in particular they never call `logger` (:23), so the move cannot rename a log channel; `tests/unit/test_fr1056_deepseek_thinking.py:56` asserts on the `yamlgraph.utils.llm_providers` logger and is untouched because the DeepSeek factory stays. `llm_bounds.py` imports nothing from `yamlgraph`, so `llm_providers → anthropic_thinking → llm_bounds` introduces no cycle, and both modules sit inside `yamlgraph.utils`, a non-independent sibling in `.importlinter:14` — `lint-imports` has nothing to say about the new edge.
- **The importer enumeration is true.** My own repo-wide `*.py` grep for the three names returns only `llm_providers.py` itself (:29, :32, :40, :50, :60, :68, :371) and a copy under `.claude/worktrees/phased-summary-pattern/`, which is a separate working tree. Every `llm_providers` patch target in the suite — `test_fr230_google_vertex_thinking.py` (four `patch.dict` calls), `test_race_node.py:1552-1559`, `test_fr680/708/710` — reaches `_PROVIDER_FACTORIES` or a non-moving factory, all of which stay. FR-1063 judgement R-2's enumerate-importers duty is discharged.
- **The tautology diagnosis and its repair are both exact.** `.github/hooks/tests/test_size_gate.py:122` proves `actual <= allowed`, so `:123`'s `allowed >= actual` disjunct can never be false — the clause is unfalsifiable, as FR-1150:61-65 says. I counted the actual length of the three BASELINE entries closest to the limit: `scripts/migrate_capabilities.py` 501, `scripts/vscode/now.py` 510, `.github/hooks/tests/test_main_write_guard.py` 549 (allowed 550). Every remaining entry is above `LIMIT`, so the repaired assert goes green once the temporary entry is gone and red for nothing this FR does not own.
- **The RED witness is constructible in the stated order.** At commit 1 the file is 426 against `allowed = 473`, so `test_repo_passes_the_widened_gate` (:109-111) and the old `:123` both stay green; at commit 2 the repaired assert is the only thing red, and it names `llm_providers.py`; at commit 3 the entry goes and 426 ≤ 450 carries the gate. The three-commit split is the only order that produces a real RED.
- **The ruff rebuttal of round-1 R-3 holds on this repo's config, not just on a probe.** `pyproject.toml:186-198` selects `F` but no `PL` prefix other than `PLW1514`, so `PLC0414` (useless-import-alias) cannot fire on `from … import x as x`, and F401 exempts the redundant-alias re-export form. Refusing half of R-3 with evidence, and saying plainly in the fold table that it was refused (FR-1150:240), is the right way to disagree with a judgement.
- **The cross-FR ledger stays honest.** The FR names what it does *not* close of FR-1148 AC-08 (FR-1150:157-163) and chooses an addendum over editing a written-before artifact. `refactor` is an accepted PR type (`commitlint.yml:41`) and the changelog gate fires only on `feat`/`fix` titles (`commitlint.yml:165-170`), so AC-11's no-fragment conclusion is correct.

## Required revisions

### R-1: AC-06 pins a line that `ruff format` will not leave alone

AC-06 (FR-1150:213-215) requires `.github/hooks/tests/test_size_gate.py` **line 123** to read

```
        assert actual > size_gate.LIMIT, f"stale baseline entry: {rel} is {actual} lines, not over LIMIT"
```

That statement is 105 characters. `ruff-format` runs in pre-commit (`.pre-commit-config.yaml:14`) at `line-length = 88` (`pyproject.toml:178`), so the formatter will rewrite it across several lines — `E501` being ignored (`pyproject.toml:199-201`) does not help, because the formatter is a separate hook from the linter. AC-06 and AC-09 (`pre-commit run --files …` passes) therefore cannot both be satisfied, and the surviving statement will not be on line 123 either.

Fold — replace AC-06 with a content-based criterion and let the formatter choose the layout:

> AC-06: in `.github/hooks/tests/test_size_gate.py::test_baseline_is_shrink_only_and_honest`, the loop body's final assertion is `assert actual > size_gate.LIMIT` carrying a failure message that interpolates `rel` and `actual` and contains the words `stale baseline entry`; the disjunct `or allowed >= actual` no longer appears anywhere in the file; `ruff format --check .github/hooks/tests/test_size_gate.py` exits 0; `LIMIT`, `WARN`, `BYTE_CEILING` and every other `BASELINE` entry are unchanged.

Delete the words "line 123" from AC-06 and from Proposed Solution item 4; nothing else in the FR depends on the number.

### R-2: Prove the byte-identity anchor is the tree being moved from

AC-02 (FR-1150:195-198) anchors byte-identity to `llm_providers.py:28-77` **at `c1db2321`**, a SHA the FR knows only through `scripts/size_gate.py:46`'s comment. The branch head is several commits later, and round 1's judgement anchored the same region to a different SHA (`431c0ef8`). Nothing in the FR asserts the file is unchanged between the anchor and the commit the move is made from, so a byte-identity check against `c1db2321` could pass while the moved text differs from what was in the tree a moment earlier — the whole "no behaviour change" claim rests on an unverified equality. (I read `:28-77` in the working tree and it is the three names in the stated order, which is consistent with the anchor; I could not run `git` in this session to close it.)

Fold, into Planned Operations `probes:` and into AC-02:

1. Before the move, run and paste `git diff --stat <anchor-sha>..HEAD -- yamlgraph/utils/llm_providers.py`. Empty output is the precondition for using the anchor.
2. If that output is non-empty, re-anchor AC-02 to the branch `HEAD` the move is made from, record both SHAs and the diff in the FR, and re-state the line range against that file.
3. Record the SHA actually used in AC-02 as a literal (not "the recorded base SHA"), and paste the identity script's output together with the `git diff --stat` output in Implementation status.

### R-3: Probe the line-keyed hedging confession that this move shifts by 50 lines

`scripts/hedging_check.py:81` keys an allowlist entry by **line number** — `"yamlgraph/utils/llm_providers.py:342": "CONF-352"` — and `docs/confessions.md:1329-1333` anchors the same confession at `#L342`. Removing `:28-77` shifts every line below it by −50, so L342 becomes L292. `hedging-check` runs `--strict` over `yamlgraph scripts` on any `.py` change with `pass_filenames: false` (`.pre-commit-config.yaml:212-218`), and AC-09 depends on it passing. FR-998:166 is this repo's own precedent for the duty: a change that moved three confessions **by one line** updated both the `hedging_check.py` ALLOWLIST and the `docs/confessions.md` anchors, and verified the finding set was otherwise identical before and after against a worktree of the RED commit. FR-1150 moves one by fifty and says nothing.

One complication the fold must handle rather than assume away: `scripts/hedging_check.py`'s detector fires only on the literal token `fallback` (`:86-87`, `:157-169`, `:205-224`), and that token does not appear anywhere in `llm_providers.py` today — so CONF-352 may already point at nothing. `_validate_allowlist_for_scan` (`:267-300`) only cross-checks ALLOWLIST against `docs/confessions.md`; it never checks that the finding still exists, so the gate stays green either way and cannot answer the question for you.

Fold:

1. Add to Planned Operations `probes:`: `python scripts/hedging_check.py yamlgraph scripts --strict`, run before and after the move, with both finding sets recorded in Implementation status.
2. Add to `branches:`: if a finding exists in `llm_providers.py` after the move, re-key both `scripts/hedging_check.py`'s ALLOWLIST entry and the `docs/confessions.md` CONF-352 anchor to the shifted line, per FR-998:166 — and add those two files to the deliverables. If the probe shows no finding in the file at all, state that in the FR, leave both artifacts untouched, and name the dead CONF-352 entry as a parked observation for a separate FR.
3. Add to AC-09: the before/after hedging finding sets are identical modulo the recorded shift.

### R-4: The FR-1148 addendum must say what the new tests close

The hand-off (FR-1150:157-163) lists what closes of FR-1148 AC-08 and what stays owed, but omits that AC-04 of this FR adds direct unit assertions of the rule's three outcomes to `tests/unit/test_thinking_budget.py`. FR-1148's own AC-01..AC-03 and AC-06 are payload-level assertions through `create_llm` and the 14-id table (FR-1148:208-213) — adjacent but not the same — and FR-1148's enforcer, reading only the addendum, cannot tell which exist.

Fold: add one sentence to the dated addendum and to FR-1150's hand-off paragraph — FR-1150 adds unit assertions of `_anthropic_thinking_off`'s three outcomes and of the error text under `REQ-YG-083`; FR-1148's AC-01..AC-03 payload-level tests, AC-06's 14-id table and AC-07's amendment remain owed and must not be assumed covered by them.

### R-5: Record the ruff re-export probe as output, not as a sentence

FR-1150:240 rebuts round-1 R-3 by describing a ruff probe ("flags `from os import sep` and not `from os.path import join as join`") without showing it. The producer-facing façade — two names re-exported from `llm_providers` with no importer anywhere — survives only if that exemption holds under this repo's config at the pinned ruff version, and AC-09 is the thing that would discover otherwise, at enforcement time.

Fold: paste the probe's command and verbatim output into the FR (Alternatives Considered or Implementation status), naming the ruff version from `.pre-commit-config.yaml`'s pin. The existing branch — "ruff F401 flags a same-name re-export → stop and report; no noqa" — stays as written and is the correct stop.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/utils/anthropic_thinking.py` — new; `llm_providers.py:28-77` moved byte-identically at the SHA fixed by R-2; module-level `BaseChatModel` and `_bounded` imports; docstring naming FR-1148 as the rule's owner and FR-1150 as the move |
| D-2 | `yamlgraph/utils/llm_providers.py` — the 50-line region removed, the three names imported back (`_create_anthropic_llm` plain, the other two in `import x as x` form), module docstring updated |
| D-3 | `scripts/size_gate.py` — the `"yamlgraph/utils/llm_providers.py": 473` entry and its two comment lines removed (`:46-48`) |
| D-4 | `.github/hooks/tests/test_size_gate.py` — the tautological disjunct replaced per R-1 |
| D-5 | `tests/unit/test_thinking_budget.py` — AC-03 identity and AC-04 message/mapping assertions, `@pytest.mark.req("REQ-YG-083")` |
| D-6 | `feature-requests/FR-1150-llm-providers-split.md` — R-1..R-5 folded, round-2 fold table, Implementation status with the verbatim RED witness and the pasted probe outputs |
| D-7 | `feature-requests/FR-1148-anthropic-thinking-off.md` — the dated addendum only (R-4), appended; no edit to its existing paragraphs |
| D-8 | `docs/diary/` — one reflection with a **Seed:** |
| D-9 | *Conditional on R-3's probe only*: `scripts/hedging_check.py` ALLOWLIST key and `docs/confessions.md` CONF-352 anchor, re-keyed to the shifted line. If the probe shows no finding, neither file is touched. |

**Not authorized:** moving `is_anthropic_chat_model`, `is_anthropic_unsupported_structured_output`, `_structured_error_message` or the three term tuples out of `llm_providers.py` (FR-998 review #599 P2, FR-998:159/:174); renaming `_ANTHROPIC_THINKING_ALWAYS_ON` to `_THINKING_OFF_UNSUPPORTED` or adding any alias for it; any character change inside the moved region — message text, prefix tuple, docstrings, reflow; any edit to `_create_*_llm` bodies, `dispatch_provider`, `_PROVIDER_FACTORIES`, `_THINKING_PROVIDERS`, `llm_bounds.py`, `llm_factory.py` or `structured_output.py`; retargeting any existing import at the new module; editing `tests/unit/test_fr998_structured_output.py`; changing `LIMIT`, `WARN`, `BYTE_CEILING`, `SCAN_DIRS` or any other `BASELINE` entry, or adding one; splitting `llm_providers.py` by provider or into a `providers/` package; deleting the CONF-352 entry or any other confession; FR-1148's owed payload-level tests, 14-id table, AC-07 amendment, CAP-28/`ARCHITECTURE.md` regeneration, `reference/graph-yaml.md` edits and the `effort` setting; any `# noqa`; any `changelog/unreleased/` fragment; any file under `.claude/worktrees/`, which is a separate working tree containing its own copy of every file named here.

## Revised acceptance criteria

- [ ] AC-01: `wc -l yamlgraph/utils/llm_providers.py` ≤ 450 and `scripts/size_gate.py`'s `BASELINE` holds no `yamlgraph/utils/llm_providers.py` key; `PYTHONUTF8=1 python scripts/size_gate.py` exits 0 with no `✗` line (output pasted into Implementation status).
- [ ] AC-02: `yamlgraph/utils/anthropic_thinking.py` exists and its moved region is byte-identical to `yamlgraph/utils/llm_providers.py:28-77` at the literal SHA recorded in the FR; `git diff --stat <that SHA>..HEAD -- yamlgraph/utils/llm_providers.py` was empty before the move, or the re-anchoring of R-2.2 is recorded; both outputs pasted. The module has no module-level `langchain_anthropic` or `anthropic` import.
- [ ] AC-03: `_anthropic_thinking_off`, `_ANTHROPIC_THINKING_ALWAYS_ON` and `_create_anthropic_llm` import from `yamlgraph.utils.llm_providers` and are the same objects (`is`) as in `yamlgraph.utils.anthropic_thinking`; `_PROVIDER_FACTORIES["anthropic"] is anthropic_thinking._create_anthropic_llm`. In `tests/unit/test_thinking_budget.py`, `@pytest.mark.req("REQ-YG-083")`.
- [ ] AC-04: `_anthropic_thinking_off("claude-opus-5-5")` raises `ValueError` whose message is exactly `thinking_budget=0: thinking cannot be turned off on claude-opus-5-5; omit thinking_budget for this model`; `_anthropic_thinking_off("claude-sonnet-5-5") == {"type": "between_tools"}`; `_anthropic_thinking_off("claude-haiku-5-5") == {"type": "disabled"}`. Same file and marker as AC-03.
- [ ] AC-05: `is_anthropic_chat_model` and `is_anthropic_unsupported_structured_output` are still **defined** in `llm_providers.py`; `tests/unit/test_fr998_structured_output.py` is byte-unchanged and passes.
- [ ] AC-06: in `test_baseline_is_shrink_only_and_honest`, the loop body's final assertion is `assert actual > size_gate.LIMIT` with a message interpolating `rel` and `actual` and containing `stale baseline entry`; `or allowed >= actual` appears nowhere in the file; `ruff format --check .github/hooks/tests/test_size_gate.py` exits 0; `LIMIT`, `WARN`, `BYTE_CEILING` and every other `BASELINE` entry unchanged (R-1).
- [ ] AC-07: RED witness — at commit 2 (repaired assert, 473 entry still present) `pytest .github/hooks/tests/test_size_gate.py -q --no-cov` fails naming `llm_providers.py`; the output is pasted verbatim into Implementation status; the three-commit order is visible in `git log`.
- [ ] AC-08: the targeted pytest command of Planned Operations passes at the final commit; `pytest tests/unit/ -q --no-cov -m "not slow" -n auto` passes, or every failure is shown to be untouched by this change against a baseline run of the same command on `main`.
- [ ] AC-09: `lint-imports` exits 0; `python scripts/req_coverage.py --strict` exits 0; `PYTHONUTF8=1 pre-commit run --files <changed files>` passes; `python scripts/hedging_check.py yamlgraph scripts --strict` was run before and after the move and the finding sets are identical modulo the recorded shift, with both sets in Implementation status (R-3).
- [ ] AC-10: `llm_providers.py`'s module docstring says the Anthropic thinking rule and factory live in `anthropic_thinking.py`, and keeps the FR-263 extraction sentence; `anthropic_thinking.py`'s docstring names FR-1148 as the rule's owner and FR-1150 as the move.
- [ ] AC-11: the PR title is `refactor(utils): FR-1150 split llm_providers.py under the size gate`, and no `changelog/unreleased/` fragment is added.
- [ ] AC-12: FR-1148 carries the dated hand-off addendum, including R-4's sentence on which assertions FR-1150 adds and which of FR-1148's tests stay owed.
- [ ] AC-13: the FR records the ruff re-export probe's command and verbatim output (R-5).
- [ ] AC-14: no new `# noqa`; no `--no-verify`; no `Co-authored-by` trailer; every `SKIP=` recorded with its commit and reason in the PR body.
- [ ] AC-15: a `docs/diary/` reflection with a **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is void until R-1..R-5 are folded into the FR with a round-2 fold table. The fold requires no further judgement round — the FR-1022 sentinel is armed by this verdict, and a further `judge.sh` run on this file returns the fixed REJECTED. | GATE |
| C-2 | Behaviour-free: not one character changes inside `llm_providers.py:28-77` as it lands in the new module — no reflow, no docstring rewording, no message edit. A diff that touches the moved text fails AC-02. | GATE |
| C-3 | `scripts/size_gate.py` and `.github/hooks/tests/test_size_gate.py` are enforcement infrastructure and are adversarial input: the human reviewer must confirm the entry removal and the repaired assert before merge. The enforcer may not weaken `LIMIT`, `WARN` or `BYTE_CEILING`, add any `BASELINE` entry, or exempt any path. | GATE |
| C-4 | The FR-998 predicates stay defined in `llm_providers.py`, and `tests/unit/test_fr998_structured_output.py` stays byte-unchanged. If the file must change, stop and report — that is FR-998's frozen boundary, not this FR's. | GATE |
| C-5 | No rename and no alias of `_ANTHROPIC_THINKING_ALWAYS_ON`; it stays FR-1148's owed rename. | GATE |
| C-6 | If a moved name turns out to be imported or patched from `llm_providers` at a site not enumerated in Proposed Solution item 2, keep it importable there and record the site in the FR — never drop an import path silently. | GATE |
| C-7 | RED precedes GREEN in `git log`, one concern per commit; no `--no-verify`; no `Co-authored-by` trailer; each `SKIP=` named with its reason in the PR body. | GATE |
| C-8 | `docs/confessions.md` and `scripts/hedging_check.py` are touched only under R-3's conditional branch, and only to re-key CONF-352. Deleting or re-describing the confession is out of scope. | GATE |
| C-9 | `.claude/worktrees/phased-summary-pattern/` holds its own copy of `llm_providers.py`, the provider tests and `hedging_check.py`. It is a separate working tree: every command and every edit targets `C:/src/yamlgraph` only. Verify the changed-file list before committing. | GATE |
| C-10 | Supervision is separate from execution: the enforcer stops at "ready for supervision". It does not self-certify AC-07's RED witness, does not approve, and does not merge. | GATE |

## Questions for the human (not absorbed)

1. **The façade, kept on your word alone.** The FR re-exports `_anthropic_thinking_off` and `_ANTHROPIC_THINKING_ALWAYS_ON` from `llm_providers` solely because the producer requires the old names importable from there; I confirmed nothing in the tree imports either from `llm_providers`, and ruff will not object. That is one object with two import paths and no consumer for the second — the "no shims, no adapters" clause of Commandment 8, decided by requirement rather than by need. If you drop the requirement, the fold is to delete the two `as` lines and AC-03's exposure clause; nothing else changes.
2. **FR-1149's temporary entry still expires only through this PR.** The `473` BASELINE entry has no mechanical expiry until R-1..R-5 are folded and the third commit lands. If you want the expiry independent of this FR's fold, say so and the entry removal plus the honesty repair can ship as their own small PR ahead of the move.
3. **CONF-352 appears to be already dead, and this FR is not the place to bury it.** The token `fallback` does not appear anywhere in `llm_providers.py`, yet the allowlist and the confession both still point into it at L342, and `hedging_check.py`'s validator cannot notice. R-3 makes FR-1150 record the fact; cleaning it up — and the general gap that a stale allowlist key is invisible to its own gate — belongs to a separate FR, which is a close cousin of the tautology this FR exists to repair.

Authority granted: none at this round. On the fold of R-1..R-5 into `feature-requests/FR-1150-llm-providers-split.md`, the enforcer may move `yamlgraph/utils/llm_providers.py:28-77` byte-identically into a new `yamlgraph/utils/anthropic_thinking.py`, import the three names back (one for use, two as explicit re-exports), update both module docstrings, add the AC-03/AC-04 assertions to `tests/unit/test_thinking_budget.py`, replace the tautological disjunct in `.github/hooks/tests/test_size_gate.py`, remove the temporary `BASELINE` entry and its comment from `scripts/size_gate.py`, re-key CONF-352 only if R-3's probe demands it, and write the FR update, the FR-1148 addendum and the diary entry — and nothing else.
