# Feature Request: Fix Changelog Fragment REQ Cross-Wiring

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-19

## Summary

Four changelog fragments in `changelog/unreleased/` have incorrect `req:` values in YAML front matter and body text, mapping features to unrelated requirements. This breaks the traceability chain ARCHITECTURE.md → changelog → feature request.

## Value Statement

Maintainers get accurate requirement traceability in the generated CHANGELOG, preventing misleading audit trails and broken `req_coverage.py` cross-references.

## Problem

Copy-paste during batch enforcement sessions and partial renumber operations left 4 changelog fragments pointing to wrong requirements. The Inquisitor flagged this across audits 171–180 (7+ cycles unfixed).

Specific cross-wiring (verified against ARCHITECTURE.md capability table):

| Fragment | Current `req:` | Correct `req:` | Reason |
|---|---|---|---|
| `fr-032-node-level-caching.md` | REQ-YG-032 (CLI entry point) | REQ-YG-239 (node-level caching) | CAP-100 → REQ-YG-239 |
| `fr-234-parallel-fan-out-edges.md` | REQ-YG-235 (voice clone) | REQ-YG-237 (fan-out edges) | CAP-95 → REQ-YG-237 |
| `fr-235-compile-time-pipeline-templates.md` | REQ-YG-235 (voice clone) | REQ-YG-236 (pipeline templates) | CAP-94 → REQ-YG-236 |
| `fr-237-chatterbox-consolidate-and-cli.md` | REQ-YG-235 only | REQ-YG-235, REQ-YG-238 | Body references both but front matter missing REQ-YG-238 |

(`fr-236-chatterbox-voice-clone-demo.md` audited and confirmed correct — REQ-YG-235.)

Body text `(REQ-YG-XXX)` parenthetical references are also wrong in 3 of 4 fragments:

| Fragment | Current body REQ | Correct body REQ |
|---|---|---|
| `fr-032-node-level-caching.md` | `(REQ-YG-032)` | `(REQ-YG-239)` |
| `fr-234-parallel-fan-out-edges.md` | `(REQ-YG-235)` | `(REQ-YG-237)` |
| `fr-235-compile-time-pipeline-templates.md` | `(REQ-YG-235)` | `(REQ-YG-236)` |
| `fr-237-chatterbox-consolidate-and-cli.md` | ✅ Already correct | — |

## Proposed Solution

Edit YAML front matter `req:` field and body text `(REQ-YG-XXX)` in each of the 4 affected fragments. No structural changes, no new files, no code changes.

### Target state

```yaml
# fr-032-node-level-caching.md
---
type: feat
scope: graph
req: REQ-YG-239
---
- **FR-032 Node-Level Caching**: ... (REQ-YG-239)
```

```yaml
# fr-234-parallel-fan-out-edges.md
---
type: feat
scope: graph
req: REQ-YG-237
---
- **FR-234 Parallel Fan-Out Edges**: ... (REQ-YG-237)
```

```yaml
# fr-235-compile-time-pipeline-templates.md
---
type: feat
scope: graph
req: REQ-YG-236
---
- **FR-235 Compile-Time Pipeline Templates**: ... (REQ-YG-236)
```

```yaml
# fr-237-chatterbox-consolidate-and-cli.md
---
type: feat
scope: demos
req: REQ-YG-235, REQ-YG-238
---
- **FR-237 Chatterbox Consolidation**: ... (REQ-YG-235, REQ-YG-238)
```

## Acceptance Criteria

- [ ] `fr-032-node-level-caching.md` front matter `req: REQ-YG-239` AND body text `(REQ-YG-239)`
- [ ] `fr-234-parallel-fan-out-edges.md` front matter `req: REQ-YG-237` AND body text `(REQ-YG-237)`
- [ ] `fr-235-compile-time-pipeline-templates.md` front matter `req: REQ-YG-236` AND body text `(REQ-YG-236)`
- [ ] `fr-237-chatterbox-consolidate-and-cli.md` front matter `req: REQ-YG-235, REQ-YG-238` (body already correct)
- [ ] `python scripts/aggregate_changelog.py > /dev/null` succeeds without error
- [ ] Each fragment's `req:` matches the corresponding capability's requirement in ARCHITECTURE.md
- [ ] No other fragments modified (only the 4 listed)

## Alternatives Considered

1. **Automated cross-check lint rule** — A lint rule validating changelog `req:` against ARCHITECTURE.md capability mappings would prevent future drift. Separate enhancement (potential future FR); does not address the immediate data corruption.

2. **Regenerate fragments from FR metadata** — Rejected; fragments contain hand-written descriptions that would be lost.

## Related

- Inquisitor audits 171–180 (`.chaplain/inquisitor.log`)
- `scripts/aggregate_changelog.py` — changelog generator that reads front matter
- `scripts/req_coverage.py` — requirement traceability checker
- ARCHITECTURE.md capability table (CAP-94, CAP-95, CAP-100)
- FR-179 (append-only changelog fragment system)
