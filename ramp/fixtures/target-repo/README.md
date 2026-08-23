# ramp fixture target

Committed fixture scratch repo for FR-865 installer tests. Matches the
Tier-1 supported target contract: Python, `pyproject.toml`, a pytest
`tests/` suite, ruff configured. Tests copy this tree into a tmp dir and
add a `.git/` directory (or `git init` for the pre-commit consumption
test) — the fixture itself is never installed into.
