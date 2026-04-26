**Context:** Implemented FR-286 to enforce `-m "not slow"` in the root pre-commit pytest hook, then added a runnable demo and validated repository-wide unit/test gates after introducing new demo artifacts.

**Trap:** **partial_remediation** — the first pass added the new demo directory but missed the required `examples/README.md` index update, causing `test_examples_readme_audit` to fail.

**Heuristic:** When adding any `examples/demos/<name>/` entry, treat the examples index as part of the same boundary: update `examples/README.md` in the same change and run the full unit suite immediately after adding demo files.

**Seed:** Should we add a pre-commit hook that fails fast when a new `examples/demos/*/` directory exists without a corresponding `examples/README.md` entry?
