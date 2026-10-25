# Judgement: FR-1149 The size gate keys its baseline by POSIX paths on Windows

**Prior art:** [FR-1149-size-gate-windows-paths.md](FR-1149-size-gate-windows-paths.md) — the FR this judgement rules on, not precedent; dismissed; its own Prior art line dispositions FR-889 and FR-942. (Added by the FR author at promotion to satisfy the FR-738 gate; not judge output. Backend: `JUDGE_BACKEND=claude scripts/judge.sh`, 2026-10-25, round 1.)

**Verdict:** APPROVED WITH REVISIONS — the defect is real, reproduced, and the one-line normalisation at the `relative_to` boundary is the smallest correct fix; authority activates once R-1..R-7 are folded into the FR, because the FR's stated RED witness does not condemn what it claims, AC-08 cites a dead assertion as its witness, and the temporary baseline exemption has no named owner for its removal.

**Reviewed against:** `feature-requests/FR-1149-size-gate-windows-paths.md`; cited evidence `scripts/size_gate.py`, `.github/hooks/tests/test_size_gate.py` (working-tree state; shown modified at session start), `feature-requests/FR-889-os-enforced-main-write-lock.md` (prior art, by reference), `feature-requests/FR-1148-anthropic-thinking-off.md` (lines 144–151, 296–349); doctrine `.github/skills/judge-fr/doctrine.md`, `.github/skills/judge-fr/judgement.template.md`, `.github/copilot-instructions.md` (Scripture), `CLAUDE.md`; corroborating repo artifacts `capabilities/CAP-255-os-enforced-main-write-lock.yaml`, `scripts/req_coverage.py` (lines 44–45), `scripts/check_changelog_req.py` (lines 87–91, 279–298), `.pre-commit-config.yaml` (lines 160–168), `tests/unit/test_os_main_write_lock.py` (lines 15–30), `yamlgraph/utils/llm_providers.py` (line count), `changelog/unreleased/fr-1148-anthropic-thinking-off.md`. No chat transcript, planning narrative, or uncommitted author notes were consumed.

## What is sound

- **The defect is real and the diagnosis is exact.** `scripts/size_gate.py` keys `BASELINE` by forward-slash paths (lines 37–49) and the pre-fix lookup used `str(p.relative_to(root))`; on Windows that string carries `\`, so `BASELINE.get(rel, LIMIT)` misses for every entry. `.pre-commit-config.yaml:167` fires the gate on `\.(py|sh)$`, so the Value Statement's claim — no Python change can be committed from Windows through the hooks — is accurate, not rhetorical.
- **The fix is at the boundary, not downstream.** `baseline_key()` normalises once where the OS path enters, and the same value feeds both the lookup and the printed line (`size_gate.py:103–110`). This is `the_one_law` applied at the `platform` boundary, and alternative C (compare with `Path(rel) == Path(key)`) is rejected for exactly the right reason — it normalises at every comparison, downstream of entry.
- **No behaviour change on POSIX.** `PurePosixPath.as_posix()` equals `str()`, so the "no change to output on macOS or Linux" constraint holds by construction; nothing else in the script compares OS separators (`EXCLUDE_PARTS` uses `p.parts`; `INSTRUCTION_FILES` are literal forward-slash keys joined with `/`), so the Planned-Operations branch probe closes negative and the change stays one function.
- **Research substance is adequate for a one-line defect (FR-890 clause).** The in-body table carries four genuinely distinct solution classes (normalise the key / store `os.sep` keys / compare as `Path` objects / exempt Windows), each with a reason rather than a verdict word, plus the `is_this_a_graph` answer ("no — a one-line key normalisation"). Alternative D is correctly killed by name as `infrastructure_self_exempt`. Prior art cites FR-889 (the ratchet's origin) and FR-942 (the byte ceiling, untouched) with what each contributed; no rejected FR occupies this territory, consistent with the FR-737 precedent rule.
- **The temporary baseline number is honest.** `yamlgraph/utils/llm_providers.py` is 473 lines in the tree, so the proposed entry `473` is the file's exact size — the shrink-only ratchet pins it rather than granting headroom, and the ninth failure is correctly separated from the eight path artefacts.
- **The operator decision is surfaced, not absorbed.** The FR records the exemption as an explicit `[O]` decision with its date and the two rejected alternatives (combined commit, commit from macOS). That is the right shape for a human-owned call.

## Required revisions

### R-1: Record that the implementation already exists on the branch, and name its commit

At judgement time `scripts/size_gate.py` already contains `baseline_key()` (lines 52–54) and the temporary `BASELINE` entry (lines 46–48), and the session-start `git status` shows `scripts/size_gate.py` unmodified — i.e. the GREEN change is already committed on `fix/size-gate-windows-paths`, while the FR is `Status: Proposed` with every AC unchecked. Add to **Implementation status**: the commit SHA that introduced `baseline_key` and the `llm_providers.py` entry, and a one-line honest note that the code landed before judgement, so the Sermon's plan → judge → enforce order was not followed for this change. If that SHA is `246f909e` (`docs(fr): …`), say so plainly and name it as a mixed commit (`mixed_commits_erode_auditability`); do not re-write history to hide it.

### R-2: Produce a real RED witness and paste it into the FR

Commandment 7 requires the fix to be condemned by a failing test, and the GREEN code pre-exists (R-1), so a RED *commit* is no longer available. Fold the cheaper substitute: run the two new tests against the pre-fix line (either at `c1db2321`, or locally with `baseline_key` replaced by `str(path.relative_to(root))`), and paste the verbatim failure output into **Implementation status** under a `RED witness` heading, stating which OS produced it. If the only failure obtainable on the running OS is `AttributeError: module 'size_gate' has no attribute 'baseline_key'`, record exactly that text — an honest weak witness beats a claimed strong one.

### R-3: State AC-01's condemnation accurately and make it backslash-explicit

AC-01's parenthetical "a test that fails on the old `str(...)` line on every OS" is false as written: against the pre-fix code the test does not exercise the old line, it fails because the function does not exist. Rewrite the parenthetical to say so, and extend the criterion with the cross-OS regression assertion that actually guards the key shape on Linux CI: `"\\" not in key`. Both assertions belong in `test_baseline_key_is_posix_for_a_windows_path`.

### R-4: State AC-02's vacuity on POSIX

Against the pre-fix code, `test_a_baselined_file_is_held_on_this_os` passes on macOS and Linux, because `rel` already uses `/` there — on CI it can never condemn this defect. Amend AC-02 to say explicitly: "non-regression on the running OS; on POSIX this test also passes against the pre-fix code, so AC-01 is the cross-OS regression witness, not AC-02."

### R-5: Replace AC-08's dead witness with the live one

AC-08 nominates `test_baseline_is_shrink_only_and_honest` as the witness that the temporary entry is honest. Its staleness clause is dead: line 123 asserts `actual > LIMIT or allowed >= actual`, and `allowed >= actual` is already guaranteed by line 122, so the disjunction is a tautology that can never fail. Restate AC-08's witness as the clause that is live — `assert actual <= allowed` (the shrink-only ratchet) plus `assert p.is_file()` (no phantom entry) — and drop the word "honest" from the claim. Do **not** repair line 123 under this FR; it is parked below as separate work.

### R-6: Name the owner that removes the temporary entry

"the refactor PR right after removes the entry" names no artifact. FR-1148 records the owed split at AC-08 and in its "Follow-up owed" paragraph (lines 333, 344–349), so the removal has a home but is not written down there. Fold both halves: (a) in FR-1149, cite the owner as "FR-1148 AC-08 / its Follow-up owed paragraph"; (b) add one sentence to that paragraph in `feature-requests/FR-1148-anthropic-thinking-off.md` — "the same work removes the temporary `yamlgraph/utils/llm_providers.py: 473` entry added to `scripts/size_gate.py` BASELINE by FR-1149." Add a matching AC (AC-09 below) so the cross-reference is checkable by grep.

### R-7: Make AC-03 and AC-05 mechanically checkable as recorded facts

AC-03 asserts a Windows exit code but names no recorded witness: amend it to require the command, its exit code, and the first lines of its output pasted into **Implementation status** (the eight `✗` lines gone, `llm_providers.py` held). AC-05 must state the fragment's front matter in full — `type: fix`, `scope: hooks`, `req: REQ-YG-631` — and note that CAP-255 is single-REQ, so `scripts/check_changelog_req.py` passes mechanically without an LLM call.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/size_gate.py` — `baseline_key()` and its two call sites (`rel` lookup, printed path) |
| D-2 | `scripts/size_gate.py` — the single temporary `BASELINE` entry `"yamlgraph/utils/llm_providers.py": 473` with its FR-1148/FR-1149 removal comment |
| D-3 | `.github/hooks/tests/test_size_gate.py` — the two new tests (AC-01 incl. the backslash assertion, AC-02), module `pytestmark` unchanged |
| D-4 | `changelog/unreleased/fr-1149-size-gate-windows-paths.md` |
| D-5 | `docs/diary/` — one reflection with a **Seed:** |
| D-6 | `feature-requests/FR-1149-size-gate-windows-paths.md` — revisions R-1..R-7, Implementation status, witnesses |
| D-7 | `feature-requests/FR-1148-anthropic-thinking-off.md` — the single removal sentence required by R-6 |

**Not authorized by this FR:**

- Changing `LIMIT`, `WARN`, `SCAN_DIRS`, `SUFFIXES`, `EXCLUDE_PARTS`, `BYTE_CEILING`, or `INSTRUCTION_FILES`.
- Adding, removing, or re-numbering any `BASELINE` entry other than D-2's single temporary one.
- Splitting `yamlgraph/utils/llm_providers.py` (that is FR-1148 AC-08's owed work) or touching any provider module.
- Repairing the tautological assertion at `.github/hooks/tests/test_size_gate.py:123` (see Recommendation below).
- Any change to `.github/hooks/`, `.pre-commit-config.yaml`, CI workflow files, or judge/review doctrine.
- Editing `capabilities/CAP-255-*.yaml`, `ARCHITECTURE.md`, or REQ text; `.github/hooks/tests` is outside `req_coverage` scope (`scripts/req_coverage.py:45`), so no registry change is owed.
- Any `--no-verify`, skipped hook, force-push, or `Co-authored-by` trailer.

## Revised acceptance criteria

- [ ] AC-01: `baseline_key(PureWindowsPath(r"C:\r\.github\hooks\tests\x.py"), PureWindowsPath(r"C:\r"))` is `".github/hooks/tests/x.py"` and the result contains no `\`. The test runs and passes on every OS; the FR records accurately that against the pre-fix code it fails for a missing function, not for the old `str(...)` line (R-3).
- [ ] AC-02: a tree with a baselined file over `LIMIT` but within its baseline length passes `main()` on the running OS. Non-regression only — the FR states that on POSIX this passes against the pre-fix code too, so AC-01 is the cross-OS regression witness (R-4).
- [ ] AC-03: `PYTHONUTF8=1 python scripts/size_gate.py` exits 0 on Windows at the fixed commit; the command, exit code, and output (no `✗` lines; `llm_providers.py` held by AC-08's entry) are pasted into the FR's Implementation status (R-7).
- [ ] AC-04: `pytest .github/hooks/tests/test_size_gate.py -q --no-cov` passes with every pre-existing test unchanged; the module-level `pytestmark = pytest.mark.req("REQ-YG-631")` covers the new tests (infrastructure scope, excluded from `req_coverage`).
- [ ] AC-05: `changelog/unreleased/fr-1149-size-gate-windows-paths.md` exists with front matter `type: fix`, `scope: hooks`, `req: REQ-YG-631`, and `python scripts/check_changelog_req.py` passes (R-7).
- [ ] AC-06: a `docs/diary/` reflection with a **Seed:**.
- [ ] AC-07: no `--no-verify`, no skipped hook, no `Co-authored-by` trailer; `PYTHONUTF8=1 pre-commit run --files <changed files>` passes.
- [ ] AC-08: `BASELINE` holds exactly one temporary entry, `"yamlgraph/utils/llm_providers.py": 473`, with a comment naming FR-1149 and FR-1148 and stating that FR-1148's split removes it; the number equals the file's current line count, and `test_baseline_is_shrink_only_and_honest` passes on its live clauses — `p.is_file()` and `actual <= allowed` (R-5).
- [ ] AC-09: `feature-requests/FR-1148-anthropic-thinking-off.md` names the removal of the FR-1149 temporary `BASELINE` entry in its Follow-up-owed paragraph, and FR-1149 cites FR-1148 AC-08 as that entry's owner (R-6).
- [ ] AC-10: the FR's Implementation status records the pre-judgement landing of the code with its commit SHA (R-1) and the verbatim RED-witness output against the pre-fix line (R-2).

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | This is enforcement-infrastructure change (`scripts/size_gate.py` is a pre-commit gate, `.pre-commit-config.yaml:162`). It merges only on an explicit human review decision; the enforcer must not self-certify or auto-merge. | GATE |
| C-2 | The temporary `BASELINE` entry is a deliberate, operator-approved weakening of a gate. It must be exactly one entry, at the file's exact current size, carrying the removal comment, and recorded in both FRs (AC-08, AC-09). A second temporary entry, a rounded-up number, or an entry without a named owner voids authority. | GATE |
| C-3 | No `--no-verify`, no `SKIP=`, no force-push, no `Co-authored-by` trailer; the gate change must itself pass through the hooks it governs (`infrastructure_self_exempt`). | GATE |
| C-4 | Output on macOS and Linux must be byte-identical to the pre-fix gate for the same tree; only the Windows path rendering changes. | GATE |
| C-5 | R-1..R-7 are folded into the FR before any further commit on this branch; authority does not exist until the FR text carries them. | GATE |
| C-6 | Honest recording wins over a clean record: if the RED witness is only an `AttributeError`, or if the code landed in a `docs(fr):` commit, the FR says so (`pre-existing failure` and retroactive tidying are both forbidden). | GATE |

**Question for the human (not absorbed):** the temporary exemption's removal depends on FR-1148 AC-08 being done. If that split slips, `yamlgraph/utils/llm_providers.py` sits above `LIMIT` with the gate's blessing and no expiry mechanism — C-2 records the obligation but nothing mechanically fires when it is missed. Confirm at merge that FR-1148's follow-up is the next PR, as the `[O]` decision of 2026-10-25 assumed.

**Recommendation, parked as separate work (not authorized here):** `.github/hooks/tests/test_size_gate.py:123` asserts `actual > size_gate.LIMIT or allowed >= actual`, whose right-hand side is implied by the preceding assertion — the "goes stale loudly" promise in `scripts/size_gate.py`'s docstring (lines 6–8) is therefore unenforced; a baselined file that shrinks below `LIMIT` keeps its entry silently. The intended assertion is `actual > LIMIT` with a message naming the stale entry. File it as its own FR — `gate_checks_shape_not_substance` applied to the gate's own test.

Authority granted: once R-1..R-7 are folded into `feature-requests/FR-1149-size-gate-windows-paths.md`, the enforcer may land D-1..D-7 exactly as frozen above — the `baseline_key` normalisation with its two call sites, the single temporary `BASELINE` entry, the two tests, the changelog fragment, the diary reflection, and the one-sentence cross-reference in FR-1148 — and nothing else.
