---
type: fix
scope: ci
---
- **CI pipeline fix**: Add `pytest.importorskip("feedparser")` to `test_diary_digest.py` so tests skip gracefully in CI where only `[dev]` extras are installed (no `[digest]`). This was blocking all PyPI releases since v0.4.43.
