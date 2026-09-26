# Judgement: FR-1110 Close every hatch on the unit tier and let it fail

**Prior art:** `FR-1110-unit-test-runtime-sandbox.md` is the FR this judgement governs. Substantive prior art (FR-756, FR-982, FR-1084, FR-1104) is dispositioned in the FR header.

**Verdict:** APPROVED WITH REVISIONS — the unit-tier runtime boundary is a sound internal enforcement change, but authority activates only after the credential timing, sandbox lifetime, filesystem policy, allowlist semantics, and Phase 2 scope gates below are folded into the FR.

**Reviewed against:** `feature-requests/FR-1110-unit-test-runtime-sandbox.md`; cited prior art and evidence `feature-requests/FR-756-core-test-isolation.md`, `feature-requests/FR-982-unit-suite-runs-with-tracer-live.md`, `feature-requests/FR-982-unit-suite-runs-with-tracer-live.judgement.md`, `feature-requests/FR-1084-reject-undeclared-cli-vars.md`, `feature-requests/FR-1084-reject-undeclared-cli-vars.judgement.md`, `docs/diary/diary-2026-09-26-the-unit-test-that-owned-the-repo.md`, `tests/conftest.py`, `yamlgraph/config.py`, and `.github/workflows/workflow.yml`; repo doctrine `.github/copilot-instructions.md`, `feature-requests/TEMPLATE.md`, `.github/skills/judge-fr/doctrine.md`, and `.github/skills/judge-fr/judgement.template.md`. The open FR-1104 / PR #714 assertion and issue-only references #712/#713 were not consumed as authority-bearing evidence; the committed checkout still contains the `core-test` job (`.github/workflows/workflow.yml:40-63`).

## What is sound

The problem is real and has a named consumer. The cited FR-1084 census compiled repository-wide artifacts and compared a generated snapshot byte-for-byte, then was removed after unrelated changes repeatedly broke it without finding the defect it claimed to guard (`feature-requests/FR-1084-reject-undeclared-cli-vars.md:317-344`; `docs/diary/diary-2026-09-26-the-unit-test-that-owned-the-repo.md:9-25`). FR-756 proves that source classification is already present but deliberately only labels modules (`feature-requests/FR-756-core-test-isolation.md:32-35,68-81`); FR-1110 correctly targets observed runtime behavior instead (`feature-requests/FR-1110-unit-test-runtime-sandbox.md:17-23,69-74`).

The architecture choice is minimal. The policy belongs at the pytest boundary, uses the standard-library audit mechanism, adds no production dependency, and leaves production modules untouched (`FR-1110:76-87,97-112`). The current required matrix really does execute all of `tests/unit/` on Python 3.11 and 3.13 (`.github/workflows/workflow.yml:65-101`), so an autouse boundary in `tests/unit/conftest.py` protects both required jobs without a wrapper. The RED-then-GREEN sequence, exact-call diagnostics, and explicit fixture/move/reopen dispositions conform to the repository's TDD and visible-error rules (`FR-1110:113-140`; `.github/copilot-instructions.md:198-214`).

The research substitute is substantive enough for this non-measurement FR. It dispositions six solution classes, preserves the stronger OS-sandbox alternative, and answers `is_this_a_graph` in substance by rejecting the LLM census in favor of runtime observation (`FR-1110:205-214`; `.github/skills/judge-fr/doctrine.md:116-128`). Prior art is distinguished rather than merely listed (`FR-1110:16-32`). The raw-output gate does not apply because this proposal adds no scorer, measure graph, evaluator, or score combiner (`feature-requests/TEMPLATE.md:45-49`).

The scope is one cohesive internal test-enforcement responsibility, not a framework primitive: its sole consumer is this repository's unit tier, and it composes existing pytest, environment-normalization, and audit-hook mechanisms. Credentials, network, process creation, and filesystem access are four capabilities of that one boundary. The focused calls in AC-02 through AC-05 can become direct failing witnesses once the contracts below are made exact (`FR-1110:152-175`).

## Required revisions

### R-1: Move credential normalization before package import

Replace the session-fixture-only design at `FR-1110:91-96`. A fixture starts after test-module collection, while the shared conftest imports `yamlgraph.models` at module import (`tests/conftest.py:17`) and `yamlgraph.config` loads `.env` at import (`yamlgraph/config.py:39-44`). Therefore the current proposal can expose or cache real provider values before the fixture runs.

Fold an exact lifecycle into the FR: at the top of `tests/conftest.py`, before any `yamlgraph` import, save absence or the exact value of all eight named variables and set each to `fr1110-sentinel-not-a-key`; restore that saved state once, at pytest session finish. Keep FR-982's tracing fixture and cache-clearing behavior intact (`feature-requests/FR-982-unit-suite-runs-with-tracer-live.judgement.md:26,42,56-68`). Require separate witnesses for a value inherited from the parent environment and a value present only in `.env`, and assert a package import observes only the sentinel.

### R-2: Bind activation to a per-test fixture and its own temporary root

Replace `pytest_runtest_setup` / `pytest_runtest_teardown` as the owner of active state (`FR-1110:97-101`) with a function-scoped autouse fixture in `tests/unit/conftest.py` that depends on `tmp_path`, records the current node id and that test's canonical temporary root, arms immediately before yielding, and clears in `finally`. The same process may collect integration tests, and a failed setup or teardown must not leave the next item armed.

Remove `tempfile.gettempdir()` as an allowed root. It grants every unit test access to every pytest worker's and unrelated process's temporary files, contradicting the stated "its own `tmp_path`" boundary (`FR-1110:78-81,108-111`). Add sequential and xdist witnesses proving two tests cannot access each other's temporary roots and proving the hook is inert for an integration item in the same session.

### R-3: Separate filesystem read authority from mutation authority

Replace the single four-root filesystem rule at `FR-1110:108-112` with two explicit policies:

1. Reads may target canonical paths under `yamlgraph/`, `tests/`, the current test's `tmp_path`, `sys.prefix`, or `sys.base_prefix`.
2. Creates, writes, truncation, deletion, rename, directory creation/removal, permission/ownership changes, and timestamp changes may target only the current test's `tmp_path`.

This correction is required because allowing `open` under `yamlgraph/` and `tests/` without inspecting mode/flags permits the developer-working-tree mutation the Value Statement says is prevented (`FR-1110:43-48,108-112`). Freeze normalization for relative paths, `PathLike` values, non-existent write targets, file descriptors, `..`, and symlinks before allowlist comparison. Add real-operation witnesses for an allowed package/test read, an allowed `tmp_path` write, a denied repository-root read, a denied package/test write, and a symlink under an allowed root that resolves outside it.

### R-4: Freeze the event and target contracts

Replace the phrases "every hatch" and "no reach" with the exact enforced capability matrix, or expand the matrix until those claims are true (`FR-1110:34-41,76-81,97-112`). At minimum, the network row must disposition connection, bind/listen exposure, name resolution, and datagram sends; the process row must list every supported audited spawn/exec/fork event on Python 3.11 and 3.13; and the filesystem row must include both content access and the mutation operations required by R-3. Each claimed operation needs a real API witness that fails before the side effect, not only a synthetic `sys.audit` call.

Define `UNIT_TIER_ALLOWLIST` matching mechanically. Each typed entry must contain hatch, normalized exact target, and non-empty reason; no regex, glob, empty target, catch-all, or prefix that denotes an entire filesystem root is permitted. Define target extraction for every event, including `str`, `bytes`, `PathLike`, integer file descriptors, subprocess argv/executable variants, and socket address families. Unknown argument shapes must raise a diagnostic rather than silently pass. AC-05 must prove both exact positive matching and near-match refusal.

### R-5: Bound Phase 2 to the observed failure set

The current Phase 2 authorizes an unknown number of test rewrites and moves before the Phase 1 inventory exists (`FR-1110:116-139,193-197`). Fold the table schema and staging gate into the plan now: after Phase 1, the implementation record must contain one row per failure with Python version, test node id, module, hatch, event, normalized target, and exactly one proposed disposition. No Phase 2 change starts until that populated table is committed. Phase 2 may touch only modules in that table, plus the frozen enforcement and repository-required artifact surfaces below. A newly discovered failure is appended with the same fields before it is changed; unrelated test cleanup is not authorized.

Every proposed allowlist row and move must receive explicit human review before merge because each changes enforcement coverage or required-job coverage (`FR-1110:129-136`; `.github/copilot-instructions.md:75`). If moves exceed one third of the Phase 1 failures, stop and ask the human to choose one of: approve the exact move list, first create a separately judged required integration-job FR, or abandon those moves. Do not absorb that product/CI decision into implementation.

### R-6: Turn performance and platform claims into gates

Replace the report-only slowdown clause (`FR-1110:198-200`) with a mechanically comparable result: record commit SHA, Python version, worker mode, exact command, test count, and wall time for three baseline and three sandboxed full-unit runs; compare medians. More than 20 percent regression blocks enforcement pending an explicit human decision.

State the supported platforms honestly. The required acceptance surface is Python 3.11 and 3.13 on the CI platform plus the operator's local platform used for the Phase 1 record; do not imply that audit-event coverage has been proven on untested platforms. Record event-matrix results separately for each tested Python/platform pair.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `tests/conftest.py` — early eight-variable sentinel installation and exact session-end restoration, preserving FR-982 tracing behavior |
| D-2 | `tests/unit/conftest.py` — one audit hook, per-test activation state, canonical root/target handling, typed exact-target allowlist, and `UnitTierViolation` |
| D-3 | Focused FR-1110 witness tests for credential timing, lifecycle reset, network/process/filesystem events, path escape, outside-unit inertness, allowlist exactness, and diagnostic content |
| D-4 | The FR-1110 implementation record — Phase 1 failure table, per-platform event matrix, RED/GREEN commit identities, moved-path table, allowlist review record, and performance measurements |
| D-5 | Only test modules named by the Phase 1 failure table, each receiving exactly one fixture, move, or reviewed reopen disposition |
| D-6 | One capability/REQ entry, regenerated `ARCHITECTURE.md`, one changelog fragment, the bounded `CLAUDE.md` testing note, and one FR-1110 diary entry with `Seed:` |

Not authorized: production changes under `yamlgraph/`; CI workflow or required-check changes; changes to the FR-756 `process` marker; an OS/container sandbox; child-process confinement; report-only or opt-out modes; marker exemptions; broad filesystem or executable allowlists; changes to integration tests except path moves explicitly listed in the approved Phase 1 table; repairs to unrelated test behavior; or adoption in csap or any other repository.

## Revised acceptance criteria

- [ ] AC-01: before the first `yamlgraph` import in the pytest process, all eight named credential variables equal `fr1110-sentinel-not-a-key`; separate parent-environment and `.env`-only witnesses prove no real value is observed, and session finish restores absence or the exact inherited value.
- [ ] AC-02: a function-scoped autouse unit fixture arms the hook with the current node id and canonical `tmp_path`, clears it in `finally`, remains active through dependent fixture teardown, and cannot leak active state after a setup, call, or teardown failure.
- [ ] AC-03: the frozen real-operation matrix raises `UnitTierViolation` before each denied network, process, filesystem-read, or filesystem-mutation side effect on Python 3.11 and 3.13; every message contains hatch, event, normalized target, node id, `FR-1110`, and the three dispositions.
- [ ] AC-04: package and test-tree reads and current-`tmp_path` reads/writes succeed; repository-root reads, package/test-tree writes, another test's temporary root, `..` traversal, and symlink escape raise. Integer file-descriptor behavior matches the folded contract.
- [ ] AC-05: patching `subprocess.run` emits no process audit event and succeeds; a real denied `sys.executable`, `kubectl`, and `git` call fails before launch.
- [ ] AC-06: one reviewed exact-target `git` allowlist entry permits only its normalized `git` target; a near match, `kubectl`, every other hatch, and every other target still raise. Invalid or broad entries fail validation at collection.
- [ ] AC-07: in one `pytest tests/` session the hook is inert during collection and for integration items, then re-arms for the next unit item. The focused witnesses pass sequentially and under xdist.
- [ ] AC-08: the Phase 1 RED commit exists and the FR contains the complete failure table for full unit runs, including slow tests, on Python 3.11 and 3.13 and the tested local platform; counts reconcile to table rows by hatch and module.
- [ ] AC-09: every Phase 1 row has exactly one fixture, move, or reviewed reopen disposition; every moved module records old/new path; every allowlist row has explicit human approval; no test module outside the table changes under Phase 2.
- [ ] AC-10: the full unit suite passes sequentially on Python 3.11 and 3.13 with the hook active, both required `test` jobs pass, and the repository's documented xdist non-slow unit command passes with the hook active.
- [ ] AC-11: three matched baseline/sandbox runs show a median wall-time increase of at most 20 percent, or an explicit human decision records why a larger regression is accepted before merge.
- [ ] AC-12: the capability/REQ entry, marked tests, `python scripts/req_coverage.py --strict`, changelog fragment, implementation record, no-more-than-six-line `CLAUDE.md` note, and diary entry with `Seed:` are present and pass their repository checks.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-6 into FR-1110 before implementation authority activates. | GATE |
| C-2 | Install credential sentinels before any `yamlgraph` import; do not weaken or replace FR-982 tracing normalization. | GATE |
| C-3 | Permit writes and filesystem mutations only inside the current test's canonical `tmp_path`; broad temporary-directory, repository, package, and test-tree write roots are forbidden. | GATE |
| C-4 | Every claimed denied capability must have a real-operation witness on the stated Python/platform matrix; synthetic audit calls alone are insufficient. | GATE |
| C-5 | Phase 2 is limited to rows in the committed Phase 1 table; allowlist and move dispositions require explicit human review before merge. | GATE |
| C-6 | A greater-than-20-percent median slowdown or moves exceeding one third of failures stops enforcement for the corresponding explicit human decision. | GATE |
| C-7 | Enforcement-infrastructure changes receive adversarial human review; no CI, production, OS-sandbox, child-confinement, or other-repository work enters this FR. | GATE |
| C-8 | RED precedes GREEN in git history, all affected tests carry the new REQ marker, and strict requirement coverage passes. | GATE |

Authority granted: after R-1 through R-6 are folded and C-1 is satisfied, implement D-1 through D-6 exactly within the frozen surfaces; Phase 2 changes remain limited by C-5 and the human decisions in C-6.
