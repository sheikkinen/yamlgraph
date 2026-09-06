You are classifying ONE repository artifact coupled to `.chaplain/`, the retired
autonomous "Chaplain" pipeline (an FSM dispatcher/worker, watcher graphs,
inquisitor, inbox importer) that has not run since July 2026 and is being
removed. Three graphs that were inside it are still live and have already been
moved out: `graphs/fr_triage/` (a pre-commit triage gate), `graphs/world_distill/`
(writes the world-context file) and `graphs/philosopher/` (dormant, kept). The
shell library `scripts/lib/finalize_lib.sh` and its consumer
`scripts/finalize_merge.sh` are live.

The payload begins with a "Facts" block computed by code — file path, kind,
requirement IDs, per-requirement fan-in (how many tests OUTSIDE the candidate set
mark the same requirement), and for capability records the module list and
whether each module still exists. Treat the facts as ground truth; do not
recount them. Then comes the file text.

Answer ONE question with ONE label:

- For a test file (`kind: test`): does this file witness the retired runtime
  itself (its FSM, watchers, dispatcher, inquisitor, inbox importer, watcher
  actions, `.chaplain/` scripts or config), or does it witness a behaviour that
  is still live and merely mentions one of those words?
  - `delete` — its subject is the retired runtime.
  - `keep` — its subject is live behaviour (core framework, a relocated graph, a
    live script, a hook, a gate), even if it names `.chaplain`, "watcher",
    "inbox", "triage" or "distill" in passing.
- For a capability record (`kind: cap`): does every requirement it defines and
  every module it lists that still exists describe the retired runtime?
  - `retire` — everything it claims is the retired runtime.
  - `keep` — at least one requirement or present module is live behaviour.
- `manual_review` — the artifact is mixed, or you cannot tell from the text.
  Prefer this over guessing.

Set `evidence_span` to a short EXACT span copied from the payload that shows
the subject (a docstring line, a path constant, a requirement description).
Confidence reflects how clearly the text settles the question.
