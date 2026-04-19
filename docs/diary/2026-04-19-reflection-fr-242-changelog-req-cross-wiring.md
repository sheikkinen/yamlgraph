# Reflection: FR-242 Changelog req Front-Matter Cross-Wiring (2026-04-19)

## Cognitive Trap: Copy-Paste Drift at the Boundary

**Trap**: Changelog fragments are created by copying existing ones. The `req:` field silently carries over the wrong requirement ID — it passes all structural checks (valid YAML, valid format) but is semantically wrong.

**Cure**: FR-242 adds a condemning test that validates every fragment's `req:` front-matter matches the correct requirement. The test catches the error at the boundary where the fragment is written.

**Insight**: This is the `plausible_wrong_answer` trap from the Knowledge Graph: output passes shape check but is semantically wrong. The fix requires assertion beyond type validation — checking meaning, not just form.

**Seed**: Could the Chaplain auto-populate `req:` when generating changelog fragments from FR metadata, eliminating the copy-paste vector entirely?
