# Incaller - Inbound Voice Call Demo

IC-000: Inbound Twilio voice call with ElevenLabs TTS/STT.
Reuses outcaller TTS/STT/probe-recap (REQ-YG-086).

Receives incoming calls to a Twilio phone number and conducts voicebot conversations.

## Architecture

The incaller supports two base modes based on CLI parameters (same as outcaller),
plus an optional issue-intake post-confirmation mode:

### Mode 1: Questions Mode

Pass `--var 'questions=...'` for free-form conversation:

```
[await_call] → [generate_response] → [speak] → [listen] → [accumulate_answer] ─┐
                      ↑                                                         │
                      └─────────────────────────────────────────────────────────┘
```

### Mode 2: Targets Mode (Probe-Recap)

Pass `--var 'targets=...'` for structured data collection:

```
[await_call] → [parse_targets] → [check_missing] → [generate_probe] → [speak] → ...
```

(Same flow as outcaller after `await_call` — see outcaller README for details)

### Mode 3: GitHub Issue Intake (`mode=github_issue_intake`)

When running Targets Mode, set `--var 'mode=github_issue_intake'` to create a
GitHub issue after recap confirmation. The caller hears either:

1. Issue URL + issue number on success, or
2. Explicit error details on failure.

Optional `chaplain_opt_in` controls whether the created issue includes the
`chaplain` label.

## Key Difference from Outcaller

| Aspect | Outcaller | Incaller |
|--------|-----------|----------|
| Entry node | `initiate_call` (dials out) | `await_call` (waits for incoming) |
| Twilio trigger | REST API outbound call | Webhook POST to `/incoming` |
| Phone var | Required (`--var phone=...`) | Not needed (caller dials in) |
| Timeout | 30s (call placed immediately) | 300s (waiting for human to call) |
| Greeting | "Hello, I'm calling..." | "Thank you for calling..." |

## Prerequisites

### System Dependencies

**ffmpeg** is required for TTS audio transcoding (MP3 → mulaw 8kHz):

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

For `github_issue_intake` mode, install GitHub CLI and authenticate:

```bash
gh auth login
```

### Python Dependencies

Install optional telco extras:

```bash
pip install "yamlgraph[telco]"
```

Or manually:

```bash
pip install twilio elevenlabs httpx
```

### Environment Variables

Copy from outcaller or create `.env`:

```bash
cp ../outcaller/.env .env
```

Required environment variables:

```bash
# Twilio credentials
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+your_twilio_number

# ElevenLabs API
ELEVENLABS_API_KEY=your_elevenlabs_key

# Public URL for WebSocket (ngrok)
VOICE_STREAM_URL=https://your-subdomain.ngrok.io

# Optional: timeout for waiting for call (default: 300s)
INCALLER_TIMEOUT=300
```

### ngrok Setup

The incaller server must be reachable by Twilio. For local development, use ngrok:

```bash
# Start ngrok
ngrok http 8080

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
export VOICE_STREAM_URL="https://abc123.ngrok.io"
```

### Twilio Phone Number Configuration

Your Twilio phone number must be configured to webhook to the incaller:

1. Go to [Twilio Console](https://console.twilio.com) → Phone Numbers → Active Numbers
2. Select your phone number
3. Under "Voice & Fax":
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-subdomain.ngrok.io/incoming`
   - **HTTP**: POST
4. Save

Alternatively, configure via Twilio CLI:

```bash
twilio phone-numbers:update +358454918222 \
  --voice-url="https://your-subdomain.ngrok.io/incoming"
```

## Quick Start (Automated)

The easiest way to run the incaller:

```bash
# 1. Copy and edit .env
cp .env.example .env
# Edit .env with your Twilio and ElevenLabs credentials

# 2. Run the start script
./start.sh
```

The script automatically:
1. Starts ngrok on port 8080
2. Updates your Twilio phone number webhook
3. Runs the voicebot graph

Then just dial your Twilio number!

## Usage (Manual)

### Targets Mode (Structured Data Collection)

```bash
# Start ngrok first
ngrok http 8080

# In another terminal
VOICE_STREAM_URL="https://your-subdomain.ngrok.io" \
yamlgraph graph run projects/incaller/graph.yaml \
  --var 'targets=caller_name:Your full name|issue:Describe your issue' \
  --full
```

Then dial your Twilio phone number. The bot will greet you and collect the target fields.

### Targets + GitHub Issue Intake Mode

```bash
VOICE_STREAM_URL="https://your-subdomain.ngrok.io" \
yamlgraph graph run projects/incaller/graph.yaml \
  --var 'mode=github_issue_intake' \
  --var 'targets=issue_title:Issue title|issue_type:feat fix docs chore|issue_summary:Problem and expected outcome|chaplain_opt_in:yes or no' \
  --full
```

If recap is confirmed, the graph runs `gh issue create` and reads back either
the issue URL or an explicit creation error.

### Questions Mode (Free-Form Conversation)

```bash
VOICE_STREAM_URL="https://your-subdomain.ngrok.io" \
yamlgraph graph run projects/incaller/graph.yaml \
  --var 'questions=What is your name?,How can I help you today?' \
  --full
```

## File Structure

```
projects/incaller/
├── __init__.py                       # Package marker
├── .env                              # API keys (copy from outcaller)
├── graph.yaml                        # Incaller graph (await_call + shared nodes)
├── server.py                         # FastAPI: POST /incoming + WS /voice
├── README.md                         # This file
├── IC-000-incaller-voicebot.md       # Feature request
├── nodes/
│   ├── __init__.py
│   └── twilio_inbound.py             # await_call() — only new node
└── prompts/
    ├── conversation.yaml             # Inbound conversation prompt
    ├── generate_probe.yaml           # Welcome + probe (inbound tone)
    ├── generate_recap.yaml           # Recap prompt
    ├── analyze_recap_response.yaml   # Recap analysis
    ├── extract_answers.yaml          # Answer extraction
    ├── goodbye.yaml                  # "Thank you for calling"
    └── goodbye_refused.yaml          # Polite exit on refusal
```

## Testing

```bash
# Unit tests
pytest tests/unit/test_incaller.py -v

# Integration tests (require API keys)
pytest tests/integration/test_telco_*.py -v
```

## Troubleshooting

### Call connects but no audio

- Check that `VOICE_STREAM_URL` is publicly accessible
- Verify ngrok is running and the URL matches
- Check Twilio console for webhook errors

### "MissingStreamUrlError"

Set `VOICE_STREAM_URL` environment variable.

### "CallNotAnsweredError"

No call received within timeout. Check:
- Twilio phone number webhook configuration
- ngrok is running and URL is correct
- You're dialing the correct number

### WebSocket disconnects immediately

Twilio may reject the TwiML response. Check:
- `/incoming` endpoint returns valid XML
- Stream URL uses `wss://` not `ws://`

## Related

- [Outcaller README](../outcaller/README.md) — Outbound call demo
- [IC-000 Feature Request](./IC-000-incaller-voicebot.md) — Full specification
- [Twilio Media Streams](https://www.twilio.com/docs/voice/media-streams) — Twilio WebSocket protocol
