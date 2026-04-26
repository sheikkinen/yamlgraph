**Context:** Implemented FR-288 to harden watcher2 preflight with a fail-closed git hook integrity gate (`core.hooksPath` policy + executable `pre-commit`/`commit-msg` checks), validated with RED acceptance tests, full unit suite, and a runnable demo.

**Trap:** **partial_remediation** and **quick_confidence**. After the feature and targeted tests were green, adding a new demo looked complete, but `test_examples_readme_audit` failed because the demo index in `examples/README.md` was not updated.

**Heuristic:** Any new demo is not complete until three linked artifacts are present together: demo directory files, `demo-output.log`, and `examples/README.md` index entry. Run the full unit suite after demo additions to catch repository-level contracts.

**Seed:** Should we add a dedicated CI check that enforces every `examples/demos/*/` directory has both a `demo-output.log` and a corresponding `examples/README.md` entry to prevent documentation/demo drift?
