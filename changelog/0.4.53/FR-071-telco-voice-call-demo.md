---
type: feat
scope: telco
req: REQ-YG-083
---
- **FR-071 Telco Voice Call Demo** (REQ-YG-078–082): Outbound Twilio voice call with ElevenLabs TTS/STT
  - `projects/outcaller/`: YAMLGraph orchestrates call flow via Python tool nodes
  - `initiate_call`: Twilio REST API + FastAPI WebSocket server + ngrok tunnel
  - `speak`: ElevenLabs TTS → ffmpeg mulaw 8kHz → Twilio Media Stream
  - `listen_and_transcribe`: Twilio audio → ffmpeg PCM16 → ElevenLabs STT
  - `accumulate_answer`: Append transcript to state, loop back to LLM
  - Conditional edges replace router node for `[DONE]` detection
  - No audioop dependency (ffmpeg only); Python 3.13 compatible
  - Integration tests: `test_telco_twilio.py` (4 pass), `test_telco_elevenlabs.py` (4 pass)
  - Unit tests: `test_telco_nodes.py` (17 pass) with fixture-based mocking (no test pollution)
  - Optional `[telco]` extra: `twilio>=9.0.0`, `elevenlabs>=1.0.0`
