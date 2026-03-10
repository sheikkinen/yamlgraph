---
type: fix
scope: pre-commit
---
- **Pre-commit hook installation**: `.git/hooks/pre-commit` was missing — only commit-msg hooks ran; now both stages install correctly
