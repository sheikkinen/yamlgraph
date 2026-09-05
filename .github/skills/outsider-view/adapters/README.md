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

The wrapper passes only the pull request title and body to the graph. The child
process runs from a clean directory outside the repository, with no path grants
and no tool grants, so the reader cannot open repository files or load project
instructions.

Direct invocation (what the wrapper runs; use the wrapper instead):

```bash
OUTSIDER_EXECUTION=1 yamlgraph graph run .github/skills/outsider-view/adapters/graph.yaml \
  --var input_path=<title-body-file> --var report_path=tmp/outsider-<label>-<stamp>.md \
  --var model=gpt-5.6-sol --var repo=<owner/name|-> --var pr=<number|-> --var head_sha=<40-hex|-> \
  --var prompt_digest=<16-hex> --var tool_sha=<short-sha> --full
```

The report is written under `tmp/outsider-<label>-<stamp>.md`. The wrapper
verifies the artifact by reading its content, never by trusting the graph exit
code. The second line of the report is the typed observation marker (FR-1004):
the base fields above plus the input SHA-256, derived verdict and section
counts. A run posted with `--comment` makes that comment the durable record;
nothing is written under the repository, and there is no ledger.

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
