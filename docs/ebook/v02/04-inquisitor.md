# Chapter 04: The Inquisitor

*From the YAMLGraph Development Pipeline eBook*

---

## 1. What is the Inquisitor?

The Inquisitor is YAMLGraph's post-commit auditor — a process that examines changes *after* they've been committed, checking them against the project's doctrine. Where the Chaplain and pre-commit hooks act as gatekeepers that prevent bad commits from entering the repository, the Inquisitor operates on the other side: it reviews what actually got through and records its findings.

The name is deliberate. An inquisitor doesn't block the door; it examines what's inside. Every commit that lands in the repository is subject to audit. The Inquisitor reads the Scripture (the project's commandments in `CLAUDE.md`), gathers evidence from recent commits, investigates compliance, renders judgement, and writes its findings to the project diary.

This creates a closed feedback loop: the pre-commit gates enforce known rules mechanically, while the post-commit Inquisitor catches the things that mechanical checks cannot — missing diary entries, gaps in requirement traceability, or the slow accumulation of drift that no single commit reveals.

> *Source: `.chaplain/inquisitor.sh` — FR-076*

---

## 2. When It Runs

The Inquisitor is triggered automatically after every successful commit via the `post-commit` hook stage defined in `.pre-commit-config.yaml`.

### The Hook Definition

> As defined in `.pre-commit-config.yaml` (lines 173–181):

```yaml
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

### Key Design Decisions

**Post-commit, not pre-commit.** The Inquisitor runs at the `post-commit` stage. This is a fundamental architectural choice — auditing should never block the developer's commit flow. The pre-commit hooks (Chapter 02) handle blocking gates. The Inquisitor is advisory.

**Asynchronous execution.** The hook wraps the script in `nohup ... &`, launching it as a background process. The developer's terminal returns immediately after the commit completes. The audit runs silently in the background, writing its output to `.chaplain/inquisitor.log`.

**Always runs.** The `always_run: true` and `pass_filenames: false` settings mean the Inquisitor fires on every commit regardless of which files changed. It audits the *state of the project*, not individual file changes.

**No blocking.** Because it runs asynchronously in the background, even a slow audit (involving LLM calls) never delays the developer. If the audit fails, it fails silently into the log file — it never prevents the next commit.

---

## 3. The Audit Process

The Inquisitor script follows a four-phase protocol: **Quote → Investigate → Judge → Record**.

> As defined in `.chaplain/inquisitor.sh`:

```bash
#!/usr/bin/env bash
# .chaplain/inquisitor.sh — Audit loop: Quote → Investigate → Judge → Record
# FR-076: Quotes the Scripture, audits recent work, writes diary entry
set -euo pipefail
cd "$(dirname "$0")/.."

echo "🔍 Inquisitor: Auditing recent work against the Scripture..."
```

The script delegates the entire audit to GitHub Copilot CLI with a structured prompt that defines each phase.

### Phase 1: Gather Evidence

The Inquisitor begins by collecting context from four sources:

| Source | Command / Action | Purpose |
|--------|-----------------|---------|
| Recent commits | `git log --oneline -5` | What changed recently |
| Changelog | First 30 lines of `CHANGELOG.md` | Whether changes are documented |
| Latest diary entry | First entry in `docs/diary.md` | Whether reflection happened |
| The Scripture | `CLAUDE.md` | The doctrine to audit against |

This evidence gathering ensures the Inquisitor has both the *facts* (what happened) and the *law* (what should have happened).

### Phase 2: Investigate

For each recent commit, the Inquisitor checks six specific compliance criteria:

1. **Conventional Commits (Commandment 10)** — Does the commit message follow the `type(scope): description` format?
2. **CHANGELOG entries (Commandment 10)** — Do `feat:` and `fix:` commits have corresponding entries?
3. **Requirement traceability (ADR-001)** — If a new capability was introduced, was a requirement added to `ARCHITECTURE.md`?
4. **Test tagging (ADR-001)** — Do new tests carry `@pytest.mark.req` decorators linking them to requirements?
5. **Diary reflection (Sermon: Distill)** — Was a diary entry written for the completed task?
6. **noqa Confessions** — Are there any `# noqa` suppressions without corresponding `CONF-XXX` entries in `docs/confessions.md`?

These six checks map directly to the project's doctrine. The Inquisitor doesn't invent rules — it enforces the ones already written in the Scripture.

### Phase 3: Judge

Each finding is classified into one of three severity levels:

| Classification | Meaning |
|---------------|---------|
| ✓ **COMPLIANT** | Doctrine followed correctly |
| ⚠ **DRIFT** | Minor deviation, no immediate harm, but worth recording |
| ✗ **VIOLATION** | Doctrine broken, action needed |

The three-level system avoids false urgency. A missing `Co-authored-by` trailer is drift; a `feat:` commit without a requirement is a violation. The distinction matters because it guides the developer's response: drift can wait, violations cannot.

### Phase 4: Record

The Inquisitor appends a structured entry to `docs/diary.md`. This is the *only* file it modifies. The entry follows a strict format:

```
## YYYY-MM-DD: Inquisitor Audit — [summary]

**Context:** What was audited and why
**Findings:** List of ✓/⚠/✗ items (max 5 most significant)
**Heuristic:** One actionable lesson extracted
**Seed:** One forward-looking question
```

Even when all findings are compliant, the audit is still recorded. As the script's prompt states: *"compliance is worth witnessing."* An audit trail that only records failures creates a biased view of the project's health.

### Where Results Are Logged

Results appear in two places:

- **`docs/diary.md`** — The permanent record, committed to the repository as part of the project's history.
- **`.chaplain/inquisitor.log`** — The transient execution log, capturing stdout/stderr from the background process. Useful for debugging audit failures but not part of the project record.

---

## 4. Sample Audit Entry

Here is an actual Inquisitor audit entry from the project diary, showing the format in practice.

> As recorded in `docs/diary.md`:

```markdown
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
```

### Anatomy of the Entry

**Context** establishes the audit scope: which commits, which SHAs, which features. This makes the entry traceable — a reader can `git show 0704063` to see exactly what was audited.

**Findings** are the heart of the entry. Each item maps to a specific doctrine rule, states the evidence, and renders a verdict. The format is consistent: `classification — rule (source): evidence`. Note that compliant findings are recorded alongside drift — the audit is a complete picture, not just a list of problems.

**Heuristic** distills one lesson from the audit. This follows the Sermon's *Distill* step — every audit should leave the project slightly wiser. Heuristics that recur across audits are candidates for graduation into the Scripture itself.

**Seed** plants a forward-looking question. In this case, the Inquisitor has noticed that its own audit entries are becoming the dominant content in the diary — a recursive problem that the next chapter of development must address.

---

## 5. Relationship to the Chaplain

The Chaplain (Chapter 03) and the Inquisitor form a complementary pair — two sides of the same quality assurance strategy.

### The Chaplain: Prevention (Pre-Commit)

The Chaplain and its pre-commit hooks run *before* a commit is accepted. They are blocking gates:

- **Ruff** catches style and lint errors
- **req-coverage** enforces requirement traceability
- **noqa-confession** ensures suppressions are documented
- **pytest** runs the unit test suite
- **vulture** detects dead code
- **conventional-pre-commit** validates commit message format

If any gate fails, the commit is rejected. The developer must fix the issue before trying again. This is mechanical enforcement — the rules are codified in scripts, and there is no discretion.

### The Inquisitor: Audit (Post-Commit)

The Inquisitor runs *after* the commit is accepted. It is non-blocking and advisory:

- Checks compliance with doctrine that can't be mechanically enforced
- Identifies *drift* — small deviations that are individually harmless but collectively dangerous
- Records findings for human review
- Extracts heuristics and plants seeds for future improvement

The Inquisitor catches what the Chaplain cannot: missing diary reflections, gaps in the narrative between commits and changelog entries, requirement coverage that passes `--strict` but misses the spirit of the rule.

### The Complete Picture

```
Developer writes code
        │
        ▼
┌─────────────────────┐
│  Pre-Commit Gates    │  ← Chaplain (Chapter 03)
│  (blocking)          │     Ruff, pytest, vulture,
│                      │     req-coverage, jscpd, ...
└─────────┬───────────┘
          │ Pass
          ▼
┌─────────────────────┐
│  Commit Message      │  ← Conventional Commits,
│  Validation          │     FR-tag enforcement,
│  (blocking)          │     CHANGELOG requirement
└─────────┬───────────┘
          │ Pass
          ▼
    Commit accepted
          │
          ▼
┌─────────────────────┐
│  Post-Commit Audit   │  ← Inquisitor (this chapter)
│  (async, advisory)   │     Doctrine compliance,
│                      │     drift detection,
└─────────┬───────────┘     diary recording
          │
          ▼
    Findings in diary
```

The Chaplain prevents known defects. The Inquisitor discovers unknown drift. Together, they implement the Scripture's vision: *"What survives the fire may merge."* The pre-commit hooks are the fire. The Inquisitor is the witness that inspects what emerged.

---

## Summary

| Aspect | Detail |
|--------|--------|
| **Script** | `.chaplain/inquisitor.sh` |
| **Trigger** | `post-commit` hook in `.pre-commit-config.yaml` |
| **Execution** | Async background process (`nohup ... &`) |
| **Input** | Last 5 commits, CHANGELOG, diary, Scripture |
| **Checks** | 6 compliance criteria against doctrine |
| **Output** | Structured entry in `docs/diary.md` |
| **Log** | `.chaplain/inquisitor.log` |
| **Blocking** | No — advisory only |

The Inquisitor completes the development loop: the Chaplain ensures you follow the rules going in, and the Inquisitor verifies you followed them coming out. Neither replaces the other. Prevention without audit breeds complacency; audit without prevention breeds chaos.

---

*Next: Chapter 05*


