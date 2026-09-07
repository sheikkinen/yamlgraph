# Judgement: FR-1022 Judge round sentinel — the third judgement is not a model call

**Prior art:** dispositioned in the parent FR header ([FR-1022](FR-1022-judge-round-sentinel.md) — NC-414, FR-767, FR-886, FR-980, FR-883, FR-916, FR-960; FR-1013 is the REJECTED witness incident, not a competing solution).

**Route:** `scripts/judge.sh` (Copilot backend, `gpt-5.6-sol`) on branch commit `b83c5470`, 2026-09-06. Promoted verbatim; R-1…R-5 folded into the FR.

**Verdict:** APPROVED WITH REVISIONS — the deterministic third-run boundary is justified and minimal, but authority activates only after the FR uses the closed verdict taxonomy, preserves existing guard precedence, reuses CAP-211, corrects the research provenance, and adopts the mechanically checkable criteria below; the result remains advisory until human-reviewed.

**Reviewed against:** `feature-requests/FR-1022-judge-round-sentinel.md`; `feature-requests/FR-1022.research.md`; `feature-requests/research-briefs/judge-round-sentinel.md`; `scripts/judge.sh`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/judge-fr/adapters/README.md`; `tests/unit/test_fr758_judge_review_wrappers.py`; `docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`; `feature-requests/FR-1013-chaplain-doctrine-sweep.judgement.md`; `ARCHITECTURE.md`; `capabilities/CAP-211-sole-route-judge-review.yaml`; `capabilities/CAP-44-judge-split-verdict.yaml`; `.github/copilot-instructions.md`; `CLAUDE.md`.

## What is sound

| Rubric criterion | Finding |
|---|---|
| Scope | The first consumer and trigger are concrete: a third `scripts/judge.sh` invocation when the adjacent judgement already contains two verdict lines (`FR-1022`, lines 8-11). The ideal explicitly leaves the rest of the route unchanged (`FR-1022`, lines 85-92). |
| Consistency | The central rule is consistent across the Summary, Ideal Result, and threshold alternative: rounds one and two remain model runs; round three is deterministic (`FR-1022`, lines 41-43, 85-92, 191-195). The token and ordering contradictions are repairable by R-1 and R-2. |
| Measurability | The proposed fixtures directly distinguish zero, one, two, four, and unanchored verdict occurrences and use an executor marker to prove no model route ran (`FR-1022`, lines 135-152). R-5 removes the two criteria that do not prove their claims. |
| Feasibility | The wrapper already derives a per-backend artifact, has a re-entry sentinel, takes an atomic lock, and validates artifacts (`scripts/judge.sh`, lines 21-40, 42-57, 70-82). An anchored count and early exit fit this shell boundary without changing the graph. |
| Architecture alignment | Research correctly classifies the termination rule as wrapper-level boundary enforcement rather than a graph (`FR-1022.research.md`, lines 34-37). The implementation must extend the existing sole-route capability rather than mint a parallel one; see R-3. |
| Single responsibility | The authorized concern is one policy: bound model judgement to two invocations per FR file. Backend changes, graph changes, fold-verification redesign, and growth metrics are explicitly excluded or parked (`FR-1022`, lines 92, 188-208). |
| Strategic classification | **Pattern-level enforcement, not a framework primitive.** One judge-route use case is served by the existing shell-wrapper abstraction; no new YAMLGraph abstraction is needed (`FR-1022.research.md`, lines 34-37; `CAP-211`, description and REQ-YG-569/642). |
| Testability | Failing tests can be written directly against exit status, stderr, executor-marker absence, lock absence, and exact artifact bytes. The existing stubbed harness already witnesses the relevant wrapper contracts (`tests/unit/test_fr758_judge_review_wrappers.py`, lines 20-48, 68-74, 188-213). |

The problem is evidenced independently of the unavailable hook log: seven committed judgement files contain at least two verdict lines, and FR-1013 contains four. Its committed judgement records rounds 1-4 (`FR-1013-chaplain-doctrine-sweep.judgement.md`, lines 3, 103-107, 196-198, 323-325), while the diary records the associated growth and absence of a fixed point (`docs/diary/2026-09-06-reflection-fr-1013-rigor-as-surface-area.md`, lines 12-17, 45-57).

## Required revisions

### R-1: Use the closed verdict taxonomy

Replace `REWRITE` with `REJECTED` in the Summary, proposed shell text, doctrine bullet, tests, and acceptance criteria. The exact sentinel line shall be `**Verdict:** REJECTED — Operator: Rethink and rewrite the FR. It's getting too complicated as a planning document.`

`REWRITE` is not one of the four permitted verdicts; the core contract says to render exactly one of `APPROVED`, `APPROVED WITH REVISIONS`, `REJECTED`, or `SPLIT` (`doctrine.md`, lines 63-77). Keep the operator directive as the rationale and state that the generated draft is advisory: the human either marks the current FR rejected or re-files a shorter plan. Replace the inaccurate “same eleven words” claim (`FR-1022`, lines 58-60) with “same fixed directive.”

### R-2: Preserve validation and sentinel precedence

Replace every claim that the round sentinel runs before backend validation (`FR-1022`, line 96) with this exact order:

1. usage and FR-existence checks;
2. closed backend validation;
3. per-backend artifact derivation;
4. `JUDGE_EXECUTION` re-entry guard;
5. output-directory creation and round count;
6. round-sentinel artifact write and exit 77 when the count is at least two;
7. lock acquisition and normal executor path.

The current closed backend validation prevents an unvalidated `JUDGE_BACKEND` value from entering the artifact path (`scripts/judge.sh`, lines 21-33; `ARCHITECTURE.md`, lines 2683-2686). The re-entry guard must continue to win over the new round sentinel (`scripts/judge.sh`, lines 35-38; `FR-1022`, lines 149-150). Narrow “no environment variable or argument changes AC-2” (`FR-1022`, lines 169-172) to “no force/override input bypasses the sentinel after the existing usage, FR-existence, backend-validation, and re-entry checks.”

### R-3: Extend CAP-211 instead of creating CAP-266

Delete the proposed `capabilities/CAP-266-judge-round-sentinel.yaml`. Add REQ-YG-668 to `capabilities/CAP-211-sole-route-judge-review.yaml`, update CAP-211's description/modules, and add REQ-YG-668 to the CAP-211 registry row and requirement table in `ARCHITECTURE.md`. CAP-211 already owns `scripts/judge.sh`, its sentinel and artifact contracts, backend validation, and `tests/unit/test_fr758_judge_review_wrappers.py` (`ARCHITECTURE.md`, lines 528-530, 2683-2687; `CAP-211`, description and requirements). A second capability over the same behavior would duplicate the active abstraction.

Add the FR-1022 tests to `tests/unit/test_fr758_judge_review_wrappers.py` so they reuse its `_run`, stub, and FR fixtures rather than creating a second wrapper harness. Tag each new test with `@pytest.mark.req("REQ-YG-668")`.

### R-4: Correct research provenance and disagreement

Delete the hook-audit invocation counts from the FR Problem and research brief, or first promote their source into a committed evidence artifact. `.github/hooks/logs/audit.jsonl` is not tracked, so it cannot support the brief's “Committed evidence on main” claim (`research-briefs/judge-round-sentinel.md`, lines 27-30, 88-89). The seven committed judgement files and FR-1013 diary are sufficient.

Correct `FR-1022.research.md` lines 12-14 so they do not claim that all surviving personas converged on threshold two while the FR attributes threshold one to the Subtractionist (`FR-1022`, lines 191-195). State the disagreement explicitly: the selected design permits one fold-verification rerun and blocks the third invocation; the stricter threshold-one alternative is rejected for the reason already recorded.

### R-5: Replace the acceptance criteria with the revised set

Replace AC-1 through AC-11 with the criteria below. This removes the repository-wide `grep FORCE|OVERRIDE` proxy, which cannot prove runtime precedence (`FR-1022`, lines 169-171), and removes the self-referential future-process assertion in AC-11 (`FR-1022`, lines 183-184).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/judge.sh`: anchored adjacent-judgement count, round stderr, deterministic exit-77 artifact |
| D-2 | `.github/skills/judge-fr/doctrine.md`: one Local conventions bullet |
| D-3 | `.github/skills/judge-fr/adapters/README.md`: exit-77 operator documentation |
| D-4 | `tests/unit/test_fr758_judge_review_wrappers.py`: REQ-YG-668 sentinel tests using the existing harness |
| D-5 | `ARCHITECTURE.md` and `capabilities/CAP-211-sole-route-judge-review.yaml`: REQ-YG-668 extension |
| D-6 | `changelog/unreleased/fr-1022-judge-round-sentinel.md` |
| D-7 | `feature-requests/FR-1022-judge-round-sentinel.md`: folded judgement, implementation status, and decisions |
| D-8 | One FR-1022 Distill entry under `docs/diary/` with `**Seed:**` |

Not authorized: a new CAP-266; edits to `.github/skills/judge-fr/adapters/graph.yaml` or `.github/skills/judge-fr/adapters/prompts/judge.yaml`; changes to the core verdict taxonomy; changes to `scripts/review.sh`; a force/override flag or environment variable; growth metrics; delta-only fold verification; rewriting historical judgement files; automatic FR status changes, commits, or re-filing.

## Revised acceptance criteria

- [ ] AC-01: With no adjacent judgement, the stubbed executor runs once, the wrapper exits 0 with a conforming stub artifact, and stderr contains `round 1`.
- [ ] AC-02: With exactly one anchored verdict line in the adjacent judgement, the stubbed executor runs once, the wrapper exits 0 with a conforming stub artifact, and stderr contains `round 2`.
- [ ] AC-03: With exactly two anchored verdict lines and the default backend, the wrapper exits 77; the executor marker is absent; the judge lock is absent; and `tmp/draft-judgement-copilot-<fr-slug>.md` consists exactly of `**Verdict:** REJECTED — Operator: Rethink and rewrite the FR. It's getting too complicated as a planning document.` plus one newline.
- [ ] AC-04: A four-verdict judgement with intervening `# Round N` headings produces the same exit, no-executor, no-lock, and exact-artifact result as AC-03.
- [ ] AC-05: With two verdicts and `JUDGE_BACKEND=claude`, the wrapper exits 77 and writes the exact sentinel to the Claude artifact; the executor marker is absent.
- [ ] AC-06: With two verdicts and an invalid `JUDGE_BACKEND`, the existing backend contract wins: exit 64, no sentinel artifact, no executor marker, and no lock.
- [ ] AC-07: With two verdicts, a valid backend, and `JUDGE_EXECUTION=1`, the existing re-entry contract wins: exit 70, no sentinel artifact, no executor marker, and no lock.
- [ ] AC-08: A verdict token not beginning a line does not increment the round; counting uses exactly the existing anchored grammar `^\*\*Verdict:\*\*`.
- [ ] AC-09: No new argument or environment-variable bypass is introduced; setting an otherwise unused `JUDGE_FORCE=1` or passing an extra `--force` argument does not change the AC-03 result.
- [ ] AC-10: The Local conventions bullet and adapter README document exit 77, the exact `REJECTED` sentinel, the two permitted human exits, and advisory status; `git diff --exit-code <base> -- .github/skills/judge-fr/adapters/graph.yaml .github/skills/judge-fr/adapters/prompts/judge.yaml` succeeds.
- [ ] AC-11: The new tests live in `tests/unit/test_fr758_judge_review_wrappers.py`, each carries `@pytest.mark.req("REQ-YG-668")`, and the committed RED test precedes the GREEN implementation commit.
- [ ] AC-12: REQ-YG-668 appears under CAP-211 in both `ARCHITECTURE.md` and `capabilities/CAP-211-sole-route-judge-review.yaml`; no CAP-266 file exists; `python scripts/req_coverage.py --strict` passes; the capability registry loads.
- [ ] AC-13: `pytest tests/unit/test_fr758_judge_review_wrappers.py -q --no-cov` passes without invoking a real judge graph.
- [ ] AC-14: The changelog fragment exists, and the FR-1022 diary entry contains `**Seed:**`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation authority is claimed. | GATE |
| C-2 | Preserve the existing exit-priority chain in AC-06 and AC-07; no unvalidated backend value may influence a written path. | GATE |
| C-3 | Do not edit either judge adapter graph or pointer prompt, and do not expand the core verdict taxonomy. | GATE |
| C-4 | Confirm REQ-YG-668 is still free immediately before allocation; reuse CAP-211 and do not allocate CAP-266. | GATE |
| C-5 | Commit the failing REQ-YG-668 tests before the implementation commit. | GATE |
| C-6 | A human must review the folded FR and the enforcement-infrastructure diff before merge; model approval alone cannot clear this gate (`doctrine.md`, lines 97-101). | GATE |
| C-7 | The sentinel path must be witnessed with a stub marker proving that no YAMLGraph or model executor ran. | GATE |

Authority granted: after the required revisions are folded and this advisory draft is human-reviewed, implement only the frozen deterministic third-run sentinel and its listed doctrine, documentation, traceability, changelog, test, and Distill surfaces.
