# Chapter 04: The Inquisitor

> *"When the corrective mechanism produces more entropy than the defects it finds, the mechanism itself needs correction."*
> — docs/diary.md, Inquisitor Audit

---

## What Is the Inquisitor?

The Chaplain guards the gate before a commit enters the repository. But what about the commits that make it through? Who audits whether the development work — across multiple commits, across a session — actually follows the doctrine?

That is the Inquisitor's role.

The Inquisitor is a **post-commit auditor**: an AI-powered script that runs *after* every successful commit, examining the recent history against the Scripture's Commandments, the Sermon, ADR-001, and the Confessions registry. Where the Chaplain is a bouncer checking IDs at the door, the Inquisitor is the inspector who reviews the building after the tenants move in.

The key difference is scope. The Chaplain validates the commit *being made* — its format, its linting, its tests. The Inquisitor examines *patterns across commits* — whether diary entries exist for completed features, whether requirement traceability chains are intact, whether the same drift keeps appearing without resolution.

---

## When It Runs

The Inquisitor is triggered by the `post-commit` stage in `.pre-commit-config.yaml`:

```yaml
# .pre-commit-config.yaml (lines 173–181)
- repo: local
  hooks:
    - id: inquisitor-background
      name: inquisitor (async audit)
      entry: bash -c 'nohup .chaplain/inquisitor.sh > .chaplain/inquisitor.log 2>&1 &'
      language: system
      pass_filenames: false
      always_run: true
      stages: [post-commit]
```

Three design decisions are embedded in this configuration:

1. **`stages: [post-commit]`** — The Inquisitor fires after the commit succeeds, never before. It cannot block or reject. It can only observe and record. This is deliberate: the Chaplain's pre-commit hooks are the gatekeepers; the Inquisitor is the auditor.

2. **`always_run: true`** — Every commit triggers an audit. There is no condition that silences the Inquisitor. Whether the commit is a single-line docs fix or a 500-line feature, the audit runs.

3. **`nohup ... &` (async execution)** — The Inquisitor runs in the background via `nohup`, with output redirected to `.chaplain/inquisitor.log`. This means the developer's terminal is not blocked waiting for the audit to complete. The commit finishes instantly; the Inquisitor works silently behind the scenes. This is critical because the audit involves an LLM call, which can take 10–30 seconds.

The combination of `always_run` and async execution means: **every commit is audited, and the developer never waits**.

---

## The Audit Process

The Inquisitor's implementation lives in `.chaplain/inquisitor.sh`. It follows a four-step protocol: **Quote → Investigate → Judge → Record**.

### Step 1: Gather Evidence

```bash
# .chaplain/inquisitor.sh (lines 13–17)
# - Read the latest 5 commits: git log --oneline -5
# - Read the top of CHANGELOG.md (first 30 lines)
# - Read the latest diary entry in docs/diary.md
# - Read CLAUDE.md to refresh the Scripture
```

The Inquisitor begins by collecting evidence from four sources:

- **Git history** — The last 5 commits provide the audit window. This sliding window means every commit is covered by at least one audit, and the overlap ensures nothing falls through gaps.
- **CHANGELOG.md** — The recent changelog entries reveal whether `feat:` and `fix:` commits have corresponding user-facing documentation.
- **docs/diary.md** — The latest diary entry shows whether the Sermon's Distill step has been followed — did the developer reflect on completed work?
- **CLAUDE.md** — The Scripture itself, re-read fresh each time. The Inquisitor never relies on cached knowledge of the rules; it reads the canonical source on every invocation.

### Step 2: Investigate

The Inquisitor checks each recent commit against six doctrine requirements:

```bash
# .chaplain/inquisitor.sh (lines 19–26)
# 1. Does it follow Conventional Commits? (Commandment 10)
# 2. Is there a corresponding CHANGELOG entry? (Commandment 10)
# 3. If it introduced a new capability, was a requirement added
#    to ARCHITECTURE.md? (ADR-001)
# 4. If tests were added, do they have @pytest.mark.req tags? (ADR-001)
# 5. Was a diary entry written for the task? (Sermon: Distill)
# 6. Are there any noqa suppressions without CONF-XXX entries?
#    (noqa Confessions)
```

These six checks cover the full traceability chain:

| Check | Doctrine Source | What It Catches |
|-------|----------------|-----------------|
| Conventional Commits | Commandment 10 | Malformed commit messages |
| CHANGELOG entry | Commandment 10 | Features/fixes without user documentation |
| ARCHITECTURE.md requirement | ADR-001 | New capabilities without traceability |
| `@pytest.mark.req` tags | ADR-001 | Tests disconnected from requirements |
| Diary entry | Sermon: Distill | Completed work without reflection |
| noqa confessions | Confessions registry | Suppressed warnings without justification |

### Step 3: Judge

Each finding receives one of three classifications:

```bash
# .chaplain/inquisitor.sh (lines 28–32)
# - ✓ COMPLIANT — Doctrine followed
# - ⚠ DRIFT — Minor deviation, no immediate harm
# - ✗ VIOLATION — Doctrine broken, action needed
```

- **✓ COMPLIANT** means the doctrine was followed for that specific check. The Inquisitor records compliance as evidence, not just violations — a clean audit is still worth witnessing.
- **⚠ DRIFT** means a minor deviation was found. Drift doesn't break anything today, but left unchecked it erodes standards. Examples: a missing `Co-authored-by` trailer, diary entries growing without rotation.
- **✗ VIOLATION** means doctrine was broken and action is needed. Examples: a `feat:` commit without a CHANGELOG entry, new tests without `@pytest.mark.req` tags.

### Step 4: Record

```bash
# .chaplain/inquisitor.sh (lines 34–42)
# Append a new diary entry to docs/diary.md following the established format:
# - Header: '## YYYY-MM-DD: Inquisitor Audit — [summary]'
# - **Context:** What was audited and why
# - **Findings:** List of ✓/⚠/✗ items (keep concise — max 5 most significant)
# - **Heuristic:** One actionable lesson extracted
# - **Seed:** One forward-looking question
```

The Inquisitor writes its findings directly into `docs/diary.md` — the same file used for developer reflections. The entry follows the diary's established format: Context, Findings, Heuristic, and Seed. This means audit results are version-controlled, searchable, and part of the project's metacognitive record.

Critically, the Inquisitor is instructed: *"If all findings are COMPLIANT, still record the audit — compliance is worth witnessing."* A clean audit is not silence; it is affirmation.

The script is also constrained: *"Do NOT create or modify any files other than docs/diary.md."* The Inquisitor observes and records. It never fixes.

---

## Sample Audit Entry

Here is a real Inquisitor audit entry from `docs/diary.md`, showing the structure in practice:

```markdown
## 2026-02-25: Inquisitor Audit — Post-Fix Persistence, Doctrine Intact

**Context:** Audit of HEAD (`a9bffc8`), covering 5 commits: `a9bffc8`
(fix: FR-103 per-chapter persistence), `0704063` (docs: FR-103 diary),
`b0fa74c` (feat: FR-103 judge-amend subgraph), `9048d03` (docs: FR-100
progress), `bd1d6ce` (feat: FR-100 ebook scaffold). Two `feat` and one
`fix` commit introduce or restore capabilities. Audited against
Commandments, ADR-001, Confessions, and the Sermon.

**Findings:**

- ✓ COMPLIANT — **Conventional Commits + CHANGELOG (Commandment 10):**
  All 5 commits use correct type/scope/FR-tag format. Both `feat` commits
  and the `fix` commit have corresponding CHANGELOG 0.4.58 entries.
- ✓ COMPLIANT — **ADR-001 (Requirement Traceability):** REQ-YG-091 and
  REQ-YG-092 both present in ARCHITECTURE.md. 8 tests all carry
  `@pytest.mark.req` tags. Full chain intact.
- ✓ COMPLIANT — **noqa Confessions:** Zero new suppressions introduced.
  2 framework suppressions (CONF-002, CONF-003) remain confessed.
- ⚠ DRIFT — **Co-authored-by trailer:** 0/5 commits include the
  required trailer. Recurring accepted deviation.
- ⚠ DRIFT — **Diary entropy (Commandment 8):** 25 entries for
  2026-02-25 in 340 lines. The Inquisitor's own entries remain
  the dominant entropy contributor.

**Heuristic:** When the same drift is flagged across 5+ audits without
resolution, the finding has graduated from observation to technical debt.
Either apply the existing fix or accept the drift formally — repeated
flagging without action is itself entropy.

**Seed:** Could audit findings be accumulated in a lightweight structure
and flushed to diary.md only once per session — collapsing N audits into
one entry per working period?
```

*Source: docs/diary.md, lines 46–60 (condensed for clarity)*

### Anatomy of the Entry

**Header** — `## YYYY-MM-DD: Inquisitor Audit — [summary]` makes audit entries immediately identifiable in the diary. The summary captures the audit's theme in a few words.

**Context** — Lists the exact commits audited (by SHA), their types, and what doctrine aspects were checked. This makes every audit reproducible: you can trace back to exactly what code was examined.

**Findings** — A flat list of `✓`/`⚠`/`✗` items, capped at 5 for conciseness. Each finding cites the specific doctrine rule (Commandment number, ADR-001, Sermon step) and gives concrete evidence (commit counts, test counts, file names). Notice how even compliant findings are recorded — they prove the audit was thorough.

**Heuristic** — One actionable lesson distilled from the audit. This is the Inquisitor's version of the Sermon's Distill step. The best heuristics are reusable: "When the same drift is flagged across 5+ audits without resolution, the finding has graduated from observation to technical debt."

**Seed** — A forward-looking question that plants ideas for future improvement. Seeds from Inquisitor audits have proposed diary rotation, audit batching, accepted-deviations registries, and structural changes to the audit process itself.

---

## Relationship to the Chaplain

The Chaplain and the Inquisitor form a complementary pair — prevention and detection, gate and audit:

| Aspect | Chaplain (Pre-Commit) | Inquisitor (Post-Commit) |
|--------|----------------------|-------------------------|
| **When** | Before the commit is created | After the commit succeeds |
| **Can block?** | Yes — fails the commit | No — only observes and records |
| **Scope** | The single commit being made | The last 5 commits (sliding window) |
| **Checks** | Syntax, formatting, tests, file sizes, complexity | Doctrine compliance, traceability chains, reflection |
| **Speed** | Synchronous — developer waits | Asynchronous — runs in background |
| **Output** | Pass/fail in terminal | Diary entry in `docs/diary.md` |
| **Nature** | Mechanical — deterministic rules | Interpretive — AI-powered judgment |

### What the Chaplain Catches

The Chaplain's pre-commit hooks (Chapter 02) enforce mechanical rules: ruff linting, trailing whitespace, YAML validity, file size limits, cyclomatic complexity, dead code, duplicate code, test execution, conventional commit format, and FR-tag enforcement. These are binary pass/fail checks. Either the code passes ruff or it doesn't. Either the commit message follows Conventional Commits or it doesn't.

### What the Inquisitor Catches

The Inquisitor catches *semantic* and *cross-commit* concerns that no mechanical hook can enforce:

- **Was a diary entry written?** — The Chaplain can check if `diary.md` was modified in the commit, but it can't judge whether the entry is meaningful or relevant to the work done.
- **Is the requirement chain complete?** — The Chaplain runs `req_coverage.py` to check that requirements have tests, but the Inquisitor checks whether a *new capability* prompted a new requirement in the first place.
- **Is the CHANGELOG accurate?** — The `changelog-required` hook checks that `feat:`/`fix:` commits include CHANGELOG modifications, but the Inquisitor reads the actual content to verify it matches the commit.
- **Are patterns degrading over time?** — The Inquisitor tracks recurring drift across audits. When it flags "this is the 5th consecutive audit finding the same gap," it's performing trend analysis that no single-commit hook can do.

### The Feedback Loop

Together, the Chaplain and Inquisitor create a closed loop:

```
Developer writes code
        │
        ▼
  ┌─────────────┐
  │  Chaplain    │ ── FAIL → Developer fixes and retries
  │  (pre-commit)│
  └──────┬──────┘
         │ PASS
         ▼
    Commit created
         │
         ▼
  ┌─────────────┐
  │  Inquisitor  │ ── Records findings in diary
  │ (post-commit)│
  └──────┬──────┘
         │
         ▼
  Findings inform next session
         │
         ▼
  Developer addresses drift → Next commit → Chaplain...
```

The Chaplain prevents the obviously wrong. The Inquisitor surfaces the subtly incomplete. Between them, the doctrine is both enforced and audited — not perfectly, but persistently.

### The Entropy Paradox

The diary reveals a fascinating tension: the Inquisitor's own audit entries can become the dominant source of entropy in `docs/diary.md`. Multiple audit entries from the same day, covering overlapping commit ranges, with similar findings — the auditor becomes the problem it was designed to detect.

This paradox is acknowledged directly in the diary's heuristics:

> *"When the audit tool generates more diary entries than the development it audits, the tool has become the primary source of entropy."*

The proposed solutions — audit batching, separate audit logs, last-audited-SHA markers, diary rotation — are themselves Seeds planted by the Inquisitor. The system is self-diagnosing, even when the diagnosis is "I am the problem."

This is doctrine working as designed: the Inquisitor follows the Sermon's Distill step, reflecting on its own operation, planting Seeds for improvement, and trusting that the next iteration will address the findings. What survives the fire may merge.

---

## File References

| File | Role |
|------|------|
| `.chaplain/inquisitor.sh` | Audit script — the Inquisitor's implementation |
| `.pre-commit-config.yaml` (lines 173–181) | Post-commit hook definition — when and how it triggers |
| `docs/diary.md` | Audit output — where findings are recorded |
| `.chaplain/inquisitor.log` | Runtime log — stdout/stderr from async execution |


