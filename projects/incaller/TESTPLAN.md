# Incaller Live Test Checklist

Manual integration test for IC-000 inbound voice call demo.

**Date:** _______________
**Tester:** _______________
**Twilio Number:** +358454913431

---

## Pre-flight Checks

- [ ] `.env` file exists in `projects/incaller/`
- [ ] `TWILIO_ACCOUNT_SID` set
- [ ] `TWILIO_AUTH_TOKEN` set
- [ ] `TWILIO_PHONE_NUMBER` set (+358454913431)
- [ ] `ELEVENLABS_API_KEY` set
- [ ] `PROVIDER` and API key set (e.g., `GOOGLE_API_KEY`)
- [ ] `ffmpeg` installed (`which ffmpeg`)
- [ ] `ngrok` installed (`which ngrok`)
- [ ] `jq` installed (`which jq`)

---

## Pre-Test Validation: Dialogue Prompts (No Twilio)

Before running live tests, verify the dialogue logic works:

```bash
python test_dialogue_e2e.py
```

### Expected Output

- [x] parse_targets → 2 targets parsed
- [x] check_missing → phase: probe
- [x] generate_probe → conversational question generated
- [x] extract_answers → both fields extracted from response
- [x] check_missing → phase: recap
- [x] generate_recap → summary generated
- [x] goodbye → farewell with [DONE] marker

**Status:** ✅ PASSED (2026-02-23)

---

## Test 1: Start Script Execution

```bash
cd projects/incaller
./start.sh
```

### Expected Output

- [ ] ngrok starts successfully
- [ ] ngrok URL displayed (e.g., `https://xxx.ngrok-free.app`)
- [ ] Twilio webhook update succeeds
- [ ] "Incaller ready!" message displayed
- [ ] Graph starts waiting for call

### Actual Result

```
ngrok URL: _______________
Twilio update: [ ] Success / [ ] Failed
```

**Notes:** _______________

---

## Test 2: Webhook Verification (curl)

In a separate terminal:

```bash
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
curl -X POST "${NGROK_URL}/incoming" \
  -d "From=+1234567890" \
  -d "To=+358454913431" \
  -d "CallSid=TEST123"
```

### Expected Output

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://xxx.ngrok-free.app/voice" />
    </Connect>
</Response>
```

### Actual Result

- [ ] TwiML response received
- [ ] Stream URL uses `wss://`
- [ ] Stream URL matches ngrok URL

**Notes:** _______________

---

## Test 3: Inbound Call — Targets Mode

1. Ensure `start.sh` is running with default targets:
   ```
   targets=caller_name:Your full name|reason:Why are you calling
   ```

2. Dial **+358454913431** from your phone

### Expected Behavior

| Step | Expected | Actual |
|------|----------|--------|
| Call connects | Ringing → Connected | [ ] Pass / [ ] Fail |
| Bot speaks greeting | "Thank you for calling..." | [ ] Pass / [ ] Fail |
| Bot asks for name | Probes for `caller_name` | [ ] Pass / [ ] Fail |
| STT transcribes response | Your name appears in logs | [ ] Pass / [ ] Fail |
| Bot asks reason | Probes for `reason` | [ ] Pass / [ ] Fail |
| STT transcribes response | Reason appears in logs | [ ] Pass / [ ] Fail |
| Bot recaps | Reads back collected data | [ ] Pass / [ ] Fail |
| User confirms | "Yes" / "Correct" | [ ] Pass / [ ] Fail |
| Bot says goodbye | "Thank you for calling..." | [ ] Pass / [ ] Fail |
| Call ends | Hangup | [ ] Pass / [ ] Fail |

### Final State Output

```
caller_name: _______________
reason: _______________
```

**Audio Quality:**
- [ ] TTS clear and understandable
- [ ] STT transcription accurate
- [ ] No audio dropouts
- [ ] Latency acceptable (<2s response)

**Notes:** _______________

---

## Test 4: Inbound Call — Questions Mode

1. Stop current `start.sh` (Ctrl+C)
2. Restart with questions:
   ```bash
   ./start.sh --var 'questions=What is your name?,How can I help you today?'
   ```
3. Dial **+358454913431**

### Expected Behavior

| Step | Expected | Actual |
|------|----------|--------|
| Bot asks question 1 | "What is your name?" | [ ] Pass / [ ] Fail |
| User responds | Transcribed | [ ] Pass / [ ] Fail |
| Bot asks question 2 | "How can I help you today?" | [ ] Pass / [ ] Fail |
| User responds | Transcribed | [ ] Pass / [ ] Fail |
| Conversation ends | Goodbye or timeout | [ ] Pass / [ ] Fail |

**Notes:** _______________

---

## Test 5: Error Handling

### 5a. No Answer Timeout

1. Start incaller
2. Do NOT call within 300 seconds

**Expected:** `CallNotAnsweredError` raised, script exits

- [ ] Error message displayed
- [ ] Clean shutdown (no zombie processes)

### 5b. User Refuses

1. Start incaller
2. Call and say "I don't want to answer" or "No"

**Expected:** Bot handles refusal gracefully

- [ ] Polite exit message
- [ ] Call ends

### 5c. WebSocket Disconnect

1. Start incaller
2. Call and hang up mid-conversation

**Expected:** Clean handling

- [ ] No crash
- [ ] Resources released

**Notes:** _______________

---

## Test 6: Cleanup

After all tests:

```bash
# Check for zombie processes
ps aux | grep -E 'ngrok|uvicorn|ffmpeg' | grep -v grep

# Kill any stragglers
pkill -f "ngrok http 8080"
```

- [ ] No orphan processes remain
- [ ] ngrok tunnel closed

---

## Summary

| Test | Result | Notes |
|------|--------|-------|
| 1. Start Script | [ ] Pass / [ ] Fail | |
| 2. Webhook curl | [ ] Pass / [ ] Fail | |
| 3. Targets Mode | [ ] Pass / [ ] Fail | |
| 4. Questions Mode | [ ] Pass / [ ] Fail | |
| 5a. Timeout | [ ] Pass / [ ] Fail | |
| 5b. Refusal | [ ] Pass / [ ] Fail | |
| 5c. Disconnect | [ ] Pass / [ ] Fail | |
| 6. Cleanup | [ ] Pass / [ ] Fail | |

**Overall Result:** [ ] PASS / [ ] FAIL

**Blocking Issues:**

1. _______________
2. _______________

**Observations:**

_______________

---

## Sign-off

Tested by: _______________ Date: _______________
