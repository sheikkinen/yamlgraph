# Feature Request: Marketing Campaign — Alternative Deployment from ninchat_voice

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced — Option A (reuse probe_recap tools)
**Effort:** 1 day
**Requested:** 2026-04-29

## Summary

Add alternative deployment files to `projects/ninchat_voice` for a marketing voice questionnaire campaign: new Fly.io app, new Twilio number, simple 3-field graph (name, organization, quote). Results delivered via Ninchat + SMS — same stack as ninchat_voice production.

## Value Statement

Marketing gets a dedicated inbound phone number that collects testimonial data via voice and delivers structured results to Ninchat, without forking or duplicating the ninchat_voice codebase.

## Problem

Marketing needs a standalone voice bot on a separate phone number to collect three fields from callers: name, organization, and a quote/testimonial. This requires:

- A separate Fly.io app (independent scaling, secrets, phone number)
- A simple questionnaire graph (same navigator FSM, but a non-classifying graph that skips intent routing)
- Same result delivery (Ninchat + SMS) as ninchat_voice production

**Fork vs alternative deployment:** ninchat_voice is the most evolved codebase (yamlgraph 0.4.74, 21 services, 12 actions, voice_runtime vendoring). CSAP is a stale staging baseline (yamlgraph 0.4.67, fewer services/actions). Forking either creates maintenance debt — every bug fix needs manual porting. Alternative deployment files share the same codebase with zero duplication.

## Proposed Solution

### Phase 1: Deployment files

Add to `projects/ninchat_voice/`:

| File | Purpose |
|------|---------|
| `fly.marketing.toml` | Fly config: app `marketing-questionnaire`, same VM/concurrency, `QUESTIONNAIRE_GRAPH=graphs/marketing/graph.yaml` |
| `deploy-marketing.sh` | Vendors voice_runtime, runs `fly deploy --app marketing-questionnaire --config fly.marketing.toml --ha=false` |

`fly.marketing.toml` reuses the same `Dockerfile`, `entrypoint.sh`, `supervisord.conf`, `requirements-deploy.txt`. Key env var differences from production `fly.toml`:

```toml
app = 'marketing-questionnaire'
primary_region = 'arn'

[env]
  NINCHAT_VOICE_MODE = 'navigator'                        # Keep navigator — most refined FSM config
  QUESTIONNAIRE_GRAPH = 'graphs/marketing/graph.yaml'     # Non-classifying graph, no graph switching
  # rest identical to fly.toml
```

**FSM mode rationale:** The navigator FSM coordinator (`voice_coordinator_navigator.yaml`) is the most battle-tested and refined config. Other modes (`questionnaire`, `triage`, `simple`) are outdated and less hardened. Instead of switching FSM mode, the marketing graph simply skips classification — it greets and goes straight into the questionnaire without emitting `switch_graph` events. The navigator FSM's graph-switching machinery sits idle. No changes to `entrypoint.sh` needed.

### Phase 2: Questionnaire graph

```
graphs/marketing/
  graph.yaml           # 3-field questionnaire
  prompts/
    extract.yaml       # Extract name, organization, quote from utterance
    probe.yaml         # Ask for missing fields
    recap.yaml         # Confirm collected data
  marketing.py         # Python tools (parse_targets, check_missing, etc.)
```

**Tool reuse decision:** `graphs/probe_recap/probe_recap.py` has generic, schema-driven tools (`parse_targets`, `check_missing`, `merge_extraction`, `apply_corrections`, `mark_continue`, `mark_done`). These are field-agnostic — they operate on `target_fields` from state. Two options:

- **Option A (preferred):** Reuse probe_recap tools directly. Graph YAML references `graphs.probe_recap.probe_recap` module. Only new files: `graph.yaml` + 3 prompts. Zero new Python.
- **Option B:** Write standalone `marketing.py` tools. Justified only if probe_recap's multi-turn FSM re-entry pattern is incompatible with the simpler flow.

Schema (passed as `targets` state var to probe_recap tools):
```yaml
schema:
  name: MarketingQuote
  fields:
    name: {type: str, description: "Caller's full name"}
    organization: {type: str, description: "Caller's organization or company"}
    quote: {type: str, description: "Testimonial or statement from the caller"}
```

### Phase 3: Fly.io + Twilio setup

```bash
# Create app
fly apps create marketing-questionnaire

# Set secrets (new Twilio number, shared API keys)
fly secrets set --app marketing-questionnaire \
  GOOGLE_API_KEY=... \
  TWILIO_ACCOUNT_SID=... \
  TWILIO_AUTH_TOKEN=... \
  TWILIO_PHONE_NUMBER=+358... \
  AZURE_SPEECH_KEY=... \
  AZURE_SPEECH_REGION=northeurope \
  NINCHAT_BOT_QUEUE_ID=... \
  VOICE_STREAM_URL='https://marketing-questionnaire.fly.dev' \
  AWS_ACCESS_KEY_ID=... \
  AWS_SECRET_ACCESS_KEY=...

# Deploy
./deploy-marketing.sh
```

Twilio: buy new number, set webhook to `https://marketing-questionnaire.fly.dev/incoming`.

## Acceptance Criteria

### Code (enforceable)

- [ ] `fly.marketing.toml` exists with `NINCHAT_VOICE_MODE=navigator` and `QUESTIONNAIRE_GRAPH=graphs/marketing/graph.yaml`
- [ ] `deploy-marketing.sh` vendors voice_runtime and deploys to `marketing-questionnaire` app
- [ ] `graphs/marketing/graph.yaml` collects name, organization, quote
- [ ] 3 prompt files (extract, probe, recap) in `graphs/marketing/prompts/`
- [ ] Graph reuses `graphs.probe_recap.probe_recap` tools (Option A) or justifies standalone tools (Option B)
- [ ] Shared codebase — no duplicated services, actions, or infrastructure files

### Testing (enforceable)

Testing follows the established ninchat_voice 3-tier pattern:

**Tier 1: Dialogue E2E — no telephony, real LLM** (pattern: `test_dialogue_e2e.py`)
- [ ] `test_dialogue_e2e_marketing.py` — multi-turn dialogue through marketing graph
  - Turn 0: initialize with `targets="name:Nimi|organization:Organisaatio|quote:Sitaatti"`, empty transcript → probe
  - Turn 1: provide name + org → extract, check missing, probe for quote
  - Turn 2: provide quote → extract, check missing → recap
  - Turn 3: confirm recap → done event
  - Validates: `result_event`, `extracted` dict has all 3 fields, `phase` transitions
  - Requires: `GOOGLE_API_KEY` (Gemini 2.5 Flash), skipped if unset
  - Uses `run_graph_async` with `thread_id` for checkpointed multi-turn state

**Tier 2: FSM integration — timed mocks, no API keys** (pattern: `tests/integration/test_timed_happy_call.sh`)
- [ ] `test-marketing-timed.sh` — full FSM flow with timed mock actions
  - Starts coordinator with `--mock` and `QUESTIONNAIRE_GRAPH=graphs/marketing/graph.yaml`
  - Injects `incoming_call` event
  - Validates state sequence through navigator FSM states
  - Confirms `yamlgraph_async` action receives the marketing graph path
  - ~5-8s runtime, no API keys needed

**Tier 3: Live call E2E — real telephony** (pattern: `test-appointment-e2e.sh`)
- [ ] `test-marketing-e2e.sh` — real call through the marketing Fly.io app
  - Starts `start-fsm.sh` with marketing graph
  - Dials Twilio number (or uses Twilio API to initiate call)
  - Validates full pipeline: voice greeting → questionnaire → recap → Ninchat delivery + SMS

### Operational (post-deploy)

- [ ] Fly app `marketing-questionnaire` created
- [ ] Twilio number purchased and webhook set to `https://marketing-questionnaire.fly.dev/incoming`
- [ ] Fly secrets configured (API keys, Twilio creds, Ninchat queue, Tigris)
- [ ] Tier 3 live call test passes on deployed app
- [ ] Transcripts archived to Tigris S3

## Alternatives Considered

1. **Fork CSAP** — Rejected. CSAP is stale (yamlgraph 0.4.67, fewer services). Would inherit old defects.
2. **Fork ninchat_voice** — Rejected. 100% code copy with zero divergence = pure maintenance debt. Every bug fix needs manual porting.
3. **Alternative deployment (chosen)** — Same codebase, separate Fly app via `fly.marketing.toml` + `deploy-marketing.sh`. Zero duplication. Scales to future campaigns by adding `fly.campaign2.toml`.

## Related

- `projects/ninchat_voice/fly.toml` — production deployment config (pattern to follow)
- `projects/ninchat_voice/deploy.sh` — production deploy script (pattern to follow)
- `projects/ninchat_voice/graphs/probe_recap/` — probe/recap pattern (graph pattern to simplify)
- `customer-service-agent-platform/fly.staging.toml` — CSAP staging config (stale baseline)
