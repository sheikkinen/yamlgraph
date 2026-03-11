---
type: feat
scope: ninchat
---
- **FR-109 Ninchat Voice Coordinator** (`projects/ninchat_voice`): Graph-as-coordinator for Twilio ↔ Ninchat bot voice calls
  - `graphs/ninchat-voice-coordinator.yaml`: 10-node graph with conditional call-loop and hangup guard
  - `nodes/ninchat_session.py`: NinchatConnection WebSocket client (`create_session`/`send_to_bot`/`close_session`)
  - `nodes/voice_ws.py`: Twilio Media Stream TTS/STT via shared outcaller TelcoSession
  - `prompts/`: Finnish mediator prompts (greeting rewrite + response rewrite with Jinja2)
  - `server.py`: FastAPI `/incoming` webhook + WebSocket voice endpoint
  - 21 unit tests with `NV-000` project-local req markers, lint-clean
