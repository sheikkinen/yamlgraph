# Feature Request: Chaplain CLI — Plan → Judge Loop for Research Subjects

**FR-055**
**Priority:** HIGH
**Type:** Feature
**Status:** Implementing
**Effort:** 0.5 days
**Requested:** 2026-02-20

## Summary

A shell script that takes a list of research subjects and, for each one, runs a `copilot -p` plan → judge → amend loop. Research and brainstorming happen separately (human + AI). The script automates the mechanical part: writing FRs and critically judging them.

## Pipeline

```
┌─────────────────────────────┐
│  You & Me (interactive)     │
│  Research, brainstorm,      │
│  discuss ideas              │
│                             │
│  Output: subjects.md        │
│    - subject 1              │
│    - subject 2              │
│    - subject 3              │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  scripts/chaplain.sh subjects.md            │
│                                             │
│  For each subject:                          │
│    1. copilot -p PLAN  → draft FR           │
│    2. copilot -p JUDGE → verdict            │
│    3. If AMEND: copilot -p AMEND, goto 2    │
│    4. Max 3 judge cycles                    │
│                                             │
│  Output: feature-requests/draft-*.md        │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  You & Me (interactive)                     │
│  Review judged FRs, approve/reject/refine   │
└─────────────────────────────────────────────┘
```

## Usage

```bash
# Create subjects file
cat > .chaplain/subjects.md << 'EOF'
- Copilot CLI as post-build reflection trigger
- Map node timeout per-item
- YAML prompt inheritance (base + override)
EOF

# Run the chaplain
scripts/chaplain.sh .chaplain/subjects.md

# With options
scripts/chaplain.sh .chaplain/subjects.md --model claude-opus-4.6 --dry-run
```

## Acceptance Criteria

- [x] `scripts/chaplain.sh` reads subjects from a file (one per line, `- ` prefix stripped)
- [x] For each subject: invokes `copilot -p` with plan prompt
- [x] For each draft: invokes `copilot -p` with judge prompt
- [x] If judge says AMEND: invokes `copilot -p` with amend prompt, re-judges (max 3 cycles)
- [x] Draft FRs written to `feature-requests/draft-*.md`
- [x] `--dry-run` prints prompts without invoking copilot
- [x] `--model` overrides default model
- [x] Timeouts on all copilot invocations

## Design Decisions

- **No graph integration** — research is interactive, not automated
- **Separate sessions per phase** — plan and judge are independent copilot invocations
- **Different models** — planner uses sonnet (creative), judge uses opus (critical)
- **No auto-commit** — human reviews everything
- **Prompts as files** — `scripts/chaplain-prompts/` for easy iteration

## Related

- FR-054: Copilot CLI reflection (proved `copilot -p` loads Scripture)
- `.github/copilot-instructions.md` §Sermon of the Chaplain
- `examples/demos/reflexion/` — draft→critique→refine pattern
