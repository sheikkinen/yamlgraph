# Feature Request: FR-298 Marketing Campaign E2E Test (Outcaller)

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-04-29
**Enforced:** 2026-04-29

## Summary

Create an automated E2E test for the `callback_marketing` questionnaire graph,
following the proven `test-other-topic-e2e.sh` + outcaller answerer pattern.

## Value Statement

Developers get automated live-call regression testing for the marketing
questionnaire, catching prompt, routing, and telephony failures before
they reach production callers.

## Problem

The `callback_marketing` graph has unit tests (Tier 0: structure) and an FSM
wiring test (Tier 2: timed mock), but no test drives a real call through the
full pipeline: Twilio → WebSocket → STT → FSM → YAMLGraph interrupt/resume →
TTS → caller hears response → confirms.

The deleted `test_fr297_marketing_e2e.sh` was a shim that only dialed Twilio
and waited for `completed` status — no utterance injection, no assertion on
extraction, graph state, or call flow.

## Proposed Solution

Three deliverables, following the NC-254 `callback_other_topic` pattern exactly:

### 1. Outcaller answerer graph: `outcaller_marketing_answerer.yaml`

Deterministic (no LLM) scripted graph in `projects/outcaller/graphs/`:

```
initiate_call → listen_greeting → speak_answer_1(name + organization)
→ listen_probe → speak_answer_2(memento_atk_days)
→ listen_recap → speak_confirm("Kyllä, oikein")
→ listen_farewell → end_call
```

**No navigator intent step.** Marketing mode sets `QUESTIONNAIRE_GRAPH`
directly to `graphs/callback_marketing/graph.yaml` — the navigator never
runs, no intent classification occurs. The FSM loads the marketing graph
immediately on `incoming_call`. The answerer speaks directly to the
questionnaire's opening prompt.

Variables passed from CLI:
- `phone` — target number (E.164)
- `name` — default "Testi Henkilö"
- `organization` — default "Testi Oy"
- `memento_atk_days` — default "Muistan kun ensimmäinen tietokone tuli toimistoon"
- `confirm` — default "Kyllä, yhteenveto on oikein"

Marketing has 4 fields (name, organization, memento_atk_days, miscellaneous)
but miscellaneous is optional — so the answerer provides 3 required fields
across 2 turns, matching the natural flow.

### 2. Shell wrapper: `start-marketing-answerer.sh`

In `projects/outcaller/`, mirrors `start-other-topic-answerer.sh`:
- Loads env (Twilio, ElevenLabs, ngrok)
- Parses `--phone`, `--name`, `--organization`, `--memento`, `--confirm`
- Fails fast with clear error if `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
  `TWILIO_PHONE_NUMBER`, or `ELEVENLABS_API_KEY` are unset
- Runs `yamlgraph graph run projects/outcaller/graphs/outcaller_marketing_answerer.yaml --var ... --full`

### 3. E2E test: `test-marketing-e2e.sh`

In `projects/ninchat_voice/`, mirrors `test-other-topic-e2e.sh`:
1. Starts ninchat_voice with `start-marketing.sh` (background, log capture)
2. Waits for "ready" in log (max 90s)
3. Reads phone from `.env`
4. Calls `start-marketing-answerer.sh --phone $PHONE`
5. Asserts on coordinator log:
   - ≥3 speak events (opening + probe + recap/farewell)
   - `graph_done` observed
   - No error transitions
   - `phase=done` or `complete=True` observed

**Note:** No `graph_switch` assertion — marketing mode loads the graph
directly without navigator routing.

### 4. Answerer graph structure test

`yamlgraph graph lint projects/outcaller/graphs/outcaller_marketing_answerer.yaml`
run as part of the answerer creation to verify compilation and node/edge
references. Cheap insurance against typos. (No separate test file — the
other_topic answerer has no structure test either; lint is sufficient.)

## Acceptance Criteria

- [ ] `outcaller_marketing_answerer.yaml` compiles and lints clean
- [ ] `start-marketing-answerer.sh` makes a successful call against running server
- [ ] `test-marketing-e2e.sh` passes against local `start-marketing.sh`
- [ ] All 4 coordinator log assertions pass
- [ ] Test exits cleanly (cleanup trap kills all child processes)
- [ ] Marketing schema fields extracted correctly (name, organization, memento_atk_days)
- [ ] Credential check: test script fails fast with clear message if env vars missing

## Alternatives Considered

1. **Direct Python interrupt/resume test** — Drives the compiled graph via
   `Command(resume=...)` without telephony. Higher value-per-cost for graph
   logic testing, but doesn't cover STT/TTS/WebSocket/Twilio integration.
   Should be Tier 1 (separate FR, complements this).

2. **Twilio call-to-self shim** (deleted `test_fr297_marketing_e2e.sh`) —
   Only checked call completion status. No utterance injection, no assertion
   on extraction. Useless as regression test.

## Judgement

**Verdict:** APPROVED — 3 refinements incorporated.

### Refinements applied

1. **Navigator intent trigger removed.** Marketing mode sets `QUESTIONNAIRE_GRAPH`
   directly — navigator never runs, no intent classification. The answerer graph
   no longer has a `speak_intent("Markkinointikysely")` step. The `graph_switch`
   log assertion is removed from the E2E test.

2. **Answerer Tier 0 test.** Added section §4: `yamlgraph graph lint` on the
   answerer graph as compilation guard. No separate test file — consistent with
   existing outcaller answerers, lint is sufficient.

3. **Credential fail-fast.** `start-marketing-answerer.sh` checks `TWILIO_ACCOUNT_SID`,
   `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `ELEVENLABS_API_KEY` before
   proceeding. Added to acceptance criteria.

## Related

- FR-297: Marketing campaign deployment (callback_marketing graph)
- NC-254: Other topic answerer (pattern source)
- `projects/outcaller/start-other-topic-answerer.sh` — reference implementation
- `projects/ninchat_voice/test-other-topic-e2e.sh` — reference E2E test
- `projects/outcaller/graphs/outcaller_other_topic_answerer.yaml` — reference graph

## Implementation

### Files created

1. **`projects/outcaller/graphs/outcaller_marketing_answerer.yaml`** — Deterministic
   2-turn scripted graph. No navigator intent step. Turn 1: name + organization,
   Turn 2: memento_atk_days. Cloned from `outcaller_other_topic_answerer.yaml`,
   intent classification nodes removed, second answer turn added.

2. **`projects/outcaller/start-marketing-answerer.sh`** — Shell wrapper with
   `--phone`, `--name`, `--organization`, `--memento`, `--confirm` arguments.
   Composes individual fields into `answer_1` and `answer_2` utterances.
   Credential fail-fast for TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
   TWILIO_PHONE_NUMBER, ELEVENLABS_API_KEY.

3. **`projects/ninchat_voice/test-marketing-e2e.sh`** — E2E test. Starts
   `start-marketing.sh`, waits for ready, calls via marketing answerer,
   asserts on 4 coordinator log conditions (≥3 speak events, graph_done,
   no error transitions, phase=done/complete=True). No `graph_switch`
   assertion per Judgement refinement §1.

### Lint result

`yamlgraph graph lint` on answerer graph: **0 errors**, 22 W003 warnings
(no path to END — consistent with all outcaller answerer graphs which
terminate at `end_call` without explicit END edge).
