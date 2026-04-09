# Voice AI Test Platform Research

**Date:** 2026-04-09
**Context:** Evaluating existing platforms and approaches for automated voice system testing, with outcaller as the candidate engine.

## Problem Statement

We need to automatically test voice AI systems (e.g. ninchat_voice) by calling them, conversing, and verifying behavior. The outcaller project already makes real outbound Twilio calls with ElevenLabs TTS/STT and YAMLGraph orchestration. The question: build on outcaller, adopt an existing platform, or something else?

## Current Assets

### outcaller (internal)

| Capability | Status |
|-----------|--------|
| Real Twilio outbound/inbound calls | ✅ Working |
| ElevenLabs TTS (eleven_flash_v2_5) + STT (scribe_v2_realtime) | ✅ Working |
| YAMLGraph declarative call flow | ✅ Working |
| Probe-recap structured data extraction with LLM | ✅ Working |
| Pydantic-validated LLM outputs (Extraction, RecapAnalysis) | ✅ Working |
| Disconnect/refusal detection with graceful exit | ✅ Working |
| E2E dialogue test (no telephony, simulated turns) | ✅ Working |
| 314 unit tests (no API keys needed) | ✅ Working |
| Declarative test scenario format | ❌ Missing |
| Turn-level assertions | ❌ Missing |
| Structured verdict/report output | ❌ Missing |
| Multi-scenario batch runner | ❌ Missing |
| CI/CD integration (exit codes, headless) | ❌ Missing |

### ninchat_voice (sample target system)

FSM-based voice coordinator bridging Twilio inbound calls to Ninchat chatbot backend. 361+ unit tests. Three modes: simple, bargein, questionnaire. Not a test tool — an example of a system to test.

### voice_runtime (shared)

Shared transport layer: VoiceSession, Twilio WebSocket handler, ElevenLabs TTS/STT providers, audio codec. Used by both outcaller and ninchat_voice.

## Market Landscape

### Commercial Platforms

#### Cyara (incl. Botium)

- **What:** Full CX assurance platform — IVR testing, chatbot testing (55+ connectors), load testing, monitoring, LLM trust validation (FactCheck, hallucination, bias detection).
- **Voice:** Real PSTN calls in 140+ countries, outbound + inbound.
- **Pricing:** Enterprise ~$50K+/yr.
- **Fit:** Overkill. Designed for large contact centers with 100+ agents. No open API for custom orchestration. Botium (acquired) is text-only.
- **URL:** https://cyara.com/platform/

#### Hammer (Infovista)

- **What:** Voice Explorer (IVR testing), CallMaster (IVR development), VoiceWatch (monitoring), on-demand performance/QA.
- **Voice:** Real PSTN, DTMF IVR navigation.
- **Fit:** Legacy IVR/DTMF era tooling. Not designed for conversational AI or LLM-powered bots.
- **URL:** https://www.hammer.com/products

**Verdict:** Neither commercial platform fits. Both are enterprise-priced, contact-center-scoped, and not designed for testing individual LLM voice bots.

### Open Source

#### Botium (botium-core) — "Selenium for Chatbots"

- **Stars:** 250 | **Language:** JavaScript | **License:** MIT
- **What:** Text-based bot testing framework with connectors for 55+ chatbot platforms. Declarative test scripts. Now acquired by Cyara.
- **Voice:** None — text-only.
- **Relevance:** Connector pattern is interesting but inapplicable to voice.
- **URL:** https://github.com/codeforequity-at/botium-core

#### Vocode (vocode-core)

- **Stars:** 3,700 | **Language:** Python | **License:** MIT
- **What:** Open source voice AI agent framework (Twilio, Deepgram, ElevenLabs, multiple LLMs). Build voice apps, not test them.
- **Voice:** Yes, but for building agents, not testing them. Last updated Nov 2024 — appears stale.
- **Relevance:** Architecture reference for voice app building. Not a test framework.
- **URL:** https://github.com/vocodedev/vocode-core

#### Audrique — E2E Voice Workflow Testing

- **Stars:** 1 | **Language:** JS/TS | **License:** MIT
- **What:** End-to-end voice testing for Salesforce Service Cloud Voice + Amazon Connect. Real calls via Connect CCP or Twilio REST. Playwright browser verification. CRM record validation. **AI-to-AI voice testing via Gemini Live** (NL Caller).
- **Voice:** Yes — real calls + AI caller persona.
- **Key features:**
  - Declarative JSON scenario DSL
  - Visual Scenario Studio (drag-and-drop at localhost:4200)
  - Video evidence capture (FFmpeg merge)
  - PostgreSQL test results tracking
  - Auth/RBAC, headless CI, exit codes
- **Limitation:** Tightly coupled to Salesforce + Amazon Connect. Not generalizable without major work.
- **URL:** https://github.com/snehalsurti12/audrique

#### TRACER — Chatbot Explorer

- **Stars:** 2 | **Language:** Python | **License:** GPL-3.0
- **What:** Automated chatbot exploration using LLMs. Multi-session conversations to discover functionalities, generate workflow graphs, create user profiles for testing. Connector-based architecture.
- **Voice:** Text only.
- **Relevance:** The "explorer" concept — autonomously probe unknown systems — is valuable for discovery phase before scripted tests.
- **URL:** https://github.com/Chatbot-TRACER/TRACER

#### ContextCheck — LLM/RAG/Chatbot Testing

- **Stars:** 94 | **Language:** Python | **License:** MIT
- **What:** YAML-defined test scenarios for LLMs, RAGs, chatbots. Deterministic (rule-based) + LLM-based assertion metrics. CI/CD ready with `--exit-on-failure`. Jinja2 templating in YAML.
- **Voice:** None — HTTP request/response oriented.
- **Relevance:** **Scenario YAML format and assertion engine are directly applicable.** Best ergonomic reference for how test scenarios should look.
- **CLI:** `ccheck --output-type console --filename scenario.yaml`
- **URL:** https://github.com/Addepto/contextcheck

#### VoiceEval

- **Stars:** 1 | **Language:** Python | **License:** Apache 2.0
- **What:** Planned voice AI testing framework — WER, latency, task completion, LLM-as-judge, pytest integration.
- **Status:** **Vaporware.** Empty repo, "coming soon," no code, no releases.
- **URL:** https://github.com/voiceeval/voiceeval

### Landscape Summary

```
                    Voice Support
                    ▲
                    │
         Cyara ●    │    ● Audrique (Salesforce-coupled)
    (enterprise)    │
                    │
         Hammer ●   │
      (IVR/DTMF)   │
                    │                    ● Outcaller (ours)
                    │
                    ├──────────────────────────────────────► Generalizability
                    │
       Botium ●     │    ● ContextCheck
    (text-only)     │    (YAML scenarios, CI/CD)
                    │
        TRACER ●    │    ● VoiceEval (vaporware)
    (explorer)      │
```

**Key finding:** No general-purpose open-source voice AI test framework exists. The closest (Audrique) is Salesforce-coupled. ContextCheck has the best scenario ergonomics but is text-only. The space is wide open.

## Feature Comparison: What a Voice Test Platform Needs

| Capability | Cyara | Audrique | ContextCheck | Outcaller Today | Outcaller + Test Layer |
|-----------|-------|----------|-------------|-----------------|----------------------|
| Real voice calls | ✅ | ✅ | ❌ | ✅ | ✅ |
| Declarative scenario format | ✅ | JSON DSL | YAML | ❌ (flat `--var`) | ✅ (YAML) |
| Turn-level assertions | ✅ | Playwright | Deterministic + LLM | ❌ | ✅ |
| AI caller persona | ❌ | Gemini Live | ❌ | LLM-generated speech | ✅ |
| Multi-scenario batch | ✅ | Suite runner | `--folder` | ❌ | ✅ |
| Verdict/report | Dashboard | JSON + video | Console + exit code | Console print | JSON + exit code |
| CI/CD exit codes | ✅ | ✅ | `--exit-on-failure` | ❌ | ✅ |
| LLM-as-judge | ❌ | ❌ | ✅ | ❌ | ✅ |
| Text-mode (no telephony) | ❌ | ❌ | ✅ | ✅ (e2e dialogue) | ✅ |
| Open source | ❌ | ✅ (MIT) | ✅ (MIT) | Internal | Potential |
| Price | ~$50K+/yr | Free | Free | Free | Free |

## Strategic Options

### Option A: Extend Outcaller with Test Layer (recommended)

Keep outcaller as the voice transport engine. Add scenario format, assertion engine, and verdict reporter on top.

```
YAML test scenarios (new)
        │
    Test Runner CLI (new)
        │  orchestrates
    Outcaller YAMLGraph (existing)
        │  via Twilio + ElevenLabs
    Target Voice System (any)
```

**Steal from:**
- ContextCheck: YAML scenario format, deterministic + LLM assertion metrics, `--exit-on-failure` CI mode
- Audrique: AI caller persona concept, structured verdict output, video evidence idea

**Keep from outcaller:** Twilio transport, ElevenLabs TTS/STT, YAMLGraph orchestration, probe-recap loop, Pydantic validation

**Effort:** Medium. The probe-recap loop is already a test framework that collects structured data and verifies it.

### Option B: Fork ContextCheck, Add Voice

ContextCheck is MIT, Python, YAML-first, CI-ready. Add a `voice` endpoint type using Twilio + ElevenLabs.

**Problem:** ContextCheck is request/response oriented. Voice conversations are stateful multi-turn with timing, barge-in, silence detection. Retrofitting is harder than building on outcaller.

### Option C: TRACER-Style Autonomous Explorer

Use outcaller to autonomously explore unknown voice systems:
- Dial the target
- LLM decides what to say each turn (no script)
- Map discovered workflows as a directed graph
- Generate test scenarios from discovered paths

**Best for:** Unknown target systems, discovery phase before writing scripted tests. Complementary to Option A.

### Option D: Adopt Audrique

Use Audrique's NL Caller (Gemini Live) as the AI caller.

**Problem:** JS/TS, tightly coupled to Salesforce + Amazon Connect. Would require a near-complete rewrite to work with arbitrary voice systems. Not practical.

## Recommended Architecture

### Option A Implementation Plan

#### Scenario YAML Format (inspired by ContextCheck)

```yaml
# test-scenarios/booking-happy-path.yaml
name: "Appointment booking - happy path"
target:
  phone: "+358401234567"
  label: "ninchat_voice staging"
  language: "fi"

caller:
  persona: |
    You are Matti Virtanen, age 45.
    You want to book a dental appointment for next Tuesday at 10am.
    Be cooperative and answer questions directly.
  voice_id: "EXAVITQu4vr4xnSDxMaL"  # optional ElevenLabs voice

turns:
  - wait_for: greeting
    assert:
      - type: contains_any
        values: ["tervetuloa", "hei", "miten voin auttaa"]
      - type: language
        expected: "fi"
    respond: "Haluaisin varata ajan hammaslääkärille"

  - wait_for: response
    assert:
      - type: intent
        expected: "asking_for_date_or_time"
        model: "gemini-2.5-flash"
    respond: "Ensi tiistaina kello kymmenen"

  - wait_for: confirmation
    assert:
      - type: intent
        expected: "confirming_appointment"
      - type: contains_any
        values: ["tiistai", "kello 10"]
    respond: "Kyllä, se sopii"

  - wait_for: goodbye
    assert:
      - type: intent
        expected: "farewell"

verdict:
  require_all_turns: true
  max_duration_s: 120
  require_clean_hangup: true
```

#### Assertion Types

| Type | Method | Cost |
|------|--------|------|
| `contains_any` | Substring match (any of values) | Free |
| `contains_all` | Substring match (all values) | Free |
| `not_contains` | Negative substring | Free |
| `regex` | Regex pattern match | Free |
| `language` | Detected language matches expected | Free (heuristic) or LLM |
| `intent` | LLM judges semantic intent | ~$0.001/call |
| `sentiment` | Positive/negative/neutral | ~$0.001/call |
| `schema` | LLM extracts structured data, validates against fields | ~$0.001/call |
| `min_words` / `max_words` | Response length bounds | Free |
| `silence_timeout` | System responds within N seconds | Free |

#### Verdict Output (JSON)

```json
{
  "scenario": "booking-happy-path",
  "target": "+358401234567",
  "status": "PASS",
  "duration_s": 67.3,
  "turns": [
    {
      "turn": 0,
      "system_said": "Hei, tervetuloa. Miten voin auttaa?",
      "assertions": [
        {"type": "contains_any", "passed": true, "matched": "tervetuloa"},
        {"type": "language", "passed": true, "detected": "fi"}
      ],
      "caller_said": "Haluaisin varata ajan hammaslääkärille"
    }
  ],
  "assertions_passed": 7,
  "assertions_failed": 0,
  "call_sid": "CA1234567890abcdef",
  "timestamp": "2026-04-09T14:30:00Z"
}
```

#### CLI

```bash
# Run single scenario
yamlgraph voice-test run scenarios/booking-happy-path.yaml

# Run all scenarios in folder
yamlgraph voice-test run scenarios/ --exit-on-failure

# Text-mode (no Twilio, simulated turns — for CI)
yamlgraph voice-test run scenarios/ --text-mode

# Output JSON verdicts
yamlgraph voice-test run scenarios/ --output verdicts/
```

### Implementation Phases

| Phase | What | Effort | Value |
|-------|------|--------|-------|
| **P0** | Scenario YAML schema + `load_scenario` parser | Small | Foundation |
| **P1** | Assertion engine (deterministic: contains, regex, length) | Small | First automated pass/fail |
| **P2** | LLM-as-judge assertions (intent, sentiment) | Small | Semantic validation |
| **P3** | Text-mode harness (mock TelcoSession, no Twilio) for CI | Small | Fast feedback, no cost |
| **P4** | Verdict JSON output + CLI `--exit-on-failure` | Small | CI/CD integration |
| **P5** | Batch runner (`yamlgraph voice-test run folder/`) | Small | Multi-scenario automation |
| **P6** | Real-call runner (Twilio) for staging | Small (reuse P0-P4) | End-to-end confidence |
| **P7** | Golden transcript regression (record once, diff later) | Medium | Drift detection |
| **P8** | TRACER-style explorer mode (autonomous, no script) | Medium | Discovery for unknown systems |

## Competitive Position

Outcaller as a voice test platform would be:
- **The only open-source tool combining real telephony + LLM orchestration + declarative test scenarios**
- Built on proven infrastructure (Twilio, ElevenLabs, YAMLGraph)
- Python-native with pytest integration potential
- YAML-first (consistent with ContextCheck's approach, which has 94 stars with text-only)

The market gap is real: enterprises pay $50K+/yr for Cyara doing roughly this. No OSS alternative exists for voice.

## References

| Source | URL |
|--------|-----|
| Cyara Platform | https://cyara.com/platform/ |
| Cyara Botium | https://cyara.com/products/botium/ |
| Hammer Products | https://www.hammer.com/products |
| Audrique | https://github.com/snehalsurti12/audrique |
| ContextCheck | https://github.com/Addepto/contextcheck |
| TRACER | https://github.com/Chatbot-TRACER/TRACER |
| VoiceEval | https://github.com/voiceeval/voiceeval |
| Botium Core | https://github.com/codeforequity-at/botium-core |
| Vocode Core | https://github.com/vocodedev/vocode-core |
