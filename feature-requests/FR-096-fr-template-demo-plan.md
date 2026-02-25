# Feature Request: Require Demo Plan in Feature Request Template

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-02-25

## Summary

Add a mandatory **Demo Plan** section to `feature-requests/TEMPLATE.md` so every feature ships with a planned demonstration. This makes demos a first-class deliverable rather than an afterthought.

## Value Statement

Users and maintainers discover new features through compelling, pre-planned demos rather than code spelunking, turning every feature into an adoption asset.

## Problem

Feature requests define specifications but not demonstrations. After implementation:

1. **No canonical example** — features ship without a working demo in `examples/demos/`.
2. **Discovery friction** — users learn about features by reading source code, not running examples.
3. **Unrealized marketing value** — compelling stories like novel_generator's "4000→80 lines" reduction are accidents, not planned outcomes.

Pattern observation: the best-adopted features (novel_generator, booking, cost-router) all have compelling demos. Features without demos have higher adoption friction. The gap is structural — nothing in the process requires demo planning.

## Proposed Solution

### 1. Template change

Add a **Demo Plan** section to `feature-requests/TEMPLATE.md` between Acceptance Criteria and Alternatives Considered:

```markdown
## Demo Plan

**Location**: `examples/demos/<feature>/` or enhancement to existing demo
**Showcase**: What capability is demonstrated
**Before/After**: If replacing a manual approach, show the comparison
**Marketing Angle**: One-liner suitable for README/changelog
```

### 2. Acceptance criteria update

Add to the template's default acceptance criteria checklist:

```markdown
- [ ] Demo implemented per Demo Plan
```

### 3. Examples of good demos

| Feature | Demo | Marketing Angle |
|---------|------|-----------------|
| Map node | `novel_generator` | Parallel prose generation |
| Router | `cost-router` | Model selection by complexity |
| Agent | `booking` | Tool-calling with human loop |

### Anti-pattern this prevents

Feature merged → Example added as afterthought → Half-baked demo → Users confused.

## Acceptance Criteria

- [ ] `feature-requests/TEMPLATE.md` contains a `## Demo Plan` section with Location, Showcase, Before/After, and Marketing Angle fields
- [ ] Template's default acceptance criteria checklist includes a demo implementation item
- [ ] `## Demo Plan` section is positioned between Acceptance Criteria and Alternatives Considered
- [ ] Documentation in both `reference/getting-started.md` and `CLAUDE.md` updated to mention demo planning as part of the FR workflow
- [ ] Existing feature requests are NOT retroactively modified (template-only change)

## Demo Plan

**Location**: Enhancement to `feature-requests/TEMPLATE.md` (no standalone demo needed — the template itself is the artifact)
**Showcase**: The new Demo Plan section visible in the template, with inline guidance comments
**Before/After**: Template without demo section → Template with mandatory Demo Plan section
**Marketing Angle**: Every feature ships with a planned demo — no more afterthought examples

## Future Work

**FR linter enforcement**: A future `scripts/fr_lint.py` (or pre-commit hook) should check that feature-type FRs contain a `## Demo Plan` heading. Bug-type FRs would be exempt. This is deliberately deferred — establish the habit before automating the gate.

## Alternatives Considered

**Make demos optional with a nudge** — Add the section as a comment (`<!-- Demo Plan: ... -->`) that authors can delete. Rejected because optional sections get skipped; the whole point is to make demo planning a first-class part of the process.

**Require demo before merge (enforcement only)** — Add a CI check that every FR-linked PR includes changes under `examples/demos/`. Rejected because: (a) not all features need a new demo directory — some enhance existing demos; (b) enforcement without a planning section means demos are still afterthoughts; (c) premature — we should establish the habit before automating the gate.

**Separate demo request template** — Create a second template for demo planning. Rejected because it splits a single concern across two documents, increasing overhead and reducing compliance.

## Related

- `feature-requests/TEMPLATE.md`: The template to be modified
- `examples/demos/`: Existing demo directory (24+ demos)
- `examples/demos/demo.sh`: Demo runner script
- FR-095: Doc staleness monitor (complementary — monitors existing docs, this ensures new demos are planned)
- `.chaplain/inquisitor.sh`: Post-commit audit (could eventually validate demo presence)
