# Self-Portrait — your device's record of you, handed to your agents

**FR-782 | CAP-223 | REQ-YG-584**

Extract the people, topics, locations, and contacts that macOS's
**PersonalizationPortrait** database already knows about you, resolve
topic Q-IDs against Wikidata, and synthesize a portrait whose *primary
consumer is an AI agent*: `self-portrait.json` plus an `agent_briefing`
section written in second person to a future agent.

```
prepare → extract (read-only SQLite) → enrich (Wikidata labels)
       → build_payload (exact outbound JSON + SHA-256)
       → confirm_egress (interrupt)  ─ no ──→ render_denied (nothing sent)
                 │ yes / auto_approve
                 ▼
          verify_payload (byte-for-byte) → synthesize (LLM) → render
```

Outputs (default `~/.yamlgraph/self-portrait/`, **outside the repo**):

| File | For |
|---|---|
| `self-portrait.json` | agents — the frozen contract, load it as system context |
| `self-portrait.md` | you — the narrative rendering |
| `portrait-diff.md` | drift — new people, shifted topic scores, dropped locations |
| `synthesis-payload.json` | the exact bytes the consent gate previewed |

## Intent boundary: personal data is the product

This example exists to read *your* device's record of *you* and hand it
to *your* agents. There is no redaction mode, no "public version", no
anonymization — those would delete the product. The honest boundaries
are different ones:

- Everything stays local. The repo ships the pipeline, the schema, and a
  **synthetic fixture**; a real portrait is never committed.
- Egress is gated and proven (below).
- Tests and the demo witness run on the synthetic fixture only.

If you prefer zero egress entirely, this example uses the standard
`PROVIDER` mechanism — point it at a local provider (e.g. LM Studio) the
same way any other graph does. That is a provider choice, not a feature
of this example.

## The Full Disk Access (TCC) gate

`~/Library/PersonalizationPortrait/PPSQLDatabase.db` is TCC-protected.
The **executing binary** needs Full Disk Access — your terminal for
manual runs, and the exact `python`/`yamlgraph` binary that `launchd`
invokes for scheduled runs (the FR-781 trap: granting Terminal access
does nothing for a launchd-spawned interpreter).

Grant it in **System Settings → Privacy & Security → Full Disk Access**,
then restart that binary. Without it the graph fails fast and prints
this remediation — it never degrades into an empty portrait.

## Consent: the preview IS the payload

A summary-only preview would be compliance theatre. Instead:

1. `build_payload` serializes the outbound JSON **once**, writes it to
   `synthesis-payload.json`, and records its byte count and SHA-256.
2. `confirm_egress` (an `interrupt` node — hence the memory
   checkpointer) shows the counts, the top entries, the byte count, the
   hash, **and the path to the full payload file**. Read that file: it
   is exactly what will be sent.
3. Answering anything other than `yes` routes to `render_denied`, which
   writes a local extraction summary. Nothing leaves the machine.
4. Answering `yes` routes to `verify_payload`, which re-reads the file
   and refuses to continue unless the bytes are identical to the
   preview (`ConsentPayloadMismatchError`).

`auto_approve=true` is the **only** bypass and it is opt-in — for
headless/scheduled runs. The interactive gate is the default.

## Run it

Against the committed synthetic fixture (safe, no real data):

```bash
# The demo witness runs a disposable copy so the committed fixture stays pristine
cp examples/demos/self-portrait/fixture/PPSQLDatabase.db /tmp/pp-demo.db

# C-9: probe a synthetic home so the witness never records real database availability
mkdir -p /tmp/fr782-synthetic-home
export SELF_PORTRAIT_PROBE_HOME=/tmp/fr782-synthetic-home

yamlgraph graph run examples/demos/self-portrait/graph.yaml \
  --var db_path=/tmp/pp-demo.db \
  --var output_dir=/tmp/self-portrait-demo \
  --var portrait_date=2026-08-08 \
  --var auto_approve=true --full
```

Against your real database (interactive consent gate, the default):

```bash
yamlgraph graph run examples/demos/self-portrait/graph.yaml \
  --var db_path=~/Library/PersonalizationPortrait/PPSQLDatabase.db --full
# → read the previewed payload file, then answer: yes
```

Rebuild the synthetic fixture:

```bash
python examples/demos/self-portrait/fixture_builder.py
```

## What the boundary asserts

Schema drift across macOS versions is expected, so it is asserted where
the database enters, never patched downstream:

| Condition | Behaviour |
|---|---|
| database missing / TCC-blocked | `DatabaseUnreadableError` naming the Full Disk Access path |
| unknown `ne_records.category` | `SchemaDriftError` naming the category id |
| required table missing | `SchemaDriftError` naming the table |
| optional column missing | field is `None` — run continues |
| Wikidata offline / label missing | bare Q-IDs kept, never a fabricated label |
| `knowledgeC.db`, Safari, Calendar, WhatsApp | **availability probe only** — reported as absent / "present (not parsed)"; FR-782 ships no parsers for them |

Wikidata resolution batches at ≤ 50 Q-IDs, caches under
`<output_dir>/cache/wikidata-labels.json` keyed by Q-ID + language, makes
no network call on a cache hit, and uses only `urllib` from the standard
library (no new dependency).

### Availability is data

The supplementary probe reports *whether* those databases exist. That is
a fact about your machine, so it rides inside the consent payload like
any other personal datum — and it must never be committed. Two controls
enforce this:

- every path in the payload is home-relative (`~/Library/…`), never
  `/Users/<account>/…`, so the payload cannot carry your account name;
- `SELF_PORTRAIT_PROBE_HOME` points the probe at a synthetic home. The
  committed witness and the test suite set it, so `demo-output.log`
  records every supplementary source as `absent` regardless of what is
  installed on the machine that generated it. Leave it unset for a real
  run.

```bash
export SELF_PORTRAIT_PROBE_HOME=/tmp/fr782-synthetic-home   # fixture/demo runs only
```

## Weekly refresh (launchd)

Install a `StartCalendarInterval` agent using the **Pattern B deploy**
documented in [`../file-hook/README.md`](../file-hook/README.md) — a
copy of the runner outside `~/Documents` so TCC grants apply to the
executing binary. This example ships **no installer**; the file-hook
README is the canonical install guide. A scheduled run must pass
`--var auto_approve=true` (headless runs cannot answer an interrupt) and
is idempotent by portrait date. Each refresh writes a fresh
`portrait-diff.md` against the previous snapshot.

## Files

| Path | Role |
|---|---|
| `graph.yaml` | pipeline (authored via `scripts/author.sh`) |
| `prompts/synthesize_portrait.yaml` | inline-schema synthesis prompt |
| `models.py` | typed boundary: row models + named errors |
| `extract.py` | read-only SQLite extraction + supplementary probes |
| `wikidata.py` | batched, cached, stdlib-only label resolution |
| `portrait_io.py` | payload/consent identity, render, diff |
| `tools.py` | graph-facing state adapters |
| `fixture_builder.py` | deterministic synthetic fixture generator |
| `fixture/PPSQLDatabase.db` | committed synthetic database (obviously fake) |
| `demo-output.log` | grounded witness run against the fixture |
