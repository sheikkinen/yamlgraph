---
type: feat
scope: ic-000
req: REQ-YG-084
---
- **IC-000 Incaller Voice Demo** (REQ-YG-084–086): Inbound Twilio voice call with ElevenLabs TTS/STT
  - `projects/incaller/`: Receives incoming calls to Twilio phone number
  - `await_call`: New node starts HTTP+WS server, waits for `/incoming` webhook (300s timeout)
  - `/incoming` webhook: Returns TwiML `<Connect><Stream>` for bidirectional audio
  - Reuses outcaller TTS/STT/probe-recap nodes — only `await_call` is new
  - TelcoSession extended with `caller_number` field and `start_with_app()` method
  - 7 prompts adapted for inbound tone ("Thank you for calling...")
  - `start.sh`: Automated setup — starts ngrok, updates Twilio webhook via API, runs graph
  - Unit tests: `test_incaller.py` (9 pass) covering all three requirements
