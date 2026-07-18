---
type: fix
scope: docs
req: REQ-YG-566
---
- **FR-748 Atlas Liquid-Safety + Parenthetical ID Repair**: the generated FR atlas broke the GitHub Pages build for 6 consecutive runs — Jekyll renders `docs/` as Liquid, and one FR title contains a literal Jinja2 `set` tag. `render_atlas` now wraps the document in `raw`/`endraw` at the boundary where the artifact enters Jekyll's jurisdiction (titles stay verbatim). Re-proving the demo surfaced the third live decoration strike in the token-fidelity boundary: models append title parentheticals to FR ids — `_repair_id` strips them mechanically (slug-embedded parens preserved); fabrications still die in `enforce_coverage`. (REQ-YG-566)
