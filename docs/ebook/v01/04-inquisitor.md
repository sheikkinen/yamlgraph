# Chapter 04: The Inquisitor

> *"An audit finding repeated four times without remediation is not drift — it is accepted practice."*
> — Inquisitor Audit, `docs/diary.md`

---

## What is the Inquisitor?

The Chaplain guards the gate before a commit enters the repository. But what about the work that passes through? Code can satisfy every pre-commit check — linting, tests, coverage, conventional commit format — and still violate the project's deeper doctrine. A feature might land without a diary entry. A `feat:` commit might forget its CHANGELOG update. A new capability might ship without requirement traceability.

The Inquisitor is YAMLGraph's post-commit auditor. Where the Chaplain is a gatekeeper — blocking commits that fail structural checks — the Inquisitor is a detective. It examines what already got through, compares it against the Scripture's full doctrine, and records its findings in the project diary. It doesn't block anything; it *witnesses* and *records*.

The name follows the project's ecclesiastical metaphor: after the Chaplain has blessed the commit, the Inquisitor arrives to ask harder questions. Did the developer follow the Sermon? Was the Rite of Correction observed? Did institutional knowledge get captured, or did it evaporate with the coding session?

This separation of concerns — prevention vs. audit — is deliberate. Pre-commit hooks must be fast and deterministic; they check syntax, format, and structural rules. Post-commit audits can be slow, agentic, and reflective; they check intent, completeness, and doctrinal alignment. The Inquisitor lives in this second category.

---

## When It Runs

The Inquisitor is defined as a post-commit hook in `.pre-commit-config.yaml`:

```yaml
# Source: .pre-commit-config.yaml, lines 173–181
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

Three properties define its activation:

**1. Post-commit stage.** The `stages: [post-commit]` declaration means this hook runs *after* a commit succeeds — after the Chaplain's pre-commit gates, after the commit-msg validators, after everything else has passed. The commit is already in the repository when the Inquisitor begins.

**2. Always runs.** The `always_run: true` flag means every commit triggers an audit. There is no file-path filter, no conditional skip. The Inquisitor treats every commit as worth examining, regardless of whether it touched code, documentation, or configuration.

**3. Background execution.** The `entry` wraps the audit script in `nohup ... &`, detaching it from the commit process. This is critical: the developer's terminal returns immediately. The audit runs asynchronously, writing its output to `.chaplain/inquisitor.log`. The developer doesn't wait for the Inquisitor; the Inquisitor works on its own schedule.

This background design reflects a philosophical choice. Pre-commit hooks *must* be synchronous — the developer waits because the commit depends on the result. Post-commit audits have no such constraint. The commit is done. The audit is for the record, not for the gate. Running it asynchronously means the Inquisitor never slows down the development loop.

---

## The Audit Process

The Inquisitor's logic lives in a single script: `.chaplain/inquisitor.sh`. It follows a four-phase protocol — **Quote, Investigate, Judge, Record** — executed as a single Copilot CLI invocation.

```bash
# Source: .chaplain/inquisitor.sh, lines 1–4
#!/usr/bin/env bash
# .chaplain/inquisitor.sh — Audit loop: Quote → Investigate → Judge → Record
# FR-076: Quotes the Scripture, audits recent work, writes diary entry
set -euo pipefail
```

The script delegates the entire audit to GitHub Copilot CLI via `copilot --allow-all-paths --allow-all-tools`, passing a detailed prompt that implements the four phases.

### Phase 1: Gather Evidence

The Inquisitor begins by reading the project's recent state:

```
- Read the latest 5 commits: git log --oneline -5
- Read the top of CHANGELOG.md (first 30 lines)
- Read the latest diary entry in docs/diary.md (first entry after the header)
- Read CLAUDE.md to refresh the Scripture (Commandments, Sermon, Rite of Correction)
```
*(Source: `.chaplain/inquisitor.sh`, lines 14–17)*

This evidence-gathering phase is deliberately broad. The Inquisitor doesn't just look at the latest commit — it examines the last five, giving it context about the current work session. It reads the CHANGELOG to verify traceability. It reads the diary to understand what's already been reflected upon. And it re-reads the Scripture itself, ensuring the audit applies the current doctrine, not a stale memory of it.

### Phase 2: Investigate

With evidence in hand, the Inquisitor checks each commit against six doctrinal rules:

```
1. Does it follow Conventional Commits? (Commandment 10)
2. Is there a corresponding CHANGELOG entry? (Commandment 10)
3. If it introduced a new capability, was a requirement added
   to ARCHITECTURE.md? (ADR-001)
4. If tests were added, do they have @pytest.mark.req tags? (ADR-001)
5. Was a diary entry written for the task? (Sermon: Distill)
6. Are there any noqa suppressions without CONF-XXX entries?
   (noqa Confessions)
```
*(Source: `.chaplain/inquisitor.sh`, lines 20–27)*

These six checks map directly to the Scripture's enforceable rules. Items 1–2 enforce Commandment 10 ("preserve and improve the doctrine"). Items 3–4 enforce ADR-001 (requirement traceability). Item 5 enforces the Sermon's Distill step. Item 6 enforces the noqa Confessions doctrine.

Note what the Inquisitor does *not* check: code quality, test coverage, formatting, complexity. Those are the Chaplain's domain — enforced mechanically at pre-commit time. The Inquisitor audits the things that can't be checked mechanically: intent, completeness, and reflective discipline.

### Phase 3: Judge

Each finding is classified into one of three severity levels:

```
- ✓ COMPLIANT — Doctrine followed
- ⚠ DRIFT — Minor deviation, no immediate harm
- ✗ VIOLATION — Doctrine broken, action needed
```
*(Source: `.chaplain/inquisitor.sh`, lines 29–32)*

The three-tier classification mirrors traditional audit practice. COMPLIANT findings are recorded as evidence that the system works — compliance is worth witnessing, not just assumed. DRIFT findings flag deviations that don't require immediate action but should be tracked for patterns. VIOLATION findings demand correction.

In practice, as the diary entries reveal, most findings fall into COMPLIANT or DRIFT. Outright violations are rare because the pre-commit Chaplain catches the structural ones. The Inquisitor's DRIFT findings tend to surface softer gaps: missing diary reflections, terse commit messages, absent co-authorship trailers — the things that erode institutional knowledge over time.

### Phase 4: Record

The Inquisitor writes its findings directly into `docs/diary.md`:

```
Append a new diary entry to docs/diary.md following the established format:
- Header: '## YYYY-MM-DD: Inquisitor Audit — [summary]'
- **Context:** What was audited and why
- **Findings:** List of ✓/⚠/✗ items (keep concise — max 5 most significant)
- **Heuristic:** One actionable lesson extracted
- **Seed:** One forward-looking question
```
*(Source: `.chaplain/inquisitor.sh`, lines 35–41)*

A crucial constraint: the Inquisitor is instructed to modify *only* `docs/diary.md`. It cannot fix the problems it finds. It cannot amend code, update the CHANGELOG, or add missing requirement tags. Its sole output is a diary entry. This read-only-except-diary design prevents the auditor from becoming an actor — a separation that keeps the audit trail trustworthy.

The output goes to `.chaplain/inquisitor.log` for the current session, and the permanent record lands in the diary.

---

## Anatomy of an Audit Entry

Here is a representative Inquisitor audit entry from `docs/diary.md`, showing the full structure:

```markdown
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
```
*(Source: `docs/diary.md`, entry for commit `bd1d6ce`)*

### What Gets Recorded

Each audit entry contains five elements:

| Element | Purpose |
|---------|---------|
| **Header** | Date, "Inquisitor Audit" tag, and a brief summary for `grep` discoverability |
| **Context** | The commit SHA, range examined, and what kind of work was audited |
| **Findings** | Up to 5 classified items (✓/⚠/✗) with doctrine citations |
| **Heuristic** | One actionable lesson distilled from the findings |
| **Seed** | A forward-looking question to inspire future improvement |

The Heuristic and Seed fields are where the Inquisitor transcends simple compliance checking. A linter reports pass/fail. The Inquisitor extracts *lessons* and plants *questions*. Over time, these accumulate into a body of institutional wisdom — the project teaching itself.

### How Issues Are Flagged

The classification system creates a natural escalation path:

- **✓ COMPLIANT** findings build confidence that the doctrine works. When the same check passes across many audits, it validates the pre-commit gates.
- **⚠ DRIFT** findings track erosion. A single drift is a data point. Three drifts on the same issue are a pattern. Five drifts are technical debt — as the diary itself records: *"When the same drift is flagged across 5+ audits without resolution, the finding has graduated from observation to technical debt."*
- **✗ VIOLATION** findings trigger the Rite of Correction: inspect, amend, escalate. In practice, violations are rare because the pre-commit pipeline catches most structural issues before they reach the Inquisitor.

---

## The Chaplain and the Inquisitor

The Chaplain and the Inquisitor form two halves of a complete quality system. Understanding their relationship reveals the design philosophy behind YAMLGraph's development pipeline.

### The Chaplain: Prevention (Pre-Commit)

The Chaplain runs *before* commits enter the repository. As defined in `.pre-commit-config.yaml`, the pre-commit stage includes:

| Hook | What It Checks |
|------|---------------|
| `ruff` | Code style and lint errors |
| `ruff-format` | Code formatting |
| `req-coverage-strict` | Requirement traceability (ADR-001) |
| `noqa-confession` | Undocumented lint suppressions |
| `radon-complexity` | Cyclomatic complexity gate |
| `file-size-gate` | Module size limits |
| `vulture-dead-code` | Dead code detection |
| `jscpd-dup` | Code duplication |
| `pytest` | Unit test suite |
| `conventional-pre-commit` | Commit message format |
| `feat-requires-fr` | Feature request traceability |
| `changelog-required` | CHANGELOG discipline |

These are *mechanical* checks — deterministic, fast, binary. They answer: "Does this commit meet the minimum structural bar?" If any check fails, the commit is blocked. No negotiation, no judgement call.

### The Inquisitor: Audit (Post-Commit)

The Inquisitor runs *after* commits succeed. It checks things that can't be reduced to a lint rule:

| Check | What It Asks |
|-------|-------------|
| Conventional Commits | Not just format — is the message *descriptive*? |
| CHANGELOG alignment | Not just present — does the entry *match* the commit? |
| Requirement traceability | Not just tagged — is the *full chain* intact? |
| Test tagging | Not just present — do tags reference *real* requirements? |
| Diary discipline | Was the Sermon's Distill step followed? |
| noqa confessions | Are all suppressions *documented* with rationale? |

These are *judgement* checks — agentic, reflective, graduated. They answer: "Does this commit respect the project's deeper values?" Findings are classified, not blocked.

### Complementary by Design

The two systems are deliberately complementary:

```
Developer writes code
        │
        ▼
┌──────────────────┐
│   PRE-COMMIT     │  ← Chaplain: mechanical gates
│   (synchronous)  │     Blocks on failure
│                  │     Fast, deterministic
└───────┬──────────┘
        │ commit succeeds
        ▼
┌──────────────────┐
│   POST-COMMIT    │  ← Inquisitor: doctrinal audit
│   (asynchronous) │     Records findings
│                  │     Slow, agentic, reflective
└───────┬──────────┘
        │
        ▼
   docs/diary.md     ← Institutional memory
```

The Chaplain ensures the commit is *correct*. The Inquisitor asks whether it is *complete*. Together, they implement the Scripture's full quality vision: Commandments enforced mechanically, Sermon observed reflectively.

### The Entropy Paradox

The diary reveals an ironic pattern: the Inquisitor itself became the largest source of diary entropy. With `always_run: true` on every commit, and each audit producing a full diary entry, the Inquisitor generated more entries than the development work it audited. As one audit candidly recorded:

> *"When the corrective mechanism produces more entropy than the defects it finds, the mechanism itself needs correction."*
> — Inquisitor Audit, `docs/diary.md`

This self-diagnosis — an auditor recognizing its own cost — is itself a valuable finding. It led to proposals for minimum-delta heuristics (don't re-audit already-audited commits), diary rotation (archive entries to dated files), and audit batching (one entry per session, not per commit). The Inquisitor's ability to identify its own dysfunction demonstrates the value of the Seed field: each audit plants a question that future audits can act on.

---

## Summary

The Inquisitor completes YAMLGraph's quality loop. Where pre-commit hooks enforce the letter of the law, the Inquisitor examines the spirit. It runs after every commit, gathers evidence from the recent work, judges it against the Scripture's full doctrine, and records its findings with extracted heuristics and forward-looking questions.

Its design embodies three principles:

1. **Separation of prevention and audit.** The Chaplain blocks; the Inquisitor records. Neither does the other's job.
2. **Agentic reflection over mechanical checking.** An LLM reads the Scripture, examines the commits, and renders graduated judgement — something no lint rule can do.
3. **Institutional memory.** Every audit entry adds to the project's body of knowledge. Heuristics compound. Seeds grow into improvements. Even the Inquisitor's failures become lessons.

The result is a development pipeline where no commit goes unexamined, and every examination leaves behind something the project can learn from.


