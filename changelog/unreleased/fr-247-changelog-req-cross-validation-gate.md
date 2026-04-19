---
type: feat
scope: enforcement
req: REQ-YG-254
---
- **FR-247 Changelog REQ Cross-Validation Gate**: `scripts/check_changelog_req.py` validates changelog fragment `req:` front-matter against capabilities registry. Mechanical pre-filter catches phantom REQs, unparseable front-matter; single-REQ CAPs pass mechanically. Multi-REQ CAPs deferred to LLM graph `graphs/enforcement/changelog-req-check.yaml` (Haiku, temperature 0). Supports `--strict`, `--skip-llm`, `--verbose` flags. Pre-commit hook and CI job wired. (REQ-YG-254)
