# Judgement: FR-951 Declare UTF-8 at every first-party text boundary

**Verdict:** APPROVED WITH REVISIONS - the root-cause fix is sound, but authority activates only after the research record, inventory, CI gate, and deterministic Windows witnesses are folded into the FR.

**Reviewed against:** `feature-requests/FR-951-declare-utf8-at-text-boundaries.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/TEMPLATE.md`; `feature-requests/FR-950-windows-safe-bridge-fork-registration.md`; `feature-requests/FR-950-windows-safe-bridge-fork-registration.judgement.md`; `feature-requests/FR-948-lan-copilot-delegation.judgement.md`; `feature-requests/FR-754-id-registry-chaplain-path-leak.md`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/utils/prompts.py`; `yamlgraph/schema_loader.py`; `yamlgraph/discovery.py`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/__main__.py`; `yamlgraph/cli/graph_validate.py`; `tests/unit/test_cli_package.py`; `pyproject.toml`; `.github/workflows/workflow.yml`; `ARCHITECTURE.md`. All were consumed from committed `HEAD`; the three cited `tmp/` reproductions were not consumed because the input-closure rule excludes uncommitted working artifacts (`.github/skills/judge-fr/doctrine.md:16-24`).

## What is sound

| Criterion | Finding |
|---|---|
| Scope | The production change fixes the external-data boundary rather than catching decode errors downstream: the FR identifies concrete undecorated graph, prompt, schema, and discovery reads (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:47-49`; `yamlgraph/compile/graph_loader.py:130-135`; `yamlgraph/utils/prompts.py:191-202`; `yamlgraph/schema_loader.py:240-254`; `yamlgraph/discovery.py:177-186`). The repository-wide count and roots need reconciliation under R-2 before this scope is minimal and frozen. |
| Consistency | The problem, ideal result, and chosen solution consistently target inherited locale defaults and silent corruption (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:31-35`, `:62-75`, `:97-108`). The stated 496-site scope and the claimed blocking gate conflict with their own evidence and require R-2 and R-3. |
| Measurability | Exact-character and byte-identity assertions correctly reject the plausible-wrong-answer path rather than accepting a merely non-raising load (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:153-156`; `.github/copilot-instructions.md:69`). R-4 makes the locale and pipe preconditions deterministic and removes a non-gating diagnostic from the acceptance list. |
| Feasibility | Explicit `encoding="utf-8"` is directly workable at the cited stdlib `open()` call sites, Ruff is already configured, and the console script already converges on one `main()` entry (`pyproject.toml:162-164`, `:174-190`; `yamlgraph/cli/__init__.py:316-325`; `yamlgraph/cli/__main__.py:1-6`). No new runtime dependency or wrapper abstraction is needed. |
| Architecture alignment | Boundary normalization follows the repository's platform-boundary law and the static gate follows `detection_without_enforcement` (`.github/copilot-instructions.md:41-51`, `:149`; `feature-requests/FR-951-declare-utf8-at-text-boundaries.md:108-140`). The proposed CAP/REQ allocation also follows ADR-001, with `CAP-259` and `REQ-YG-638` currently unallocated (`ARCHITECTURE.md:573-576`). |
| Single responsibility | File decoding, file encoding, CLI text emission, a lint rule, and a focused Windows witness all enforce one policy: first-party text must not inherit the host codec. They are not orthogonal product capabilities, so SPLIT is not warranted. Adjacent Windows-suite failures remain expressly excluded (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:167-175`). |
| Strategic classification | **Framework primitive.** Graph, prompt, and schema loading plus CLI diagnostics provide more than three first-party use cases, and the FR correctly rejects adding a runtime helper where explicit stdlib arguments and a static rule suffice (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:181-187`). |
| Testability | Direct RED witnesses can be derived for the loader and stream seams, and separate RED/GREEN commits match repository TDD law (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:153-164`; `.github/copilot-instructions.md:194`). The current phrase "forced cp1252 locale" does not define a reproducible mechanism, so R-4 is required before enforcement. |

## Required revisions

### R-1: Satisfy the committed research-substance gate

Replace the recommendation in the `Research` field (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:9`) with either a link to a committed `feature-requests/FR-951.research.md` or a revised in-body research record. The committed record must contain 4-6 genuine solution classes, the prior-art retrieval block and dispositions, the `is_this_a_graph` answer, and the preserved disagreement between research perspectives. Consolidate the present seven alternatives as needed; do not manufacture unanimity or omit the strongest objection. This is a no-authority gate under `.github/skills/judge-fr/doctrine.md:118-130` and `feature-requests/TEMPLATE.md:11-20`.

Promote any reproduction needed as evidence into a committed fixture, test, or research artifact. Remove the dangling `tmp/enc-repro/graph.yaml`, `tmp/enc_mojibake_probe.py`, and `tmp/fr950-ac07.log` citations from Related, or replace them with committed paths. Input closure forbids relying on those working artifacts (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:193-200`; `.github/skills/judge-fr/doctrine.md:18-24`).

### R-2: Reconcile the inventory and freeze the exact roots

Replace the 496-site table with a fresh committed inventory whose per-root counts sum to the reported total. The current rows sum to 478, leaving 18 sites unclassified (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:37-45`). Add an in-scope roots table covering every root reached by `ruff check --select PLW1514 --preview .`, including the currently omitted roots that account for the remainder. For each omitted root, either include and remediate it or list it explicitly under Out of Scope with a concrete boundary rationale; do not retain the universal "every first-party" claim while silently excluding findings.

Update the effort estimate after the inventory is reconciled. Keep AC-07's exception ledger, and define a non-UTF-8 exception as an explicit codec (including `encoding="locale"` only where inherited locale text is the actual contract) plus an FR entry explaining the boundary.

### R-3: Make the PLW1514 gate cover the remediated scope

Add a dedicated blocking Linux CI step that runs `ruff check --select PLW1514 --preview .`, or the exact frozen root list from R-2. Merely adding `PLW1514` to Ruff's global `select` does not enforce the claimed repository-wide policy because the only committed CI lint command scans `yamlgraph/` (`.github/workflows/workflow.yml:93-103`), while AC-05 and the summary claim all first-party roots (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:19-21`, `:157-158`).

Preserve the existing general `ruff check yamlgraph/` gate. Do not replace it with an unrestricted `ruff check .`, which would silently widen this FR to every already-selected Ruff rule across support and example trees.

### R-4: Define deterministic codec and pipe witnesses

Rewrite AC-01 through AC-04 and AC-10 to name test paths, fixture paths, subprocess environment, and assertions. The Windows subprocess must set `PYTHONUTF8=0`; the file-decoding witness must first assert that `locale.getencoding()` resolves to cp1252 (accepting only documented aliases), and the piped CLI witness must set `PYTHONIOENCODING=cp1252` before invoking the console entry with `stdout` and `stderr` captured as pipes. A failed codec precondition is a failed witness, not a skip. The GREEN assertions must decode captured CLI bytes as UTF-8, preserve `U+201D` and `U+20AC` exactly through graph, prompt, and schema load paths, and prove that neither Unicode exception appears.

Add a focused entry-point witness for both streams because the proposed process-wide normalization is placed in `main()` (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:123-133`; `yamlgraph/cli/__init__.py:316-325`) while the reproduced error is written to an injected `error_stream` (`yamlgraph/cli/graph_validate.py:183-194`). The witness must exercise the installed console path rather than calling `_lint_single_graph` with an already UTF-8 test stream.

Move current AC-08 to `Implementation Status` as a diagnostic command and result. An aggregate command whose exit status is expressly non-gating cannot remain an acceptance criterion (`feature-requests/FR-951-declare-utf8-at-text-boundaries.md:160`, `:167-175`). Retain the mechanically gated assertion that its captured log contains zero `UnicodeDecodeError` and zero `UnicodeEncodeError`.

### R-5: Fold the revised deliverables and criteria into the FR

Copy the frozen deliverable table and revised acceptance criteria below into FR-951, replace the superseded AC list, and update Proposed Solution and Out of Scope so they use the same roots, commands, fixtures, and gate semantics. Record all deviations discovered while reviewing Ruff's unsafe fixes in the FR before GREEN.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Committed research/reproduction evidence and folded planning revisions in `feature-requests/FR-951-declare-utf8-at-text-boundaries.md` and optionally `feature-requests/FR-951.research.md` |
| D-2 | Explicit text encodings at every PLW1514 site in the roots frozen by R-2 |
| D-3 | One CLI stdout/stderr UTF-8 normalization at `yamlgraph/cli/__init__.py:316-325` |
| D-4 | `PLW1514` configuration in `pyproject.toml` and its dedicated blocking Linux CI invocation in `.github/workflows/workflow.yml` |
| D-5 | Committed UTF-8 fixtures and focused graph, prompt, schema, corruption, and CLI-pipe witnesses under `tests/` |
| D-6 | One focused blocking `windows-latest` CI job for import and D-5 witnesses |
| D-7 | `capabilities/CAP-259-*.yaml`, `ARCHITECTURE.md`, and `REQ-YG-638` test markers |
| D-8 | One FR-951 fix changelog fragment, implementation-status record, and diary entry |

Not authorized: new dependencies; a text-I/O wrapper abstraction; provider, YAML parser, or third-party code changes; `PYTHONUTF8` as a shipped-user requirement; locale mutation outside the witnesses; changes to non-PLW1514 Ruff policy; broad CLI output refactoring; a full Windows test matrix; fixes for optional dependencies, POSIX assumptions, or any other Windows-suite defect; CAP or REQ work beyond CAP-259/REQ-YG-638.

## Revised acceptance criteria

- [ ] AC-01: The committed R-2 inventory names every root reported by `ruff check --select PLW1514 --preview .`, its per-root counts sum to the recorded total, and every root is explicitly in scope or out of scope.
- [ ] AC-02: Under a Windows subprocess with `PYTHONUTF8=0` and an asserted cp1252 `locale.getencoding()`, focused tests load committed UTF-8 fixtures containing `U+201D` and `U+20AC` through graph, prompt, and schema loaders and assert the exact source characters.
- [ ] AC-03: A focused silent-corruption test asserts that each loaded value equals the explicit-UTF-8 reference value exactly, not merely that loading did not raise.
- [ ] AC-04: With `PYTHONUTF8=0`, `PYTHONIOENCODING=cp1252`, and captured pipes, the installed `yamlgraph graph lint` command exits zero for the Unicode graph fixture; captured stdout and stderr decode as UTF-8 and contain neither `UnicodeDecodeError` nor `UnicodeEncodeError`.
- [ ] AC-05: A focused installed-entry-point witness exercises a non-ASCII status or error glyph on each applicable output stream and exits without a Unicode exception; calling an internal lint helper with a prepared UTF-8 stream does not satisfy this criterion.
- [ ] AC-06: `ruff check --select PLW1514 --preview .` exits zero, and every non-bare fix is recorded in the FR with its codec and reason.
- [ ] AC-07: `PLW1514` is present in `[tool.ruff.lint] select`, the existing general `ruff check yamlgraph/` CI gate remains, and a dedicated blocking Linux CI step runs the exact AC-06 command.
- [ ] AC-08: A blocking `windows-latest` job installs the project, imports `yamlgraph`, asserts the required codec preconditions, runs AC-02 through AC-05, and runs no full unit-suite gate.
- [ ] AC-09: `python scripts/req_coverage.py --strict` exits zero on Windows with `PYTHONUTF8` unset, `CAP-259` and `REQ-YG-638` are allocated in the registry and `ARCHITECTURE.md`, and every new test carries `@pytest.mark.req("REQ-YG-638")`.
- [ ] AC-10: The focused witnesses are committed RED before production/configuration fixes and GREEN afterward in separate commits.
- [ ] AC-11: The Windows non-slow unit-suite diagnostic is recorded in Implementation Status with its command, exit status, and zero counts for both Unicode exception classes; its aggregate pass/fail is context and is not a merge gate.
- [ ] AC-12: A `type: fix` changelog fragment names FR-951 and REQ-YG-638; Implementation Status records dated AC commands and results; one `docs/diary/` entry records a trap or insight, a heuristic, and a `Seed:`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-5 and the revised acceptance criteria are folded into committed FR-951 before implementation authority activates. | GATE |
| C-2 | Human review must approve the changes to `pyproject.toml` and `.github/workflows/workflow.yml`; CI enforcement infrastructure is adversarial input under `.github/skills/judge-fr/doctrine.md:97-101`. | GATE |
| C-3 | RED witnesses must fail for missing explicit codec/stream normalization, not for an unavailable fixture, import error, skipped locale precondition, or optional dependency. | GATE |
| C-4 | The dedicated PLW1514 CI command must cover exactly the roots frozen by R-2 and must remain blocking on pull requests and merge-group candidates. | GATE |
| C-5 | Unsafe Ruff fixes require review; an intentionally non-UTF-8 boundary must use an explicit codec and appear in the FR exception ledger. No blanket ignore is permitted. | GATE |
| C-6 | No adjacent Windows-suite, dependency, parser, provider, generic CLI-output, or non-PLW1514 lint work may enter enforcement. | GATE |
| C-7 | This draft judgement is advisory until human-reviewed. | GATE |

Authority granted: none yet; after C-1 and C-2 are satisfied, authority is limited to D-1 through D-8 under AC-01 through AC-12.
