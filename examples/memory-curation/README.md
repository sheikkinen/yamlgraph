# Memory-Corpus Curation (FR-875)

Selective amnesia for the Copilot memory tool: judge every repo-scope
note against a declared audience premise, render a human-review
disposition draft, and — only after hash-bound written sign-off —
execute the amnesia.

## Contract (judgement-frozen; FR-878 amended)

- **Repo scope only** (v1). User/session scope needs its own FR.
- **Outputs only under `tmp/memory-curation/`** — never committed.
- **The judge stage is egress**: note bodies transit to the configured
  LLM provider. Real-corpus runs require a local-only provider or the
  FR's recorded approval (vertex/azure approved 2026-08-24). Fixture
  runs may use any test-safe provider.
- **Amnesia is reversible (FR-878)**: `forget` archives to
  `<memory-root>/.archive/<op_id>/…` and `redact` stashes its original
  there; every event appends a schema row to `repo/_tombstones.md`
  (protected — apply refuses to forget/redact it); nothing is ever
  hard-deleted. `apply.py restore <op_id>/<path>` brings a note back,
  conflict-safe. Collect warns when a live note resembles a forgotten
  one (re-derivation — the forecast-was-wrong signal).
- **Approval is tiered by residual risk (FR-878)**, computed from the
  disposition content; hash-binding and drift refusal unchanged:

  | Tier | Trigger (precedence top-down) | Sign-off requirement |
  |---|---|---|
  | 3 | `premise_kind: export_publication` — or missing/unknown (fail closed) | `HUMAN=<name>` + `EXPORT_PUBLICATION_APPROVED`; non-delegable |
  | 2 | any `forget` | `HUMAN=<name>` |
  | 1 | any `redact`, zero forgets | `HUMAN=<name>` or `DELEGATION: FR-878 tier-1 standing (operator 2026-08-24)`; audit line appended |
  | 0 | keep-only | none |

  `premise_kind` is set by reconcile's `--premise-kind` flag
  (`hygiene | export_publication`) — an explicit variable, never inferred
  from premise prose.

## Usage

```bash
# 1. judge (draft only; prints resolved paths)
yamlgraph graph run examples/memory-curation/graph.yaml \
  --var memory_root=/path/to/memory-tool/memories \
  --var audience_premise="public repo workspace; worst-case reader: internet" \
  --full

# 2. review tmp/memory-curation/disposition.md, then append:
#    SIGN-OFF: approved by <name> manifest=<sha256> disposition=<sha256>

# 3. apply (validate-all-then-apply-all)
python examples/memory-curation/apply.py \
  --disposition tmp/memory-curation/disposition.json \
  --review tmp/memory-curation/disposition.md \
  --manifest tmp/memory-curation/manifest.json \
  --memory-root /path/to/memory-tool/memories
```

## Recurrence (FR-877)

Curation has no schedule by design: a cron'd draft is voided by the hash
chain the moment any note changes, and per-session judge runs would be
egress multiplied by session frequency. Instead, detection is mechanical
and execution stays deliberate: every successful apply writes a
post-apply live baseline (`.curation-state.json`, forgotten paths
absent), and `advisory.py` — pure stdlib, zero egress — diffs the live
corpus against it by sha256 at SessionStart (via
`.github/hooks/scripts/memory-advisory.sh`, env-overridable, fail-open
with one bounded JSONL record on failure). One line at/above the
threshold (default 5 drifted notes) or for a never-curated corpus;
silence otherwise. A malformed marker is a real error, never faked as
no-drift.

## Verdicts

| verdict | meaning | apply action |
|---|---|---|
| keep | accurate, still true, safe for the audience | untouched |
| redact | valuable but contains facts above the audience level | replaced with `redacted_draft` |
| forget | stale, superseded, wrong, or one-off glimpse | deleted |

Plus per-note `audience` (public / peer / customer_private /
machine_local) and `staleness` (fresh / dated / expired, with cited
evidence).

## Fixture smoke

```bash
yamlgraph graph run examples/memory-curation/graph.yaml \
  --var memory_root=examples/memory-curation/fixtures/memories \
  --var audience_premise="public repo workspace; worst-case reader: internet" --full
```

The 3-note fixture plants one durable fact (keep), one expired version
pin (forget), and one synthetic sensitive note (redact) — the leak
classes from the FR-874 rejection.
