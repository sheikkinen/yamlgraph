# outsider-view adapters — execution instructions (operational, not doctrine)

## YAMLGraph adapter (manual only, output advisory)

Sole documented operator command:

```bash
scripts/outsider.sh <pr-number> [--comment]
```

Supported manual modes:

```bash
scripts/outsider.sh <pr-number> [--comment]
scripts/outsider.sh --input <path> [--label <name>]
scripts/outsider.sh --selftest
```

Only the pull request title and body reach the model. The wrapper additionally
passes the run's base observation fields (FR-1004: `repo`, `pr`, `head_sha`,
`prompt_digest`, `tool_sha`) as graph state; they never enter the prompt and
are consumed only by the Python finalisation step that writes the report's
marker. The child process runs from a clean directory outside the repository,
with no path grants and no tool grants, so the reader cannot open repository
files or load project instructions.

Direct invocation (what the wrapper runs; use the wrapper instead):

```bash
OUTSIDER_EXECUTION=1 yamlgraph graph run .github/skills/outsider-view/adapters/graph.yaml \
  --var input_path=<title-body-file> --var report_path=tmp/outsider-<label>-<stamp>.md \
  --var model=gpt-5.6-sol --var repo=<owner/name|-> --var pr=<number|-> --var head_sha=<40-hex|-> \
  --var prompt_digest=<16-hex> --var tool_sha=<short-sha> --full
```

All five observation variables are required (`finalize_report` fails closed
without them); a non-PR run passes the `-` placeholders for `repo`, `pr` and
`head_sha`.

The report is written under `tmp/outsider-<label>-<stamp>.md`. The wrapper
verifies the artifact by reading its content, never by trusting the graph exit
code. The report's second line is the typed observation marker (FR-1004); a run
posted with `--comment` makes that comment the durable record. Outsider
execution changes no tracked repository state — reports, logs and the lock live
under git-ignored `tmp/`; there is no ledger.

The first line is the **derived verdict**, computed in Python from the typed
report. Section 2 is the model's non-authoritative opinion and must not be used
as the decision signal. The whole report is advisory: it informs the author and
reviewer, but it does not gate, approve, merge, or reject anything.

Forbidden actions:

- No automatic invocation.
- No gate or blocking status.
- No PR comment unless `--comment` is passed.
- No feature request body input.
- No edits to `docs/spikes/outsider-reader-2026-09-05/` outputs.

Source copy: `docs/spikes/outsider-reader-2026-09-05/`.
