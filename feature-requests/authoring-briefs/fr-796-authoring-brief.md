# FR-796 watcher2 witness curation

Execute only the governed artifact deletion and relocation slice authorized by
`feature-requests/FR-796-reclassify-watcher2-witness-demos.md` and its committed
judgement.

## Delete

Delete these directories completely:

- `examples/demos/script-retirement/`
- `examples/demos/security-cve-ignore/`
- `examples/demos/watcher2-red-verification/`

## Relocate

Move these seven complete directories from `examples/demos/` to the newly
created `.chaplain/demos/` directory:

- `watcher2-changelog-gen`
- `watcher2-ci-remediation`
- `watcher2-deduplication-gate`
- `watcher2-hook-preflight-gate`
- `watcher2-merged-branch-collision-guard`
- `watcher2-post-merge-inbox-consumption`
- `watcher2-remediation`

Use moves that preserve Git rename detection. For every relocated directory,
`graph.yaml`, `prompts/**`, Python node files, scripts, and the existing
`demo-output.log` must remain byte-for-byte identical to their committed source
versions. README files may change only by replacing runnable command paths from
`examples/demos/<name>/...` to `.chaplain/demos/<name>/...`.

Do not change graph semantics, prompts, Python nodes, scripts, existing output
logs, framework code, discovery patterns, tests, feature requests, indexes,
taxonomy, capabilities, changelog, diary, or any non-target demo. If any graph
needs a semantic or code change to lint or run after relocation, stop and record
the blocker rather than repairing it.

## Validation

1. Compute and compare hashes from committed source content versus relocated
   working-tree content for all non-README files in the seven retained demos.
2. Run `yamlgraph graph lint` against all seven relocated `graph.yaml` files.
3. Run the representative tool-only witness:
   `.venv/bin/yamlgraph graph run .chaplain/demos/watcher2-deduplication-gate/graph.yaml --full 2>&1 | tee .chaplain/demos/watcher2-deduplication-gate/fr796-verification.log`
   The new verification log is authorized evidence; do not overwrite the
   existing `demo-output.log`.

Write `tmp/draft-authoring-report.md` with headings `Artifacts`, `Precedent`,
`Validation`, `Repairs`, and `Blocked validation`. List all ten source paths and
seven destinations, report byte-comparison results, exact lint commands and
outcomes, and the representative run outcome honestly.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
