# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-24.md](diary-2026-02-24.md) — 11 entries from 2026-02-24.

---

## 2026-02-27: FR-106 Enforce Pipeline — Tooling Mirrors the Doctrine

**Context:** Implemented parallel development pipeline using Git worktrees. Shell script creates isolated environment (`tmp/worktrees/feat/<branch>`), symlinks `.venv`, runs 4-phase copilot graph (implement → test → precommit → submit), cleans up on exit.

**Observation:** The pipeline structure mirrors the Scripture's enforcement rite: Research → Plan → Judge → Enforce → Purge → Submit → Distill. Each phase is a discrete copilot node with session continuation, meaning the agent accumulates context across all four phases. The worktree isolation ensures `main` stays clean while feature work happens in parallel.

**Trap Avoided — Premature Abstraction:** Initial instinct was to make the Python helpers more sophisticated (branch naming patterns, worktree registry, cleanup scheduler). Resisted. Three simple functions suffice: `derive_branch_name()`, `construct_worktree_path()`, `validate_clean_working_tree()`. The shell script handles orchestration. The graph handles LLM interaction. Each layer does one thing.

**Heuristic — Layered Simplicity:** When building automation that spans shell, Python, and YAML, keep each layer minimal. Shell for lifecycle orchestration (git operations, traps, cleanup). Python for pure functions (string transformation, validation). YAML for LLM choreography (prompts, state, edges). Complexity in any layer is a sign the responsibility belongs elsewhere.

**Insight:** The TDD sequence (19 tests written before implementation stabilized) caught several edge cases: untracked files vs staged changes, concurrent worktree paths, script exit codes. The tests serve as executable documentation — reading `test_worktree_helpers.py` explains the contract faster than any prose.

**Seed:** The enforce pipeline assumes sequential phases. What if some phases could run in parallel? Could `test` and `demo` be independent map targets? Would the session context still cohere if phases fork and merge?

---

## 2026-02-27: Inquisitor Audit — Clean Sheet on Session Test Demo

**Context:** Audit of HEAD (`c89e6e3`), covering 5 commits. High-water mark from prior audit: `8915290`. Only `c89e6e3` (`docs(examples): FR-105 add session continuation test demo`) is new — 9 files, 471 insertions, 75 deletions. Prior audit's ⚠ DRIFT (missing FR-107 diary) is tracked for resolution.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits & FR traceability (Commandments 10, ADR-001).** `docs(examples): FR-105 ...` — valid type, scope, FR reference. CHANGELOG already carries the FR-105 feature entry; `docs` commit on an example correctly omits additional entry. `req_coverage.py --strict` passes clean.
- ✓ COMPLIANT — **noqa Confessions.** Two `# noqa: E402` in `run_demo.py` for post-env-var imports. Both confessed as CONF-124 and CONF-125 in `docs/confessions.md`. Commit message explicitly references them. Prior suppressions (CONF-200, CONF-204) still intact. No unconfessed suppressions in codebase.
- ✓ COMPLIANT — **Diary entry (Sermon: Distill).** "FR-105 Session Continuation — Proof by Noir" is a thorough metacognitive reflection: experiment design, hypothesis-distinguishing test, named heuristic, and a forward-looking Seed on session-aware graph patterns. This closes the prior 3-audit ⚠ DRIFT on missing FR-105 implementation diary.
- ✓ COMPLIANT — **ADR-001: REQ-YG-105 remains resolved.** Verified in ARCHITECTURE.md at lines 305 and 583. CAP-30 shows 3/3 reqs, 30 tests. The phantom requirement saga is closed.
- ⚠ DRIFT — **FR-107 implementation diary still absent (Sermon: Distill) — second audit noting.** `feat(req-coverage): FR-107 add architecture cross-check` shipped in `8915290` with no dedicated metacognitive entry. The insight (phantom requirements, tautological self-validation) appears in the FR-105 diary but the Sermon requires per-task reflection. Given FR-107's narrow scope (tooling fix for a known gap), this remains minor drift rather than violation.

**Heuristic:** A commit that arrives fully confessed — noqa entries referenced in the commit message, diary written in the same commit, no new capability requiring architecture updates — is a sign of mature process internalization. The doctrine is no longer external constraint but habitual practice. The gap is FR-107's missing diary, suggesting the habit weakens for "infrastructure" commits perceived as less creative. Infrastructure deserves reflection too; the best Seeds often come from tooling work.

**Seed:** Five consecutive Inquisitor audits now exist in this diary. Is the audit itself subject to entropy? Should the format be tightened — e.g., a structured YAML audit log that could be queried, or a summary table tracking violation resolution timelines — to prevent the diary from becoming a wall of prose that no one reads?

---

## 2026-02-27: FR-105 Session Continuation — Proof by Noir

**Context:** Designed experiment to answer: Does Copilot's `--continue` flag actually preserve conversation context, or does it rebuild from file state? Created `examples/demos/session-test/` with two-node pipeline — Node 1 creates characters, Node 2 writes their meeting using only session memory.

**Experiment Design:**
- Node 1 (`create_characters`): Invents two characters with unique names and traits
- Node 2 (`write_meeting`): Prompt references "these two characters" without any character info
- Node 2 uses `continue_session: true` → `--continue` flag
- If session works: Node 2 uses exact names and traits from Node 1
- If session fails: Node 2 invents new characters or is confused

**Result:** Session continuation is **real context preservation**, not file reconstruction.

Noir genre test produced Milo Varnish (forensic accountant, glass eye, prices everything) and Sable Morrigan (ambulance dispatcher, throat scar, hums when nervous). Node 2 — with zero character data in prompt — wrote a scene using both exact names, the glass eye, the pricing quirk ("That conversation? Worth about three hundred"), the scar, and even *Moonlight Serenade* humming. The session memory is genuine.

**Trap Avoided:** Assumed `--continue` might just provide workspace context (recent files edited) rather than actual conversation history. Designed experiment to distinguish these cases. If it had been file-based, Node 2 would have no knowledge of characters invented purely in conversation.

**Heuristic:** *When testing an abstraction's behavior, design experiments where the two hypothesized implementations would produce distinguishably different outputs.* A test that passes under both hypotheses proves nothing. The "characters known only via session memory" design made file-vs-conversation reconstruction produce different observable outcomes.

**Seed:** Session continuation enables multi-agent workflows where context accumulates without explicit state plumbing. What graph patterns become possible when agents can "remember" prior phases? Could the Enforcer's demo phase benefit from knowing *how* the implementation evolved, not just *what* was implemented?

---

## 2026-02-27: Inquisitor Audit — Phantom Slain, Tooling Gate Closes

**Context:** Audit of HEAD (`8915290`), covering 5 commits. High-water mark from prior audit: `8d0e4bf`. Only `8915290` (`feat(req-coverage): FR-107 add architecture cross-check`) is new — 12 files, 504 insertions, 66 deletions. This commit directly addresses the ✗ VIOLATION flagged in three consecutive prior audits (phantom REQ-YG-105) and implements the tooling fix (architecture cross-check) recommended by the Inquisitor's Seeds.

**Findings:**

- ✓ COMPLIANT — **ADR-001: REQ-YG-105 phantom resolved — three-audit violation closed.** REQ-YG-105 now appears in ARCHITECTURE.md (lines 305, 583) with full description. `req_coverage.py --strict` passes. The traceability triangle (architecture → requirement → test) is intact for the first time since FR-105 landed.
- ✓ COMPLIANT — **Conventional Commits, CHANGELOG, FR traceability (Commandments 10, ADR-001).** `feat(req-coverage): FR-107 ...` — valid format. CHANGELOG entry under [Unreleased]. Feature request `FR-107-req-architecture-cross-check.md` exists and marked Implemented. 3 new tests tagged `@pytest.mark.req("REQ-YG-063")`.
- ✓ COMPLIANT — **Entropy cleanup (Commandment 8).** Garbage "Git Report" diary entry removed. FR-105 implementation diary added (previously flagged as missing in 3 audits). Net positive entropy reduction in `docs/diary.md`.
- ✓ COMPLIANT — **noqa Confessions.** 2 existing suppressions (ANN001, ARG002), both confessed in CONF-200/CONF-204. No new suppressions.
- ⚠ DRIFT — **No FR-107 implementation diary (Sermon: Distill).** Chaplain approval for FR-107 exists. The key insight (phantom requirements, tautological self-validation) is captured in the FR-105 implementation diary, which FR-107 directly resolves. However, the Sermon strictly requires a dedicated metacognitive entry per task. Given the 0.5-day scope and that the insight is recorded, this is minor.

**Heuristic:** The Inquisitor's power is proportional to the tooling behind it. Three audits flagging the same violation produced zero remediation — but the moment the violation was encoded as a CI-blocking check (`req_coverage.py --strict` architecture cross-check), it was fixed in the same commit. Advisory findings decay; automated gates endure. The audit's highest-value output is not the finding itself but the Seed that becomes a tool.

**Seed:** The phantom-requirement gap is now closed by tooling. Are there analogous gaps where the audit relies on manual inspection that could be automated — e.g., verifying CHANGELOG entries exist for every `feat`/`fix` commit, or that every `# noqa` has a matching CONF-XXX in confessions.md?

---

## 2026-02-27: Inquisitor Audit — Third Strike on Phantom Requirement

**Context:** Audit of HEAD (`8d0e4bf`), covering 5 commits. High-water mark from prior audit: `5544083`. Only `8d0e4bf` (`refactor(examples): simplify enforcer to take only FR ID`) is new — 4 YAML/markdown files, net -15 lines, zero Python. Re-checking the persistent ✗ VIOLATION (REQ-YG-105 phantom requirement) now flagged in two prior audits.

**Findings:**

- ✗ VIOLATION — **ADR-001: REQ-YG-105 absent from ARCHITECTURE.md — third consecutive audit.** CAP-30 row (line 305) still lists only `REQ-YG-087, REQ-YG-089`. Tests at `test_copilot_node.py:514` and `test_linter_patterns_copilot.py:13` tag `REQ-YG-105`. `req_coverage.py` includes it in range. The requirement text does not exist in the architecture document. Three audits, zero remediation. This has graduated from debt to delinquency.
- ✓ COMPLIANT — **Conventional Commits (Commandment 10).** `refactor(examples):` — valid type and scope. Commit message is descriptive and concise.
- ✓ COMPLIANT — **CHANGELOG & noqa (Commandments 8, 10).** `refactor` on examples correctly omits CHANGELOG. 2 noqa suppressions (ANN001, ARG002) both confessed in CONF-200/CONF-204. No new suppressions.
- ✓ COMPLIANT — **Code simplification (Commandment 8: Kill entropy).** Net -15 lines. Reduced enforcer interface from multiple path variables to a single `fr_id`. Entropy decreased.
- ⚠ DRIFT — **FR-105 implementation diary missing (Sermon: Distill) — third audit noting.** Three commits now ship under FR-105 (`38dbfb4` feat, `5544083` docs, `8d0e4bf` refactor) with no metacognitive reflection on the implementation process itself.

**Heuristic:** Three consecutive audits flagging the same unresolved violation exposes a systemic gap: the audit process has no enforcement mechanism beyond diary notation. The Inquisitor can diagnose but cannot compel. Without a blocking gate — whether CI check, pre-commit hook, or structured debt tracker — violations persist indefinitely in the diary's narrative log where they are easily overlooked. The prior audit's Seed (structured debt table) remains the cheapest fix: make violations queryable, not just readable.

**Seed:** Should the Inquisitor be granted authority to create a blocking `docs/debt.md` file that pre-commit or CI checks for unresolved ✗ items, converting audit findings from advisory to enforceable?

---

## 2026-02-27: Inquisitor Audit — Phantom Requirement Persists, Enforcer Demo Lands Clean

**Context:** Audit of HEAD (`5544083`), covering 5 commits. Applying high-water mark: prior audit judged through `38dbfb4`. Only `5544083` (`docs(examples): FR-105 add enforcer pipeline demo`) is new — 4 YAML/markdown files, 182 insertions, zero Python. The prior audit's ✗ VIOLATION (REQ-YG-105 phantom requirement) is re-checked for resolution. Prior DRIFT items (missing FR-105 implementation diary, garbage diary entry) also tracked.

**Findings:**

- ✗ VIOLATION — **ADR-001: REQ-YG-105 still absent from ARCHITECTURE.md.** CAP-30 row at line 305 lists only `REQ-YG-087, REQ-YG-089`. Tests at `test_copilot_node.py:514` and `test_linter_patterns_copilot.py:13` tag `REQ-YG-105`, and `req_coverage.py` includes it in its range, but the requirement text does not exist in the architecture document. Second consecutive audit flagging this. The traceability chain remains broken.
- ✓ COMPLIANT — **Conventional Commits (Commandment 10).** `5544083` uses `docs(examples): FR-105 ...` — valid type, scope, and FR reference.
- ✓ COMPLIANT — **CHANGELOG & noqa (Commandments 8, 10).** `docs` commit correctly omits CHANGELOG. 2 noqa suppressions (ANN001, ARG002) both confessed in CONF-200/204. No new suppressions.
- ⚠ DRIFT — **FR-105 implementation diary still missing (Sermon: Distill).** Two commits now ship under FR-105 (`38dbfb4` feat, `5544083` docs) with no metacognitive reflection on the implementation. The planning diary ("Chaplain Approved") exists but the coding diary does not. This is the second audit noting the gap.
- ✓ COMPLIANT — **Enforcer demo structure.** `examples/enforcer/` follows the three-layer pattern: graph YAML orchestrates, prompts in `prompts/`, README documents. No hardcoded prompts. State expression `{state.enforce_result.session_id}` correctly uses the new session continuation feature.

**Heuristic:** A violation flagged in two consecutive audits with no intervening fix is no longer drift — it is accruing debt. The prior audit's Seed asked whether `req_coverage.py` should validate against ARCHITECTURE.md text. The answer is now empirically yes: without that cross-check, the phantom requirement survived a full commit cycle undetected by CI. Until the tooling gap is closed, the Inquisitor must manually verify ARCHITECTURE.md on every `feat` audit.

**Seed:** Should unresolved ✗ VIOLATION items from prior audits be tracked in a structured debt table (e.g., `docs/debt.md` or a SQL-based ledger) so they cannot silently age out of the diary's rolling window?

---

## 2026-02-27: Inquisitor Audit — Return from Quiescence, Phantom Requirement Found

**Context:** Audit of HEAD (`38dbfb4`), covering 5 commits. Applying the high-water mark heuristic: commits `e57d8ae`, `cd41906`, `3bdb3c2`, `a90ff61` were already judged compliant in prior audits. Deep audit focused on `38dbfb4` (`feat(copilot): FR-105 add session continuation support`) — the first `feat` commit touching Python since the quiescence window began. This is the "return from quiescence" deep audit anticipated by prior Seeds. Ran `req_coverage.py --strict` (passed: CAP-30 3/3 reqs, 30 tests) and verified all `noqa` suppressions (2 existing, both confessed).

**Findings:**

- ✗ VIOLATION — **ADR-001: REQ-YG-105 missing from ARCHITECTURE.md.** Commit message claims "REQ-YG-105 added to CAP-30" but the requirement appears nowhere in ARCHITECTURE.md. It was added only to `req_coverage.py` (lines 29, 185), making `--strict` pass without an actual architecture entry. The CAP-30 table row still lists only `REQ-YG-087, REQ-YG-089`. The detailed section (### 30. Copilot Node) has two requirement rows, not three. Tests reference a phantom requirement — the traceability chain is broken at the architecture layer.
- ⚠ DRIFT — **Implementation diary missing (Sermon: Distill).** FR-105 planning/approval is documented ("Chaplain — Copilot Node Session Continuations Approved") but the implementation itself — 994 insertions across 14 files, 12 new tests, new linter patterns — has no metacognitive reflection. The Sermon requires naming cognitive traps and extracting heuristics from the coding process, not just the planning process.
- ⚠ DRIFT — **Committed garbage diary entry.** The "Git Report" entry at the bottom of diary.md is a verbatim Xcode-license error message offering no insight. This is entropy in a living document (Commandment 8).
- ✓ COMPLIANT — **Conventional Commits (Commandment 10).** All 5 commits well-formed. `38dbfb4` uses `feat(copilot): FR-105 ...` with scope and FR reference.
- ✓ COMPLIANT — **CHANGELOG & test tags (Commandment 10, ADR-001).** FR-105 documented under [Unreleased] with full detail. Both test files carry `@pytest.mark.req("REQ-YG-105")`. No new `noqa` suppressions.

**Heuristic:** A green `req_coverage.py --strict` does not prove architectural documentation exists — it only proves tests are tagged and the script's expected range includes the ID. The script validates the test→requirement mapping but not the requirement→architecture-text mapping. ADR-001 compliance requires both: the requirement must be *described* in ARCHITECTURE.md **and** *tagged* in tests. When the coverage script is updated in the same commit as the tests, the cross-check becomes tautological. Fix: `req_coverage.py` should parse ARCHITECTURE.md for requirement IDs and fail if a tagged ID has no corresponding row.

**Seed:** Should `req_coverage.py --strict` be extended to verify that every REQ-YG-XXX in its expected range also appears as a table row in ARCHITECTURE.md, closing the phantom-requirement gap?

---

## 2026-02-26: Inquisitor Audit — Fifth Docs Window, High-Water Mark Reached

**Context:** Audit of HEAD (`e57d8ae`), covering 5 commits: `e57d8ae` (docs: continue reading link), `cd41906` (docs: link ebook chapters), `3bdb3c2` (fix: raw tags for Jinja2), `a90ff61` (fix: front matter for Liquid), `1760d7e` (fix: Jekyll config). One new commit (`e57d8ae`) since the prior audit; four commits overlap with prior audit window. All docs-only — zero Python files changed. Fifth consecutive docs-only audit window.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use valid Conventional Commits format. `e57d8ae` uses `docs:` without scope — acceptable per spec. The three `fix(docs):` commits remain the same iterative Jekyll/Liquid series noted in prior audits.
- ✓ COMPLIANT — **CHANGELOG coverage (Commandment 10):** `docs:` type commits correctly omit CHANGELOG entries. `fix(docs)` commits covered by existing "GitHub Pages Build" entry in 0.4.58. No gaps.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** Zero Python changes. No new capabilities, tests, or requirements. Vacuously compliant.
- ✓ COMPLIANT — **noqa Confessions:** 2 suppressions in codebase (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`), both documented in `docs/confessions.md` with CONF-XXX entries. No drift since last audit.
- ✓ COMPLIANT — **Retired findings stable:** Co-authored-by trailer retired in audit #6. `76f2873` CHANGELOG debt formally waived. Neither has regressed. 0/5 commits include the trailer — consistent with retirement decision.

**Heuristic:** Five overlapping docs-only audit windows confirm diminishing marginal value of re-auditing the same commits. The prior audit's Seed question — whether to adopt a "high-water mark" — is now empirically justified: auditing `e57d8ae` alone would have been sufficient, since the other four commits were already judged compliant. For future audits, the Inquisitor should record the audited HEAD SHA and only deeply audit commits newer than the last recorded high-water mark, while performing a shallow consistency check on the overlap.

**Seed:** When the next `feat` or `fix` commit touching Python lands, should the Inquisitor perform a "return from quiescence" deep audit — re-running `req_coverage.py --strict` and `noqa_coverage.py` as a full baseline reset before judging the new commits?

---

## 2026-02-26: Inquisitor Audit — Fourth Consecutive Docs Window, Steady State Holds

**Context:** Audit of HEAD (`cd41906`), covering 5 commits: `cd41906` (docs: link ebook chapters to GitHub rendered markdown), `3bdb3c2` (fix: raw tags for Jinja2), `a90ff61` (fix: front matter for Liquid), `1760d7e` (fix: Jekyll config), `86ff405` (docs: eBook ToC landing page). One `docs:`, three `fix(docs):`, one `docs(ebook):` — zero Python files changed, 12 files touched (docs, config, CHANGELOG). All within FR-103 eBook pipeline and GitHub Pages build scope. The newest commit `cd41906` uses bare `docs:` type (no scope) — a minor style variance but still Conventional Commits compliant. This is the fourth consecutive docs-only audit window. Prior audits formally waived the `76f2873` CHANGELOG debt and retired the Co-authored-by trailer finding.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use valid Conventional Commits format. `cd41906` uses `docs:` without scope — acceptable per spec (scope is optional). The three `fix(docs):` commits are an iterative series fixing the same Jekyll/Liquid issue — already noted in prior audit as acceptable rapid iteration.
- ✓ COMPLIANT — **CHANGELOG coverage (Commandment 10):** Three `fix(docs)` commits covered by "GitHub Pages Build" entry in 0.4.58. Two `docs:` commits correctly omit CHANGELOG (docs-type commits don't require entries). No new `feat` commits — no gaps.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** Zero Python changes. No new capabilities, tests, or requirements. Vacuously compliant.
- ✓ COMPLIANT — **noqa Confessions:** 2 suppressions in codebase (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`), both documented in `docs/confessions.md` with proper CONF-XXX entries. No drift.
- ✓ COMPLIANT — **Diary entries (Sermon: Distill):** Four prior Inquisitor audits recorded today. The audit cadence itself serves as the diary mechanism during docs-only windows.

**Heuristic:** Four consecutive compliant docs-only windows confirm the project is in a stable documentation-refinement phase. The audit value during quiescence is not in catching violations but in maintaining the heartbeat — verifying that retired findings stay retired (Co-authored-by, `76f2873` CHANGELOG) and no new debt silently accrues. The real stress test remains the next Python-touching `feat` commit, where code-centric rules (TDD, ADR-001, noqa) will have material surface area to audit.

**Seed:** The four audits today all cover overlapping commit windows (each shifted by one commit). Should the Inquisitor adopt a "high-water mark" — only auditing commits newer than the last audited HEAD — to avoid redundant coverage of already-judged commits?

---

## 2026-02-26: Inquisitor Audit — Quiescent Docs Window, Steady State Confirmed

**Context:** Audit of HEAD (`3bdb3c2`), covering 5 commits: `3bdb3c2` (fix: raw tags for Jinja2), `a90ff61` (fix: front matter for Liquid), `1760d7e` (fix: Jekyll config), `86ff405` (docs: eBook ToC landing page), `a0ea832` (chore: clean up old ebook versions). Three `fix(docs)`, one `docs(ebook)`, one `chore(ebook)` — zero Python files changed, ~9,800 lines removed (old ebook cleanup), ~290 lines added. All within FR-103 eBook pipeline and GitHub Pages build scope. This is the third consecutive docs-only audit window. Previous audit formally waived the `76f2873` CHANGELOG debt and retired the Co-authored-by trailer finding.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): description` format. The three `fix(docs):` commits are iterative fixes to the same Jekyll/Liquid issue — acceptable as a rapid-iteration sequence, not commit-spam.
- ✓ COMPLIANT — **CHANGELOG coverage (Commandment 10):** The three `fix(docs)` commits are collectively covered by the "GitHub Pages Build" entry in 0.4.58. `docs:` and `chore:` commits correctly omit CHANGELOG entries. No new `feat` commits — no new gaps.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** Zero Python changes. No new capabilities, tests, or requirements. Vacuously compliant.
- ✓ COMPLIANT — **noqa Confessions:** Zero Python changes — no new suppressions possible.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the trailer. Per the previous audit, the Inquisitor has retired this as a flagged item. Noting here for continuity only — this will not be raised again unless mechanical enforcement (commit-msg hook or CI gate) is implemented.

**Heuristic:** Three consecutive clean docs-only audit windows confirm that the waiver/retirement decisions from prior audits were correct — no new debt has accrued, and the audit process is no longer repeating stale findings. The audit cadence during quiescent windows serves as a heartbeat: confirming the system is alive and clean, even when there is nothing to catch. The real test of the graduated escalation ladder will come when the next `feat` or `fix` commit touching Python lands.

**Seed:** The three `fix(docs)` commits addressing the same Jekyll/Liquid issue suggest a "fix-test-fix" anti-pattern for non-CI-validated changes (GitHub Pages builds aren't locally testable by default). Should the project add a local Jekyll build check (e.g., `bundle exec jekyll build`) to the docs workflow to catch these before push?

---

## 2026-02-26: Inquisitor Audit — Clean Docs Window, Retired Findings Holding

**Context:** Audit of HEAD (`a90ff61`), covering 5 commits: `a90ff61` (fix: front matter for Jinja2 files), `1760d7e` (fix: Jekyll config), `86ff405` (docs: eBook ToC landing page), `a0ea832` (chore: clean up old ebook versions), `57d9d06` (docs: LinkedIn promo). Two `fix(docs)`, two `docs(ebook)`, one `chore(ebook)` — zero Python files changed. All within FR-103 eBook pipeline scope. Audited against Commandments, ADR-001, Confessions, and the Sermon. This is the first audit since the previous audit formally waived the chronic `76f2873` CHANGELOG debt and retired the Co-authored-by trailer finding.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): description` format. `fix(docs):`, `docs(ebook):`, `chore(ebook):` all well-formed.
- ✓ COMPLIANT — **CHANGELOG coverage (Commandment 10):** Both `fix(docs)` commits (`a90ff61`, `1760d7e`) covered by the "GitHub Pages Build" CHANGELOG entry. `86ff405` covered by "eBook Landing Page" entry. `docs:` and `chore:` commits correctly omit CHANGELOG entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** Zero Python files changed. No new capabilities, tests, or requirements needed. Vacuously compliant.
- ✓ COMPLIANT — **noqa Confessions:** Zero Python changes — no new suppressions possible.
- ✓ COMPLIANT — **Retired findings stable:** The Co-authored-by trailer retirement (audit #6) and `76f2873` CHANGELOG waiver remain in effect. No new `feat` or `fix` commits touching Python have appeared to re-trigger code-centric audit checks.

**Heuristic:** A fully compliant docs-only window following a debt-closing audit is the expected steady state. The value of auditing it is not in catching violations but in confirming that retired findings stay retired and no new debt accrues silently. The audit cadence itself is the guardrail — skipping "clean" windows would create blind spots where drift could accumulate unnoticed between code-heavy windows.

**Seed:** Now that the chronic debt items are formally closed, should the next code-touching commit window trigger a deeper "return from quiescence" audit — checking not just the new commits but re-running `req_coverage.py` and `noqa` checks as a baseline reset?

---

## 2026-02-26: Inquisitor Audit — Docs-Only Window, Closing Chronic Debt

**Context:** Audit of HEAD (`1760d7e`), covering 5 commits: `1760d7e` (fix: Jekyll config), `86ff405` (docs: eBook ToC landing page), `a0ea832` (chore: clean up old ebook versions), `57d9d06` (docs: LinkedIn promo), `771ebdc` (docs: v3 generation). One `fix`, one `chore`, three `docs` — zero Python files changed. All within FR-103 eBook pipeline scope. Audited against Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): description` format. `fix(docs):`, `docs(ebook):`, `chore(ebook):` all well-formed.
- ✓ COMPLIANT — **CHANGELOG coverage (Commandment 10):** `1760d7e` fix covered by "GitHub Pages Build" entry; `86ff405` covered by "eBook Landing Page" entry. `docs:`/`chore:` commits correctly omit CHANGELOG. The current 5-commit window is clean.
- ✗ VIOLATION — **Chronic CHANGELOG gap — `76f2873` (Commandment 10):** 6th consecutive audit. `feat(ebook): FR-103 per-chapter graphs with parallel runner` still absent from CHANGELOG 0.4.58. Per the escalation ladder proposed in audit #5: this item is now **formally waived** — the FR-103 scope is broadly covered by the existing judge-amend subgraph entry ("Rewired graph to 18 nodes"), and no further Python capability was shipped. The Inquisitor closes this item. If a future `feat` commit lacks a CHANGELOG entry, the 3-audit escalation ladder applies fresh.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** No new Python code or tests. Prior coverage clean (53 noqa, 54 confessions, 0 undocumented).
- ⚠ DRIFT — **Co-authored-by trailer — final disposition:** 0/5 commits include the trailer. 11th consecutive audit. Per the ultimatum in audit #5, the Inquisitor ceases flagging this item. **Recommendation: retire from Scripture or automate via `commit-msg` hook.** The Inquisitor will not raise this again unless the rule is mechanically enforced.

**Heuristic:** A docs-only commit window is the cleanest audit possible — no code means no new surface for violations. But it also means zero opportunity to verify enforcement of code-centric rules (ADR-001, TDD, noqa). The Inquisitor must note when a window is "vacuously compliant" — compliance by absence is not the same as compliance by discipline. True signal comes from auditing windows that include `feat` and `fix` commits touching Python.

**Seed:** Should the Inquisitor skip audits on docs-only windows entirely (since code rules cannot be tested), or is witnessing even vacuous compliance valuable for maintaining audit cadence?

---

## 2026-02-26: Inquisitor Audit — Landing Page, Governance Fatigue

**Context:** Audit of HEAD (`86ff405`), covering 5 commits: `86ff405` (docs: eBook ToC landing page), `a0ea832` (chore: clean up old ebook versions), `57d9d06` (docs: LinkedIn promo), `771ebdc` (docs: v3 generation), `76f2873` (feat: per-chapter graphs). Four `docs`/`chore` commits and one `feat` — all within FR-103 eBook pipeline scope. No Python code changed in the 4 newest commits. Audited against Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✗ VIOLATION — **CHANGELOG debt now 5 audits old (Commandment 10):** `76f2873` (`feat`: per-chapter graphs, parallel runner, `test_copilot_subgraph_variables.py`) still has no CHANGELOG entry under 0.4.58. Fifth consecutive audit. Per the graduated heuristic from audit #4: this has crossed from "accepted debt" to "governance failure." The audit process itself is degraded — repeating an identical finding 5 times without resolution proves neither the finding nor the process has teeth. **Action required:** either add the CHANGELOG entry now, or formally document this as a waived deviation in the next release notes, so the audit can close the item.
- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): FR-XXX description` format. `docs:` and `chore:` commits correctly omit CHANGELOG entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** No new Python code or test files in the 4 newest commits. Prior audit confirmed REQ-YG-091/092 coverage clean with 15 tests.
- ✓ COMPLIANT — **noqa Confessions:** Zero new `# noqa` suppressions across the 5-commit range. No Python files modified.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required trailer. 10th+ consecutive audit flagging this. This rule meets the sunset criterion proposed in audit #4's Seed. It should be formally retired or mechanically enforced — the Inquisitor will no longer flag it after this entry unless action is taken.

**Heuristic:** An audit that repeats the same findings verbatim across 5+ cycles is not auditing — it is echoing. When the Inquisitor's findings become predictable, the audit loses its diagnostic value. The cure: escalate with a deadline. Any ✗ finding surviving 3 audits without remediation must be either (a) resolved before the next version bump, or (b) formally waived with a rationale recorded in CHANGELOG, at which point the Inquisitor closes the item. Infinite repetition is the enemy of signal.

**Seed:** Should the Scripture codify an "audit escalation ladder" — 1st flag = finding, 2nd flag = accepted debt, 3rd flag = mandatory resolution-or-waiver before next release — to prevent the Inquisitor from becoming a broken record?

---

## 2026-02-26: Inquisitor Audit — Cleanup Commit, Chronic Enforcement Gaps

**Context:** Audit of HEAD (`a0ea832`), covering 5 commits: `a0ea832` (chore: clean up old ebook versions), `57d9d06` (docs: FR-103 LinkedIn promo), `771ebdc` (docs: FR-103 v3 generation), `76f2873` (feat: FR-103 per-chapter graphs), `a9bffc8` (fix: FR-103 per-chapter persistence). One `chore`, two `docs`, one `feat`, one `fix` — all within FR-103 eBook pipeline scope. Audited against Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✗ VIOLATION — **CHANGELOG gap now 4 audits old (Commandment 10):** `76f2873` (`feat`: per-chapter graphs, parallel runner, `test_copilot_subgraph_variables.py`) still has no CHANGELOG entry under 0.4.58. Fourth consecutive audit citing this. Per the graduated heuristic: this is no longer a finding — it is an enforcement failure. Either add the entry or formally waive it in the next release.
- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): description` format. `chore:` and `docs:` commits correctly omit CHANGELOG entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** `req_coverage.py` reports CAP-32 clean (2/2 reqs, 15 tests). All tests in `test_copilot_subgraph_variables.py` carry `@pytest.mark.req("REQ-YG-092")`. No orphans.
- ✓ COMPLIANT — **noqa Confessions:** Zero new `# noqa` Python suppressions in the 5-commit range.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required trailer. 9th+ audit flagging this. This rule is dead letter — it has never been enforced. Recommend formal retirement from Scripture or mechanical injection via `commit-msg` hook.

**Heuristic:** A rule that has been violated in every audit for 9+ cycles without remediation is not a rule — it is aspirational prose. The Inquisitor's duty is to distinguish enforceable law from unenforced aspiration. Dead-letter rules should be either automated into existence (hook, CI gate) or formally struck from the canon to preserve the audit's credibility.

**Seed:** Should the Scripture include a "sunset clause" — any rule flagged as DRIFT in 5+ consecutive audits is automatically nominated for retirement vote, forcing an explicit keep-or-kill decision?

---

## 2026-02-26: Inquisitor Audit — LinkedIn Promo, Aging CHANGELOG Debt

**Context:** Audit of HEAD (`57d9d06`), covering 5 commits: `57d9d06` (docs: FR-103 LinkedIn promo), `771ebdc` (docs: FR-103 v3 generation), `76f2873` (feat: FR-103 per-chapter graphs), `a9bffc8` (fix: FR-103 per-chapter persistence), `0704063` (docs: FR-103 diary). One `feat`, one `fix`, three `docs` commits — all within FR-103 eBook pipeline scope. Audited against Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✗ VIOLATION — **CHANGELOG gap now 3 audits old (Commandment 10):** `76f2873` (`feat`: per-chapter graphs, parallel runner, `test_copilot_subgraph_variables.py`) still has no CHANGELOG entry. Third consecutive audit citing this. Per the heuristic from the previous audit, this is now "accepted debt" — it must be either fixed before next release or formally waived.
- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): FR-XXX description` format. The three `docs:` commits correctly omit CHANGELOG entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091, REQ-YG-092 present in ARCHITECTURE.md. All 3 tests in `test_copilot_subgraph_variables.py` carry `@pytest.mark.req("REQ-YG-092")`. No orphan tests.
- ✓ COMPLIANT — **noqa Confessions:** `noqa_coverage.py` reports 53 suppressions, 54 confessions, 0 undocumented. Clean.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required trailer. 8th+ audit flagging this. This is no longer drift — it is an unenforced rule. Recommend either adding a `commit-msg` hook to inject the trailer automatically, or removing the requirement from the Scripture.

**Heuristic:** When an audit finding survives three cycles without action, the finding is not the problem — the enforcement mechanism is. Either automate the fix (hook, CI gate) or formally retire the rule. Repeating the same finding indefinitely degrades the audit's signal-to-noise ratio.

**Seed:** Should the Inquisitor maintain a "debt ledger" — a structured table of open violations with age, owner, and deadline — so that aging debt is visible outside diary prose and can be queried programmatically?

---

## 2026-02-26: Inquisitor Audit — v3 Generation, Persistent CHANGELOG Gap

**Context:** Audit of HEAD (`771ebdc`), covering 5 commits: `771ebdc` (docs: FR-103 v3 generation), `76f2873` (feat: FR-103 per-chapter graphs), `a9bffc8` (fix: FR-103 per-chapter persistence), `0704063` (docs: FR-103 diary), `b0fa74c` (feat: FR-103 judge-amend subgraph). One `docs` commit generates 9 eBook chapters (v3); one `feat` adds per-chapter graphs and parallel runner. Audited against Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✗ VIOLATION — **CHANGELOG gap persists (Commandment 10):** `76f2873` (feat: per-chapter graphs with parallel runner, test_copilot_subgraph_variables.py, FR-104) still has no CHANGELOG entry. Flagged in previous audit; not remediated in subsequent `771ebdc` commit. Two consecutive audits now cite the same gap — the violation is aging.
- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): FR-XXX description` format. `docs:` commits correctly omit CHANGELOG.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091, REQ-YG-092 in ARCHITECTURE.md. New `test_copilot_subgraph_variables.py` (3 tests) all carry `@pytest.mark.req("REQ-YG-092")`. No orphan tests.
- ✓ COMPLIANT — **noqa Confessions:** Zero new `# noqa` Python suppressions across the 5-commit range. The `noqa` string in `precommit_gates.yaml` is example content in a prompt, not a code suppression.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required trailer. 7th+ audit flagging this. At this point, either enforce mechanically or formally accept as non-enforced convention.

**Heuristic:** When a violation survives two consecutive audits without remediation, it transitions from "finding" to "accepted debt." Accepted debt must be either (a) fixed before next release, or (b) formally documented as a known deviation with rationale. Leaving it in audit limbo creates noise that erodes trust in the audit process itself.

**Seed:** Should the Inquisitor audit carry enforcement authority — e.g., blocking the next version bump until all ✗ VIOLATION items from the previous audit are resolved or formally waived?

---

## 2026-02-26: Inquisitor Audit — Per-Chapter Graphs, Missing CHANGELOG

**Context:** Audit of HEAD (`76f2873`), covering 5 commits: `76f2873` (feat: FR-103 per-chapter graphs with parallel runner), `a9bffc8` (fix: FR-103 per-chapter persistence), `0704063` (docs: FR-103 diary), `b0fa74c` (feat: FR-103 judge-amend subgraph), `9048d03` (docs: FR-100 progress). Three substantive commits (two `feat`, one `fix`) introduce or restore capabilities. Audited against Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✗ VIOLATION — **CHANGELOG gap (Commandment 10):** HEAD commit `76f2873` is a `feat` adding 9 per-chapter graph files, `run-chapters.sh` parallel runner, FR-104 feature request, and `test_copilot_subgraph_variables.py` (391 lines) — yet CHANGELOG 0.4.58 has no entry for these additions. The prior 4 commits are properly reflected; only the latest `feat` is missing.
- ✓ COMPLIANT — **Conventional Commits (Commandment 10):** All 5 commits use correct `type(scope): FR-XXX description` format. `docs:` commits omit CHANGELOG entries as expected.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091, REQ-YG-092 in ARCHITECTURE.md. 7 new tests across `test_copilot_subgraph_variables.py` (3) and `test_ebook_doctrine_validation.py` (4) all carry `@pytest.mark.req("REQ-YG-092")`. No orphan tests.
- ✓ COMPLIANT — **Distill (Sermon):** Diary entry "FR-103 eBook Pipeline — The Simplification Arc" included in HEAD commit, documenting the accretion trap and the unit-of-work heuristic. Comprehensive and reflective.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required trailer. Recurring accepted deviation (6th+ audit flagging this).

**Heuristic:** A `feat` commit that ships code without updating CHANGELOG is invisible to users who rely on release notes. The CHANGELOG is the commit's public witness — if the commit is worth a `feat:` prefix, it is worth a CHANGELOG line. Enforce this at the pre-commit level: if `git diff --cached` touches code and the commit message starts with `feat` or `fix`, require CHANGELOG to be staged.

**Seed:** Could a pre-commit hook parse the commit message type (`feat`/`fix`) and reject commits that don't include staged changes to CHANGELOG.md — closing the gap mechanically rather than by audit?

---

## 2026-02-26: FR-103 eBook Pipeline — The Simplification Arc

**Context:** FR-100 → FR-101 → FR-102 → FR-103 represents a complete feature arc for the eBook authoring pipeline. The final implementation: 7 per-chapter graphs (graph-ch00.yaml through graph-ch06.yaml) with a unified write→judge→amend pattern. Each chapter gets its own 3-node graph. Variables reduced to just `output_dir` and `filename`.

**Trap:** *Accretion through iteration.* Each FR iteration added complexity to solve perceived problems:
- FR-100: Initial scaffold with research→write split (hallucination source)
- FR-101: 32-node pipeline with elaborate checkpointing (over-engineered)
- FR-102: Subgraph with input/output mapping (complexity for complexity's sake)
- FR-103: File-based pattern with per-chapter filenames (still 21 nodes in main graph)

The breakthrough came when the user asked: "how to run one chapter separately?" — revealing that the monolithic graph forced full pipeline runs. The solution wasn't `--start-node`/`--end-node` flags; it was **separate graphs per chapter**.

**Heuristic:** When you find yourself wishing for partial execution flags, you've designed the wrong unit of work. A good pipeline is composed of small, independently-runnable graphs — not a monolith with escape hatches. The copilot node pattern (agent reads/writes files) makes composition trivial because state flows through the filesystem, not through graph state mapping.

**Technical insight:** The file-based pattern eliminates subgraph input/output mapping entirely:
```yaml
# Complex: subgraph mapping
input_mapping:
  chapter_content: content
output_mapping:
  validated: validated_chapter

# Simple: file-based
variables:
  output_dir: "{state.output_dir}"
  filename: "{state.filename}"
```
Files are the original shared state. When copilot nodes all operate on the same file path, the agent becomes stateless — it reads the file, does work, writes the file. No mapping required.

**Seed:** Could a `graph-composition` CLI command chain multiple single-chapter graphs into a batch run? E.g., `yamlgraph graph compose graph-ch00.yaml graph-ch01.yaml --var output_dir=docs/ebook/v1` — maintaining isolation while enabling sequential execution?

**User reflection:** The copilot node encapsulates an agentic process that *prefers* file-based operation — agents naturally read files, do work, write files. We struggled to give the copilot node meaningful and big enough tasks; repeatedly, the write→judge→amend cycle felt like over-engineering. The judge/amend step was questioned multiple times ("is this really needed?"). Visibility into what the agent was doing was also dropped multiple times during iteration.

**Root cause:** Lack of a precise FR from the start. FR-100 was vague ("write an eBook"), FR-101/102/103 were reactive corrections. A tighter initial spec — defining chapter scope, output format, and success criteria before coding — would have prevented the accretion trap. The Sermon says "Plan" before "Enforce", but we planned after we started building.

---

## 2026-02-25: Inquisitor Audit — Post-Fix Persistence, Doctrine Intact

**Context:** Audit of HEAD (`a9bffc8`), covering 5 commits: `a9bffc8` (fix: FR-103 per-chapter persistence), `0704063` (docs: FR-103 diary), `b0fa74c` (feat: FR-103 judge-amend subgraph), `9048d03` (docs: FR-100 progress), `bd1d6ce` (feat: FR-100 ebook scaffold). Two `feat` and one `fix` commit introduce or restore capabilities. Audited against Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits + CHANGELOG (Commandment 10):** All 5 commits use correct type/scope/FR-tag format (`fix(ebook):`, `docs:`, `feat(ebook):`). Both `feat` commits and the `fix` commit have corresponding CHANGELOG 0.4.58 entries under Added and Fixed sections. `docs:` commits correctly omit CHANGELOG entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 and REQ-YG-092 both present in ARCHITECTURE.md. 8 tests across `test_ebook_writing.py` (4) and `test_ebook_doctrine_validation.py` (4) all carry `@pytest.mark.req` tags. Full chain intact.
- ✓ COMPLIANT — **noqa Confessions:** Zero new `# noqa` suppressions introduced across the 5-commit range. 2 framework suppressions (CONF-002, CONF-003) and all example/test/script suppressions remain confessed. `confessions.md` comprehensive.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required `Co-authored-by: Copilot` trailer. Recurring accepted deviation — awaiting mechanical enforcement via pre-commit hook.
- ⚠ DRIFT — **Diary entropy (Commandment 8):** 25 entries for 2026-02-25 in 340 lines. `scripts/diary_rotate.py` exists but hasn't been invoked. This is the 5th+ audit flagging diary bloat. The Inquisitor's own entries remain the dominant entropy contributor.

**Heuristic:** When the same drift is flagged across 5+ audits without resolution, the finding has graduated from observation to technical debt. Either apply the existing fix (`diary_rotate.py`) or accept the drift formally — repeated flagging without action is itself entropy.

**Seed:** Could audit findings be accumulated in a lightweight structure (e.g., a session-scoped table or a YAML sidecar) and flushed to diary.md only once per session — collapsing N audits into one entry per working period?

---

## 2026-02-25: Inquisitor Audit — FR-103 Cycle Complete, Doctrine Holding

**Context:** Audit of HEAD (`0704063`), covering 5 commits: `0704063` (docs: FR-103 diary), `b0fa74c` (feat: FR-103 judge-amend subgraph), `9048d03` (docs: FR-100 progress), `bd1d6ce` (feat: FR-100 ebook scaffold), `e909641` (docs: FR-100 feature request). Two `feat` commits introduce new capabilities (CAP-32, REQ-YG-091, REQ-YG-092). Audited against all 10 Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits + CHANGELOG (Commandment 10):** All 5 commits use correct type/scope/FR-tag format. Both `feat` commits have corresponding CHANGELOG 0.4.58 entries. `docs:` commits correctly omit CHANGELOG entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 (4 tests in `test_ebook_writing.py`) and REQ-YG-092 (4 tests in `test_ebook_doctrine_validation.py`) all carry `@pytest.mark.req` tags. Both requirements documented in ARCHITECTURE.md. `req_coverage.py` updated.
- ✓ COMPLIANT — **noqa Confessions:** 2 suppressions (CONF-002: ARG002, CONF-003: ANN001) remain confessed. No new suppressions introduced across the 5-commit range.
- ✓ COMPLIANT — **Distill (Sermon):** FR-103 has a diary entry (`0704063`) documenting the normalize-at-boundary trap, the FR-101→FR-102→FR-103 convergence path, and a seed for generalizing the judge-amend pattern. This resolves the prior audit's drift finding about missing Distill for this work.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the required `Co-authored-by: Copilot` trailer. Accepted deviation per prior ruling — no further escalation until a pre-commit hook addresses this mechanically.

**Heuristic:** A full FR cycle (FR-100→FR-101→FR-102→FR-103) that ends with a diary entry closing every prior audit finding is the doctrine working as designed. The iterative narrowing from 32 nodes to a minimal judge-amend subgraph is exactly the Research→Plan→Judge→Enforce→Distill sermon in practice.

**Seed:** The diary now has 23 entries (322 lines), with audit entries outnumbering development reflections. Should rotation to a dated archive (e.g., `diary-2026-02-25.md`) trigger when entry count exceeds 10 per day — preserving the current file as a rolling window of the most recent work?

---

## 2026-02-25: FR-103 Judge-Amend Subgraph — The Normalize-at-Boundary Trap

**Context:** FR-100 pipeline ran successfully but produced 9/10 fabricated Commandments in Ch01 Doctrine. Root cause: research→write split lost verbatim quotes. The LLM invented content from summaries instead of citing source files.

**Trap:** *Downstream Fix.* Initial reaction (FR-101) proposed elaborate 32-node pipeline with per-section persistence and 24 checkpoint calls. This was treating the symptom (hallucination visible late) rather than the cause (verbatim quotes lost at research boundary).

**Insight:** The Scripture's `the_one_law` applies directly: "Normalize at the boundary where external data enters, not downstream where it manifests." The fix was merging research+write into a single copilot node with inline citations — the prompt itself reads the source files, not a separate research node producing summaries.

**Process:**
1. FR-101 created (32 nodes) → Judged AMEND for over-engineering
2. FR-102 consolidated 5 options → Too sprawling, no clear winner
3. FR-103 distilled to minimal pattern: merged chapter prompts + judge-amend subgraph
4. TDD: wrote `verify_commandments_verbatim()` test first (4 tests)
5. Implementation: 6 merged prompts, subgraph, rewired graph
6. Pre-commit caught YAML quoting issue in subgraph conditions

**Heuristic:** When hallucination appears late in pipeline, trace backward to find where verbatim content was converted to summary. The fix is moving the raw source access closer to the generation point — ideally into the same prompt.

**Seed:** Could the judge-amend subgraph pattern be generalized as a reusable validation primitive? A `validate_with_sources` subgraph that takes content + cited files and returns corrected content?

---

## 2026-02-25: Inquisitor Audit — FR-103 Judge-Amend, Full Compliance

**Context:** Audit of HEAD (`b0fa74c`), 1 new commit since prior audit at `9048d03`. The commit (`feat(ebook): FR-103 judge-amend subgraph pattern`) introduces a validation subgraph, 6 merged chapter prompts, judge/amend prompts, 4 new tests, and a Distill diary entry. Minimum-delta heuristic applied.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits + CHANGELOG (Commandment 10):** `b0fa74c` uses `feat(ebook):` scope, FR-103 tag, detailed body with 7 bullet points. CHANGELOG 0.4.58 has a matching FR-103 entry with REQ-YG-092.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-092 in ARCHITECTURE.md under CAP-32. `req_coverage.py` updated. 4 tests in `test_ebook_doctrine_validation.py` carry `@pytest.mark.req("REQ-YG-092")`. Full chain intact.
- ✓ COMPLIANT — **noqa Confessions:** 2 existing suppressions (CONF-002, CONF-003) remain confessed. Zero new suppressions.
- ✓ COMPLIANT — **Distill (Sermon):** FR-103 includes a model diary entry ("FR-103 Judge-Amend Subgraph — The Normalize-at-Boundary Trap") documenting the trap (downstream fix), the FR-101→FR-102→FR-103 evolution, the TDD process, and a graduated heuristic from `the_one_law`. This resolves the Distill drift flagged in 3 prior audits.
- ⚠ DRIFT — **Diary entropy (Commandment 8):** 23 `## 2026-02-25` entries now exist. The split proposal (dev reflections vs. audit log) remains unacted after 4 prior Seeds. The Inquisitor's own entries remain the dominant entropy source.

**Heuristic:** When a persistently flagged gap (missing Distill) is finally resolved, the Inquisitor should acknowledge the correction explicitly — not continue flagging from stale heuristics. Verify current state, not pattern-match from prior findings.

**Seed:** With FR-103's Distill as exemplar, could a `docs/diary-template.md` codify the Trap→Insight→Process→Heuristic→Seed structure — making future Distill entries faster to write and more consistent?

---

## 2026-02-25: Inquisitor Audit — Minimal Delta, Compliance Holding, Audit Entropy Peak

**Context:** Audit of HEAD (`9048d03`), 1 new commit since prior audit at `bd1d6ce`. The new commit (`9048d03` docs: FR-100 implementation progress update) is docs-only — a progress update to the feature request file. All 5 commits in the `git log -5` window were already covered by the prior audit except this one. Applied minimum-delta heuristic: focus on the single unaudited commit and systemic patterns.

**Findings:**

- ✓ COMPLIANT — **`9048d03` follows Conventional Commits** (`docs:` type, FR tag in subject, descriptive). No CHANGELOG entry needed for a feature request progress update. No code changes, no new capabilities, no new noqa suppressions. Commandments 4, 8, 10 and ADR-001 unaffected.
- ✓ COMPLIANT — **ADR-001 intact:** REQ-YG-091 (CAP-32) in ARCHITECTURE.md, 4 tests tagged `@pytest.mark.req("REQ-YG-091")` in `test_ebook_writing.py`, `req_coverage.py` updated. Full traceability chain holds from prior commit.
- ✓ COMPLIANT — **noqa Confessions:** 2 suppressions (CONF-002: ARG002, CONF-003: ANN001), both confessed. Zero new suppressions.
- ⚠ DRIFT — **Missing Distill for FR-100 (Sermon):** Flagged in prior audit — `bd1d6ce` implemented a 14-node pipeline with no metacognitive diary entry. `9048d03` updated the FR progress but is not a Distill entry. The implementation experience, traps, and lessons remain unrecorded.
- ⚠ DRIFT — **Audit entropy (Commandment 8):** This is the **9th** `## 2026-02-25: Inquisitor Audit` entry in `diary.md`. The file has 264 lines, the majority being audit entries. The diary has become an audit log. Prior audits proposed solutions (separate `audit-log.md`, last-audited-SHA marker, batch audits per session) — none adopted. The Inquisitor is now the primary entropy source it was designed to detect.

**Heuristic:** When the corrective mechanism produces more entropy than the defects it finds, the mechanism itself needs correction. An Inquisitor with no memory of prior audits and no minimum-delta gate will always re-discover and re-record. The fix is structural: store last-audited SHA, separate audit entries from development reflections, and enforce a cooldown.

**Seed:** Should `docs/diary.md` be split into `docs/diary.md` (development reflections only) and `docs/audit-log.md` (Inquisitor findings), with the Inquisitor writing exclusively to the latter — preserving the diary's original metacognitive purpose?

---

## 2026-02-25: Inquisitor Audit — FR-100 eBook Pipeline, Doctrine Largely Held

**Context:** Audit of HEAD (`bd1d6ce`), covering 5 commits since last audit. One functional commit (`bd1d6ce` feat(ebook): FR-100) introduced a new capability — a 14-node eBook authoring pipeline. Four remaining commits are docs-only (FR-100 feature request, duplicate diary cleanup, diary restore, FR-082 minesweeper FR). Audited against all 10 Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits + CHANGELOG (Commandment 10):** `bd1d6ce` uses scope, FR tag, and detailed body listing every artifact. CHANGELOG 0.4.58 has a matching entry. `docs:` commits correctly omit CHANGELOG entries. All 5 subjects are descriptive.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 added to ARCHITECTURE.md under new CAP-32. `scripts/req_coverage.py` updated with the new REQ and capability. 4 tests in `test_ebook_writing.py` carry `@pytest.mark.req("REQ-YG-091")`. Full chain intact.
- ✓ COMPLIANT — **noqa Confessions:** 2 existing suppressions (CONF-002: ARG002, CONF-003: ANN001) remain confessed. No new suppressions introduced in `yamlgraph/` or the new `examples/ebook/` code.
- ⚠ DRIFT — **Missing Distill (Sermon):** `bd1d6ce` implements FR-100 — a non-trivial 14-node pipeline scaffold with custom tool, 12 prompts, and a build script. No metacognitive diary entry reflects on the implementation decisions, traps, or lessons learned. The Sermon requires Distill after completing a task list.
- ⚠ DRIFT — **Co-authored-by trailer:** 0 of 5 commits include the trailer. Per prior audit's ruling, this is an **accepted deviation** — no further flagging until an FR or hook change addresses it.

**Heuristic:** A feature that passes every structural gate (Conventional Commits, CHANGELOG, ADR-001, tests, confessions) but skips the Distill step is 90% compliant and 0% reflective. The Distill is where institutional knowledge compounds; omitting it means the next person building a similar pipeline starts from zero context.

**Seed:** Should the pre-commit hook enforce that `feat:` commits touching `examples/` include a diary entry in the same commit — making Distill a mechanical gate rather than a voluntary discipline?

---

## 2026-02-25: Inquisitor Audit — Minimal Delta, Diary Bloat

**Context:** Audit of HEAD (`5a102f1`), covering 5 commits: `5a102f1` (docs: remove duplicate diary file), `51d744c` (docs: restore lost diary entries), `5fcede9` (docs: FR-082 minesweeper FR), `63de507` (feat: FR-097/FR-098 shared diary refactor), `80be03a` (chore: diary commit). Only 1 commit (`5a102f1`) is genuinely new since the prior audit at `51d744c`. Applying the minimum-delta heuristic from prior audits: this audit validates the new commit and reassesses systemic patterns rather than re-discovering known findings.

**Findings:**

- ✓ COMPLIANT — **New commit `5a102f1`** follows Conventional Commits (`docs:` type, descriptive subject). No CHANGELOG entry needed for file cleanup. No code changes, no new noqa suppressions, no new capabilities — ADR-001 and Confessions doctrine unaffected. Commandments 4, 8, 10 upheld.
- ✓ COMPLIANT — **noqa hygiene intact:** 2 suppressions in `yamlgraph/` (ANN001 → CONF-003, ARG002 → CONF-002) remain confessed. No new suppressions introduced across the 5-commit range.
- ✓ COMPLIANT — **ADR-001 coverage:** FR-097/FR-098 (refactoring, no new capability) correctly omitted new REQs. Existing REQ-YG-090 tests retain `@pytest.mark.req` tags (3 tests in `test_diary_digest.py`).
- ⚠ DRIFT — **Diary entropy (Commandment 8):** `docs/diary.md` now contains 18 `##` entries for 2026-02-25 alone — 7 are Inquisitor audits covering overlapping commit ranges. The diary's signal-to-noise ratio has inverted: audit entries outnumber development reflections. The file is becoming an audit log, not a metacognitive journal. Prior audits diagnosed this but the pattern continues.
- ⚠ DRIFT — **Missing Distill for FR-097/FR-098 (Sermon):** Flagged in the prior audit — `63de507` implemented a non-trivial refactoring without a corresponding metacognitive diary entry. Still unresolved. The Chaplain entries about FR-097/FR-098 (lines 162, 168, 176) describe planning/approval but not the implementation experience, traps, or lessons.

**Heuristic:** When the audit tool generates more diary entries than the development it audits, the tool has become the primary source of entropy. The Inquisitor should batch findings and write at most one audit entry per development session, not per invocation. Diary rotation (archiving to dated files) should trigger when entry count exceeds a threshold.

**Seed:** Should Inquisitor audits be appended to a separate `docs/audit-log.md` to keep `diary.md` focused on metacognitive development reflections — preserving both traceability and signal clarity?

---

## 2026-02-25: Inquisitor Audit — Shared Refactor, Trailer Fatigue, Missing Distill

**Context:** Audit of HEAD (`51d744c`), covering 5 commits since `dec470a`. Three commits are genuinely new since the last audit: `63de507` (feat: FR-097/FR-098 shared diary refactor + copilot graph consolidation), `5fcede9` (docs: FR-082 minesweeper feature request), `51d744c` (docs: restore lost diary entries). Two older commits (`80be03a`, `dec470a`) were already audited. This audit focuses on the 3 unaudited commits only, heeding the prior audit's heuristic about minimum-delta.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits + CHANGELOG (Commandment 10):** All 3 new commits follow Conventional Commits. `63de507` uses scope, FR tags, and descriptive body. CHANGELOG 0.4.57 has FR-097 and FR-098 entries matching the feat commit. `docs:` commits correctly omit CHANGELOG entries.
- ✓ COMPLIANT — **ADR-001 + noqa Confessions:** FR-097/FR-098 is a refactoring (no new capability → no new REQ needed). Existing tests retain `@pytest.mark.req` tags. `noqa_coverage.py` reports 53/53 confessed — zero undocumented suppressions.
- ✓ COMPLIANT — **Pattern Conformance (Commandment 4):** `examples/shared/diary.py` extracts shared utilities cleanly. `examples/diary_digest/nodes/writing.py` re-exports via `__all__` for backward compatibility. Tests unchanged and passing with same req tags.
- ⚠ DRIFT — **Co-authored-by trailer:** 0 of 3 new commits include the trailer. This is the **fifth consecutive audit** flagging this identical gap. Prior audits recommended mechanical enforcement (commit-msg hook) or rule amendment. Neither has occurred. Reclassifying as **accepted deviation** — further flagging without remediation is itself entropy (Commandment 8). This is the last time this finding will be raised without a corresponding FR or hook change.
- ⚠ DRIFT — **Diary Distill (Sermon):** `63de507` implements FR-097/FR-098 — a non-trivial refactoring that moved diary utilities to a shared module and consolidated the copilot graph. No metacognitive diary entry was written reflecting on the refactoring decisions, traps encountered, or lessons learned. The Sermon requires Distill after completing a task list.

**Heuristic:** When an audit finding has been raised N ≥ 4 times without remediation, the Inquisitor must either (a) file an FR to fix the root cause, or (b) formally accept the deviation and stop flagging. Perpetual drift findings violate Commandment 8 — they are entropy masquerading as diligence.

**Seed:** Should the project maintain an `ACCEPTED_DEVIATIONS.md` file (or a section in ARCHITECTURE.md) that records doctrine rules consciously relaxed, preventing future audits from re-discovering known, tolerated gaps?

---

## 2026-02-25: Inquisitor Audit — Redundant Audits and Stale Trailer Rule

**Context:** Fourth audit of HEAD (`dec470a`), covering 5 commits: `dec470a` (chore: FRs commit), `9666c56` (fix: FR-093 string repr), `eb966cc` (feat: FR-093 diary append), `7b00537` (feat: FR-094 memory nodes), `96aa12a` (docs: FR-090/091/092). Three prior Inquisitor audits already exist in this diary covering overlapping ranges. This audit focuses on what's new and what's stale.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits. CHANGELOG 0.4.57 has matching entries for every feat/fix/docs commit. `eb966cc` added REQ-YG-090 to ARCHITECTURE.md; 3 tests tagged `@pytest.mark.req("REQ-YG-090")` including the regression test in `9666c56`. Fix commit wrote the failing test first (TDD observed). Commandments 7 and 10, ADR-001 all upheld.
- ✓ COMPLIANT — Both `# noqa` suppressions (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`) confessed as CONF-003 and CONF-002. No new suppressions introduced.
- ⚠ DRIFT — `dec470a` ("chore: FRs commit") bundles 5 feature requests (FR-095–FR-099), a test file, and 117 diary lines in a single commit with an opaque message. No scope, no FR tags, empty body. Technically valid Conventional Commits but violates the spirit of traceability — `git log --oneline` reveals nothing about what was planned.
- ⚠ DRIFT — Co-authored-by trailer missing on 4 of 5 commits. This is the fourth consecutive audit flagging the same gap. The prior audit correctly diagnosed this as a specification bug ("a doctrine rule flagged three times without correction is not a compliance failure — it is a specification bug"). No amendment has been made. Continued flagging is noise.
- ⚠ DRIFT — Three prior Inquisitor audits in this diary cover the same commit range (`96aa12a..dec470a`). Each re-discovers the same trailer finding and produces overlapping COMPLIANT verdicts. The audit process is generating entropy, not reducing it — violating Commandment 8.

**Heuristic:** An audit that re-discovers known findings without triggering correction is itself a source of entropy. The Inquisitor needs a "last audited SHA" marker and a minimum-delta rule: no audit unless N new commits exist beyond the last audited SHA. Without this, the Rite of Correction degrades into the Rite of Repetition.

**Seed:** Should the Inquisitor store its last-audited SHA in a `.inquisitor` state file (or session DB), and refuse to run until the commit range contains genuinely unaudited work?

---

## 2026-02-25: Inquisitor Audit — Terse Chores and the Trailer That Won't Stick

**Context:** Fourth audit of HEAD (`80be03a`), covering 5 commits: two `chore:` housekeeping commits (diary + FRs), one `fix(chaplain):` for FR-093 string repr parsing, one `feat(chaplain):` for FR-093 diary append, and one `feat(memory):` for FR-094 approval. Examined Conventional Commits, CHANGELOG traceability, ADR-001 compliance, noqa confessions, Co-authored-by trailers, and diary Distill discipline.

**Findings:**

- ✓ COMPLIANT — All 5 commits use Conventional Commits format. CHANGELOG 0.4.57 has entries for every functional change (FR-093 feat + fix, FR-094 approval). `chore:` commits correctly omit CHANGELOG entries. Commandment 10 upheld.
- ✓ COMPLIANT — FR-093 added REQ-YG-090 to ARCHITECTURE.md. Tests carry `@pytest.mark.req("REQ-YG-090")`. Fix commit `9666c56` added failing test before code fix — TDD Rite observed. FR-094 defers REQ-YG-091/092 until implementation lands. ADR-001 satisfied.
- ✓ COMPLIANT — Both existing `# noqa` suppressions (ANN001 → CONF-003, ARG002 → CONF-002) remain properly confessed. No new suppressions introduced. Confessions doctrine intact.
- ⚠ DRIFT — Co-authored-by trailer absent from 4 of 5 commits (only `7b00537` has it). This is the **fourth consecutive audit** flagging this gap. The third audit explicitly recommended amending the Scripture to scope the rule or enforce it via commit-msg hook. Neither action has been taken. At this point the finding is no longer drift — it is a known, tolerated specification defect.
- ⚠ DRIFT — `80be03a` ("chore: diary commit") and `dec470a` ("chore: FRs commit") follow Conventional Commits in letter but not spirit. Subject lines should describe *what* changed, not merely *what type of file was touched*. Compare: "chore: add FR-095 through FR-099 planning docs" vs. "chore: FRs commit." Terse subjects defeat `git log --oneline` as a changelog substitute.

**Heuristic:** An audit finding repeated four times without remediation is not drift — it is accepted practice. Either amend the rule to match reality or enforce it mechanically. Human willpower is not a reliable control; pre-commit hooks are. The same applies to commit message quality: if terse subjects keep appearing, add a `commit-msg` hook that rejects subjects shorter than 20 characters.

**Seed:** Could a `commit-msg` hook enforce both the Co-authored-by trailer (when in a Copilot session) and a minimum subject-line length, collapsing two recurring audit findings into a single mechanical gate?

---

## 2026-02-25: Environment Issue — Disappearing File Edits

**Context:** During FR-093 implementation, multiple `replace_string_in_file` operations reported success but changes didn't persist. The tool confirmed "file successfully edited" yet subsequent `read_file`, `grep`, and `pytest` showed original content. This happened repeatedly with both test additions and implementation changes.

**Symptoms:**
- Tool reports successful edit
- Immediate `grep` for the new content returns empty
- `pytest` doesn't collect newly added tests
- `read_file` shows pre-edit content

**Workaround:** Re-running the exact same edit eventually worked, but multiple attempts were required. No clear pattern for when edits would "stick."

**Impact:** Significant debugging time spent verifying whether code was correct vs. whether the file even contained the code. Trust in tool output eroded.

**Investigation Needed:**
1. VS Code file sync / buffer caching issue?
2. Multiple terminals/processes holding file handles?
3. Tool implementation race condition?
4. File system caching on macOS?

**Heuristic:** When tool reports success but behavior doesn't match, verify file content with `cat` or `head` in terminal (bypasses any VS Code caching) before debugging logic.

**Seed:** Could we add a verification step to file-editing tools that re-reads and confirms the change was written, rather than just reporting success based on the write call?

---

## 2026-02-25: Inquisitor Audit — Co-author Trailer and TDD Discipline

**Context:** Third audit of HEAD (`9666c56..f4c02f4`), covering 5 commits: two FR-093 commits (feat + fix for chaplain diary append), one FR-094 approval, one FR-090/091/092 docs batch, and one FR-089 docs fix. Focus: Conventional Commits, CHANGELOG traceability, ADR-001 compliance, noqa hygiene, and diary Distill discipline.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags. CHANGELOG 0.4.57 has matching entries for every commit including the `9666c56` fix. Commandment 10 upheld.
- ✓ COMPLIANT — FR-093 added REQ-YG-090 to ARCHITECTURE.md. New tests in `test_diary_digest.py` carry `@pytest.mark.req("REQ-YG-090")`. The fix commit (`9666c56`) also added a test with the correct req tag before fixing the code — TDD Rite observed. ADR-001 satisfied.
- ✓ COMPLIANT — All `# noqa` suppressions in `yamlgraph/` (2 total: ANN001, ARG002) are confessed as CONF-003 and CONF-002. No new suppressions introduced in either FR-093 commit. Confessions doctrine intact.
- ⚠ DRIFT — Neither `9666c56` nor `eb966cc` (both FR-093) include the `Co-authored-by: Copilot` trailer. Only `7b00537` (FR-094) has it. This is the third consecutive audit flagging the same gap. The trailer rule in Scripture is unconditional, but repeated non-enforcement suggests the rule needs amendment rather than further flagging.
- ⚠ DRIFT — The two prior Inquisitor audits already exist as diary entries but cover overlapping commit ranges (the same 5 commits shift as HEAD advances). This creates audit duplication rather than fresh coverage. The Inquisitor cadence should be tied to release tags or PR merges, not ad-hoc invocation.

**Heuristic:** A doctrine rule flagged three times without correction is not a compliance failure — it is a specification bug. The Co-authored-by trailer rule should be scoped explicitly: "When Copilot contributed to the commit, include the trailer." Amend the Scripture or accept universal non-compliance as the de facto standard.

**Seed:** Should the pre-commit `commit-msg` hook enforce the Co-authored-by trailer automatically (detecting Copilot session context), eliminating the human-judgment gap entirely?

---

## 2026-02-25: Inquisitor Audit — FR-093/094 Feature Commits

**Context:** Audited the latest 5 commits (`5e782d5`..`eb966cc`) spanning FR-088 through FR-094. The batch covers three documentation-only fixes (FR-088, FR-089, FR-090/091/092), one feature implementation (FR-093 chaplain diary append), and one feature approval (FR-094 memory nodes). Previous audit already covered the doc commits; this audit focuses on the two new `feat` commits at HEAD.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags. CHANGELOG 0.4.57 has entries for every commit. Commandment 10 upheld.
- ✓ COMPLIANT — FR-093 added REQ-YG-090 to ARCHITECTURE.md, tests tagged with `@pytest.mark.req("REQ-YG-090")` (32 total req markers in test file). ADR-001 satisfied.
- ✓ COMPLIANT — FR-094 is an approval commit (not implementation). REQ-YG-091/092 correctly absent from ARCHITECTURE.md — they belong when implementation lands. ADR-001 deferred, not violated.
- ⚠ DRIFT — `eb966cc` (FR-093) lacks the `Co-authored-by: Copilot` trailer. Only `7b00537` (FR-094) includes it. Recurring finding from the prior audit. The trailer rule remains ambiguous on human-only commits.
- ⚠ DRIFT — No diary entry exists for FR-093 specifically. The Chaplain auto-generated entries (FR-095, FR-096) cover later planning work, and the prior Inquisitor entry covered the doc sprint, but FR-093's implementation — which added nodes, prompts, and a YAML schema — received no Distill reflection.

**Heuristic:** Feature implementation commits that introduce new node types and YAML schemas are exactly the kind of work the Distill step was designed for. The absence suggests diary entries are being treated as optional "if there's a lesson" rather than mandatory "close the loop." The Sermon says "After completing a task list, add a metacognitive entry" — not "if you learned something new."

**Seed:** Could the `.chaplain/graph.yaml` workflow itself enforce the Distill step — refusing to close a task until a diary entry is detected in the diff?

---

## 2026-02-25: Inquisitor Audit — Documentation Sprint and Co-author Trailer Gap

**Context:** Audited the latest 5 commits (`5cec937`..`7b00537`) spanning FR-087 through FR-094. The batch covers four documentation-only fixes (FR-087, FR-088, FR-089, FR-090/091/092) and one feature approval (FR-094 memory nodes). No Python code was changed; all work is docs, CHANGELOG, and feature request authoring.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags (`feat(memory):`, `docs:`, `fix(docs):`, `docs(readme):`). CHANGELOG entries present for all in version 0.4.57. Commandment 10 upheld.
- ✓ COMPLIANT — Both existing `# noqa` suppressions (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`) are properly confessed as CONF-003 and CONF-002 in `docs/confessions.md`. No new suppressions introduced.
- ⚠ DRIFT — 4 of 5 commits lack `Co-authored-by: Copilot` trailer. Only `7b00537` (FR-094) includes it. The git commit trailer rule in the Scripture is unconditional. Likely cause: the 4 doc commits were authored directly without Copilot assistance, making the trailer feel inaccurate. The rule doesn't distinguish human-only vs. Copilot-assisted commits — this ambiguity permits reasonable omission but creates inconsistency.
- ⚠ DRIFT — No diary entry was written for the documentation sprint (FR-087 through FR-092). Six FRs were planned, judged, and enforced in sequence — a substantive task list. The diary was rotated (`diary-2026-02-24.md`) during FR-094 but no reflection was distilled for the batch. The Sermon's Distill step was skipped.
- ✓ COMPLIANT — FR-094 declares REQ-YG-091/092 but they are not yet in ARCHITECTURE.md. This is correct: the commit is an approval ("scope frozen, authority granted"), not implementation. Requirements belong in ARCHITECTURE.md when the implementation lands. ADR-001 deferred, not violated.

**Heuristic:** The Co-authored-by trailer rule creates a false signal when applied to human-only commits. A doctrine rule that participants routinely skip because it feels dishonest is worse than no rule — it trains selective compliance. Either scope the trailer to Copilot-assisted commits explicitly, or accept it as a universal attribution and stop flagging omissions.

**Seed:** Should the documentation sprint pattern (batching 4–6 small FRs into one session) have its own lightweight Distill format — a single diary entry covering the batch rather than one per FR — to reduce ceremony without losing the metacognitive signal?

---

## 2026-02-25: Chaplain — FR-095 Documentation Staleness Monitor Approved

The planning phase proposed FR-095, detailing a lightweight Python script (scripts/doc_staleness.py) for a pre-commit hook. This script would implement three deterministic checks
—node type table completeness, orphan reference docs, and stale requirement ranges—to automate drift issues similar to previous manual fixes, crucially avoiding LLM calls. The judging phase found the FR clear, minimal, and feasible, leading to an APPROVE verdict. Minor inaccuracies concerning NODE_TYPE_MAP (should be NodeType StrEnum) and argparse (should be sys.argv) were noted as guidance-level details, not blockers. The scope is now frozen, and the FR moved to feature-requests/.

**Seed:** How might we identify and automate other classes of documentation or codebase drift issues using deterministic, non-LLM based checks?

---

## 2026-02-25: Chaplain — FR Template Enhancement and Scope Refinement

FR-096 proposed adding a mandatory 'Demo Plan' section to the FR template, complete with four specific fields and initial plans for linting enforcement. The core idea was strong, directly supporting Commandment #2 by addressing a structural gap. However, the judging process led to an 'AMEND' verdict. Key adjustments involved removing the linter enforcement from the immediate scope, relocating it to a 'Future Work' section. This decision was made because the linter work referenced a non-existent workflow and exceeded the initial 0.5-day effort. An ambiguous acceptance criterion was also clarified, ensuring a clean and focused scope on template and documentation updates, ready for re-review.

**Seed:** What is the optimal strategy for reintroducing the deferred FR linter enforcement into a future planning cycle?

---

## 2026-02-25: Chaplain — Refactoring Diary Writing to Shared Utilities

We planned and approved FR-097, refactoring diary writing utilities into a shared module. The core decision was to relocate `format_diary_entry`, `append_to_diary`, `should_write_entry`, and `write_diary` to `examples/shared/diary.py`, while keeping `filter_relevant` within `diary_digest`. This move centralizes shared code, aligning with our architectural principles. Initial research confirmed no adverse impact on existing consumers like `daily_digest`. The judging phase meticulously verified the `DIARY_PATH` calculation and confirmed the minimal scope, backward compatibility via re-exports, and measurable acceptance criteria. This straightforward refactor leverages existing patterns in `examples/shared/` and is estimated at 0.5 days, ensuring cleaner separation of concerns.

**Seed:** How might we proactively identify other common utility functions across examples that would benefit from similar shared module consolidation?

---

## 2026-02-25: Chaplain — FR-098: Graph Consolidation Amended

The planning session drafted FR-098, aiming to consolidate divergent graph files from `.chaplain/` and `examples/copilot/` into a single source of truth, `examples/copilot/graph.yaml`. This was driven by `.chaplain/` accumulating more production features. The subsequent judgment largely affirmed the FR's clear scope, adherence to Commandment 8, and feasible 0.5-day estimate. However, the FR was marked for amendment due to three critical ambiguities: an unspecified ordering for FR-097's dependency, a potential silent breakage in the graph's `exports` section due to a `state_key` change, and an implicit resolution for state variable formatting. The FR is now in the inbox for minor revisions.

**Seed:** How can we proactively detect graph inconsistencies or breaking changes in `exports` and state variables before human judgment?

---

## 2026-02-25: Chaplain — Consolidating Watch Graph FR-098 Approved

The session successfully finalized FR-098, focusing on consolidating the watch graph. The planning phase resolved critical design ambiguities: accepting cross-example tool dependency as tech debt, removing the 'exports' section entirely, and standardizing state variable reference formats using Jinja2. This resulted in a clear, minimal feature request. The subsequent judgment rigorously audited the FR against the codebase, verifying all claims. While the verdict was 'APPROVE', three minor gaps were identified and annotated: updating ARCHITECTURE.md for requirement traceability, removing a dead defaults: temperature configuration, and documenting a historical docs/diary.md reference. This thorough validation process ensured the FR's robustness before its final approval and move to feature-requests/.

**Seed:** How can we proactively identify and address similar architectural inconsistencies or dead configurations during the planning phase, rather than relying solely on post-plan judgment?

---

## 2026-02-25: Chaplain — Graph Consolidation Approved, Refactor Confirmed

Today's session confirmed that FR-097-refactor-diary-writing-shared.md is already approved, saving redundant planning for diary utility refactoring. The primary focus then shifted to judging FR-098-consolidate-watch-graph.md, which received a clear **APPROVE** verdict. The plan to merge watch and copilot graphs was lauded for its minimal scope, measurable acceptance criteria, and alignment with Commandment 8 to kill entropy. Key findings included verifying graph divergences, noting necessary updates to ARCHITECTURE.md, and acknowledging FR-097 as a bounded tech debt. Scope is now frozen, and authority granted for implementing this crucial consolidation.

**Seed:** What other redundant or divergent graph configurations exist that could benefit from similar consolidation efforts?

---

## 2026-02-25: Chaplain — Chaplain Inbox Smoke Test Approval

FR-099, proposing a Chaplain Inbox Smoke Test, was approved after a thorough review. The core idea  a lightweight `smoke-test.sh` script to validate the chaplain pipeline's linting and compilation without LLM calls, enabling fast, offline checks  was deemed sound and essential. During judging, minor editorial corrections were applied to resolve discrepancies between the narrative and the proposed script's actual behavior. Specifically, references to a non-existent `--dry-run` flag and dropping test files were removed, aligning the description with the script's `lint` and `info` operations. A vacuous acceptance criterion was also removed, streamlining the FR. These fixes enhanced clarity and accuracy, solidifying a valuable addition to our validation toolkit.

**Seed:** How might we further enhance our pipeline's offline validation capabilities, perhaps by integrating more comprehensive structural checks?

---

## 2026-02-25: Chaplain — Inbox Throughput Test Handling

The session addressed an inbox entry explicitly stating "Do not plan. Judgement: pass." This was recognized as a test of inbox pattern throughput, not a genuine feature request. The planning phase appropriately copied the entry to drafts and cleared the inbox, adhering to the instruction. The subsequent judging process rigorously evaluated the draft, confirming its lack of scope, acceptance criteria, and implementation details. It correctly identified the self-declared 'pass' as a contradiction to the Chaplain's structured rite. Ultimately, the entry was rejected as a pipeline test artifact, its purpose served, with its underlying need for inbox validation already addressed by FR-099. This workflow demonstrated robust handling of non-standard inputs.

**Seed:** How can the system be further refined to automatically flag or route test artifacts and other non-feature-request entries, preventing them from entering the full Plan-Judge cycle?

---

## 2026-02-19: World Digest — Test

Body.

**Seed:** Q?

---

## 2026-02-25: Chaplain — FR-096 Approved

The FR was approved with clear scope.

**Seed:** What patterns emerged?

---

## 2026-02-25: Chaplain — Inbox Test Judgement and Process Adherence

A recent inbox entry, explicitly stating "Do not plan. Judgement: pass," served as a test of the initial planning workflow. The plan phase correctly processed it by moving it directly to drafts, confirming the inbox throughput. However, the subsequent judgement phase critically evaluated the entry's content. Despite the embedded instruction, the entry was soundly rejected for lacking any defined scope, acceptance criteria, or implementation details, violating the core `TEMPLATE.md` requirements and the Sermon's principle of challenging assumptions. This highlighted the robustness of the judgement process, preventing pre-emption and reinforcing that all requests, even tests, must adhere to established standards for proper evaluation.

**Seed:** How can we design future tests for `chaplain`'s operational pipeline that also conform to the `feature-requests/TEMPLATE.md` structure, providing measurable criteria for the test's success?

---

## 2026-02-26: World Digest — Observability & Agent Orchestration


**LangGraph releases** (SDK 0.3.7–0.3.9, core 1.0.9, prebuilt 1.0.8) continue steady iteration on the foundation YAMLGraph builds upon. The ecosystem is consolidating around agent observability as a first-class concern: LangSmith marketplace availability, "Agent Observability Powers Agent Evaluation," and "From Traces to Insights" all signal that visibility into agent behavior is becoming table-stakes for production systems.

**Memory and context patterns** are crystallizing across the ecosystem. LangChain's Agent Builder memory system, context management for deep agents, and sandbox connectivity patterns suggest that YAMLGraph's YAML-first approach could benefit from declarative memory and context scoping — avoiding the silent-fallback antipattern by making state assumptions explicit in the graph definition.

**Protocol and integration focus** appears in "Making MCP cheaper via CLI" and "Claude Code Remote Control," hinting that agent-to-tool communication costs and latency are becoming optimization targets. This connects to the open seed about what constraint becomes dominant as model costs approach zero.

**Evaluation as workflow gate** is implicit in the LangSmith + monday case study, which emphasizes "code-first evaluation strategy from day 1." This aligns with the seed about 'name the verification question' — evaluation and verification are moving upstream into design, not downstream into debugging.

The pattern: observability, memory clarity, and evaluation rigor are no longer optional add-ons. YAMLGraph's declarative nature positions it well to bake these concerns into the graph definition itself, rather than bolting them on afterward.

**Seed:** As agent observability becomes standard, could YAMLGraph's YAML schema include a mandatory 'verification_question' field at the graph level — making the falsifiable claim about what the agent should accomplish explicit before any node executes — and surface violations in LangSmith traces?

---

## 2026-02-27: Chaplain — Copilot Node Session Continuations Approved

The planning session focused on drafting FR-105: Copilot Node Session Continuations. Key decisions included leveraging existing Copilot CLI `--resume` and `--continue` flags and enabling state-based chaining by capturing the session ID from stderr into `CopilotResult`. The feature was scoped to a 2-day effort, encompassing flag injection, `CopilotResult` extension, linter rules, tests, and example updates. The subsequent judging session **approved** FR-105, validating its clear, minimal scope, lack of ambiguities, measurable criteria, and architectural alignment. Minor implementation notes were added, primarily concerning empirical verification of session ID extraction and extending state expression resolution for `cli_flags.resume`.

**Seed:** How might we generalize state expression resolution for all `cli_flags` values across various node types to enhance configurability?

---

## 2026-02-27: Chaplain — FR-106: Parallel Worktree Pipeline Amended

A feature request, FR-106, was drafted proposing a parallel development pipeline utilizing Git worktrees to enable isolated, Copilot-driven feature enforcement. The plan outlined scripts for worktree creation and pipeline execution, depending on FR-105 for session continuations. However, the proposal received an 'AMEND' verdict. The judge identified six critical issues, including a blocking dependency on a non-existent `read_file` tool, incorrect `graphs/` directory convention, an unenforced FR-105 dependency, missing test strategy for concurrent worktrees, macOS-specific syntax, and an optimistic effort estimate. The core concept remains valid but needs substantial revision.

**Seed:** What pre-planning checks or automated validations can be integrated into the FR drafting process to proactively identify and mitigate blocking issues like missing tools, architectural convention violations, and unenforced dependencies?

---

## 2026-02-27: World Digest — Agent observability & checkpoint stability


**LangGraph infrastructure hardening.** Three checkpoint release candidates (4.0.1rc1/rc2/rc3) and SDK 0.3.9 landed this week, signaling stabilization of persistence and state management — the backbone YAMLGraph relies on for reproducible YAML-first pipelines. The checkpoint iterations suggest active refinement of edge cases around resumption and consistency.

**Agent behavior remains opaque until production.** LangChain's essay "You don't know what your agent will do until it's in production" echoes a core YAMLGraph concern: declarative YAML can specify *intent*, but actual agent behavior emerges from model choices, memory state, and tool interactions. This connects to the open seed on 'name the verification question' — requiring agents to state a falsifiable hypothesis before acting could bridge the gap between declared and actual behavior.

**Observability as evaluation prerequisite.** Multiple articles (Agent Observability Powers Agent Evaluation, On Agent Frameworks and Agent Observability, monday + LangSmith case study) converge on the insight that you cannot evaluate what you cannot observe. LangSmith's Google Cloud Marketplace availability suggests observability tooling is becoming table-stakes infrastructure. For YAMLGraph, this implies YAML nodes should emit structured traces by default, not as an afterthought.

**Memory and context patterns crystallizing.** Agent Builder's memory system, context management for Deep Agents, and memory usage guides indicate the field is converging on repeatable patterns for state handling. YAMLGraph's node-based model could benefit from a memory abstraction layer that makes context flow explicit in the YAML graph structure itself.

**Tool registry and protocol archaeology.** Agent Builder's new tool registry feature aligns with the open seed on formalizing protocol archaeology — extracting endpoint URLs, auth flows, and message formats into structured briefs. A YAML-first approach could make tool integration declarative rather than imperative.

**Seed:** As agent observability becomes standard infrastructure (LangSmith, tracing, evaluation frameworks), should YAMLGraph enforce a 'trace-first' design where every node declares what observable events it will emit before execution, making silent failures and invisible decisions structurally impossible?

---

## 2026-02-27: Chaplain — FR-106: Parallel Worktree Pipeline Approved

FR-106, detailing a parallel development pipeline via Git worktrees, received approval after a comprehensive planning and judgment cycle. Key planning decisions included removing the non-existent `read_fr` node, establishing graph placement at `examples/enforce/`, and deferring `watch.sh` integration to reduce scope from 5 to 3 days. A concrete concurrency testing strategy was also defined, successfully resolving all initial judgment issues. The judge approved the FR, adding two crucial, non-blocking implementation notes concerning correct prompt path resolution (`prompts_relative: true` and `prompts_dir: prompts`) and refining a shell validation command for a robust clean-tree check. This process significantly refined the FR.

**Seed:** How can we integrate more automated checks for common technical conventions and shell script best practices into the initial FR planning phase to catch issues proactively?

---

## 2026-02-27: Chaplain — Architecture Cross-Check Approved

FR-107, proposing an extension to `req_coverage.py --strict`, has been approved. This feature will cross-check all requirement IDs in `ALL_REQS` against `ARCHITECTURE.md` to ensure no 'phantom requirements' exist without corresponding architectural documentation. The plan leverages the existing `_load_req_descriptions()` parser and is estimated at 0.5 days. The judgment highlighted the clarity, consistency, measurability, and feasibility of the proposal, noting strong alignment with current architecture. Implementation guidance includes adjusting the parser's call location, separating housekeeping ACs, and addressing the REQ-YG-105 gap first.

**Seed:** What other forms of architectural or requirement drift could be proactively detected or prevented through automated checks?

---

## 2026-02-27: FR-105 Implementation — Session Continuations

**Context:** FR-105 added `--resume` and `--continue` flag support to the Copilot node, with session ID capture from stderr into `CopilotResult.session_id`. 994 insertions across 14 files, 12 new tests, new linter patterns.

**Trap: Quick confidence from passing `req_coverage.py --strict`.** The coverage script validated that REQ-YG-105 had tagged tests, but the requirement was never added to ARCHITECTURE.md. The traceability chain (architecture → requirement → test) was broken at the architecture layer. Three consecutive Inquisitor audits flagged this before FR-107 closed the gap by adding architecture cross-checking to the script itself.

**Insight:** When the coverage script and tests are updated in the same commit, the cross-check is tautological — the script validates its own additions. The fix: `req_coverage.py --strict` now also verifies that every requirement ID exists as a table row in ARCHITECTURE.md, closing the phantom-requirement vulnerability.

**Heuristic:** A green CI gate only proves what it checks. When adding a new validation dimension (architecture ↔ tests ↔ coverage script), verify that the gate inspects all edges of the traceability triangle, not just one.

**Seed:** Could the same phantom-gap pattern exist in other cross-referencing systems (e.g., CHANGELOG entries vs. feat commits, noqa confessions vs. actual suppressions)?

---

## 2026-02-27: Chaplain — Approving FR-106: Parallel Worktree Pipeline

FR-106, detailing a parallel development pipeline via Git worktrees, was planned and subsequently approved. Key refinements during planning included fixing shell validation, adding crucial metadata flags for prompt resolution, and carefully scoping requirements to REQ-YG-106+. Significant deferrals, like `watch.sh` integration, ensured minimal scope. The judging process confirmed strong clarity, no ambiguities, measurable acceptance criteria, and feasibility, noting that dependencies (FR-081, FR-105) were already implemented. Four non-blocking implementation notes were added, covering aspects like shell test strategy and `.venv` symlink risks, ensuring the FR is now ready for development.

**Seed:** What mechanisms can ensure the non-blocking implementation notes are effectively incorporated during development?

---

## 2026-02-27: Chaplain — Mastermind Game FR Approved

The session focused on planning and judging FR-108: Mastermind Game. The planning phase involved researching existing patterns, leading to a detailed feature request for a terminal code-breaking game. It leverages the `interactive_tool` node pattern with pure Python logic, optional LLM hints, and correct duplicate-handling scoring, following the structure of FR-082 (Minesweeper). The judging process rigorously evaluated the FR, verifying its alignment with existing patterns and a canonical demo. FR-108 was **APPROVED** due to its clear, minimal scope, lack of contradictions against established schemas, and sound, measurable acceptance criteria. Minor corrections included noting FR-082's unimplemented status and adding implementation guidance.

**Seed:** How can we better track the implementation status of referenced FRs to ensure accuracy in future planning and judging cycles?
