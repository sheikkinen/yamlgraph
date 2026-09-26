# Diary 2026-09-26 — The export that could not be imported

**Context:** FR-1097 (non-stream `graph run` exits 3 on untolerated completed
errors) and FR-1098 (`--stream` exits 1 on an error event), enforced in one
worktree. FR-1098 ran without a judgement by operator decision.

## What happened

The FR-1097 judgement required every initial `state.errors` entry to pass
`PipelineError.model_validate`. That is the right boundary. `--import-state`
is where outside data comes in, and an entry that is not a real error can't
be counted honestly. The FR assumed the import would carry what the export
wrote. The first RED probe printed the `--json` result, and its `errors` list
held strings like `"type=<ErrorType.GUARD_ERROR: 'guard_error'> message=..."`.
`_serialize_state` passed lists through raw, and `json.dump(default=str)`
turned each model into its `repr`. So the export boundary broke what the
import boundary was about to enforce. Every `--export-state` →
`--import-state` chain after a lossy run would have hit the new validation and
exited 1. Every witness built from hand-written import files would still have
passed.

What caught it was reading the raw output before trusting the assertions.
The fix was one branch in the serializer, plus a witness that runs the real
chain (export from run 1, import into run 2) instead of a fixture pretending
to be run 1's export. That change is outside the frozen FR text, so it is
recorded as a deviation rather than folded in silently.

Two smaller events. The FR-335 module-map budget test failed by one line
when I added `cli/error_tally.py`. The test comment shows a long history of
raising that limit. I moved the tally into an existing helper module instead,
because raising a limit in the same session that trips it is
`guard_widening_when_caught`. Separately, a new outsider test failed a
sibling test's tempdir leak check under xdist. The sibling globs the shared
`$TMPDIR`, so my test now gets its own `TMPDIR`. Both fixes kept an existing
gate intact.

## Heuristic

**Heuristic:** when a new validation guards an import boundary, test it
against the real export, not a hand-written fixture. The two boundaries are
one contract, and only a round trip checks both halves.

**Seed:** how many other `--export-*` / `--import-*` pairs in the CLI have
never been witnessed as a round trip? A census could run every export path
into its matching import path and diff the typed state.
