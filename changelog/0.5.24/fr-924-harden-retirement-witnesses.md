---
type: fix
scope: tests
---
- **FR-924 Harden retirement witnesses**: The FR-909 and FR-915 deletion witnesses asked `Path.exists()` where their acceptance criteria specified tracked absence, so they passed in CI (clean checkout) while failing on any working tree carrying build residue. They now ask `git ls-files`. All three retirement witnesses gained import guards asserting `ModuleNotFoundError`, because a retired package directory left on disk becomes an importable namespace package that neither git nor `Path.exists()` detects. FR-910's filesystem-absence checks are preserved — its AC-01 specified them.
