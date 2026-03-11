---
type: fix
scope: github
---
- **GitHub Pages Build**: Fixed Liquid syntax errors by wrapping Jinja2 template syntax in `{% raw %}` tags (Jekyll 3.x doesn't support `render_with_liquid` front matter)
