# Memory-Corpus Curation (FR-875)

Selective amnesia for the Copilot memory tool: judge every repo-scope
note against a declared audience premise, render a human-review
disposition draft, and — only after hash-bound written sign-off —
execute the amnesia.

## Contract (judgement-frozen)

- **Repo scope only** (v1). User/session scope needs its own FR.
- **Outputs only under `tmp/memory-curation/`** — never committed.
- **The judge stage is egress**: note bodies transit to the configured
  LLM provider. Real-corpus runs require a local-only provider or the
  FR's recorded approval (vertex/azure approved 2026-08-24). Fixture
  runs may use any test-safe provider.
- **Apply is gated**: refuses without a `SIGN-OFF:` line binding the
  manifest and disposition hashes; refuses ALL mutation on any
  live-file drift (re-collect and re-judge instead); idempotent.

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
