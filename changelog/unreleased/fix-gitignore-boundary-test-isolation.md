---
type: fix
scope: test
---
- **gh-407 Gitignore boundary test isolation**: Strip bypass env vars in test helper to prevent leakage when pre-commit runs pytest with bypass vars set.
