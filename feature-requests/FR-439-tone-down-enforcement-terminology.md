# Feature Request: FR-439 Tone Down Enforcement Terminology

**Priority:** MEDIUM
**Type:** Refactor (documentation + naming)
**Status:** Enforced
**Effort:** 0.5 day
**Requested:** 2026-05-21
**Judged:** 2026-05-21
**Enforced:** 2026-05-21

## Summary

Rename three enforcement artifacts whose current names import strong historical and literary baggage (totalitarian surveillance, mass extermination, religious sacrament) that is disproportionate to their technical function: **Thoughtcrime / Thought Police**, **Order 66**, and **Absolution**. Replace with descriptive, register-neutral names. No behavioural change.

## Value Statement

Operators and contributors gain an enforcement layer whose names match what the code does, removing in-jokes that (a) signal a stance the project may not want to hold publicly, (b) mix incompatible mythologies (Orwell + Star Wars + Christian liturgy) within a single workflow, and (c) raise the cost of onboarding for contributors who do not share the reference set.

## Problem

The current enforcement layer is technically disciplined but stylistically maximalist. Three names in particular carry historical referents whose moral valence is heavier than the engineering function they label:

| Current name | Historical referent | Technical function |
|---|---|---|
| **Thoughtcrime / Thought Police** ([FR-438](FR-438-thoughtcrime-hook.md), [thoughtcrime-scan.sh](../.github/hooks/scripts/thoughtcrime-scan.sh), [thoughtcrimes.json](../.github/hooks/scripts/thoughtcrimes.json)) | *1984* — state surveillance of private cognition, punished by Ministry of Love | Substring scan of the agent's `reasoningText` for two forbidden phrases; arms a one-shot deny |
| **Order 66** ([pre-command-guard.sh](../.github/hooks/scripts/pre-command-guard.sh), `cmd lockdown` / `unlock` / `status`) | *Star Wars* — clone troopers' mass extermination of their Jedi commanders on signal | Lockdown sentinel file that blocks all tool calls until manually cleared |
| **Absolution** ([scripts/absolution.py](../scripts/absolution.py)) | Christian sacrament of confession and forgiveness of sin | Final pre-commit hook prints "all checks passed" + diary reminder |

Concrete consequences:

1. **Aesthetic capture risk.** When the framing register is this strong, new additions get evaluated for fit with the register ("does it sound Scripture-like?") rather than on engineering merit. The doctrine itself names this trap as `audit_as_ritual`.
2. **Mixed metaphors cancel.** Christian liturgy (Scripture, Sermon, Absolution), Orwellian surveillance (Thoughtcrime, Thought Police), and Imperial command authority (Order 66) carry incompatible moral valences. The reader cannot tell whether the framing is satire, earnest belief, or stylistic flourish.
3. **Public-facing optics.** "Order 66" as the name for a kill-switch that disables an AI collaborator is on-the-nose in a way that is hard to defend in code review outside this repo. Same for `thoughtcrime` as a label for cognition surveillance.
4. **Coupling craft to cult.** The engineering doctrine (boundary normalization, callsite fix, trap → cure registry) is genuinely portable; the liturgical wrapping is not. Today they cannot be adopted separately.

## Research

### Audit of affected surface

Grep targets (to be enumerated during implementation):

```bash
grep -rniE 'thoughtcrime|thought.police|order.?66|absolution' \
  .github/ scripts/ feature-requests/ docs/ reference/ CLAUDE.md README.md \
  --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yaml'
```

Expected hit clusters:
- `.github/hooks/scripts/thoughtcrime-scan.sh`, `thoughtcrimes.json`, `pre-command-guard.sh` (sentinel filename, audit log `reason` field, deny message)
- `.github/hooks/thoughtcrime-scan.json` (hook registration filename)
- `.github/hooks/tests/` (test file names + fixture content)
- `scripts/absolution.py` + pre-commit hook id `absolution`
- `feature-requests/FR-438-*.md` (defining doc — kept as historical record but cross-referenced from this FR)
- `.github/copilot-instructions.md` (no direct uses of these three terms in the audited section, but verify)
- `docs/diary/` (historical reflections — not retroactively renamed)

### Naming proposals

| Old | Proposed | Rationale |
|---|---|---|
| `thoughtcrime-scan.sh` | `reasoning-pattern-check.sh` | Says what it does: scans reasoning text for configured patterns |
| `thoughtcrimes.json` | `reasoning-patterns.json` | Registry of patterns, not "crimes" |
| `.thoughtcrime-<sid>` sentinel | `.reasoning-flag-<sid>` | Neutral; preserves one-shot semantics |
| Deny message header `✗ THOUGHTCRIME DETECTED` | `⚠ Reasoning pattern flagged` | Advisory tone consistent with one-shot, non-lockdown behaviour |
| `cmd lockdown` / `Order 66` | `cmd lockdown` (kept) / drop "Order 66" framing in messages | The command name is already neutral; only the message text and comments reference Order 66 |
| Audit reasons `order66-lockdown`, `order66-unlock`, `order66-status`, `order66-unknown` | `lockdown-set`, `lockdown-clear`, `lockdown-status`, `lockdown-unknown` | Descriptive |
| `absolution.py` + hook id `absolution` | `final-summary.py` + hook id `final-summary` | Prints final summary + diary reminder. No sacrament implied. |

### Out of scope (deliberately)

- **The wider liturgical register** (Scripture, Sermon, Chaplain, Inquisitor, Rite of Correction, Agents' prayer, "What survives the fire may merge") is **not** in scope for this FR. Those terms are pervasive across docs, FSM runtime, and external repos. A separate FR may address the broader register later; this one targets only the three artifacts whose names import the heaviest historical baggage and whose blast radius is small.
- `FR-438` text is preserved as the historical record of the original intent and the discussion that preceded the rename.
- `docs/diary/` entries are historical and not rewritten.

## Proposed Solution

### Phase 1: Rename hook artifacts (mechanical)

1. `git mv .github/hooks/scripts/thoughtcrime-scan.sh .github/hooks/scripts/reasoning-pattern-check.sh`
2. `git mv .github/hooks/scripts/thoughtcrimes.json .github/hooks/scripts/reasoning-patterns.json`
3. `git mv .github/hooks/thoughtcrime-scan.json .github/hooks/reasoning-pattern-check.json`
4. `git mv scripts/absolution.py scripts/final_summary.py`
5. Update hook registration JSON to point at new script paths.
6. Update `.pre-commit-config.yaml` hook id `absolution` → `final-summary` and `entry` path.

### Phase 2: Update sentinel filename + audit log keys

- Sentinel: `.thoughtcrime-<session_id>` → `.reasoning-flag-<session_id>`
- Audit log `hook` field: `"thoughtcrime-scan"` → `"reasoning-pattern-check"`
- Audit log `reason` field: `"thoughtcrime"` → `"reasoning-pattern"`
- Audit log `reason` field: `"order66-*"` → `"lockdown-*"`

Note: This is a **breaking change** for any existing armed sentinel file format and for log consumers grepping on these keys. Since sentinels are one-shot session-scoped and gitignored, and the audit log is local/append-only, the breakage is contained.

### Phase 3: Update deny message text

- Replace `✗ THOUGHTCRIME DETECTED` block with `⚠ Reasoning pattern flagged` block. Keep the doctrine excerpt and one-shot semantics.
- Remove `"Welcome to 1984"` and `"the Thought Police are watching"` lines from [FR-438](FR-438-thoughtcrime-hook.md) deny-message examples (the FR document itself stays as historical record but its example messages are updated to match shipped behaviour).
- Remove the `ORDER 66 EXECUTED` and `Order 66` references in `pre-command-guard.sh` deny messages and code comments. The `cmd lockdown` channel name itself is descriptive and stays.

### Phase 4: Cross-references

- Update [.github/copilot-instructions.md](../.github/copilot-instructions.md) if it references any of the renamed artifacts (audit during implementation).
- Update [.github/hooks/README.md](../.github/hooks/README.md).
- Add a short note in [FR-438](FR-438-thoughtcrime-hook.md) header: `**See also: FR-439 (renamed to reasoning-pattern-check).**`

## Acceptance Criteria

- [ ] `.github/hooks/scripts/thoughtcrime-scan.sh` and `thoughtcrimes.json` renamed; hook registration updated; hook still fires on the same input.
- [ ] `scripts/absolution.py` renamed to `scripts/final_summary.py`; `.pre-commit-config.yaml` hook id and entry updated; final summary still prints on successful pre-commit run.
- [ ] Sentinel filename pattern updated to `.reasoning-flag-<session_id>`; `pre-command-guard.sh` consumes the new name.
- [ ] Audit log `hook` / `reason` field values updated to neutral names; existing `audit.jsonl` entries are preserved (not rewritten).
- [ ] Deny messages no longer contain `THOUGHTCRIME`, `Thought Police`, `Order 66`, or `1984` references.
- [ ] Code comments in `pre-command-guard.sh`, `reasoning-pattern-check.sh` updated to descriptive language.
- [ ] Existing tests under `.github/hooks/tests/` pass (rename test fixtures as needed).
- [ ] Grep across `.github/`, `scripts/`, `reference/`, `README.md`, `CLAUDE.md`, `.github/copilot-instructions.md` returns no remaining occurrences of `thoughtcrime`, `thought police`, `order 66`, or `absolution` outside the historical FR-438 record.
- [ ] [FR-438](FR-438-thoughtcrime-hook.md) header annotated with cross-reference to this FR.
- [ ] Diary reflection committed in the same PR documenting why the rename was undertaken (aesthetic-capture trap surfaced during literary review).

## Alternatives Considered

### 1. Keep names; document the irony

Leave the artifacts as-is and add a `STYLE.md` explaining that the names are knowing references. **Rejected:** documentation of an in-joke does not remove its cost for readers who land on the code first and the doc second. The names are the user interface.

### 2. Rename only `thoughtcrime`; keep `Order 66` and `Absolution`

Narrower scope. **Rejected:** the three artifacts share a single failure mode (mixed mythological registers signalling distrust at high amplitude). Renaming one leaves the others as residual signal. The combined surface is small enough to do together.

### 3. Wholesale rewrite of the liturgical register

Strip Scripture, Sermon, Chaplain, Inquisitor, Agents' prayer, etc. **Rejected for this FR** as out of scope: those terms are pervasive across docs, FSM runtime, capabilities, and dependent projects, and their removal is a separate, larger decision. This FR addresses only the three artifacts whose names import the heaviest baggage and whose blast radius is bounded to a few files.

### 4. Add a `--snark` flag that toggles between neutral and current names

Cosmetic configurability. **Rejected:** doubles maintenance surface for zero engineering benefit.

## Related

- [FR-438](FR-438-thoughtcrime-hook.md): Defining FR for the reasoning pattern hook (kept as historical record; renamed implementation supersedes its examples)
- [.github/copilot-instructions.md](../.github/copilot-instructions.md): Doctrine that establishes the wider register (out of scope here)
- [.github/hooks/scripts/pre-command-guard.sh](../.github/hooks/scripts/pre-command-guard.sh): Hosts the `cmd lockdown` channel and the sentinel consumer
- [scripts/absolution.py](../scripts/absolution.py): Final pre-commit summary hook

## Notes

This FR responds to a literary/psychological review of the enforcement layer that identified the three named artifacts as the highest-cost / lowest-engineering-value framing choices in the current corpus. The technical doctrine (boundary normalization, callsite fix, trap → cure registry) is not affected and is, in the reviewer's reading, the part of the system worth preserving and propagating. The rename is intended to make that propagation easier by decoupling the engineering substrate from a stylistic register that is unlikely to travel well outside this repo.

---

## Judgement (2026-05-21)

**Verdict: Approved. Scope frozen with the additions below. Authority granted to proceed.**

### Premise check (Red Hat)

The pain is real and is named correctly by the FR: three artifacts mix Orwellian, Imperial, and Christian registers within one workflow, and their names exceed their engineering function. The `audit_as_ritual` trap is already in the Scripture; this FR applies the same hygiene to the enforcement layer itself. The deliberate decision to *not* rewrite the wider register (Scripture, Sermon, Chaplain, Inquisitor) is correct — that surface is large, has external coupling, and warrants a separate decision. Scope discipline is good.

### Internal consistency

The four phases are coherent and the acceptance criteria map 1:1 to them. The "breaking change" callout for sentinel filename + audit log keys is honest and the bounded-blast-radius argument (session-scoped, gitignored, append-only local log) holds.

### Audit gaps to close before "no remaining occurrences" can be true

Grep across in-scope surface (excluding `feature-requests/` and `docs/diary/`, which are explicitly out of scope) surfaced four call sites the FR does not enumerate. The acceptance grep will fail without them:

1. **`scripts/block_ai_coauthor.py:28`** — user-facing message text: `"Delete the trailer. Recommit. Absolution follows."` → reword (e.g. `"Delete the trailer. Recommit."`).
2. **`docs/ebook/v3/02-precommit-gates.md`** — ~10 references to `absolution` / `Absolution granted` (table row, section heading, code samples, pipeline-summary samples on lines 66, 78, 80, 82, 84, 88, 90, 104, 331, 344, 347, 378). Must be rewritten to `final-summary` / "Final summary OK" (or similar) to keep the ebook consistent with shipped behaviour.
3. **`.github/hooks/logs/.gitignore`** — pattern `.thoughtcrime-*` must be updated to `.reasoning-flag-*` (or both kept transiently; recommend straight replacement since sentinels are ephemeral).
4. **`docs/final_judgment.md:26`** — single occurrence `"Absolution granted."` → rewrite or remove.

### Test rename made explicit

Phase 1 already implies it, but to satisfy the final grep:
- `git mv .github/hooks/tests/test_thoughtcrime.py .github/hooks/tests/test_reasoning_pattern_check.py`
- Update fixtures and any string assertions that match the old deny-message text or `reason="thoughtcrime"`.

### Pre-commit hook id rename — caveat

Renaming the `absolution` pre-commit hook id is a local-config breakage: any developer with cached `.git/hooks/` state or an in-flight `pre-commit` env will need `pre-commit clean && pre-commit install` after pulling. Add a one-line CHANGELOG/release-notes mention so this isn't a silent surprise. Not a blocker.

### "Order 66" residue

The FR correctly keeps the `cmd lockdown` channel name (already neutral) and only strips the "Order 66" framing from messages and comments. Verify the audit-log keys rename (`order66-*` → `lockdown-*`) is applied at all four sites in `pre-command-guard.sh` (lines 76, 82, 109, 114, 137, 141 per grep — six total including comments). The acceptance grep will catch this; calling it out so it's not missed.

### Added acceptance criteria (binding)

- [ ] `scripts/block_ai_coauthor.py` no longer contains "Absolution" in user-facing strings.
- [ ] `docs/ebook/v3/02-precommit-gates.md` rewritten to use the new hook name; sample outputs updated to match new final-summary text.
- [ ] `.github/hooks/logs/.gitignore` updated to track the new sentinel pattern (`.reasoning-flag-*`); old pattern removed.
- [ ] `docs/final_judgment.md` reference removed or rewritten.
- [ ] `.github/hooks/tests/test_thoughtcrime.py` renamed and its assertions updated.
- [ ] Release notes / changelog fragment mentions the `absolution` → `final-summary` pre-commit id rename and the `pre-commit clean && pre-commit install` step for existing checkouts.

### Out of scope (re-confirmed, do not expand)

- The wider liturgical register (Scripture, Sermon, Chaplain, Inquisitor, Rite of Correction, Agents' prayer, "What survives the fire may merge"). Separate FR if pursued.
- `feature-requests/FR-438-*.md` body text (header cross-reference only, per FR Phase 4).
- `docs/diary/` historical entries (preserved as-written).
- Existing `.github/hooks/logs/audit.jsonl` entries (not rewritten; only new entries use the new keys).

### Scope frozen

Proceed to Enforce. Write the failing tests first (assertion on new deny-message text, new audit-log keys, new sentinel filename, new hook id in `.pre-commit-config.yaml`), then execute the four phases plus the six added acceptance criteria. Final grep must return zero hits across the in-scope surface for `thoughtcrime|thought.police|order.?66|absolution`, excluding `feature-requests/FR-438*`, `feature-requests/FR-439*`, `docs/diary/`, and `.github/hooks/logs/audit.jsonl`.
