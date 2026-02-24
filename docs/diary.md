# Development Diary

Metacognitive reflections on development process.

Previous: [diary-2026-02-23.md](diary-2026-02-23.md) — 23 entries from 2026-02-23.

---

## 2026-02-24: FR-082 Sampling Backend — Teardown

**Context:** After implementing MCP sampling backend for copilot nodes (FR-082), found that multi-node chains fail due to state serialization issues. `CopilotResult` objects lose attributes when passed between LangGraph nodes. The `backend: cli` already works reliably for the same use cases.

**Trap:** Sunk cost bias. Having invested 2 days implementing sampling (context threading, async bridge, MCP session propagation), the temptation was to debug further. But: CLI works, sampling doesn't, and the value delta is marginal.

**Heuristic:** "Does this add value beyond existing solutions?" Should be asked *before* implementing.

**Gotcha:** MCP sampling creates isolated LLM sessions — debugging requires understanding the invisible boundary between host LLM and sampled responses. Log files written by the MCP server don't appear where you expect because it's a separate process.

**Decision:** DROPPED. Removed:
- `yamlgraph/mcp_context.py` (ContextVar threading)
- `examples/copilot_mcp/` (sampling demo)
- `_execute_sampling()` function
- REQ-YG-088 from requirements

**Seed:** For future MCP integrations, consider: "What happens when this runs in a subprocess?"

---

## 2026-02-24: Inquisitor Audit — The Fifth Bell Tolls

**Context:** Audit of latest 5 commits (`4152cb1`..`707e03d`). The window captures the full FR-082 sampling backend delivery cycle: feature implementation, diary reflection, example addition, bug fix, and a second diary entry with bundled debug logging. Two previous audits flagged the same CHANGELOG violation — this is the 5th consecutive detection.

**Findings:**

- ✗ VIOLATION — CHANGELOG.md line 14 **still** states `backend: sampling — deferred (raises NotImplementedError)`. This is the **5th consecutive audit** flagging this contradiction. The codebase now has: implementation (`4152cb1`), example (`ecb06bd`), and a bug fix (`73644fd`) — three commits of evidence that sampling works. The previous audit proposed escalation at 3 audits. We are now at 5 with no corrective action. The CHANGELOG has become an unreliable record.
- ✗ VIOLATION — Commit `73644fd` (`fix(copilot): support nested variable paths`) still has **no CHANGELOG entry**. Flagged in the previous audit. No `### Fixed` section exists in version `0.4.56`. Two consecutive audits, zero action.
- ⚠ DRIFT — Commit `707e03d` scoped as `docs(diary):` bundles a **production code change** (11 lines of debug logging and error handling added to `copilot_node.py`) with a diary reflection. The `docs:` scope actively misrepresents the commit contents. Previous audit flagged `73644fd` for similar bundling — but that commit at least used `fix:` scope, which implies code. Here the scope conceals the change.
- ✓ COMPLIANT — ADR-001 upheld. All test classes carry `@pytest.mark.req` tags (REQ-YG-087, REQ-YG-088, REQ-YG-089). Both `# noqa` suppressions (ANN001, ARG002) documented in `docs/confessions.md`.
- ✓ COMPLIANT — All 5 commits follow Conventional Commits format syntactically: `docs(diary):`, `fix(copilot):`, `docs(copilot-mcp):`, `docs(diary):`, `feat(mcp):`.

**Heuristic:** Detection without correction is surveillance, not governance. Five audits have identified the same CHANGELOG falsehood. The diary records findings faithfully, but diary entries have no assignee, no notification, no deadline. The audit process has proven it can detect — it has also proven it cannot compel. A violation that outlives 3 audits should exit the diary and enter a system with teeth: a GitHub issue, a blocking CI check, or a pre-commit hook that cross-references `feat:` commits against CHANGELOG diffs.

**Seed:** Could a pre-commit hook verify that `feat:` and `fix:` commits include a CHANGELOG modification? The hook already enforces Conventional Commits format — extending it to require CHANGELOG co-modification for feature/fix commits would close the audit-to-correction gap mechanically, removing reliance on humans reading diary entries.

---

## 2026-02-24: Sampling Backend — Testability vs Architectural Elegance

**Context:** Implemented FR-082 (MCP sampling backend for copilot nodes). During integration testing, hit a bug where `{state.analysis.output}` appeared as literal placeholder in downstream nodes. Spent significant time debugging with file-based logging, only to realize: the MCP server runs in a separate process, so `/tmp/debug.log` writes don't appear in the expected filesystem.

**Trap: Architecture Opacity**

The sampling backend's architecture is elegant but opaque for debugging:

```
You (human) → Claude (me) → yamlgraph_run_graph tool
                                    ↓
                           YAMLGraph MCP Server (separate process)
                                    ↓
                           copilot node: session.create_message()
                                    ↓
                           Sampling request → NEW LLM session (no history)
                                    ↓
                           Response returns to MCP server
```

Each `session.create_message()` spawns a **fresh LLM invocation** — no conversation history, no context from parent chat. The LLM generating critique/synthesis genuinely doesn't see the analysis output. If variable resolution fails, the LLM faithfully echoes the placeholder.

**Insight: Testability Layers**

The copilot node has two backends:
- `backend: cli` — calls `copilot` CLI binary. Requires binary but works via `yamlgraph graph run`
- `backend: sampling` — calls MCP sampling. Requires MCP server context; **cannot** run via CLI

For testing **graph logic** (variable resolution, state passing, prompt rendering):
1. Use `type: llm` nodes — full control, works with CLI, mock-friendly
2. Use `backend: cli` — removes MCP layer, debuggable via terminal
3. Use `backend: sampling` **only after** graph logic is verified — it's the hardest to debug

The sampling backend is powerful (zero API cost, host LLM reuse) but should be the **last layer to test**, not the first.

**Heuristic:** When debugging a pipeline, minimize layers. Each process boundary, RPC hop, or async bridge is a place where assumptions can break silently. `yamlgraph graph run` with `backend: cli` exercises the same copilot node code without MCP server, thread pool, or sampling protocol — one less variable.

**Seed:** Should there be a `backend: mock` option that returns static/configurable responses? This would allow CLI testing of multi-stage sampling graphs without any LLM calls — pure graph logic verification. The mockable surface is `_execute_sampling()` which is already isolated.

---

## 2026-02-24: Inquisitor Audit — The Fix Without a Ledger

**Context:** Audit of latest 5 commits (`2ad5006`..`73644fd`). One `fix:` commit (`73644fd`, nested variable paths in copilot node — 3 files, 110 insertions). One `docs:` commit (`ecb06bd`, sampling backend example — 5 files, 211 insertions). One `docs(diary):` reflection (`7d0b368`). One `feat:` commit (`4152cb1`, FR-082 sampling backend — 6 files, 611 lines). One `docs:` commit (`2ad5006`, Scripture cleanup + pre-commit fix). The window captures a bug fix landing atop the FR-082 delivery cycle.

**Findings:**

- ✗ VIOLATION — CHANGELOG.md line 14 **still** states `backend: sampling — deferred (raises NotImplementedError, requires MCP loopback)`. This is the **4th consecutive audit** flagging this contradiction. Commit `4152cb1` replaced the stub. Commit `ecb06bd` added a working example. Commit `73644fd` fixed a bug in it. The codebase has moved three commits past implementation while the CHANGELOG preserves the fossil. At this point the contradiction is not drift — it is an established falsehood in the project record.
- ✗ VIOLATION — Commit `73644fd` (`fix(copilot): support nested variable paths`) has **no CHANGELOG entry**. Version `0.4.56` has an `### Added` section but no `### Fixed` section. A `fix:` commit that changes runtime behavior and adds a test requires a CHANGELOG entry per Commandment 10. The fix is invisible to anyone reading the release notes.
- ✓ COMPLIANT — All 5 commits follow Conventional Commits with correct scoping: `fix(copilot):`, `docs(copilot-mcp):`, `docs(diary):`, `feat(mcp):`, `docs:`.
- ✓ COMPLIANT — ADR-001 upheld. All tests carry `@pytest.mark.req` tags (class-level `REQ-YG-087` covers CLI tests; `REQ-YG-088` on all 5 sampling tests). Both `# noqa` suppressions (`ANN001`, `ARG002`) documented in `docs/confessions.md`.
- ⚠ DRIFT — Commit `73644fd` bundles a bug fix (copilot_node.py + test) with an unrelated Inquisitor audit diary entry (54 lines to diary.md). These are independent concerns — the fix is code, the audit is reflection. Bundling them makes `git bisect` and `git log --follow` less useful on `docs/diary.md`.

**Heuristic:** A violation flagged 4 times without correction is no longer a detection problem — it is an action problem. The audit-to-correction pipeline has a gap: the Inquisitor writes findings to `docs/diary.md`, but no process ensures a human reads the diary and acts before the next commit. A violation that ages 4 audits without a corrective commit has effectively been accepted by silence. Either fix it, or formally accept it — ambiguity is the worst outcome.

**Seed:** Should there be a "violation age" threshold — say 3 audits — after which the Inquisitor escalates from diary entry to a filed GitHub issue? Issues have assignees, notifications, and visibility that diary entries lack. The diary is for reflection; issues are for action. Persistent violations need the latter.

---

## 2026-02-24: Inquisitor Audit — The Fossilized CHANGELOG Persists

**Context:** Audit of latest 5 commits (`ea737f3`..`ecb06bd`). One `feat:` commit (`4152cb1`, FR-082 sampling backend). One `docs(copilot-mcp):` commit (`ecb06bd`, sampling backend example with 5 new files). One `docs(diary):` reflection (`7d0b368`). One `docs:` Scripture cleanup (`2ad5006`). One `chore:` README update (`ea737f3`). The audit window captures the post-FR-082 delivery including an example that exercises the now-working sampling backend.

**Findings:**

- ✗ VIOLATION — CHANGELOG.md line 14 still states `backend: sampling — deferred (raises NotImplementedError, requires MCP loopback)`. This is the **3rd consecutive audit** flagging this. Commit `4152cb1` replaced the stub with a working `session.create_message()` implementation. Commit `ecb06bd` now adds a full `examples/copilot_mcp/` example exercising sampling — you cannot demonstrate a feature that the CHANGELOG claims raises `NotImplementedError`. The contradiction is now compounded: the codebase has both implementation *and* example, while the CHANGELOG describes a stub.
- ✓ COMPLIANT — All 5 commits follow Conventional Commits with correct scoping: `docs(copilot-mcp):`, `docs(diary):`, `feat(mcp):`, `docs:`, `chore:`.
- ✓ COMPLIANT — ADR-001 fully upheld. REQ-YG-088 defined in ARCHITECTURE.md. All sampling tests carry `@pytest.mark.req("REQ-YG-088")` (5 tests). All `# noqa` suppressions (ANN001, ARG002) documented in `docs/confessions.md`.
- ✓ COMPLIANT — Diary reflection written for FR-082 (ContextVar threading pattern) with Trap/Heuristic/Gotcha/Seed.
- ⚠ DRIFT — Commit `ecb06bd` adds `examples/copilot_mcp/` (5 files, 211 insertions) as a standalone `docs:` commit after the `feat:` commit. The example demonstrates `backend: sampling` but there is no CHANGELOG entry noting the example's existence. Examples are typically listed in CHANGELOG alongside the feature (see FR-081's entry: `examples/copilot/: Plan → Judge → Summarize demo`). This asymmetry suggests the example was an afterthought rather than part of the delivery cycle.

**Heuristic:** A violation that survives 3 audits without correction reveals a process gap: audits record but do not compel. The Inquisitor writes to `docs/diary.md` only — it cannot amend `CHANGELOG.md`. The person who reads the audit must also be the person who acts on it. If nobody reads the diary between audits, the audit loop is open — it detects without correcting, which is monitoring without alerting.

**Seed:** Should the Inquisitor audit produce a machine-readable artifact (e.g., a `docs/audit-violations.json`) that a pre-commit hook or CI step can check? This would close the loop: audit detects → artifact records → hook blocks commit until violation is resolved. The diary remains for human reflection; the artifact becomes the enforcement mechanism.

---

## 2026-02-24: Inquisitor Audit — CHANGELOG Contradicts Codebase

**Context:** Audit of latest 5 commits (`0e3754f`..`4152cb1`). One `feat:` commit (`4152cb1`, FR-082 sampling backend — replaces `NotImplementedError` stub with working `session.create_message()` call, 5 new tests, new `mcp_context.py` module). One `docs:` commit (`2ad5006`, Scripture cleanup + pre-commit `.venv/bin/python` fix). One `chore:` README update (`ea737f3`). One version bump (`5c1dc27`, v0.4.56 for FR-081). One `docs:` FR-081 examples (`0e3754f`).

**Findings:**

- ✗ VIOLATION — CHANGELOG.md line 14 states `backend: sampling` — "deferred (raises `NotImplementedError`, requires MCP loopback)" but commit `4152cb1` replaced that stub with a working implementation. The CHANGELOG now **actively contradicts** the codebase. This is worse than a missing entry — it is misinformation that will mislead the next reader. The `changelog-required` hook (still broken, `$0/$1` bug, 6th audit cycle) cannot catch this because the violation is semantic, not structural.
- ✓ COMPLIANT — All 5 commits follow Conventional Commits: `feat(mcp):`, `docs:`, `chore:`, `chore:`, `docs(copilot-node):` — correctly scoped with FR tags where applicable.
- ✓ COMPLIANT — ADR-001 upheld. REQ-YG-088 existed in ARCHITECTURE.md from FR-081. All 5 new tests carry `@pytest.mark.req("REQ-YG-088")`. Feature request `FR-082-sampling-backend.md` follows full Sermon cycle (Plan → Judge → Enforce → Distill).
- ✓ COMPLIANT — FR-082 has a diary reflection ("Threading State Without Polluting State") with Trap/Heuristic/Seed. No new `# noqa` suppressions.
- ⚠ DRIFT — Commit `2ad5006` touched `.pre-commit-config.yaml` to fix hook paths (bare `python` → `.venv/bin/python`) but did not fix the `$0/$1` bug in the `changelog-required` hook in the same file. A contributor edited the guard file, saw adjacent guards, and still left the known bug. Proximity did not trigger correction.

**Heuristic:** A CHANGELOG that contradicts the code is an active hazard, not just missing documentation. When a `feat:` commit transforms a `NotImplementedError` into working code, the prior CHANGELOG entry describing the stub becomes a lie. Audits that check "does a CHANGELOG entry exist?" miss this class of error — the check must also ask "does the existing entry still describe reality?"

**Seed:** Should the bump/release script include a `grep -q NotImplementedError` sanity check against CHANGELOG descriptions that mention "deferred" or "not implemented"? Stale CHANGELOG entries that describe removed limitations are a new category of documentation debt — not missing docs, but **fossilized docs** that preserve a state that no longer exists.

---

## 2026-02-24: Inquisitor Audit — The Chronic Hook and the Missing Entry

**Context:** Audit of latest 5 commits (`5c1dc27`..`7d0b368`). One `feat:` commit (`4152cb1`, FR-082 sampling backend — 5 new tests, `mcp_context.py` module, 611 lines changed). One diary reflection (`7d0b368`). One docs cleanup (`2ad5006`). One README update (`ea737f3`). One version bump/tag (`5c1dc27`, v0.4.56). The audit window captures the FR-082 delivery cycle atop the freshly-tagged v0.4.56.

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits: `docs(diary):`, `feat(mcp):`, `docs:`, `chore:`, `chore:` — all correctly scoped with FR tags where applicable.
- ✓ COMPLIANT — ADR-001 fully upheld. REQ-YG-088 (sampling backend) was already defined in ARCHITECTURE.md before implementation. All 5 new tests carry `@pytest.mark.req("REQ-YG-088")`. Diary entry written with Trap/Heuristic/Gotcha/Seed.
- ✓ COMPLIANT — All `# noqa` suppressions (ANN001, ARG002) documented in `docs/confessions.md` with CONF-XXX IDs. No new suppressions introduced.
- ✗ VIOLATION — `feat(mcp): FR-082` (`4152cb1`) has no CHANGELOG.md entry. This is a `feat:` commit introducing a new backend implementation — it requires a CHANGELOG entry per Commandment 10. The `changelog-required` hook still carries the `$0/$1` bash bug (5th consecutive audit flagging this). The hook remains structurally incapable of enforcement.
- ⚠ DRIFT — The `docs:` commit (`2ad5006`) bundles three unrelated changes: Scripture cleanup, pre-commit python path fix, and test mock fix for Python 3.13. Each is a distinct concern that warrants its own commit for traceability. Atomic commits aid bisection and review.

**Heuristic:** A violation that survives 5 audits without correction is no longer a violation — it is policy. Either fix the hook and add the CHANGELOG entry, or formally document that CHANGELOG enforcement is manual-only. The current state is the worst of both worlds: a guard that exists but doesn't guard, audits that flag but don't fix. Ambiguity in enforcement is itself a defect.

**Seed:** The `docs:` commit bundling 3 concerns suggests commit granularity guidelines are absent from the Scripture. Should there be a Commandment on atomic commits — "one logical change per commit" — or would that add friction without proportional value?

---

## 2026-02-24: FR-082 — Threading State Without Polluting State

**Context:** Implemented MCP sampling backend for copilot node. The challenge: thread an MCP session object from async tool handler → thread pool executor → sync graph node, without adding infrastructure to graph state.

**Trap:** The initial instinct was to pass `session` as a parameter through the call stack. But this would pollute the graph invocation signature — every function from `_invoke_graph` to individual node factories would need to accept and forward an MCP session parameter they don't use. Infrastructure leaking into business logic.

**Solution:** `contextvars.ContextVar` provides implicit threading without signature pollution:
1. Set context in async handler: `set_mcp_context(session, loop)`
2. Copy context: `ctx = contextvars.copy_context()`
3. Run in executor: `ctx.run(_invoke_graph, ...)`
4. Read from anywhere: `session, loop = get_mcp_context()`

The sync→async boundary required `asyncio.run_coroutine_threadsafe()` to call `session.create_message()` from the thread pool.

**Heuristic:** ContextVars are the tool for threading infrastructure concerns — sessions, tracing contexts, request IDs — without polluting function signatures. If you're about to add a parameter that 90% of the call stack doesn't use, reach for ContextVar instead.

**Gotcha:** Importing `asyncio` inside a function body breaks `patch()` targeting. The test mocked `yamlgraph.node_factory.copilot_node.asyncio.run_coroutine_threadsafe` but the import was happening inside the function at runtime, so the mock never applied. Moving the import to module level fixed it instantly. When mocking, the target must exist at the module level *before* the function runs.

**Seed:** The `LookupError` guard (`try: server.request_context.session except LookupError: pass`) means copilot nodes with `backend: sampling` silently fall through to... nothing, in unit test contexts. Should there be a `YAMLGRAPH_REQUIRE_MCP_CONTEXT=true` env var that makes this failure loud in CI, so graphs that require sampling are tested properly?

---

## 2026-02-24: Inquisitor Audit — Discipline Compensates for Broken Guards

**Context:** Audit of latest 5 commits (`30cccb9`..`5c1dc27`). Three commits complete FR-081 (copilot node): `e5ae01b` feat, `0e3754f` docs/examples, `5c1dc27` bump+CHANGELOG. One diary reflection (`2d2cf4a`), one prior audit entry (`30cccb9`). The audit window captures the full FR-081 delivery cycle including a version release (v0.4.56).

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits: `chore:`, `docs(copilot-node):`, `docs(diary):`, `feat(copilot-node):`, `docs(diary):` — all correctly scoped with FR-081 tags where applicable.
- ✓ COMPLIANT — CHANGELOG.md has a complete FR-081 entry under `[0.4.56] - 2026-02-24` covering CAP-30, REQ-YG-087–089, all node features, 12 tests. Added in bump commit (`5c1dc27`). Human discipline compensated for the broken hook.
- ✓ COMPLIANT — ADR-001 fully upheld. ARCHITECTURE.md has CAP-30 and REQ-YG-087–089. All 12 tests carry `@pytest.mark.req` tags (class-level on 3 classes, method-level on 1). Coverage: REQ-YG-087 (10 tests across 2 classes), REQ-YG-089 (1 test), REQ-YG-088 (1 test).
- ✓ COMPLIANT — Both `# noqa` suppressions in `yamlgraph/` (ANN001, ARG002) documented in `docs/confessions.md` with CONF-XXX IDs.
- ⚠ DRIFT — The `changelog-required` hook's `$0/$1` bug persists (4th audit). The hook remains structurally incapable of enforcement. However, the CHANGELOG was correctly added anyway — manual discipline succeeded where automation failed. The Inquisitor is constrained from fixing it (diary-only writes). Escalation: this requires a `fix:` commit outside audit scope.

**Heuristic:** When automation is broken but outcomes are correct, the team has internalized the discipline the guard was meant to enforce. This is better than a working guard with no understanding — but it doesn't scale. The broken hook is now technical debt that will bite the next contributor who hasn't read 4 audit entries. Fix the guard so the discipline can be forgotten safely.

**Seed:** The last 4 audits have all flagged the same `$0/$1` bug. The Inquisitor pattern creates a read-only observer that cannot self-correct. Should there be a companion "Corrector" role — an audit follow-up step with write access scoped to infrastructure fixes (hooks, CI config) but not application code?

---

## 2026-02-24: Inquisitor Audit — Diagnosis Without Correction

**Context:** Audit of the latest 5 commits (`22774ff`..`0e3754f`). Three commits complete FR-081 (copilot node): `e5ae01b` feat, `2d2cf4a` diary reflection, `0e3754f` examples/docs. Two commits are prior Inquisitor Audit entries (`30cccb9`, `22774ff`). This audit window is dominated by a single feature (FR-081) that has been fully delivered across 3 commits.

**Findings:**

- ✗ VIOLATION — `feat(copilot-node): FR-081` (`e5ae01b`) still has no CHANGELOG.md entry. The previous audit *diagnosed* the root cause (`changelog-required` hook's `$0/$1` bash bug) but the hook was never fixed. The entry `bash -c 'msg=$(cat "$1"); ...'` still uses `$1` instead of `$0`. Diagnosis without correction violates the Rite of Correction: "Amend. Correct the root cause second." The violation is now infrastructure debt with a known 30-second fix that has survived 3 audits since diagnosis.
- ✓ COMPLIANT — FR-081 followed the full Sermon cycle across all 3 commits: Plan (FR-081 feature request), Enforce (TDD, 12 tests with `@pytest.mark.req` tags for REQ-YG-087–089), Distill (diary entry at line 45 with Trap/Heuristic/Seed), Submit (Conventional Commits, FR-scoped). ADR-001 fully upheld: CAP-30 in ARCHITECTURE.md.
- ✓ COMPLIANT — All 5 commits follow Conventional Commits. `feat(copilot-node):`, `docs(diary):`, `docs(copilot-node):` — correctly scoped with FR tags.
- ✓ COMPLIANT — All `# noqa` suppressions (2 in yamlgraph/) are documented with CONF-XXX IDs in `docs/confessions.md`.
- ⚠ DRIFT — The `docs(copilot-node)` commit (`0e3754f`, +375 lines of examples and reference docs) is substantial enough to warrant its own CHANGELOG bullet, but as a `docs:` commit the hook wouldn't enforce it even if fixed. The copilot node feature is now fully delivered but invisible in CHANGELOG.

**Heuristic:** Diagnosing a root cause without scheduling its correction is worse than not diagnosing it — it creates the illusion of progress. The previous audit identified the `$0/$1` bug, planted a Seed about testing hooks, then moved on. Three audits later the bug remains. The Rite demands: Inspect → Amend → Escalate. "Amend" is not optional. A diagnosis that doesn't flow to a fix within one audit cycle is a finding that was never truly made.

**Seed:** Should the Inquisitor be empowered to make single-line fixes (like `$1` → `$0`) directly during audit, rather than only recording findings? The doctrine says "do not modify files other than diary.md" — but this constraint, meant to keep audits safe, has become the reason a known 30-second fix has survived 3 audit cycles. When is the cost of restraint higher than the cost of action?

---

## 2026-02-24: Inquisitor Audit — Root Cause Found: changelog-required Hook Has a Bash $0/$1 Bug

**Context:** Audit of latest 5 commits (`fb09db5`..`2d2cf4a`). One `feat:` commit (`e5ae01b`, FR-081 copilot node — new CAP-30 capability, 12 tests, 276 lines), one `docs(diary):` reflection (`2d2cf4a`), two `docs(diary):` prior audit entries (`30cccb9`, `22774ff`), one `chore:` (`fb09db5`, FR-080 bundling FR-081 feature request). An automated inquisitor entry already exists below for the same window — this audit adds root-cause diagnosis of the chronic CHANGELOG enforcement gap.

**Findings:**

- ✗ VIOLATION (ROOT CAUSE IDENTIFIED) — The `changelog-required` hook in `.pre-commit-config.yaml` has **never worked**. Its entry uses `bash -c 'msg=$(cat "$1"); ...'`, but `bash -c` assigns the first positional argument to `$0`, not `$1`. Pre-commit passes the commit-msg filename as the first argument → it lands in `$0` → `cat "$1"` reads empty string → the `grep -qE "^(feat|fix)"` never matches → the hook always passes. Verified: `bash -c 'echo "$1"' /tmp/file` outputs nothing. Fix: change `$1` to `$0` in the entry, or add a `_` placeholder before `"$@"`. This single bug explains **every CHANGELOG violation across 7 audits**.
- ✓ COMPLIANT — FR-081 followed the full Sermon: Plan (FR-081 feature request), Red-Green (TDD, 12 tests tagged `@pytest.mark.req`), Distill (diary entry with Trap/Heuristic/Seed). ADR-001 upheld: CAP-30 and REQ-YG-087–089 in ARCHITECTURE.md, `req_coverage.py` passes (3/3 reqs, 12 tests), `noqa_coverage.py` clean (53 suppressions, 0 undocumented).
- ✓ COMPLIANT — Conventional Commits format on all 5 commits. `feat(copilot-node):`, `docs(diary):`, `chore:` — all correctly scoped.
- ✓ COMPLIANT — Prior chronic findings (`feat(testing): FR-080` CHANGELOG, leaked LLM preamble in Git Report) were formally accepted as permanent in the automated audit below. No re-flagging warranted.
- ⚠ DRIFT — `feat(copilot-node): FR-081` (`e5ae01b`) still has no CHANGELOG entry. However, this is now explained by the root-cause `$0/$1` bug — the hook was structurally incapable of catching it. Downgraded from ✗ to ⚠ because the failure is infrastructure, not discipline.

**Heuristic:** When the same violation persists across 7 audits, stop re-classifying the symptom and diagnose the guard. A 30-second `bash -c` positional argument test (`bash -c 'echo "$1"' arg`) would have revealed the root cause on audit #1. The Inquisitor's value is not in recording violations — it is in tracing them to their structural origin. Flag → Diagnose → Fix, not Flag → Flag → Flag → Accept.

**Seed:** Should every enforcement hook in `.pre-commit-config.yaml` have a corresponding integration test in `tests/` that runs `pre-commit run <hook-id>` against a synthetic commit, verifying it rejects what it claims to reject? A guard that has never fired is indistinguishable from no guard.

---

## 2026-02-24: Inquisitor Audit — CHANGELOG Enforcement Remains Broken

**Context:** Audit of the latest 5 commits (`5ff37df`..`e5ae01b`). One new `feat:` commit (`e5ae01b`, FR-081 copilot node, +695 lines), two `docs(diary):` commits (prior Inquisitor Audit findings), one `chore: FR-080` (bundling FR-081 feature request), one `feat(testing): FR-080` (infrastructure tests). The FR-081 commit is the only new commit not previously audited.

**Findings:**

- ✗ VIOLATION — `feat(copilot-node): FR-081` (`e5ae01b`) has no CHANGELOG.md entry. This is a `feat:` commit adding a new node type (CAP-30, 12 tests, 276-line implementation) — exactly the kind of change CHANGELOG exists to document. FR-077's `changelog-required` hook has now failed for **two** `feat:` commits (`5ff37df` and `e5ae01b`). The enforcement mechanism is confirmed broken, not a one-off.
- ✗ VIOLATION — `feat(testing): FR-080` (`5ff37df`) still has no CHANGELOG.md entry. **6th consecutive audit**. At this point, the Inquisitor formally accepts this as a permanent gap and will cease re-flagging it. The violation is recorded; correction is deferred to the project owner.
- ✗ VIOLATION — "Git Report" entry (line ~150) still contains leaked LLM preamble ("Perfect! Now I have enough context."). **6th consecutive audit**. Same disposition as above — formally accepted as permanent, ceased re-flagging.
- ✓ COMPLIANT — FR-081 followed the full Sermon cycle: Plan (FR-081 feature request), Enforce (TDD with 12 tests), Distill (diary entry at line 9 with Trap/Insight/Heuristic/Seed), Submit (Conventional Commit with FR tag). ADR-001 fully upheld: CAP-30 and REQ-YG-087–089 added to ARCHITECTURE.md, all tests carry `@pytest.mark.req` tags, no undocumented `noqa` suppressions.
- ✓ COMPLIANT — `chore: FR-080` scope misattribution (`fb09db5`) is now moot: FR-081 received its own properly scoped `feat:` commit (`e5ae01b`), restoring `git log --grep=FR-081` traceability.

**Heuristic:** When the same enforcement mechanism fails across multiple commits by multiple authors/sessions, the root cause is infrastructure, not discipline. Stop auditing the symptom (missing CHANGELOG entries) and audit the mechanism (is the pre-commit hook installed? does it trigger on the correct event? is `--no-verify` being used?). The Inquisitor's role shifts from "flag the violation" to "diagnose the guard."

**Seed:** Should the next session begin with `pre-commit run changelog-required --all-files` to verify the hook is functional before any `feat:` work begins? A 5-second smoke test would have prevented 6 audits of the same finding.

---

## 2026-02-24: FR-081 Copilot Node — Pattern Recognition in Error Handling

**Context:** Implemented FR-081 (Copilot Node Type) — new `copilot` node for delegating to GitHub Copilot CLI. TDD approach: 12 tests across 4 test classes, 276-line implementation.

**Trap Encountered:** Regex Pattern Mismatch — Test `test_graceful_file_not_found` expected `RuntimeError` with pattern `copilot.*not found|not installed`. Error message was "Copilot CLI not found..." where "Copilot" (uppercase) appeared AFTER "not found" in the string. Pattern `copilot.*not found` requires "copilot" to PRECEDE "not found". Quick fix: changed message to "copilot binary not found..." so the pattern matches. Similar issue in sampling test — needed `(?i)` for case-insensitive matching.

**Insight:** Test regex patterns are contracts. When the error message structure changes, regex patterns silently fail to match — pytest shows the original exception, not a clear "regex mismatch" error. The traceback shows the exception being raised, not the regex failing. This is a debugging trap: you spend time wondering why the exception isn't caught, when actually it IS caught but the regex doesn't match.

**Heuristic:** When `pytest.raises(..., match=...)` fails, check regex before debugging exception handling. Use `(?i)` for case-insensitive matching by default when error message case isn't semantically important.

**Seed:** Should YAMLGraph standardize error message structure to always put key terms (node type, error class) in a predictable position, making test patterns more robust? E.g., `"{NodeType} error: {description}"` convention.

---

---

## 2026-02-24: Inquisitor Audit — Chronic Violations and Enforcement Decay

**Context:** Audit of the latest 5 commits (`033fdd5`..`30cccb9`). Two `docs(diary):` commits (prior Inquisitor Audit findings), one `chore: FR-080` (bundling FR-081 feature request), one `feat(testing): FR-080` (53 infrastructure tests, 10 confessions), one `docs:` (ARCHITECTURE update for FR-078/OC-008). All human-authored. No new capabilities introduced.

**Findings:**

- ✗ VIOLATION — `feat(testing): FR-080` (`5ff37df`) has no CHANGELOG.md entry. This is the **5th consecutive audit** flagging this. FR-077's `changelog-required` hook has been inert for this commit across all audits. The enforcement mechanism is either broken, bypassed, or never installed. At 5 audits, this is no longer a finding — it is an accepted gap in the process. The Inquisitor's authority is eroded each time the same violation is recorded without consequence.
- ✗ VIOLATION — "Git Report" entry (line 100) still contains leaked LLM preamble ("Perfect! Now I have enough context.") and lacks canonical diary format. **5th consecutive audit**. This malformed entry has survived every audit since its creation. It is now the oldest unresolved finding in the diary. Either delete it, rewrite it, or accept it as-is and stop flagging it.
- ✗ VIOLATION — FR-080 has no dedicated diary reflection (Distill step). **4th consecutive audit** — escalated from ⚠ DRIFT per the 3-audit escalation threshold established in the 3rd audit. The cognitive process of building 53 infrastructure tests was never captured. The Sermon's Distill step was skipped.
- ⚠ DRIFT — `chore: FR-080` (`fb09db5`) bundles `feature-requests/FR-081-copilot-node.md` under FR-080 scope. **3rd audit** — approaching escalation threshold. `git log --grep=FR-081` will not find this commit.
- ✓ COMPLIANT — ADR-001 fully upheld: all FR-080 tests carry `@pytest.mark.req` tags (25 across 5 files), both framework `# noqa` suppressions (CONF-002 ANN001, CONF-003 ARG002) are confessed, Conventional Commits format followed on all 5 commits.

**Heuristic:** An Inquisitor that records the same violation 5 times without triggering corrective action has become a ritual, not a process. The audit cycle — surface → classify → record → forget — lacks a forcing function. Findings without owners decay into noise. The doctrine demands correction (Rite of Correction: "Amend. Write the failing test first."), but the Inquisitor has no mechanism to compel amendment. Either grant it teeth (blocking hooks, mandatory fix-forward) or accept that audit entries are advisory and adjust expectations accordingly.

**Seed:** Should the doctrine establish a "3-strike rule" — any finding flagged ✗ VIOLATION in 3 consecutive audits automatically generates a blocking TODO in the pre-commit hook, preventing `feat:`/`fix:` commits until the violation is resolved? This would close the gap between observation and enforcement.

---

## 2026-02-24: Inquisitor Audit — Stale Violations and Audit Fatigue

**Context:** Audit of the latest 5 commits (`4396700`..`22774ff`). Two `docs(diary):` commits (Inquisitor Audit findings, FR-079 reflection), one `chore: FR-080` (bundling FR-081 feature request), one `feat(testing): FR-080` (53 infrastructure tests), one `docs:` (ARCHITECTURE update for FR-078/OC-008). All human-authored. No new capabilities introduced; the `feat:` commit adds test coverage for existing infrastructure scripts.

**Findings:**

- ✗ VIOLATION — `feat(testing): FR-080` (`5ff37df`) still has no CHANGELOG.md entry. This is the **4th consecutive audit** flagging this. FR-077's `changelog-required` hook has demonstrably failed for this commit. The violation is now chronic — each audit re-documents it, yet the entry remains missing. The enforcement mechanism itself needs investigation.
- ✗ VIOLATION — "Git Report" entry (line 82) still contains leaked LLM preamble ("Perfect! Now I have enough context.") and lacks canonical diary format. **4th consecutive audit** flagging this. Per the escalation heuristic established in the 3rd audit ("persistent drift past 3 audits should escalate to ✗ VIOLATION"), this is now escalated. A malformed diary entry that persists across 4 audits is an accepted defect, not drift.
- ⚠ DRIFT — `chore: FR-080` (`fb09db5`) bundles `feature-requests/FR-081-copilot-node.md` under FR-080 scope. 2nd audit flagging this misattribution. `git log --grep=FR-081` will not find this commit.
- ⚠ DRIFT — FR-080 still lacks a dedicated diary reflection (Distill step). 3rd audit. The cognitive process of testing infrastructure scripts was never captured. Approaching escalation threshold.
- ✓ COMPLIANT — ADR-001 fully upheld: all 53 FR-080 tests tagged `@pytest.mark.req('REQ-YG-063')`, `req_coverage.py` passes (78/78 reqs, 1917 tests), `noqa_coverage.py` passes (53 suppressions, 0 undocumented). Conventional Commits format followed on all 5 commits. Both framework `# noqa` suppressions (ANN001, ARG002) confessed.

**Heuristic:** When an audit re-documents the same violation 4 times without resolution, the audit process itself has become the bottleneck — it surfaces findings but lacks a mechanism to force closure. Findings need owners and deadlines, not just classifications. An Inquisitor that only observes but never compels is a chronicler, not an enforcer.

**Seed:** Should the Inquisitor gain a "compel" action — the ability to create a blocking issue or TODO that must be resolved before the next `feat:`/`fix:` commit can land? This would close the loop between finding and resolution, preventing the infinite-audit-of-the-same-defect pattern.

---

## 2026-02-24: Inquisitor Audit — Scope Drift and Persistent Gaps

**Context:** Audit of the latest 5 commits (`7894440`..`fb09db5`). One `feat:` commit (FR-080, 53 infrastructure tests), one `chore:` commit (FR-080 label but containing FR-081 feature request), two `docs:` commits (FR-078 ARCHITECTURE update, FR-079 diary), one `docs(FR-079):` marking implementation. All human-authored.

**Findings:**

- ✗ VIOLATION — `feat(testing): FR-080` (`5ff37df`) still has no CHANGELOG.md entry. This is the **3rd consecutive audit** flagging this. FR-077's `changelog-required` hook was either bypassed or failed silently. Per the previous audit's own heuristic, persistent drift past 3 audits should escalate to ✗ VIOLATION. Escalated.
- ⚠ DRIFT — HEAD commit `fb09db5` labeled `chore: FR-080` contains `feature-requests/FR-081-copilot-node.md` (325 lines). The commit scope misattributes FR-081 artifacts to FR-080. Each FR should be its own atomic commit scope — traceability suffers when deliverables are bundled under the wrong tag.
- ⚠ DRIFT — FR-080 still lacks a dedicated diary reflection (Distill step). 2nd audit flagging this. The cognitive process of testing infrastructure scripts — what was fragile, what surprised, what patterns emerged — was never captured.
- ⚠ DRIFT — "Git Report" entry (line ~66) still contains leaked LLM preamble ("Perfect! Now I have enough context."). 3rd consecutive audit. Per escalation heuristic, this should be next to escalate.
- ✓ COMPLIANT — ADR-001 upheld across all changes: 25 new test functions tagged `@pytest.mark.req('REQ-YG-063')`, noqa confessions complete (CONF-024–033), Conventional Commits format followed, `req_coverage.py` passes.

**Heuristic:** When a commit bundles unrelated deliverables under a single FR tag, it obscures traceability — `git log --grep=FR-081` will miss `fb09db5`. Atomic FR scope per commit is not aesthetic preference; it is the mechanism that makes `git log` a reliable audit trail. Treat scope misattribution as a traceability defect.

**Seed:** Should a pre-commit hook parse the commit message's FR tag and cross-check it against the paths of staged files (e.g., `feature-requests/FR-081-*` requires `FR-081` in the message)? This would catch scope misattribution at commit time rather than at audit.

---

## 2026-02-24: Inquisitor Audit — FR-080 CHANGELOG Enforcement Gap

**Context:** Audit of the latest 5 commits (`3a9e01d`..`5ff37df`). One `feat:` commit (FR-080, +1228 lines of infrastructure test coverage), two `docs:` commits (FR-079 diary/ARCHITECTURE), one `docs(FR-079):` marking implementation, one `refactor(FR-078):` deleting relocated tests. The `feat:` commit is the only one subject to FR-077 CHANGELOG enforcement.

**Findings:**

- ✗ VIOLATION — Commit `5ff37df` (`feat(testing): FR-080`) did not update CHANGELOG.md. FR-077's `changelog-required` hook enforces that all `feat:` and `fix:` commits stage CHANGELOG.md. The commit either bypassed the hook or it failed silently. A `feat:` that adds 53 tests and 10 confessions is a notable addition that deserves CHANGELOG visibility.
- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags. ADR-001 upheld: FR-080 tests are tagged `@pytest.mark.req('REQ-YG-063')`, `req_coverage.py` passes. All noqa suppressions (CONF-024–033) are confessed in `docs/confessions.md`. Feature request FR-080 exists.
- ⚠ DRIFT — No FR-080 specific diary reflection. The commit added an Inquisitor Audit entry (meta-audit of prior commits) but did not include a Distill step for the FR-080 work itself — the cognitive process of testing infrastructure scripts was not captured.
- ⚠ DRIFT — The "Git Report" entry (line 46+) still contains leaked LLM preamble ("Perfect! Now I have enough context.") and lacks canonical diary format. Flagged in the previous audit; not yet addressed.
- ✓ COMPLIANT — FR-079 completed the full Sermon cycle: Plan (FR doc), Enforce (implementation), Distill (diary entry `4396700`), Submit (marked implemented `7894440`).

**Heuristic:** When a `feat:` commit lands without a CHANGELOG entry, the enforcement hook has failed at its single purpose. Treat hook bypass as a production incident: trace the cause (was `--no-verify` used? was the hook not installed?), fix the gap, and add a regression guard. Silent enforcement failure is worse than no enforcement — it creates false confidence.

**Seed:** Should `req_coverage.py` (or a sibling script) also verify that every `feat:` commit in the last N commits has a corresponding CHANGELOG entry? This would catch enforcement gaps that the commit-msg hook missed, turning a single point of failure into defense in depth.

---

## 2026-02-24: Inquisitor Audit — Housekeeping Commits and Persistent CHANGELOG Drift

**Context:** Inquisitor audit of the latest 5 commits (`e603f29`..`033fdd5`). All five are housekeeping: two `refactor(FR-078):` commits relocating/deleting project tests (3047 lines removed), two `docs:` commits (FR-079 diary reflection, ARCHITECTURE.md update), and one `docs(FR-079):` marking implementation complete. No new features or capabilities were introduced. All commits authored by human (no Co-authored-by trailer expected).

**Findings:**

- ✓ COMPLIANT — All 5 commits follow Conventional Commits with scope and FR tags. `req_coverage.py` passes cleanly. ARCHITECTURE.md was updated in `033fdd5` to document the FR-078/OC-008 relocation. Both framework `# noqa` suppressions (ANN001, ARG002) are confessed in `docs/confessions.md`. ADR-001, Commandments 1, 3, 10 upheld.
- ⚠ DRIFT — No CHANGELOG entry for FR-078 across either commit (`e603f29`, `3a9e01d`). The `refactor:` prefix is exempt from FR-077 enforcement, so technically compliant. However, this is the **4th consecutive audit** flagging this gap. Removing 3047 lines and 8 requirements from framework tracking is a structural change that warrants visibility. The window for a retroactive entry has effectively closed; the version (0.4.55) is already published.
- ⚠ DRIFT — FR-078 has no dedicated diary entry. The cognitive process of severing project tests from the framework — a significant architectural boundary decision — was only captured indirectly through audit entries #14 and #15 (now in `diary-2026-02-23.md`). The Sermon's Distill step was served by proxy, not by the author.
- ⚠ DRIFT — The "Git Report" entry (line 28) contains leaked LLM preamble ("Perfect! Now I have enough context.") and lacks the canonical diary format (**Context:**, **Heuristic:**, **Seed:**). This is a content-quality drift: diary entries should be authored reflections, not raw LLM output pasted verbatim.
- ✓ COMPLIANT — FR-079 has a dedicated diary reflection (commit `4396700`) and the feature request was marked as implemented (`7894440`). The Sermon's full cycle — Plan, Enforce, Distill — was followed.

**Heuristic:** When a drift is flagged across 3+ consecutive audits without resolution, it has graduated from drift to accepted practice. Either amend the doctrine to codify the exception, or schedule a corrective action. Persistent drift erodes the audit's authority — each unfixed finding teaches the team that audit warnings are advisory, not binding.

**Seed:** Should the Inquisitor track a "drift backlog" — a persistent list of unresolved ⚠ findings with escalation thresholds (e.g., 3 audits → auto-escalate to ✗ VIOLATION)? This would formalize the decay signal and prevent indefinite drift.

---

## 2026-02-24: World Digest — Observability and Agent Orchestration


**LangGraph releases dominate the signal.** Five LangGraph SDK/prebuilt releases (0.3.6–0.3.8, 1.0.8, 1.0.9) landed this week, indicating steady iteration on core agent graph infrastructure. These are the foundation YAMLGraph builds on; tracking release notes will be essential for compatibility and new capabilities.

**Observability emerges as a first-class concern.** Multiple articles emphasize agent observability (tracing, evaluation, behavior analysis at scale) as central to agent reliability. LangSmith's Google Cloud Marketplace availability signals that observability tooling is becoming commoditized. This aligns with YAMLGraph's need for transparent node execution and decision logging — especially relevant to the "name the verification question" seed, where observability enables post-hoc audit of agent reasoning.

**Memory and context management patterns are crystallizing.** Agent Builder's memory system and context management for deep agents suggest that stateful orchestration is moving beyond ad-hoc solutions. YAMLGraph's YAML-first approach could benefit from formalizing memory and context as first-class graph primitives, rather than leaving them to node implementation.

**Tool registry and multi-agent patterns gaining traction.** Agent Builder's new tool registry and multi-agent application examples show the ecosystem moving toward standardized tool discovery and composition. This echoes the "protocol archaeology" seed — if tool integration becomes declarative (YAML-driven), YAMLGraph could formalize extraction of integration briefs from GitHub repos into structured tool definitions.

**Evaluation strategy is shifting left.** The monday.com + LangSmith case study emphasizes "code-first evaluation from day 1," suggesting that evaluation should be baked into development workflow, not bolted on. This connects to the "false duplicate" and "edge case diff" seeds — static analysis and boundary testing should be part of the graph definition, not post-hoc review.

**Seed:** As observability becomes standard and evaluation shifts left, should YAMLGraph embed a 'verification question' registry directly into the graph schema — allowing each node to declare what falsifiable claim it's testing, and surfacing mismatches between declared intent and observed behavior during execution?

---

## 2026-02-24: Git Report

Perfect! Now I have enough context. Let me provide you with a comprehensive feature-level summary:

## 📊 Repository Analysis: Last 3 Days Development Summary

### **Overview**
Active development across 5 major feature areas with a focus on infrastructure automation, voice call systems, testing enhancements, and system governance.

---

### **🎯 Key Features Implemented**

#### **1. FR-079: State-Based Unification for Caller Module (COMPLETED)**
- **Status**: ✅ Implemented & Documented
- **Changes**: Refactored caller functionality with state-based patterns
- **Actions**: Deleted relocated project tests, moved tests to appropriate repositories
- **Impact**: Consolidates voice system architecture

#### **2. FR-077: CHANGELOG.md Enforcement Hook (COMPLETED)**
- **Status**: ✅ Implemented
- **Details**: Pre-commit hook that enforces CHANGELOG.md updates for all `feat/` and `fix/` commits
- **Configuration**: Added to `.pre-commit-config.yaml`
- **Impact**: Improves release documentation consistency and traceability

#### **3. FR-076: Inquisitor Audit Script & Chaplain Hooks (COMPLETED)**
- **Status**: ✅ Implemented
- **Features**:
  - `inquisitor.sh`: Automated audit script for test subject archaeology
  - Post-commit trigger integration
- **Documentation**: Updated test protocols and checklist
- **Impact**: Enhanced testing governance and automated quality checks

#### **4. FR-071: Graph-Level Thinking Budget Implementation (COMPLETED)**
- **Status**: ✅ Fully Implemented with Comprehensive Testing
- **Scope**: Extended thinking support for LLM nodes with token budgets
- **Technical Implementation**:
  - Schema validation (0 or ≥1024 tokens)
  - LLM factory automatic temperature=1 override
  - Node factory parameter threading
  - 4 linter warning codes (W071-1 through W071-4)
  - **Test Coverage**: 18 unit tests + 1 integration test
  - Demo: `examples/demos/thinking/`
- **Impact**: Enables advanced reasoning capabilities in graph-based workflows

#### **5. IC-000: InCal
