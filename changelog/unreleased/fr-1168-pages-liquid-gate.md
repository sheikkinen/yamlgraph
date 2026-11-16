---
type: fix
scope: docs
req: REQ-YG-731
---
- **FR-1168 Pages docs Liquid gate**: GitHub Pages had failed on every push since one docs line carried an unterminated `{{`, and 23 other balanced `{{ … }}` tokens rendered as empty text. All 24 are now wrapped in `{% raw %}…{% endraw %}`. `scripts/check_docs_liquid.py` rejects active Liquid outside raw in every file Pages renders; it runs as the `docs-liquid` pre-commit hook and the always-run `Docs Liquid (Pages build)` CI job, which also builds the site with the Pages Jekyll action and checks the wrapped tokens render literally. Supersedes FR-751. (REQ-YG-731)
