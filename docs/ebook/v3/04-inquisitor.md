# Chapter 04: The Inquisitor

## What is the Inquisitor?

The Chaplain guards the gate before a commit enters the repository. But what about the commits that *get through*? Hooks can enforce format, lint code, and run tests — yet doctrine compliance requires deeper examination. Did the developer write a diary entry? Does the CHANGELOG reflect the new feature? Are requirement tags present on every test?

These are questions that can only be answered *after* the commit exists. The Inquisitor is YAMLGraph's post-commit auditor: an autonomous agent that examines recent work against the Scripture and records its findings in the project diary. Where the Chaplain is a bouncer — blocking entry at the door — the Inquisitor is an auditor, reviewing the books after the transaction is complete.

The Inquisitor doesn't prevent bad commits. It *witnesses* them. Its power lies not in rejection but in visibility: every deviation from doctrine is recorded, classified, and seeded with a forward-looking question. Over time, the audit trail itself becomes a pressure mechanism — recurring drift findings graduate into mechanical enforcement (new pre-commit hooks), closing the loop between observation and prevention.

---

## When It Runs

The Inquisitor is registered as a post-commit hook in `.pre-commit-config.yaml`:

> Source: `.pre-commit-config.yaml`, lines 173–181

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

Three properties define its behavior:

**`stages: [post-commit]`** — This is the critical distinction. While every other hook in the configuration runs at `pre-commit` or `commit-msg` stage (blocking the commit until they pass), the Inquisitor runs *after* the commit has already been recorded. The commit is done; the Inquisitor's job is to audit what just happened.

**`always_run: true`** — The Inquisitor fires on every commit, unconditionally. There is no file-pattern filter, no conditional trigger. Every commit is audited — even `docs:` commits, even trivial changes. As defined in `.chaplain/inquisitor.sh`: "If all findings are COMPLIANT, still record the audit — compliance is worth witnessing."

**`nohup ... &` (async execution)** — The entry command wraps the audit script in `nohup` and backgrounds it. This means the Inquisitor runs asynchronously — the developer's terminal returns immediately after the commit, and the audit proceeds in the background. Output is redirected to `.chaplain/inquisitor.log` so it never blocks the developer's workflow. The audit is thorough but invisible until you look for it.

This design reflects a deliberate philosophy: **pre-commit hooks should be fast and blocking; post-commit hooks should be thorough and non-blocking.** The Chaplain's pre-commit gates run unit tests in ~20 seconds and must all pass before the commit proceeds. The Inquisitor's audit involves an LLM agent reading multiple files, analyzing commit history, and writing a diary entry — work that could take 30–60 seconds. Running it asynchronously means the developer never waits for it.

---

## The Audit Process

The audit itself is defined in `.chaplain/inquisitor.sh` — a compact Bash script that delegates all reasoning to a Copilot agent via a structured prompt.

> Source: `.chaplain/inquisitor.sh`

### Step 1 — Gather Evidence

```
- Read the latest 5 commits: git log --oneline -5
- Read the top of CHANGELOG.md (first 30 lines)
- Read the latest diary entry in docs/diary.md (first entry after the header)
- Read CLAUDE.md to refresh the Scripture (Commandments, Sermon, Rite of Correction)
```

The agent starts by building context. It reads the five most recent commits to understand what changed, the CHANGELOG to check if changes are documented, the latest diary entry to verify the Distill step was performed, and the Scripture itself to know what rules to enforce. This is the "refresh the law before judging" pattern — the agent doesn't rely on a cached understanding of doctrine; it re-reads the source of truth every time.

### Step 2 — Investigate

For each recent commit, the agent checks six specific compliance criteria:

| Check | Doctrine Source | What It Verifies |
|-------|----------------|-----------------|
| Conventional Commits | Commandment 10 | Commit messages follow `type(scope): description` format |
| CHANGELOG entry | Commandment 10 | `feat`/`fix` commits have corresponding CHANGELOG entries |
| Requirement in ARCHITECTURE.md | ADR-001 | New capabilities have REQ-YG-XXX requirements defined |
| `@pytest.mark.req` tags | ADR-001 | New tests are linked to requirements |
| Diary entry | Sermon: Distill | Task completion includes metacognitive reflection |
| noqa confessions | noqa Confessions | Every `# noqa` suppression has a documented CONF-XXX entry |

These six checks map directly to the project's governance rules. They are not generic code quality checks — they are *doctrine-specific* audits that no standard linter or CI tool would catch.

### Step 3 — Judge

Each finding is classified into one of three severity levels:

- **✓ COMPLIANT** — Doctrine followed correctly. Recorded as positive evidence.
- **⚠ DRIFT** — Minor deviation with no immediate harm. Noted for tracking; may escalate to violation if it recurs.
- **✗ VIOLATION** — Doctrine explicitly broken. Action needed.

The three-tier classification is deliberately coarse. There's no "warning" vs "info" vs "suggestion" ambiguity. A finding either follows the law, drifts from it, or breaks it. This simplicity makes audit entries scannable and trends visible — when the same ⚠ DRIFT appears across five consecutive audits, it's obvious that the drift has become structural.

### Step 4 — Record

The agent appends a new entry to `docs/diary.md` with a fixed structure:

```markdown
## YYYY-MM-DD: Inquisitor Audit — [summary]

**Context:** What was audited and why

**Findings:**
- ✓/⚠/✗ items (max 5 most significant)

**Heuristic:** One actionable lesson extracted

**Seed:** One forward-looking question
```

The maximum of five findings forces the agent to prioritize. With six checks across five commits, there could be dozens of individual compliance points — but the diary entry captures only the most significant. This is an anti-entropy measure: the Inquisitor's own output is subject to the same brevity discipline that the Scripture demands of code.

The **Heuristic** and **Seed** fields transform the audit from a passive checklist into an active learning mechanism. Every audit produces a lesson and a question. Over time, these accumulate into a knowledge base of project-specific governance wisdom.

Critically, `docs/diary.md` is the *only* file the Inquisitor is permitted to modify:

> Source: `.chaplain/inquisitor.sh`, line 43

```
Do NOT create or modify any files other than docs/diary.md.
```

This constraint ensures the post-commit auditor can never accidentally break the codebase. It observes and records — nothing more.

---

## Sample Audit Entry

Here is a real Inquisitor audit entry from the project diary, demonstrating all four structural elements:

> Source: `docs/diary.md`, entry dated 2026-02-26

```markdown
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
```

### Anatomy of the Entry

**The Context** names the exact commit SHA, lists all five audited commits with their types and scopes, and states which doctrine sources were checked. This makes every audit reproducible — anyone can run `git log --oneline -5` from that SHA and verify the findings.

**The Findings** use the ✓/⚠/✗ classification consistently. Notice the mix: one violation, three compliant items, one drift. The compliant findings are recorded as positive evidence — they're not omitted just because nothing is wrong. The violation cites the specific commandment broken, names the exact commit and files involved, and describes the gap precisely.

**The Heuristic** distills the violation into a general principle: if a commit is worth `feat:`, it's worth a CHANGELOG line. This transforms a specific finding into reusable wisdom.

**The Seed** proposes a mechanical fix — a pre-commit hook that enforces CHANGELOG inclusion for `feat`/`fix` commits. This is the Inquisitor's most powerful pattern: *audit findings that propose their own prevention*. And indeed, examining `.pre-commit-config.yaml`, the `changelog-required` hook (lines 153–160) does exactly what this seed proposed:

```yaml
- id: changelog-required
  name: feat/fix commits require CHANGELOG.md
  entry: "bash -c 'msg=$(cat \"$1\"); if echo \"$msg\" | grep -qE
    \"^(feat|fix)(\\(.*\\))?:\" && ! git diff --cached --name-only
    | grep -qE \"^CHANGELOG\\.md$\"; then echo \"ERROR: feat:/fix:
    commits must include CHANGELOG.md changes\";
    echo \"Add your entry under the current [Unreleased] or version heading.\";
    exit 1; fi' _"
  language: system
  stages: [commit-msg]
  always_run: true
```

This is the feedback loop in action: the Inquisitor audits → finds a gap → seeds a question → the question becomes a hook → the hook prevents the gap mechanically. The post-commit auditor generates the requirements for pre-commit enforcement.

---

## The Drift Graduation Pattern

One of the most revealing patterns in the audit trail is **drift graduation** — when a ⚠ DRIFT finding recurs across enough audits to become recognized structural debt.

The Co-authored-by trailer provides a textbook example. Tracing the audit entries chronologically:

| Audit Date | Finding | Escalation |
|-----------|---------|-----------|
| 2026-02-25 (early) | ⚠ DRIFT — trailer missing | First observation |
| 2026-02-25 (mid) | ⚠ DRIFT — trailer missing | "Recurring accepted deviation" |
| 2026-02-25 (late) | ⚠ DRIFT — trailer missing | "Awaiting mechanical enforcement" |
| 2026-02-26 | ⚠ DRIFT — trailer missing | "6th+ audit flagging this" |

The Inquisitor doesn't escalate drift to violation automatically — that would create false urgency. Instead, it annotates each recurrence with increasing specificity: "recurring," "accepted deviation," "6th+ audit." This progressive annotation lets the team decide when to act. Some drift is acceptable indefinitely; some demands a hook.

As one audit heuristic noted:

> When the same drift is flagged across 5+ audits without resolution, the finding has graduated from observation to technical debt. Either apply the existing fix (`diary_rotate.py`) or accept the drift formally — repeated flagging without action is itself entropy.

---

## Relationship to the Chaplain

The Chaplain and the Inquisitor form a complementary pair — two halves of a governance loop that operates across the commit boundary:

```
┌──────────────────────────────────────────────────────────────┐
│                    The Commit Boundary                        │
│                                                              │
│  BEFORE                    │              AFTER               │
│  ─────                     │              ─────               │
│                            │                                  │
│  🛡️ Chaplain (pre-commit)  │   🔍 Inquisitor (post-commit)   │
│  Blocks bad commits        │   Audits what got through        │
│  Fast (~20s)               │   Thorough (~30-60s)             │
│  Synchronous (blocking)    │   Asynchronous (background)      │
│  Checks: syntax, format,   │   Checks: doctrine compliance,  │
│    tests, complexity,      │     traceability, diary entries, │
│    dead code, duplicates   │     CHANGELOG coverage           │
│  Verdict: pass/fail        │   Verdict: ✓/⚠/✗ per finding   │
│  Output: terminal          │   Output: docs/diary.md          │
│                            │                                  │
└──────────────────────────────────────────────────────────────┘
```

### What the Chaplain Catches

The Chaplain's pre-commit hooks (Chapter 02) are *mechanically verifiable* checks:

- Does the code pass `ruff` linting?
- Are unit tests green?
- Is cyclomatic complexity below grade D?
- Are there files over 450 lines?
- Does `vulture` find dead code?
- Does `jscpd` find duplicates?
- Are there forbidden terms (`TODO`, `FIXME`)?
- Does the commit message follow Conventional Commits?
- Do `feat` commits reference an FR-XXX?

These are binary questions — yes/no, pass/fail. They run fast because they operate on the staged diff, not on project history or semantic intent.

### What the Inquisitor Catches

The Inquisitor's checks require *contextual reasoning* that no static tool can perform:

- "This is a `feat` commit that adds a new capability — was a requirement added to ARCHITECTURE.md?"
- "Tests were added — do they all have `@pytest.mark.req` tags linking them to requirements?"
- "This task appears complete — was a diary entry written reflecting on the process?"
- "There's a new `# noqa` suppression — is it documented in confessions.md?"

These questions require reading multiple files, understanding commit intent, and applying judgment. They are inherently *semantic* checks — the kind that only an LLM agent can perform against a natural-language doctrine.

### The Feedback Loop

The most powerful aspect of this dual system is the feedback loop between them:

1. **Inquisitor finds a gap** — e.g., `feat` commits missing CHANGELOG entries
2. **Inquisitor seeds a question** — "Could a pre-commit hook enforce this?"
3. **Developer implements the hook** — `changelog-required` added to pre-commit config
4. **Chaplain now catches it mechanically** — the gap is closed before commit
5. **Inquisitor verifies compliance** — future audits show ✓ COMPLIANT for CHANGELOG

This is the doctrine's self-improvement mechanism. The Inquisitor identifies patterns that *should* be mechanical but aren't yet. Its seeds become the specifications for new pre-commit hooks. Over time, the Inquisitor's job gets easier — not because standards relax, but because more checks graduate from post-commit audit to pre-commit enforcement.

The Scripture encodes this principle:

> *"Thou shalt preserve and improve the doctrine — Every failure shalt refine the law. After correction, amend tests and linters to guard against recurrence; let success be codified, and let the CHANGELOG.md bear witness to the evolution of the Word."*
> — Commandment 10

The Inquisitor is Commandment 10 made operational. It is the mechanism by which failures refine the law.

---

## Summary

The Inquisitor completes the commit-time governance loop:

| Aspect | Detail |
|--------|--------|
| **What** | Post-commit auditor that examines recent work against the Scripture |
| **When** | After every commit, asynchronously in the background |
| **How** | LLM agent reads commits, CHANGELOG, diary, and doctrine; classifies findings |
| **Where** | Results appended to `docs/diary.md`; logs in `.chaplain/inquisitor.log` |
| **Classifications** | ✓ COMPLIANT, ⚠ DRIFT, ✗ VIOLATION |
| **Output structure** | Context → Findings → Heuristic → Seed |
| **Key constraint** | May only modify `docs/diary.md` — cannot break the codebase |
| **Feedback loop** | Audit findings seed new pre-commit hooks, graduating checks from audit to enforcement |

The Chaplain prevents what can be prevented mechanically. The Inquisitor witnesses what requires judgment. Together, they ensure that doctrine is not just written but *observed* — continuously, automatically, and with an ever-tightening feedback loop that turns audit findings into mechanical guards.

---

*Next: Chapter 05 explores the diary itself — the living document where Inquisitor findings, development reflections, and metacognitive seeds accumulate into a knowledge base that shapes the project's evolution.*
