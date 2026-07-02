# Diary: The Scattered Callsites — glob→rglob is Never Just One File

**Date**: 2026-07-02
**FR**: FR-650 (canon type subfolders)
**Trap**: partial_remediation

## The Cognitive Process

The FR was clean: four files change `glob` to `rglob`, persist writes into type subfolders. Judgement caught three write paths instead of two, skeleton exists-check needing rglob, and mkstemp needing type_dir. All mechanical.

The trap: I ran the targeted test suite (5 test files, 92 tests, all green) and went to commit. The pre-commit full suite caught 15 failures in 3 *other* test files that also read live canon with flat `glob("*.yaml")`. Tests I didn't think to check because they weren't "persist" or "reload" tests — they were schema validation, pathfinder, and wiki-core tests that happened to load canon as a fixture.

## The Heuristic

**When changing a filesystem contract (flat → nested), grep for ALL consumers, not just the ones named in the FR.** The four production files were obvious; the three test files that independently loaded canon via the same `glob` pattern were invisible because they were testing different capabilities.

`grep -rn 'glob.*yaml.*canon\|canon.*glob' tests/` would have caught them in seconds. The targeted test run created false confidence.

## Seed

Could a pre-commit hook detect glob/rglob inconsistency across files that share a directory constant? If `NOVEL_FANDOM_DIR / "canon"` appears in N files, and M use `glob` while N-M use `rglob`, that's a contract violation detectable statically.
