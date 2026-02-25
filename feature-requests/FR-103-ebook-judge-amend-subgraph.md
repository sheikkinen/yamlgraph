# Feature Request: FR-103 eBook Pipeline — Judge-Amend Subgraph

**Priority:** HIGH
**Type:** Redesign
**Status:** Enforced
**Requested:** 2026-02-25
**Enforced:** 2026-02-25
**Depends-on:** FR-100
**Supersedes:** FR-101, FR-102

## Problem

FR-100 pipeline produced 9/10 fabricated Commandments in Ch01. Root causes:
1. **research→write split** lost fidelity (summaries, not verbatim quotes)
2. **Book-level judge** detected errors too late to fix efficiently

## Solution

**Merge nodes + per-chapter judge-amend subgraph**

```
write_<chapter> (copilot) → validate (subgraph) → persist (tool)
```

**Key insight:** Chapter content includes inline citations (`As defined in \`file\`:`). Judge extracts file paths from content — no separate source_files param needed.

## Graph: 18 main nodes + 2 subgraph nodes

```yaml
# Main graph (per chapter ×6)
write_doctrine → validate_doctrine → persist_doctrine

# validate_chapter subgraph
judge (copilot) → amend (copilot, conditional)
```

## Subgraph Interface

```yaml
input:
  chapter: str  # Contains inline file citations

output:
  chapter: str           # Original or amended
  validation_passed: bool
```

## Chapter Prompt Pattern

```yaml
user: |
  ## Files to Read
  1. `.github/copilot-instructions.md` — Primary source

  ## Citation Format
  Include file references inline. Example:
  > As defined in `.github/copilot-instructions.md`:
  >
  > **1. Thou shalt research before coding**

  Quote doctrine VERBATIM within > block quotes.
```

## Judge Prompt (extracts citations)

```yaml
user: |
  ## Chapter
  {chapter}

  ## Process
  1. Find file citations (backticked paths)
  2. Read each cited file
  3. Verify quotes match source EXACTLY

schema:
  name: ChapterJudgment
  fields:
    passed: {type: bool}
    issues: {type: list[str]}
    files_verified: {type: list[str]}
```

## Acceptance Criteria

- [ ] 6 merged chapter prompts in `prompts/chapter/`
- [ ] `subgraphs/validate_chapter.yaml` with judge→amend flow
- [ ] `prompts/judge/chapter.yaml` + `prompts/amend/chapter.yaml`
- [ ] Ch01 Doctrine test: all 10 Commandments verbatim
- [ ] Delete `prompts/source/` and `prompts/write/`

## Implementation (~2h)

| Phase | Time | Action |
|-------|------|--------|
| 1 | 30min | Create validate subgraph + judge/amend prompts |
| 2 | 45min | Create 6 merged chapter prompts |
| 3 | 30min | Rewire graph.yaml |
| 4 | 15min | Test Ch01, full run |

## Files

| File | Action |
|------|--------|
| `subgraphs/validate_chapter.yaml` | CREATE |
| `prompts/judge/chapter.yaml` | CREATE |
| `prompts/amend/chapter.yaml` | CREATE |
| `prompts/chapter/*.yaml` | CREATE (6) |
| `prompts/source/` | DELETE |
| `prompts/write/` | DELETE |
| `graph.yaml` | REWRITE |
