---
type: fix
scope: docs
---
- **fix(docs): escape Liquid tags in diary and demo docs** — Jekyll processes `{% %}` Jinja2 syntax in Markdown before rendering, causing recurring "pages build and deployment" failures. Wrapped all Jinja2 syntax literals with `{% raw %}...{% endraw %}` across 5 affected docs files.
