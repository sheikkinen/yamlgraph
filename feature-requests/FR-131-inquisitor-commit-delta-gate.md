# Feature Request: Inquisitor commit-delta gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-07

## Summary

Add a pre-flight gate to `inquisitor.sh` that aborts when no `feat:` or `fix:` commits exist since the last audit, breaking the ritual loop documented in Audits XI–XIII.

## Value Statement

The Inquisitor stops wasting ~1,700 words per audit cycle on identical findings when no actionable code has changed, reclaiming time for actual fixes.

## Problem

The Inquisitor can be invoked repeatedly against the same commit window, producing identical findings. Audits V–XIII documented the same 3 violations (ARCHITECTURE.md provider count, FR-112 status, FR-116 CHANGELOG) across 8+ consecutive audits without resolution. Audit XII concluded: *"The Inquisitor is now the ritual it was designed to detect."* Audit XIII formally recused itself.

This violates the `audit_as_ritual` trap from the Knowledge Graph:

```yaml
audit_as_ritual: "3+ audits without fix → ritual, not process"
audit_gate: "Audit without blocking mechanism = post-mortem before incident"
```

**Root cause:** No structural gate prevents invocation when there is nothing new to audit. The Inquisitor relies on its own diary heuristics to self-limit, but heuristics are advisory — not enforcement.

## Proposed Solution

Add a shell pre-check to `inquisitor.sh` (before the audit copilot call) that:

1. Extracts the last audit's commit range endpoint from `docs/diary.md`
2. Counts `feat:` or `fix:` commits since that SHA
3. Aborts with a clear message if none found
4. Proceeds normally if actionable commits exist

```bash
# --- Commit-delta gate ---
LAST_SHA=$(grep -oP '(?<=\.\.)`?\K[a-f0-9]{7,}' docs/diary.md | head -1)
if [[ -n "$LAST_SHA" ]]; then
    ACTIONABLE=$(git log --oneline "$LAST_SHA"..HEAD | grep -cE '^[a-f0-9]+ (feat|fix)' || true)
    if [[ "$ACTIONABLE" -eq 0 && -z "$FORCE" ]]; then
        echo "⏭️  Inquisitor: No feat/fix commits since last audit ($LAST_SHA..HEAD). Nothing to audit."
        echo "   Use --force to override."
        exit 0
    fi
fi
```

### Flag changes

| Flag | Behavior |
|------|----------|
| (none) | Audit with commit-delta gate |
| `--force` | Bypass gate, run audit unconditionally |
| `--propose` | Run audit + propose (gate still applies) |
| `--force --propose` | Bypass gate, run audit + propose |

### Implementation detail

The gate parses the commit range from the diary header format:

```
## YYYY-MM-DD: Inquisitor Audit N — ...
**Context:** Nth audit covering commits `abc1234`..`def5678` (...)
```

It extracts the second SHA (the HEAD at time of last audit) and checks `git log --oneline <sha>..HEAD` for `feat:` or `fix:` prefixes.

**Edge cases:**
- No diary entries yet → gate skipped (first audit always runs)
- SHA not found in diary → gate skipped (degrade gracefully)
- `--force` → gate skipped explicitly
- Detached HEAD / shallow clone → `git log` still works; SHA resolution may fail → gate skipped

## Acceptance Criteria

- [ ] `inquisitor.sh` refuses to run when no `feat:` or `fix:` commits exist since last audit SHA
- [ ] Exit message clearly states the reason and how to override
- [ ] `--force` flag bypasses the gate unconditionally
- [ ] `--propose` respects the gate (no propose without audit)
- [ ] `--force --propose` bypasses gate and runs both
- [ ] Gate degrades gracefully: missing diary, unparseable SHA, first-ever audit all proceed
- [ ] Gate logic is pure shell (no Python, no copilot call)
- [ ] Tests: `tests/unit/test_inquisitor_gate.sh` (or pytest shim) validates gate behavior
- [ ] Documentation: Gate behavior documented in `inquisitor.sh` header comments

## Alternatives Considered

1. **Copilot-based gate (prompt instructs LLM to check commits first):** Rejected — wastes an API call to determine there's nothing to do. A shell pre-check is cheaper and deterministic.

2. **Timestamp-based gate (audit at most once per hour):** Rejected — time-based gates don't correlate with actual work. A developer could land 10 commits in 5 minutes or none in 3 hours.

3. **Lock file (`.chaplain/inquisitor.lock` with last SHA):** Considered — simpler than diary parsing, but introduces a new artifact to manage and gitignore. The diary already contains the information; parsing it keeps the system self-documenting.

4. **Count-based gate (require N commits, not just feat/fix):** Rejected — `docs:` and `chore:` commits don't introduce auditable changes. Only `feat:` and `fix:` commits modify behavior that the Inquisitor's 6-point checklist can evaluate.

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Evaluation:**

1. **Scope:** Clear and minimal — ~15 lines of shell gate logic before existing copilot call. No changes to audit or propose logic.
2. **Contradictions:** None. All flags compose correctly (`--force`, `--propose`, both).
3. **Acceptance criteria:** All 9 criteria are binary, testable, and unambiguous.
4. **Feasibility:** Confirmed — diary format stable across 24+ audits, regex target consistent, flag infrastructure exists from FR-118.
5. **Architecture alignment:** Follows thin-shell pattern from FR-076, addresses documented `audit_as_ritual` trap and `audit_gate` cure from Knowledge Graph.

**Implementation notes:**
- The proposed `grep -oP` (PCRE) doesn't work on macOS default grep. Use `sed` or `awk` for the SHA extraction instead.
- Flag parsing needs a proper loop (current script only checks `$1`); use `while`/`shift` or `getopts` to support `--force [--propose]` in any order.
- `refactor:` commit exclusion is a reasonable judgment call; `--force` provides the escape hatch.

## Related

- **FR-076** (`feature-requests/FR-076-chaplain-inquisitor.md`): Inquisitor design — this FR extends its invocation logic
- **FR-118** (`feature-requests/FR-118-inquisitor-auto-propose.md`): `--propose` flag — gate must compose with it
- **FR-126** (`feature-requests/FR-126-inquisitor-propose-verify-resolution.md`): Propose verification — complementary (prevents stale proposals; this FR prevents stale audits)
- **Audit XII** (`docs/diary.md`): Origin of the commit-delta gate proposal
- **Audit XIII** (`docs/diary.md`): Formal self-recusal citing absence of gate
- **Knowledge Graph** (`CLAUDE.md`): `audit_as_ritual` trap, `audit_gate` cure
