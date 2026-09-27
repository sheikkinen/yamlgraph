# Reflection: FR-1128 — the gate that fired on the next person

**Date:** 2026-09-27
**FR:** FR-1128 (spike probe inline-LLM exemption name)

## What happened

FR-1124's commits were refused by `inline-llm-check` because of a file in
another PR (#729). The hook scans the whole tree, so the violation reached
`main` without complaint and then failed the next unrelated commit that
staged any Python. The file was a spike probe, which is exactly what the
FR-599 `probe_` exemption exists for. It was named `probe.py`, so the
exemption missed it. The same file had never been through `ruff format`
either. Its first commit ran no hooks.

## Trap

`gate_fires_downstream`: a local, whole-tree gate that is not enforced at
merge punishes the next contributor instead of the author. The obvious
repairs are all wrong in the same direction. Skipping the hook, or adding
`docs/spikes/` to the exclusions, would each make the gate weaker for
everyone to unblock one person.

## Heuristic

When a whole-tree local gate fails on a file outside your diff, make the
invariant fail at merge in CI with a repo-root unit test, then fix the
file under the existing contract. The test moves the pain back to the PR
that introduces the violation.

## Seed

**Seed:** Which other `pass_filenames: false` pre-commit hooks enforce a
whole-tree invariant that no unit test asserts at the repository root, and
would the same repository-invariant test close each one?
