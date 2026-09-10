# Judgement: FR-1044 Pre-commit gate hygiene

**Verdict:** SPLIT — the incident is real, but it bundles three orthogonal tooling changes, its research table does not satisfy the prospective research-evidence gate, and no implementation authority exists until each successor FR is independently researched and judged.

**Prior art:** FR-460 (`cap-architecture-sync` hook and the mutating test), FR-179 (append-only changelog; the FR's claimed autofix precedent — corrected below), FR-1034 (#645 hand-placed REQ rows), FR-890 (research sole route and its closed-input alternatives contract), FR-1013 (REJECTED: process outgrew the change — the successor count under R-1 re-enters that territory). No REJECTED prior art authorises the bundle.

**Reviewed against:** `feature-requests/FR-1044-pre-commit-gate-hygiene.md`; `feature-requests/FR-460-cap-architecture-auto-sync.md`; `feature-requests/FR-179-append-only-changelog.md`; `feature-requests/FR-1034-census-brief-model-selection.md`; `feature-requests/FR-1034-census-brief-model-selection.judgement.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.judgement.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.pre-commit-config.yaml`; `constraints/dev-py312.txt`; `scripts/aggregate_capabilities.py`; `scripts/noqa_coverage.py`; `tests/unit/test_fr460_cap_architecture_auto_sync.py`; `tests/unit/test_noqa_coverage.py`; `tests/unit/test_fr714_bandit_gate.py`; `tests/unit/test_fr441_precommit_files_patterns_red.py`; `tests/unit/test_llm_factory.py`; `docs/confessions.md`; `capabilities/CAP-199-gate-truth.yaml`; `ARCHITECTURE.md` at `HEAD`; committed regeneration `7348d9cb860a5bc229ecce597630691beeeb7f6a`.

## What is sound

The proposal identifies three concrete defects in committed surfaces. The FR-460 test calls `main()` without `--dry-run` (`tests/unit/test_fr460_cap_architecture_auto_sync.py:94-105`), while `main()` delegates to a branch that writes `ARCHITECTURE.md` (`scripts/aggregate_capabilities.py:151-170`). The formatter versions are objectively skewed: pre-commit uses `v0.8.6` (`.pre-commit-config.yaml:5-12`) while the development constraint is `ruff==0.16.0` (`constraints/dev-py312.txt:124-132`). The confession ledger also contains six stale location records followed by six current records for the same suppressions (`docs/confessions.md:602-672`), and the current strict checker keys coverage on exact `(file, line, code)` tuples (`scripts/noqa_coverage.py:172-183`).

The proposed implementation ingredients mostly reuse existing mechanisms rather than inventing a framework primitive. `aggregate_capabilities.py` already exposes `--dry-run` (`scripts/aggregate_capabilities.py:160-170`), pre-commit already pins Ruff and runs its fixing/formatting hooks (`.pre-commit-config.yaml:5-12`), and `test_noqa_coverage.py` already has temporary-file fixtures around the parser and strict mode. Each successor is therefore a narrow contrib/tooling maintenance change with one concrete use case and an existing abstraction to repair, not a new framework primitive.

| Criterion | Assessment |
|---|---|
| Scope | Not minimal. CAP generation test purity, formatter version convergence, and confession-ledger repair touch different contracts and can ship, fail, and be reverted independently (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:29-34,66-99`). |
| Consistency | Contradictory. The proposed noqa hook "modifies files, fails once" (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:86-94`) while AC requires the same shifted-line commit to pass on its first attempt (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:119`). The FR also says regeneration commit `7348d9cb` has already landed and adds no code (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:96-99`), but current `ARCHITECTURE.md` still contains the hand-placed rows that commit removes (`ARCHITECTURE.md:567-588,3091-3103`). |
| Measurability | Most proposed checks are mechanical, but "leaves git status clean on a synced tree" cannot prove that the test performed no write: the current write path can rewrite identical bytes (`scripts/aggregate_capabilities.py:151-156`; `feature-requests/FR-1044-pre-commit-gate-hygiene.md:112-113`). |
| Feasibility | Dry-run use and Ruff pin alignment are directly feasible. The removed-noqa criterion is not feasible under the stated "strict reports as today" design because strict only finds current suppressions missing from the ledger and never computes ledger entries missing from code (`scripts/noqa_coverage.py:178-229`; `feature-requests/FR-1044-pre-commit-gate-hygiene.md:86-94,115`). |
| Architecture alignment | The changes belong in the existing deterministic scripts, tests, constraints, and pre-commit config. However, FR-179 does not establish the claimed "autofix then re-check" noqa precedent; its gate work concerns changelog fragments (`feature-requests/FR-179-append-only-changelog.md:123-143,162-175`), while the actual local fixing precedent is the Ruff hook configuration (`.pre-commit-config.yaml:5-12`). |
| Single responsibility | Failed. The three fixes have separate causes, implementation surfaces, witnesses, and rollback units; doctrine requires bundled orthogonal concerns to receive SPLIT (`.github/skills/judge-fr/doctrine.md:49-50,75-77`). |
| Strategic classification | Each successor is a contrib/tooling maintenance correction: one witnessed use case and an existing local abstraction with a gap. None qualifies as a framework primitive (`.github/skills/judge-fr/doctrine.md:51-57`). |
| Testability | Pin equality and shifted/new-noqa fixtures can be derived directly. Test purity needs a no-write witness rather than byte equality, and first-attempt success cannot be tested until the hook contract contradiction is resolved (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:68-74,86-94,112-119`). |

## Required revisions

### R-1: Refile three single-responsibility successor FRs

Replace FR-1044 with three newly numbered FR files:

1. **CAP architecture sync purity and baseline** — change the FR-460 test so its unit-test path cannot write `ARCHITECTURE.md`, verify generation idempotency in isolation, and make the generated section agree with committed capabilities.
2. **Ruff version convergence** — align the pre-commit revision with the constraints source of truth, add a drift test, and isolate the formatter-induced repository reformat in its own commit.
3. **Confession line-reference repair** — define and test `noqa_coverage.py --fix`, its ambiguity boundary, strict-mode interaction, hook ordering, and stale duplicate cleanup.

Each concern re-enters plan -> judge -> enforce independently. Do not copy item 4 into a fourth implementation bundle: in the CAP successor, record `7348d9cb` as an external dependency until that commit is an ancestor of the successor branch, or include the generated `ARCHITECTURE.md` reconciliation in that CAP-only scope.

### R-2: Supply substantive research for every successor

The current in-body table has four rows but lacks solution-class labels, precedent citations for each class, preserved disagreement, and the `is_this_a_graph` answer (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:101-108`). It therefore fails the prospective research gate (`.github/skills/judge-fr/doctrine.md:118-130`).

Each successor must cite a committed research artifact or contain an equivalent table with 4-6 genuine solution classes, a disposition and precedent for every class, disagreement preserved, and an explicit `is_this_a_graph` answer. The record must evaluate alternatives for that successor's problem rather than reuse the present cross-problem table.

### R-3: Resolve the noqa first-attempt policy as an explicit human decision

**Human decision required:** must a line-shift-only commit pass the first pre-commit invocation, or is one intentional fix-and-restage failure acceptable?

Record the selected policy in the noqa successor and make its summary, hook design, and acceptance criteria agree. If first-invocation success is required, the successor must specify a mechanism that does not rely on pre-commit modifying an unstaged ledger under `fail_fast: true`. If one fix-and-restage cycle is acceptable, delete the current first-attempt criterion and measure elimination of manual line arithmetic and repeated full-suite runs instead.

### R-4: Remove removed-noqa detection from the repair scope

Revise the noqa successor so `--fix` repairs line-only drift only when ledger entries and current suppressions match one-to-one by the frozen identity rule, and strict mode continues to reject added or code-changed suppressions. Do not claim that today's strict mode detects removed suppressions: it does not compare documented tuples back against the codebase (`scripts/noqa_coverage.py:172-183,219-229`). Bidirectional stale-confession detection is adjacent work and requires its own FR if desired.

### R-5: Replace the CAP no-write proxy with a causal witness

The CAP successor must distinguish two contracts:

- A test of the FR-460 unit-test call path patches or isolates the architecture write boundary and fails if `Path.write_text` is reached; merely comparing bytes or `git status` is insufficient because an identical rewrite leaves both unchanged.
- A separate idempotency test runs generation against an isolated synced fixture and asserts generated content equals the fixture's committed marker section.

Remove the current ambiguity that describes `main()` without a flag but equates that to `--dry-run` output (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:68-74`).

### R-6: Freeze the Ruff source, reformat surface, and witness

The Ruff successor must name `constraints/dev-py312.txt` as the version source, normalize the optional `v` prefix in the equality test, require the pre-commit `ruff-pre-commit` revision to equal that pin, and identify the exact formatter check used after the bump. The one-time formatting diff is authorized only as a separate `style:` commit within that successor; unrelated lint fixes or dependency updates are excluded.

### R-7: Assign exact requirement IDs

Replace the generic "`@pytest.mark.req` tags" criterion (`feature-requests/FR-1044-pre-commit-gate-hygiene.md:118`) with exact requirement IDs in each successor. Reuse `REQ-YG-425` for the FR-460/CAP sync witnesses and the existing gate-truth requirement where it genuinely governs confession coverage; if no existing requirement governs Ruff pin convergence or line-reference repair, amend the relevant capability record with a new requirement before tagging tests.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | New FR: CAP architecture sync test purity and generated baseline |
| D-2 | New FR: Ruff pre-commit/development version convergence |
| D-3 | New FR: noqa confession line-reference repair |
| D-4 | One committed, substantive research record per successor |
| D-5 | Human decision recorded in the noqa successor on first-invocation success versus one fix-and-restage cycle |

Not authorized by FR-1044: edits to `.pre-commit-config.yaml`, `constraints/`, `scripts/`, tests, `docs/confessions.md`, `ARCHITECTURE.md`, capability files, changelog fragments, or diary files; auto-staging hook output; moving pytest to pre-push; weakening strict coverage to warnings; retry logic in `scripts/ship.sh`; broad Ruff lint cleanup; bidirectional stale-confession detection; changes to CI, branch protection, or hook doctrine.

## Revised acceptance criteria

- [ ] AC-01: Three newly numbered successor FRs exist, each containing only one of D-1 through D-3 and each naming its own first consumer, first event, requirement IDs, implementation surfaces, and out-of-scope boundaries.
- [ ] AC-02: Each successor cites a committed research record satisfying the 4-6 solution-class, precedent, disagreement, and `is_this_a_graph` substance contract.
- [ ] AC-03: The CAP successor causally proves that the unit-test call path does not reach the `ARCHITECTURE.md` write boundary and separately proves generation idempotency against an isolated synced fixture.
- [ ] AC-04: Before CAP enforcement, `7348d9cb` is an ancestor of the implementation branch or the CAP successor explicitly owns and tests the equivalent generated-section reconciliation.
- [ ] AC-05: The Ruff successor names `constraints/dev-py312.txt` as source of truth, specifies `v`-prefix normalization, defines the formatter check, and confines formatter output to a separate `style:` commit.
- [ ] AC-06: The noqa successor records the human-selected first-invocation policy and contains no contradiction between that policy, hook exit behavior, and its end-to-end witness.
- [ ] AC-07: The noqa successor limits automatic repair to unambiguous line-only drift, requires no change on added/removed/code-changed ambiguous shapes, and claims strict failure only for conditions strict is explicitly extended and tested to detect.
- [ ] AC-08: Every successor specifies exact `@pytest.mark.req(...)` values and a targeted RED witness that fails because of the missing implementation rather than repository dirtiness or an unavailable fixture.
- [ ] AC-09: Each successor receives its own judgement granting authority before any implementation from that successor begins.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | FR-1044 grants no implementation authority; only the planning artifacts D-1 through D-5 may be produced under this verdict. | GATE |
| C-2 | Each successor must independently pass the research-evidence gate and judge route before enforcement. | GATE |
| C-3 | The human first-invocation policy decision must be recorded before the noqa successor can receive authority. | GATE |
| C-4 | All pre-commit and hook-script changes are enforcement-infrastructure changes and require recorded human review before they are treated as binding. | GATE |
| C-5 | Do not auto-stage files or weaken strict failures unless a successor FR explicitly proposes, researches, and receives authority for that policy change. | GATE |
| C-6 | Do not treat `7348d9cb` as landed unless it is an ancestor of the implementation branch; generated-state truth must be present in the branch being tested. | GATE |
| C-7 | Keep the Ruff formatter-only diff in a separate commit from hook logic, tests, and noqa/CAP changes. | GATE |
| C-8 | A failure or delay in one successor must not block, enlarge, or silently amend either of the others. | GATE |

Authority granted: no implementation authority is granted under FR-1044; authority may arise only from independently approved successor FRs within the frozen planning split above.
