---
type: fix
scope: docs
---
- **GitHub Pages build**: excluded `docs/diary/` (and stray top-level `diary-*.md`) from the Jekyll site — Pages runs Jekyll 3.10 which silently ignores `render_with_liquid: false` (a Jekyll 4 option), so diary prose quoting raw Jinja2 (`{% ... %}`) crashed Liquid; the site had 0 successful deploys since 2026-05-20.
