# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-22.md](diary-2026-02-22.md) — 12 entries from 2026-02-22.

---

## 2026-02-23: FR-079 — The State-Based Unification

**Context:** Completed FR-079 "Unify Incaller and Outcaller Under Shared Root" — prompted sharing and WebSocket handler extraction between two telco projects.

**Trap:** The initial Judgement proposed `metadata.vars.call_context` — a path that doesn't exist in LangGraph. Quick confidence almost led to implementation before verifying the API. The correction came from researching how state actually flows: LLM nodes with no explicit `variables:` get filtered state, so adding `call_context` to state and setting it in the first tool node was sufficient. Zero framework changes.

**Insight:** Parameterization at the state level is more composable than at the metadata level. The first tool node (`initiate_call` / `await_call`) is the natural place to inject context because it's the entry point for each graph instance. Any downstream node can read `call_context` without knowing how it was set.

**Line-count reduction:**
- `outcaller/server.py`: 148 → 42 lines (−72%)
- `incaller/server.py`: 187 → 80 lines (−57%)
- Combined WebSocket handler: 240 duplicated lines → 1 canonical source (134 lines)

**Heuristic:** *When unifying duplicated code between sibling projects, find the natural parameterization boundary — the earliest point where the two flows diverge. Parameterize at that boundary, not downstream. For shared prompts, that boundary is state initialization; for shared handlers, it's the session injection.*

**Seed:** The symlink approach (`incaller/prompts/shared → ../../outcaller/prompts/shared`) is a filesystem-level abstraction. Would a graph-level abstraction be more robust — e.g., a `prompt_path_alias` in graph.yaml that maps `shared/*` to an external directory? Or does the symlink's simplicity (no framework changes, visible in `ls -la`) outweigh its fragility (breaks if repo structure changes)?

---

## 2026-02-23: Inquisitor Audit — The Expanding Blind Spot

**Context:** 15th Inquisitor audit of the latest 5 commits (`376bcda`..`3a9e01d`). One new commit since last audit: `3a9e01d` (`refactor(FR-078): delete relocated project tests`) — deletes 10 test files (3047 lines) from `tests/unit/` and `tests/integration/` that were copied to `projects/{outcaller,incaller}/tests/` in the prior commit. This is the second half of the FR-078 two-commit operation. The remaining 4 commits (`e603f29`, `fbede87`, `67461e6`, `376bcda`) have been audited in rounds #11–#14 and are frozen.

**Findings:**

- ✓ COMPLIANT — `3a9e01d` follows Conventional Commits with scope and FR tag (`refactor(FR-078):`). Feature request `FR-078-relocate-project-tests.md` exists. `req_coverage.py` passes cleanly (all CAPs green). No noqa suppressions existed in the deleted files, so `confessions.md` remains consistent. The deletion is the clean second step of a planned two-commit operation. Commandments 1, 3, 10, ADR-001 upheld.
- ⚠ DRIFT — No CHANGELOG entry for FR-078 across either commit (`e603f29` or `3a9e01d`). The `refactor:` prefix is exempt from FR-077 enforcement, so technically compliant. But the combined operation removed 3047 lines and 8 requirements from framework tracking — a structural change invisible to CHANGELOG readers. 2nd consecutive audit flagging this. The window to add a retroactive entry is closing.
- ⚠ DRIFT — The `noqa_coverage.py` scanner blind spot has grown. `projects/` now contains 9 noqa suppressions (up from 3 when first flagged in audit #10). FR-078's test relocation copied `conftest.py` files with `# noqa: E402` into `projects/{outcaller,incaller}/tests/`. The scanner reports 43/44/0 — true count is 52 suppressions. Known limitation per audit #13 reclassification, but the gap is widening with each relocation. The 44-vs-43 documented-vs-actual count also reveals 1 orphaned confession (documented noqa no longer exists in scanned code).
- ⚠ DRIFT — No `Co-authored-by` trailers. 12th consecutive audit. Dead letter policy per audit #12 reclassification.
- ⚠ DRIFT — No dedicated diary entry for FR-078 completion. The two-commit refactoring (`e603f29` + `3a9e01d`) represents a significant architectural decision — severing project tests from the framework — but the only reflection exists in audit entries #14 and #15 (this one). The Sermon's Distill step was served by proxy, not by the author.

**Heuristic:** *When a scanner's blind spot grows proportionally with the codebase it excludes, the exclusion is not a static decision — it is an accelerating debt. The `projects/` exclusion was acceptable at 3 suppressions; at 9, it has tripled in 2 commits. Each relocation or new project file widens the gap without any signal. A scanner should either scan everything or explicitly report what it skips, so growth in the excluded zone is visible without an Inquisitor to count it.*

**Seed:** The `noqa_coverage.py` scanner reports 44 confessions but only 43 live suppressions — meaning 1 confession documents a noqa that no longer exists. Should orphaned confessions be pruned automatically (to keep the document honest), or preserved as archaeological record (to document what once needed suppression and why it was resolved)?

---

## 2026-02-23: Inquisitor Audit — The Severed Umbilical

**Context:** 14th Inquisitor audit of the latest 5 commits (`d45764e`..`e603f29`). One new commit since last audit: `e603f29` (`refactor(FR-078): relocate project tests to project repos`) — re-tags probe-recap tests from `REQ-YG-083/084/085` to `OC-005` (project namespace), removes CAP-27 (Telco) and CAP-29 (Incaller) from `req_coverage.py`, copies test files to `projects/{outcaller,incaller}/tests/`, and updates `ALL_REQS` to exclude project requirements (078–082, 084–086). The remaining 4 commits (`fbede87`, `67461e6`, `376bcda`, `d45764e`) have been audited in rounds #7–#13 and are frozen.

**Findings:**

- ✓ COMPLIANT — `e603f29` follows Conventional Commits with scope and FR tag (`refactor(FR-078):`). Feature request `FR-078-relocate-project-tests.md` exists — planning before coding (Commandment 1). `req_coverage.py` passes cleanly: all framework CAPs green, no uncovered requirements. The architectural decision — framework tracks framework reqs, projects track their own — is coherent and documented. Commandments 1, 3, 10 upheld.
- ⚠ DRIFT — Tests in `tests/unit/test_probe_recap.py` and `tests/unit/test_questionnaire_flow.py` are re-tagged from `REQ-YG-*` to `OC-005`, a project namespace ID. `OC-005` is not tracked by `req_coverage.py` — making the tags decorative. They satisfy the letter of ADR-001 (every test has a `@pytest.mark.req` tag) but not the spirit (tags should be verified by tooling). Until project repos have their own `req_coverage.py`, these tags are assertions nobody checks.
- ⚠ DRIFT — No CHANGELOG entry for FR-078. The `refactor:` prefix is exempt from FR-077 enforcement, so technically compliant. However, removing 8 requirements from framework tracking is a significant structural change that warrants changelog visibility. Future archaeologists will wonder when CAP-27/29 disappeared.
- ⚠ DRIFT — No dedicated diary entry for the FR-078 refactoring itself. The commit includes prior audit diary entries (#11–#13) but no reflection on the cognitive process of severing project tests from the framework. The Sermon's Distill step was skipped. This audit partially compensates.
- ⚠ DRIFT — No `Co-authored-by` trailer. 11th consecutive audit. Dead letter policy.

**Heuristic:** *When relocating ownership (tests, requirements, configs) from a monorepo to project repos, the tags must travel with their verification tooling. A `@pytest.mark.req("OC-005")` tag without a corresponding `req_coverage.py` in the project repo is a dangling pointer — it looks like traceability but provides none. The test of a tag is not its presence but whether something fails when the tagged requirement is unmet.*

**Seed:** FR-078 creates a two-tier requirement system: framework reqs verified by `scripts/req_coverage.py`, and project reqs tagged but unverified. Should each project in `projects/` carry a minimal `req_coverage.py` (or a shared one parameterized by project), so that `OC-005` tags are as enforceable as `REQ-YG-*` tags? Or should unverified tags be stripped entirely to avoid false confidence?

---

## 2026-02-23: Inquisitor Audit — The RED Before Green

**Context:** 13th Inquisitor audit of the latest 5 commits (`3c98b6b`..`fbede87`). One new commit since last audit: `fbede87` (`test(IC-001): add tests for SIN-1 user_refused, SIN-2 goodbye schema`) — adds 64 lines of RED tests to `tests/unit/test_incaller.py`. These are deliberately failing tests for two bugs discovered during the IC-001 joint audit of incaller/outcaller. The remaining 4 commits (`67461e6`, `376bcda`, `d45764e`, `3c98b6b`) have been audited in rounds #7–#12 and are frozen.

**Findings:**

- ✓ COMPLIANT — `fbede87` follows Conventional Commits with scope and FR tag (`test(IC-001):`). Both test classes carry `@pytest.mark.req("REQ-YG-084")`. The commit is textbook TDD RED phase (Commandment 7): tests written first, asserting behavior that doesn't exist yet (`user_refused` propagation, schema-free `goodbye_refused`). The IC-001 feature request (`IC-001-sins.md`) exists as an untracked working file — planning before coding (Commandment 1). No CHANGELOG required for `test:` prefix per FR-077. Commandments 1, 7, 10, ADR-001 upheld.
- ✓ COMPLIANT — `noqa_coverage.py` scanner exclusion of `projects/` reclassified per audit #12 heuristic. The SCAN_DIRS gap has been flagged as ✗ VIOLATION in audits #10–#12 with no remediation. Per the heuristic ("a violation persisting 3+ audits without remediation is a policy decision"), this is now reclassified as **KNOWN LIMITATION** and will not be re-flagged. The gap remains: 4 lines / 6 suppressions in `projects/outcaller/` are invisible to the scanner. Remediation path documented in audits #10–#12 (add `"projects"` to `SCAN_DIRS`, confess outcaller noqas).
- ⚠ DRIFT — No `Co-authored-by` trailer on `fbede87`. 10th consecutive audit. Reclassified as dead letter policy per audit #12 pattern. Will continue noting but not escalating.
- ⚠ DRIFT — No diary entry for IC-001 yet. Acceptable: IC-001 is mid-flight (RED phase only, no GREEN or REFACTOR). Diary should arrive with the completion commit per the Sermon's Distill step. Flagging as reminder, not violation.

**Heuristic:** *A RED-only commit — tests that assert unimplemented behavior — is the purest expression of Commandment 7. It deserves its own commit, separate from the fix, because it proves the test was written before the code. When the GREEN commit arrives, `git log` becomes a TDD proof trail. Squashing RED and GREEN into one commit destroys this evidence.*

**Seed:** IC-001's `test_dialogue_e2e.py` lives in `projects/incaller/` as an untracked file, outside `tests/unit/`. If it gets committed there, it won't be discovered by `pytest tests/` without explicit path inclusion. Should the test runner's scope mirror the scanner's scope problem — and should both be fixed together by adding `projects/` to every tool's search path?

---

## 2026-02-23: Inquisitor Audit — The Aging Window

**Context:** 12th Inquisitor audit of the latest 5 commits (`0ce848a`..`67461e6`). One new commit since last audit: `67461e6` (`docs(incaller): add live test checklist`) — a pure documentation addition (pre-flight checks, curl tests, call verification). The `36c5602` (`fix: Inqusitor looping`) commit, flagged as ✗ VIOLATION in audits #7–#11, has now aged out of the 5-commit window. All 5 commits belong to the IC-000 incaller delivery.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tag where applicable (`feat(incaller): IC-000`, `docs(incaller):`, `chore: IC-000`). CHANGELOG v0.4.55 covers the `feat` commits. REQ-YG-084–086 present in ARCHITECTURE.md with `@pytest.mark.req` tags on all 3 test functions. CONF-123 documents the incaller noqa. The IC-000 delivery (5 commits: feature, reflection, docs, start script, test checklist) is the most doctrinally complete delivery unit audited to date. Commandments 3, 7, 10, ADR-001, and noqa Confessions all satisfied.
- ✗ VIOLATION — `noqa_coverage.py` `SCAN_DIRS` remains `["yamlgraph", "tests", "examples", "scripts"]` — excludes `projects/`. 3 noqa suppressions in `projects/` (1 incaller, 2 outcaller) are invisible. The scanner reports "43 suppressions, 44 confessions, 0 undocumented" — true count is 46. The 2 outcaller suppressions (`twilio_call.py:40-41`, E402+F401) remain unconfessed and undetectable. 3rd consecutive ✗ finding (audits #10, #11, #12). This is now a decision, not a finding.
- ⚠ DRIFT — No `Co-authored-by` trailers on any of the 5 commits. 9th consecutive audit. No enforcement mechanism exists. The policy is dead letter law.
- ⚠ DRIFT — `67461e6` is a `docs:` commit adding a test checklist but has no CHANGELOG entry. FR-077 only enforces CHANGELOG for `feat:` and `fix:` — so technically compliant. However, the checklist represents operational knowledge (how to verify the incaller works) that would benefit from changelog visibility. Minor gap.

**Heuristic:** *A violation that persists across 3+ audits without remediation is no longer a finding — it is a policy decision made by inaction. The audit should reclassify it: either escalate to a blocking issue (file it, assign it, track it) or downgrade to "known limitation" and stop reporting it. Perpetual ✗ findings without action erode audit credibility more than the violation itself.*

**Seed:** The IC-000 delivery achieved full doctrinal compliance across 5 commits — the longest compliant streak observed. What made this delivery different? Was it the two-commit pattern (feature + reflection), the clear scope (single FR), or the heavy reuse (90% imported from outcaller)? Identifying the causal factor would let us replicate compliance by design rather than by discipline.

---

## 2026-02-23: Inquisitor Audit — The Unfixed Fix

**Context:** 11th Inquisitor audit of the latest 5 commits (`36c5602`..`376bcda`). One new commit since last audit: `376bcda` (`feat(incaller): IC-000 add automated start script`) — adds `start.sh` (137 lines), `.env.example`, and a README Quick Start section. The remaining 4 commits have been audited in prior rounds (#7–#10) and are frozen.

**Findings:**

- ✓ COMPLIANT — `376bcda` follows Conventional Commits with scope and FR tag (`feat(incaller): IC-000`), includes a CHANGELOG entry (v0.4.55 mentions `start.sh`), and introduces no new Python capability requiring ARCHITECTURE.md requirements or test tags. The commit is a shell script + documentation — no doctrinal gaps. Commandments 3, 10 upheld.
- ✗ VIOLATION — `noqa_coverage.py` `SCAN_DIRS` remains `["yamlgraph", "tests", "examples", "scripts"]` — still excludes `projects/`. 3 noqa suppressions in `projects/` (1 in incaller, 2 in outcaller) are invisible to the scanner. The tool reports "43 suppressions, 44 confessions, 0 undocumented" — but the true count is 45 suppressions. 2 outcaller suppressions (`twilio_call.py:40-41`, E402+F401) remain unconfessed and undetectable. This was escalated to ✗ in audit #10. No remediation has been applied. The scanner's false positive persists.
- ✗ VIOLATION — `36c5602` (`fix: Inqusitor looping`) has no CHANGELOG entry. 5th consecutive audit flagging this. The commit is frozen history. This finding is now permanently archaeological — noted for the record but no further escalation is meaningful without git history rewrite.
- ⚠ DRIFT — No `Co-authored-by` trailers on any of the 5 commits. 8th consecutive audit. The trailer policy has no enforcement mechanism and consistently decays. This is a dead policy unless automated via `prepare-commit-msg` hook.
- ⚠ DRIFT — The `376bcda` start script (`start.sh`) is a substantial automation (ngrok setup, Twilio API webhook update, graph execution) but has no dedicated diary entry. It ships as part of the IC-000 three-commit delivery (`0ce848a` + `3c98b6b` + `376bcda`), which does have a collective diary entry ("Reuse as Discipline"). Acceptable as a delivery unit, but the automation insights (ngrok lifecycle, Twilio webhook API) are lost to reflection.

**Heuristic:** *A scanner vulnerability flagged as ✗ VIOLATION in one audit that remains unfixed by the next audit is no longer a finding — it is a decision. Either fix it (add `"projects"` to `SCAN_DIRS` and confess the 2 outcaller noqas) or accept the blind spot and document it as a known limitation. Recurring ✗ findings that never get fixed erode the authority of the audit itself.*

**Seed:** The audit has now flagged `SCAN_DIRS` exclusion twice with no fix. Should the Inquisitor itself be empowered to apply trivial fixes (adding a directory to a list, adding a confession entry) rather than only reporting? An "Inquisitor with hands" — audit + remediate in one pass — would close the loop on mechanical violations while preserving the reporting trail.

---

## 2026-02-23: Inquisitor Audit — The Scanner's Blind Spot

**Context:** 10th Inquisitor audit of the latest 5 commits (`01b51ff`..`d45764e`). One new commit since last audit: `d45764e` (`docs(incaller): add Twilio phone number configuration guide`) — a pure documentation addition (127 lines, one `.md` file). The remaining 4 commits have been audited in prior rounds (#7–#9) and are frozen.

**Findings:**

- ✓ COMPLIANT — `d45764e` follows Conventional Commits (`docs(incaller):`), contains only a Twilio webhook configuration guide, and correctly requires no CHANGELOG entry, requirement, test, or diary entry. The incaller delivery (`0ce848a` + `3c98b6b` + `d45764e`) is now a three-commit unit: feature, reflection, documentation. All doctrinal checkpoints satisfied. Commandments 3, 10 upheld.
- ✓ COMPLIANT — `noqa_coverage.py --strict` reports 43 suppressions, 44 confessions, 0 undocumented. All scanned files are clean. CONF-123 (incaller's E402) properly documented in audit #9's remediation commit.
- ✗ VIOLATION — `noqa_coverage.py` `SCAN_DIRS` is `["yamlgraph", "tests", "examples", "scripts"]` — it excludes `projects/`. The 4 noqa suppressions in `projects/outcaller/nodes/twilio_call.py:40-41` (2× E402, 2× F401) are invisible to the tool. The script's "✓ All documented" output is a false positive. This is the root cause behind the recurring DRIFT flagged in audits #8 and #9. The fix: add `"projects"` to `SCAN_DIRS`, then confess the 4 suppressions.
- ✗ VIOLATION — `36c5602` (`fix: Inqusitor looping`) remains without a CHANGELOG entry. 4th consecutive audit. The commit is archaeological — frozen history. No further escalation possible without rewriting git history.
- ⚠ DRIFT — No `Co-authored-by` trailers on any of the 5 commits. Recurring since audit #4. The trailer policy has no hook enforcement and decays under all conditions. Either automate it (prepare-commit-msg hook) or accept the gap and remove the policy.

**Heuristic:** *A validation tool that reports "all clear" while excluding an entire directory is worse than no tool at all — it creates false confidence. When adding a new top-level directory (`projects/`), audit every scanner's scope. The one law applies: normalize at the boundary where external data enters (the scanner's `SCAN_DIRS`), not downstream where symptoms manifest (individual file audits).*

**Seed:** The `projects/` directory was born outside the scanner's awareness. What other project-wide tools (`req_coverage.py`, `ruff`, `vulture`) have blind spots for `projects/`? A meta-audit of tool configurations — scanning which directories each tool covers — would surface all such gaps in one pass. Should this be a CI check: "every top-level Python directory must appear in every scanner's scope"?

---

## 2026-02-23: Inquisitor Audit — The Two-Commit Pattern

**Context:** 9th Inquisitor audit of the latest 5 commits (`2a5515b`..`3c98b6b`). The key development since the last audit: commit `3c98b6b` (`chore: IC-000 reflection and noqa confession`) retroactively completed the doctrinal obligations left open by `0ce848a` — adding the diary entry and CONF-123 confession. Together, these two commits form the first fully compliant feature delivery in the audit window.

**Findings:**

- ✓ COMPLIANT — `0ce848a` + `3c98b6b` together satisfy every doctrinal checkpoint: Conventional Commit with scope and FR tag, CHANGELOG v0.4.55 entry, REQ-YG-084–086 in ARCHITECTURE.md, `@pytest.mark.req` tags on all 3 test functions, diary entry ("Reuse as Discipline"), and CONF-123 for the `twilio_inbound.py` noqa. The two-commit pattern (feature + reflection) is a valid delivery unit. Commandments 7, 10, ADR-001, noqa Confessions, and the Sermon's Distill step all satisfied.
- ✗ VIOLATION — `36c5602` (`fix: Inqusitor looping`) remains without a CHANGELOG entry. This is the 3rd audit flagging it (audits #7, #8, #9). The commit is frozen, the typo permanent. FR-077's `changelog-required` hook was bypassed. At this point, the finding is archaeological — the damage is done and cannot be corrected retroactively without rewriting history.
- ⚠ DRIFT — `projects/outcaller/nodes/twilio_call.py` lines 40–41 contain `# noqa: E402, F401` with no CONF-XXX entries in `docs/confessions.md`. Pre-existing debt, not introduced by these 5 commits, but surfaced during cross-reference audit. Two confessions (E402 + F401 × 2 lines = up to 4 entries) are owed.
- ⚠ DRIFT — No `Co-authored-by` trailers on any of the 5 commits. This is a recurring gap flagged in every audit since #4. The trailer is a manual discipline with no hook enforcement — the same decay pattern identified in audit #8's heuristic.
- ⚠ DRIFT — 3 of 5 commits are meta-work (2× `chore: Inquisitor audit`, 1× `fix: Inqusitor looping`). The audit-to-feature ratio has improved since audit #6's infinite loop finding, but the git log still carries the scar tissue. The incaller feature (`0ce848a` + `3c98b6b`) is the only substantive work.

**Heuristic:** *A feature delivered across two commits — implementation then reflection — can achieve full doctrinal compliance even when the first commit ships under delivery pressure. The key is that the second commit is intentional, not accidental: it exists because the developer recognized the debt and scheduled the payoff. The two-commit pattern works when the reflection commit is a deliberate act, not a cleanup discovered by an auditor.*

**Seed:** The outcaller's unconfessed noqa suppressions (`twilio_call.py:40-41`) predate the confessions system. How many other pre-confession-era files carry undocumented suppressions? A one-time `scripts/noqa_coverage.py --strict` sweep would surface the full debt. Should this be a scheduled hygiene task, or should CI enforce zero unconfessed noqas on every push?

---

## 2026-02-23: IC-000 Incaller — Reuse as Discipline

**Context:** Implemented IC-000 inbound voice call demo. Estimated 2 days; completed in ~0.5 days. The incaller receives Twilio phone calls and conducts voicebot conversations using ElevenLabs TTS/STT — the reverse of outcaller's outbound dialing.

**What worked:**
- **Aggressive reuse** — Only wrote `await_call` node (~50 lines) and `/incoming` webhook (~30 lines). TTS, STT, probe-recap, accumulate, end_call all imported directly from outcaller. 18 files shipped, but only ~100 lines were genuinely new code. The remaining 1,877 lines were prompts, README, tests, and graph wiring.
- **TelcoSession extension** — Added `start_with_app()` method and `caller_number` field to outcaller's coordinator without breaking any existing tests. The outcaller continues to work unchanged.
- **TDD for requirements** — 9 tests written first, all passing. REQ-YG-084-086 traced through ARCHITECTURE.md and req_coverage.py. The pipeline (Plan → Red → Green → Trace) held.

**Trap avoided:**
- **Premature abstraction** — Temptation was to extract a shared telephony layer (`projects/shared/telco/`). Resisted. Direct import from outcaller is simpler and equally functional. If a third voice project appears, refactor then. Two is coincidence; three is a pattern.

**Insight:**
*Reuse is not laziness — it is discipline.* The cheapest code is the code you import. The outcaller's TTS/STT/probe-recap logic was battle-tested; copying it would have doubled the maintenance surface. Direct import preserved the single source of truth and proved REQ-YG-086 ("reuse without duplication"). The effort saved was then spent on tests, documentation, and prompts — the parts that differentiate incaller from outcaller.

**Heuristic:** *Before writing a new module, ask: can I import an existing one and extend it with a method or field? Extension preserves tests; duplication abandons them.*

**Seed:** The outcaller and incaller share 90% of their graph structure (probe-recap, speak, listen, accumulate). Should there be a "telco base graph" that both inherit from, or is the current copy-adapt-prompts pattern preferable for clarity? Graph inheritance is not a thing yet — but subgraph parameterization might be.

---

## 2026-02-23: Inquisitor Audit — The Incaller Arrives

**Context:** 8th Inquisitor audit of the latest 5 commits (`9084530`..`0ce848a`). For the first time since audit #2, there is substantive new work: `0ce848a` (`feat(incaller): IC-000 add inbound voice call demo`) — 1,977 lines across 18 files. The remaining 4 commits (`36c5602` fix, 3× `chore: Inquisitor audit`) have been audited 6+ times and are frozen.

**Findings:**

- ✓ COMPLIANT — `0ce848a` is doctrinally exemplary: Conventional Commit with scope and FR tag, detailed commit body, CHANGELOG v0.4.55 entry, REQ-YG-084–086 added to ARCHITECTURE.md, and all 3 test functions carry `@pytest.mark.req` tags. The full pipeline — Plan → Implement → Trace — was followed. Commandments 7, 10, and ADR-001 all satisfied.
- ✗ VIOLATION — `projects/incaller/nodes/twilio_inbound.py:38` contains `# noqa: E402` with no corresponding CONF-XXX entry in `docs/confessions.md`. The noqa Confessions doctrine requires every suppression to be documented. This is a single-line fix: add a CONF-125 entry (next available in Example Code range, since `projects/` follows the example runner pattern).
- ✗ VIOLATION — No diary entry was written for the IC-000 incaller work. The Sermon's Distill step requires a metacognitive reflection after completing a task list. The incaller was a substantial feature (689-line FR, 18 files, new node type). This is exactly the kind of work that produces traps and seeds worth capturing. The reflection is owed.
- ⚠ DRIFT — None of the 5 commits carry `Co-authored-by` trailers. The git commit trailer policy in the development instructions requires `Co-authored-by: Copilot <...>` on AI-assisted commits. This has been a recurring gap across all audits.
- ⚠ DRIFT — The tooling TDD gap (flagged as ✗ in audits #4–#7, proposed remedy: FR-078 or CLAUDE.md Tooling Exception) remains unresolved. The incaller commit demonstrates that the project *can* do full TDD when building features — the gap is specific to dev-tooling scripts. This audit does not re-escalate; the finding is stable and awaits a decision.

**Heuristic:** *A feature that nails every checkpoint (Conventional Commit, CHANGELOG, ARCHITECTURE reqs, test req tags) but skips the diary and the noqa confession reveals a pattern: the automated guards (hooks, CI) are enforced, but the manual disciplines (reflection, confession) are forgotten under delivery pressure. Automate the reminder, or accept that manual disciplines decay.*

**Seed:** Could a pre-commit hook scan for new `# noqa` lines in staged files and reject the commit unless `docs/confessions.md` is also staged? This would graduate noqa confession from manual discipline to structural guard — the same pattern that FR-077 applied to CHANGELOG enforcement.

---

## 2026-02-23: Inquisitor Audit — The Hook That Didn't Bark

**Context:** 7th Inquisitor audit of the latest 5 commits (`36c5602`..`892ee07`). The prior audit identified the infinite audit loop and planted a seed to fix it. Commit `36c5602` acted on that seed by removing auto-commit/push from `.chaplain/inquisitor.sh` — a direct response to the diary feedback loop. This audit checks whether the fix itself was doctrinally clean.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits format (`fix:`, `chore:`). All `# noqa` suppressions (CONF-002, CONF-003) remain confessed. No new unconfessed suppressions. The diary seed from audit #6 (break the loop) was acted on — observation led to action. The Sermon's feedback loop is working.
- ✗ VIOLATION — `36c5602` (`fix: Inqusitor looping`) is a `fix:` commit with **no CHANGELOG.md entry**. FR-077's pre-commit hook (`changelog-required`, `commit-msg` stage) is designed to block exactly this. The hook either wasn't installed or was bypassed with `--no-verify`. The irony: the commit that fixed the inquisitor's `--no-verify` abuse was itself likely committed with `--no-verify`. The guard was absent when guarding itself.
- ⚠ DRIFT — `36c5602` has a typo in the commit message: "Inqusitor" → "Inquisitor". Minor, but commit messages are permanent documentation. This is the project's public history.
- ⚠ DRIFT — 4 of 5 commits are meta-work (3 audit diary entries + 1 audit-loop fix). Only `892ee07` (chaplain cleanup) represents substantive project work, and it was already fully audited in 6 prior rounds. The audit mechanism consumed more commits than it audited. The loop is now broken, but the debt remains visible in the git log.
- ⚠ DRIFT — The tooling TDD gap (flagged as ✗ in audits #5–#6 with concrete remedy: add Tooling Exception to CLAUDE.md or file FR-078) remains unresolved. However, the auto-commit loop that was inflating audit frequency has been fixed, so the urgency of repeated flagging is reduced. This finding is now stable — it will recur until a decision is made, but it no longer compounds.

**Heuristic:** *A guard that can be bypassed by the same flag it prohibits is not a guard — it is a suggestion. `--no-verify` is the escape hatch for emergencies, but when it becomes the default path for tooling commits, the hook provides false confidence. The `changelog-required` hook must either be un-bypassable (CI enforcement) or the `--no-verify` usage must be auditable (logged in commit trailers).*

**Seed:** FR-077's CHANGELOG enforcement lives only in the pre-commit hook — a local, bypassable check. Should a CI job duplicate this check on push, making it impossible to merge a `fix:`/`feat:` commit without a CHANGELOG entry regardless of local hook state? This would graduate the guard from suggestion to law.

---

## 2026-02-23: Inquisitor Audit — The Audit Loop

**Context:** 6th manual Inquisitor audit of the latest 5 commits (`01b51ff`..`52c6b33`). Three of the five commits are `chore: Inquisitor audit` diary entries. The remaining two (`892ee07` chaplain cleanup, `52c6b33` FR-077 CHANGELOG enforcement) have been audited in all five prior rounds. No new productive code has shipped since the 3rd audit.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits (`chore:`, `feat(hooks):`). CHANGELOG covers the `feat` commit (FR-077). All `# noqa` suppressions (CONF-002, CONF-003) remain confessed. No new suppressions introduced. Structural compliance is solid and has been stable across 6 audits.
- ✗ VIOLATION — The tooling TDD gap was escalated to ✗ in audit #5 with a concrete remedy (add `## Tooling Exception` to CLAUDE.md). Two commits have landed since that escalation — both are audit entries. The decision remains unmade. The Sermon: "every failure shalt refine the law." Six audits have identified the failure; zero have refined the law.
- ✗ VIOLATION — The Inquisitor has become the primary commit source: 3 of the last 5 commits are audit diary entries. The audit mechanism, designed to detect entropy (Commandment 8), is now *generating* entropy. Each audit re-examines the same frozen commits, produces the same findings, and adds ~20 lines to `diary.md` — a net increase in project surface area with zero information gain.
- ⚠ DRIFT — All 5 commits lack `Co-authored-by` trailers and commit bodies. The `892ee07` deletion of 4 files (213+ lines) still has no commit body explaining rationale. This is the 3rd audit flagging it; the commit is frozen so the finding is permanent — but it signals a habit gap in commit discipline.
- ⚠ DRIFT — `docs/diary.md` is now 267 lines with 6 audit entries covering the same 2 substantive commits. The diary rotation script exists (`scripts/diary_rotate.py`) but hasn't triggered, suggesting the threshold hasn't been reached or rotation is manual. The signal-to-noise ratio of the diary is degrading.

**Heuristic:** *An audit that audits only prior audits has zero information gain — it is a fixed point in a feedback loop. The Inquisitor must refuse to re-examine commits it has already judged. When the top-of-stack commits are all audit entries, the correct action is not another audit but a decision on the open findings. Observation without action is not diligence — it is ceremony.*

**Seed:** The Inquisitor needs a termination condition: if all commits since the last audit are audit-only commits, the Inquisitor should emit "No new work to audit" and exit without appending to the diary. This converts an infinite loop into a halting function. Should this guard live in the post-commit hook, or in the audit script itself?

---

## 2026-02-23: Inquisitor Audit — Decision Debt Compounding

**Context:** Manual Inquisitor audit of the 5 most recent commits (`9084530`..`8664452`): chore audit entry, chaplain cleanup (4 file deletions), FR-077 CHANGELOG enforcement, v0.4.54 release, FR-076 post-commit inquisitor. This is the 5th audit in the current cycle.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags (`feat(hooks)`, `feat(chaplain)`, `chore`). Commandment 10 format upheld consistently across all audited commits.
- ✓ COMPLIANT — All `# noqa` suppressions in `yamlgraph/` (CONF-002: ARG002, CONF-003: ANN001) remain confessed in `docs/confessions.md`. No new suppressions introduced. No unconfessed sins.
- ✓ COMPLIANT — CHANGELOG.md v0.4.54 entry covers both `feat` commits (FR-076, FR-077). FR-077's own hook now structurally prevents future omissions.
- ⚠ DRIFT — `892ee07` (`chore: chaplain cleanup`) deleted `scripts/chaplain.sh` (213 lines) and 3 `.chaplain/` files with no commit body. Commandment 8: "record significant removals in commit notes." This is the **2nd consecutive audit** flagging this commit — the commit is frozen, so the finding is permanent. The remedy is forward-looking: establish a pre-commit check for deletion-heavy commits, or accept that `chore` cleanup commits are exempt.
- ⚠ DRIFT → ✗ VIOLATION (escalated) — The tooling TDD gap has now been flagged in **5 consecutive audits** without resolution. The 4th audit explicitly stated: "A recurring ⚠ that persists across 4+ audits without resolution is itself a ✗ VIOLATION — not of the code, but of the feedback loop." The Sermon demands "every failure shalt refine the law." A concrete binary decision was proposed (exempt dev-tooling from Commandment 7, or require integration tests for hooks) and has received no answer. This is no longer drift — it is a refusal to close the loop. Escalating to ✗.

**Heuristic:** *An audit that repeatedly flags the same issue without triggering a decision is not auditing — it is complaining. The Inquisitor's role is not merely to observe but to force resolution. When a finding survives 3 audits, the next audit must either (a) record the explicit decision that closes it, or (b) file a feature request that schedules the decision. Observing the same drift forever is itself entropy.*

**Seed:** The tooling TDD question must die in the next commit — not the next audit. Concrete proposal: add a `## Tooling Exception` section to CLAUDE.md stating that dev-tooling commits (`scripts/`, `.chaplain/`, `.pre-commit-config.yaml`) are exempt from Commandment 7 (TDD) but must include a `Tested-manually: <description>` trailer in the commit message. This trades automated test coverage for documented manual verification — an honest compromise that closes the loop without pretending shell hooks are untestable.

---

## 2026-02-23: Inquisitor Audit — Decision Debt Reaches Critical Mass

**Context:** Audited the latest 5 commits (`c2f0e7d`..`2a5515b`) against the Scripture. Commits: two `chore: Inquisitor audit` diary additions, `chore: chaplain cleanup` (deleted 213-line `scripts/chaplain.sh` + 3 `.chaplain/` files), `feat(hooks): FR-077 enforce CHANGELOG.md in feat/fix commits`, and `chore: release 0.4.54`.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits format. `feat(hooks)` carries scope and FR tag. `chore` commits properly prefixed. Commandment 10 upheld.
- ✓ COMPLIANT — CHANGELOG.md entry present for FR-077 (`feat` commit). `chore` commits correctly omitted. No feat/fix shipped without changelog. The FR-077 hook now structurally prevents this — prior ✗ VIOLATION is now impossible.
- ✓ COMPLIANT — Both `# noqa` suppressions in `yamlgraph/` (CONF-002: ARG002, CONF-003: ANN001) remain confessed in `docs/confessions.md`. No new suppressions introduced.
- ⚠ DRIFT — `892ee07` (`chore: chaplain cleanup`) deleted `scripts/chaplain.sh` (213 lines) and 3 `.chaplain/` files with a bare one-line commit message and no body explaining removal rationale. Commandment 8: "record significant removals in commit notes." This is the **2nd consecutive audit** flagging this exact commit — it cannot be retroactively fixed without rewriting history, but the pattern must not recur.
- ✗ VIOLATION — The tooling TDD gap is now **5 audits old**. FR-077 introduced a pre-commit hook with zero tests. The prior audit explicitly escalated this from ⚠ DRIFT to a decision debt, proposed two concrete paths (exempt tooling from Commandment 7, or require integration tests), and asked for resolution. Neither path was taken. Per the prior audit's own heuristic: *"A recurring ⚠ that persists across 4+ audits without resolution is itself a ✗ VIOLATION — not of the code, but of the feedback loop."* The Sermon demands "every failure shalt refine the law." The law has not been refined. This is now a ✗.

**Heuristic:** *Audits that repeatedly flag the same drift without driving a decision are performative, not corrective. An Inquisitor who notes the same sin five times and does not escalate to Judgement is complicit in the entropy. When findings recur, the audit itself must change: either resolve the ambiguity by proposing a Scripture amendment, or close the finding as accepted risk with an explicit exception.*

**Seed:** This audit escalated the tooling TDD gap from ⚠ to ✗. The next action is not another audit — it is a Judgement. Concrete question for the Judge: create `feature-requests/FR-078-tooling-test-policy.md` that decides once: are `scripts/`, `.chaplain/`, and `.pre-commit-config.yaml` changes exempt from Commandment 7 (with documented rationale), or must they carry integration tests (with a test template)? Until FR-078 exists, this ✗ will appear in every future audit.

---

## 2026-02-23: Inquisitor Audit — Structural Compliance, Recurring Drift

**Context:** Audited the latest 5 commits (`180f5d5`..`892ee07`) against the Scripture. Commits span FR-076 (inquisitor script + post-commit hook), v0.4.54 release, FR-077 (CHANGELOG enforcement), and a chaplain cleanup that deleted `scripts/chaplain.sh` (213 lines).

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags (`feat(hooks)`, `feat(chaplain)`, `chore`). Commandment 10 format upheld.
- ✓ COMPLIANT — CHANGELOG.md entries present for all `feat` commits (FR-076, FR-077). FR-077 now enforces this structurally via pre-commit hook — the Seed from the third audit back has fully germinated into a guardrail.
- ✓ COMPLIANT — All `# noqa` suppressions in `yamlgraph/` (CONF-002: ANN001, CONF-003: ARG002) remain confessed. No new suppressions introduced. No unconfessed sins.
- ⚠ DRIFT — Tooling TDD gap persists: 3 `feat` commits (FR-076 ×2, FR-077) introduce shell scripts and pre-commit config with zero tests. This is the **4th consecutive audit** flagging this pattern. The prior Seed asked whether Scripture should carve an exception or demand integration tests — the question remains unresolved, creating a permanent ⚠ that dilutes audit signal.
- ⚠ DRIFT — `892ee07` (`chore: chaplain cleanup`) deleted `scripts/chaplain.sh` (213 lines) and 3 `.chaplain/` files with no commit body explaining the removal rationale. Commandment 8: "record significant removals in commit notes." The removal may be justified (superseded by `.chaplain/inquisitor.sh`), but the justification is implicit, not stated.

**Heuristic:** *A recurring ⚠ that persists across 4+ audits without resolution is itself a ✗ VIOLATION — not of the code, but of the feedback loop. The Sermon demands "every failure shalt refine the law." When the same drift appears in every audit, the law must either absorb the exception or enforce the fix. Permanent ambiguity is entropy.*

**Seed:** The tooling TDD question has been asked three times and answered zero times. This is now a decision debt. Concrete proposal: add a `tooling-exception` section to the Scripture that explicitly states either (a) dev-tooling commits (`scripts/`, `.chaplain/`, hook configs) are exempt from Commandment 7, or (b) integration tests for hooks are required (e.g., test that `feat` commit without CHANGELOG is rejected by pre-commit). Which path reduces entropy more?

---

## 2026-02-23: Inquisitor Audit — Seed Germination and Tooling TDD Gap

**Context:** Audited the latest 5 commits (`b7b3bb4`..`52c6b33`) against the Scripture. Commits span FR-073 (unit test perf), FR-076 (inquisitor script + post-commit hook), v0.4.54 release, and FR-077 (CHANGELOG commit enforcement).

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags (`feat(hooks)`, `feat(chaplain)`, `perf`, `chore`). Commandment 10 format upheld.
- ✓ COMPLIANT — CHANGELOG.md updated for all `feat`/`perf` commits. FR-077's own commit includes its CHANGELOG entry — the hook now enforces this structurally. The prior audit's ✗ VIOLATION (missing CHANGELOG in feat commits) is now impossible to repeat.
- ✓ COMPLIANT — All `# noqa` suppressions (ANN001 in `executor_async.py`, ARG002 in `token_tracker.py`) are confessed in `docs/confessions.md` with CONF-002 and CONF-003 IDs. No unconfessed sins.
- ✓ COMPLIANT — FR-076 and FR-077 are dev tooling (`.chaplain/`, `.pre-commit-config.yaml`), not framework capabilities. No ARCHITECTURE.md requirement needed per ADR-001 scope.
- ⚠ DRIFT — Three `feat` commits (FR-076 × 2, FR-077) introduce zero tests. These are shell scripts and pre-commit hook config — arguably outside TDD scope — but Commandment 7 makes no exception for commit type. The prior audit flagged the same gap for `fix(diary)`. The pattern recurs: tooling changes escape test discipline.

**Notable:** FR-077 directly implements the Seed planted by the prior Inquisitor audit: *"Should `pre-commit` enforce that every `feat`/`fix` commit touches `CHANGELOG.md`?"* — the answer was yes, and it shipped within the same day. This is the first observed instance of a diary Seed germinating into a feature. The doctrine's feedback loop (Distill → Seed → Plan → Enforce) is functioning.

**Heuristic:** *Seeds are not rhetorical. When a Seed asks "should X be enforced?", treat it as a latent feature request. If the answer is obviously yes, skip Judge and go straight to Enforce — the Seed already contains the spec.*

**Seed:** The tooling TDD gap recurs across three audits now. Should the Scripture carve an explicit exception for dev-tooling commits (`scripts/`, `.chaplain/`, hook configs), or should integration tests be written for hooks (e.g., test that a feat commit without CHANGELOG is rejected)? The current ambiguity lets the same ⚠ DRIFT appear in every audit without resolution.

---

## 2026-02-23: Inquisitor Audit — Post-Release Compliance Check (v0.4.54)

**Context:** Automated Inquisitor audit of the 5 most recent commits (`948caf9`..`c2f0e7d`), spanning diary rotation, FR-073 test performance, FR-076 inquisitor tooling, and the v0.4.54 release. Triggered by FR-076 post-commit hook.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags where applicable (`feat(chaplain)`, `perf`, `chore(diary)`, `chore`). Commandment 10 format upheld.
- ✓ COMPLIANT — CHANGELOG.md updated in release commit `c2f0e7d` covering both FR-076 and FR-073. The prior Inquisitor audit flagged missing CHANGELOG entries; the release commit remediated this before push. Self-correcting loop confirmed.
- ✓ COMPLIANT — All `# noqa` suppressions (`ANN001` in `executor_async.py`, `ARG002` in `token_tracker.py`) are confessed in `docs/confessions.md` with CONF-002 and CONF-003 IDs. No unconfessed sins.
- ✓ COMPLIANT — FR-076 is dev tooling (`.chaplain/`, `.pre-commit-config.yaml`), not a framework capability. No ARCHITECTURE.md requirement needed per ADR-001 scope (framework capabilities only).
- ⚠ DRIFT — FR-073 and FR-076 lack individual diary distillation entries. The prior Inquisitor audit entry covers their compliance gaps indirectly, but the Sermon demands reflection on *cognitive process*, not just compliance status. What trap was encountered during test optimization? What insight emerged from building the inquisitor? These are unrecorded.

**Heuristic:** *An audit that finds prior violations already fixed is evidence the feedback loop works — but only if the fix was intentional, not accidental. The release commit bundled CHANGELOG entries that were missing at feat-time. Track whether this pattern recurs: are CHANGELOG entries being deferred to release commits as habit, or was this a one-time catch-up?*

**Seed:** Should the Inquisitor distinguish between "violation remediated before push" (self-correction) and "violation shipped to main" (escaped defect)? The current audit runs post-commit on main, so it can only witness the final state. A pre-push audit could catch drift *before* it merges.

---

## 2026-02-23: Inquisitor Audit — CHANGELOG and TDD Gaps in Tooling Commits

**Context:** Audited the latest 5 commits (`8664452`..`ffe96b2`) against the Scripture. Commits span FR-076 (inquisitor script), FR-073 (unit test perf), diary rotation, and a diary-rotate bug fix.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits (`feat`, `perf`, `chore`, `fix` with scope and FR tag). Commandment 10 format upheld.
- ✓ COMPLIANT — All `# noqa` suppressions (`ANN001`, `ARG002`, `S603`) are documented in `docs/confessions.md` with CONF-XXX IDs. No unconfessed sins.
- ✗ VIOLATION — FR-076 introduced two `feat` commits (inquisitor script + post-commit hook) with **no CHANGELOG entry**. Commandment 10: "let the CHANGELOG.md bear witness." A `feat` is user-facing by convention; it must be logged.
- ✗ VIOLATION — `fix(diary): rotate before importing scheduled entries` (`ffe96b2`) fixed a bug in `diary_rotate.py` with **no failing test**. No test file for `diary_rotate.py` exists. Commandment 7: "No bug shall be fixed unless first condemned by a failing test."
- ⚠ DRIFT — FR-073 (`perf: reduce unit test time`) and FR-076 have no diary distillation entries. The 2026-02-23 diary entries cover unrelated work (Judge's Trap, doc drift, world digest). Sermon: Distill requires reflection after completing a task list.

**Heuristic:** *Dev-tooling commits (`scripts/`, `.chaplain/`, `.pre-commit-config.yaml`) receive less scrutiny than framework code, creating a blind spot. The Scripture makes no exception for "internal" changes — a `feat` is a `feat`, a `fix` demands a test. Apply the same rigor to the forge as to the sword.*

**Seed:** Should `pre-commit` enforce that every `feat`/`fix` commit touches `CHANGELOG.md`? A simple hook checking `git diff --cached --name-only | grep CHANGELOG.md` when the commit message starts with `feat` or `fix` would make this structurally impossible to forget.

---

## 2026-02-23: Reflection — The Shape of YAMLGraph at v0.4.54

**Context:** Stepped back from feature work to survey the whole organism. What has this project become? What are its proportions? What pressures are acting on it?

**The Numbers:**

| Layer | Lines | Ratio to Core |
|-------|------:|:---:|
| Core framework (`yamlgraph/`) | 11,935 | 1.0× |
| Tests | 36,230 | 3.0× |
| Examples | 25,103 | 2.1× |
| Projects | 29,144 | 2.4× |
| YAML (prompts + graphs) | 38,575 | 3.2× |
| Documentation (markdown) | 96,828 | 8.1× |
| Scripts | 2,058 | 0.2× |

652 commits. 91 releases. 28 capabilities. 83 requirements. 1,781 passing tests (1,959 req-tagged). 65 source files. 144 test files. 56 example graphs. 7 diary archives. 190 commits in the last 7 days alone.

**Observation 1: The docs outweigh the code 8:1.** The framework is ~12K lines. The documentation — ARCHITECTURE.md, CHANGELOG, diary, feature requests, reference docs, README — is ~97K lines. This is unusual. Most projects are code-heavy and doc-light. Here the doctrine, the diary, the feature requests, the changelog — they are the primary artifact. The code is the *residue* of a documented decision process. This is either a profound insight about software engineering or an unsustainable overhead. Possibly both.

**Observation 2: The test ratio is healthy but the *kind* of testing matters.** 3:1 test-to-code ratio. All 83 requirements covered. Zero ruff violations. But 1,781 tests running in 19.5 seconds means most are fast unit tests with mocked LLMs. The integration tests (27 files) require API keys and likely aren't running in CI. The coverage *number* is high; the coverage *confidence* depends on how well the mocks reflect real provider behavior. The One Law says "normalize at the boundary where external data enters" — are the mocks faithful to those boundaries?

**Observation 3: The project is growing satellite mass.** `projects/` (29K lines) and `examples/` (25K lines) together outweigh the core 4.5:1. The outcaller project has its own requirement numbering (`OC-XXX`). The NPC example has its own architecture doc. These are no longer examples — they're applications built on YAMLGraph. The gravitational question: does the framework serve the applications, or do the applications drive the framework? Recent commits show OC-tagged work (outcaller) being moved between repos, suggesting the boundary is still negotiated.

**Observation 4: The Chaplain is becoming infrastructure.** `watch.sh` polls for inbox items and generates feature requests. `inquisitor.sh` audits commits against doctrine. Post-commit hooks trigger audits. This is a closed feedback loop: commit → audit → diary → insight → doctrine → commit. The Scripture is not just documentation — it's executable process. But the Chaplain tooling has no tests (FR-076 introduced `inquisitor.sh` with no test file). The forge is unforged.

**Observation 5: Velocity is extraordinary — 190 commits in 7 days — but the commit type distribution tells a story.** 166 `feat`, 152 `docs`, 95 `fix`, 57 `refactor`, 70 `chore`. The feat:fix ratio of 1.7:1 suggests features are landing faster than they break — or that fix commits are catching bugs within the same day (many fix commits reference the same FR as the feature). The 57 refactor commits are a healthy sign: the codebase is being reshaped, not just accreted.

**Heuristic:** *When documentation outweighs code 8:1, the project's primary output is decisions, not software. The code is a side effect of the decision process. This means the highest-leverage improvement isn't faster code — it's faster, better decisions. The Chaplain loop (watch → plan → judge → enforce → distill) is an attempt to automate decision quality. Guard it.*

**Seed:** At what ratio does documentation become a liability instead of an asset? The diary alone is ~3,000 lines across 7 days. If a new contributor arrived tomorrow, would they read the diary — or would they skip straight to the code? Is the diary for the builder or for the building? And if it's for the builder: what happens when the builder changes?

---

## 2026-02-23: The Judge's Trap — Premature Requirement Allocation

**Context:** FR-075 audit revealed REQ-YG-078–082 (telco demo) were reserved in ARCHITECTURE.md capability table, but FR-075 originally proposed *releasing* them because outcaller uses `OC-XXX` numbering.

**Trap: Proposing Deletion Without Checking Dependencies.** The initial FR-075 draft said "release REQ-YG-078–082, remove CAP-27." But 34 tests are tagged with those requirement IDs:
```bash
grep -r "REQ-YG-07[89]\|REQ-YG-08[012]" tests/ --include="*.py" | wc -l
# 34 matches
```

If CAP-27 were removed from `req_coverage.py` while tests still reference those IDs, `--strict` would fail on "tagged tests reference unknown requirements."

**The Judge Protocol worked:** First instinct was to approve the "clean up" proposal. But the Judge must verify claims before granting authority. Running grep before signing off caught the issue. The FR was returned for amendment.

**Amended scope:** Reduced from "sync table + release reservation + add note" to just "sync table." The test coverage is real and valuable. The outcaller *application* uses `OC-XXX`, but the *framework integration tests* use `REQ-YG-XXX`. Both numbering schemes coexist correctly.

**Heuristic:** *Before approving deletion of any identifier (requirement ID, state key, function), grep for references first. The absence in one file doesn't mean absence everywhere.*

**Graduated pattern:** This extends "normalize at the boundary" — the deletion proposal was a *spec* normalized from what existed in the *code*. But the spec was wrong because it didn't consult the full truth (tests).

**Seed:** Should the Judge have a checklist? "Before approving deletion: grep codebase. Before approving rename: verify no external references. Before approving new ID: verify no collision." Formalize the verification steps that caught this issue.

---

## 2026-02-23: Documentation Drift as Entropy Signal

**Context:** ARCHITECTURE.md capability summary table was 5+ requirements behind `req_coverage.py`. Rows 3, 14, 17 were incomplete; row 28 didn't exist.

**Observation:** The *tests* were tagged correctly. The *script* (`req_coverage.py`) was correct. Only the *human-readable summary table* drifted. This pattern suggests: automated checks pass while documentation becomes stale.

**The entropy measure:** How far behind is the summary table?
- REQ-YG-050 (model override): missing from row 3
- REQ-YG-065 (native streaming): missing from row 14
- REQ-YG-059-062, 064 (safety guards): missing from row 17
- REQ-YG-083 (thinking budget): missing row 28

All these were added post-capability-table creation. The table was a snapshot, not a living document.

**Fix:** FR-075 — four table cell edits + one new row. 0.25 days. But the *detection* required an audit triggered by "disturbance in test tags."

**Heuristic:** *When tests pass but documentation feels stale, trust the tests. The stale doc is the trailing indicator of entropy, not its cause.*

**Seed:** Should there be a `docs/req_coverage.py --verify-architecture` mode that diffs the capability table against CAPABILITIES dict and reports mismatches? Automated detection of doc-code drift.

---

## 2026-02-23: World Digest — Observability & Agent Orchestration


**LangGraph ecosystem momentum:** Five LangGraph releases shipped this week (SDK 0.3.6–0.3.8, core 1.0.9, prebuilt 1.0.8), signaling active stabilization of the foundation YAMLGraph depends on. The SDK releases suggest refinement of deployment and runtime concerns.

**Agent observability as evaluation:** LangChain's recent focus on agent observability (multiple articles on tracing, behavior analysis, and evaluation frameworks) frames observability not as debugging overhead but as a first-class evaluation tool. This aligns with YAMLGraph's need to surface decision points and verify agent behavior—especially relevant to the seed on 'name the verification question' as a workflow gate.

**Memory and context patterns:** Articles on Agent Builder's memory system and context management for deep agents highlight that agent reliability depends on structured memory and context handling. YAMLGraph's YAML-first approach could formalize these patterns as declarative graph nodes, reducing silent fallbacks and invisible decisions.

**Tool registry and sandbox patterns:** New Agent Builder features (tool registry, file uploads) and the two-pattern analysis of agent-sandbox connections suggest the ecosystem is converging on explicit tool binding and execution isolation. This reinforces YAMLGraph's value: making these connections declarative rather than implicit in Python code.

**Evaluation at scale:** The monday.com + LangSmith case study demonstrates that evaluation strategy must be baked in from day one, not retrofitted. YAMLGraph's architecture should assume every node is observable and every edge is auditable—supporting the 'no-silent-fallback' lint rule seed.

**Connection to open seeds:** The observability focus directly supports the 'name the verification question' gate (agents need to state what they're verifying before acting). The memory and context articles suggest YAMLGraph should formalize 'invisible decisions' in memory handling (hardcoded defaults, deferred migrations) as a confession-style registry.

**Seed:** As agent observability becomes standard infrastructure, should YAMLGraph embed a mandatory 'trace annotation' layer — requiring every node to declare what observable state it expects and what it produces — making silent failures structurally impossible to hide?

---

## 2026-02-23: Git Report

## Repository Analysis: Last 3 Days Development Summary

Based on the git history, here's a **feature-level summary** of recent development:

### 🎯 Major Features Implemented

**1. FR-074: Outcall Probe-Recap (OC-005+) - APPROVED**
   - Voice callback system for probe recap operations
   - Redis session-lookup pattern for state management
   - ElevenLabs TTS integration path (Phase 1)
   - TTS completion tracking via Twilio marks
   - Tests for probe recap and outcaller TTS modules

**2. FR-071: Graph-Level Thinking Budget (REQ-YG-083)**
   - Extended thinking/reasoning support at graph node level
   - Schema validation (0 or ≥1024 tokens)
   - Automatic temperature=1 override for LLM calls
   - Linter warnings with 4 distinct codes (W071-1 through W071-4)
   - Full demo with configurable reasoning depth
   - 18 unit tests + 1 integration test
   - Complete requirement traceability

**3. FR-072: ElevenLabs STT Integration**
   - Streaming voice pipeline for outcaller
   - SDK-based Speech-To-Text integration tests
   - Raw bytes bug fixes and event name corrections
   - Twilio audio integration for voice modality

**4. FR-068: Chaplain Watch Loop**
   - Automated feature request workflow system
   - Plan → Judge → Amend cycle (max 3 iterations)
   - Inbox polling for topic files
   - Approved FRs auto-promote to feature-requests/
   - Dry-run mode for safe testing

### 🔧 Supporting Work

- **Code Refactoring**: FR-066/FR-067 CC distribution and edge compiler extraction
- **Template Improvements**: FR-064 Jinja2 AST migration for better variable extraction
- **Documentation**: Multiple diary entries capturing cognitive traps and architectural insights
- **Testing**: Comprehensive test coverage across telco, STT, thinking budget, and outcaller modules

### 📊 Development Statistics

- **Total commits analyzed**: 50+ recent commits
- **Files modified**: 60+ files
- **Key modules touched**: yamlgraph core, telco nodes, outcaller system, linter enhancements
- **Test cover
