---
type: feat
scope: linter
---
- **FR-430 Linter Rule W024**: Added warning `W024` to detect prompt files that mix simple `{variable}` placeholders with Jinja2 syntax (`{{ ... }}` / `{% ... %}`). The check is wired into `yamlgraph graph lint` with a fix suggestion and avoids false positives on pure Jinja2 templates.
