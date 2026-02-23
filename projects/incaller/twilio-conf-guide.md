# Twilio Phone Number Configuration Guide

How to configure your Twilio phone number to route incoming calls to the incaller voicebot.

## Prerequisites

1. **Twilio account** with a phone number that supports voice calls
2. **ngrok** (or similar tunneling service) running and exposing port 8080
3. **VOICE_STREAM_URL** environment variable set to your public ngrok URL

## Step-by-Step Configuration

### 1. Start ngrok

```bash
ngrok http 8080
```

Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok-free.app`).

### 2. Navigate to Twilio Console

1. Go to [console.twilio.com](https://console.twilio.com)
2. Click **Phone Numbers** → **Manage** → **Active numbers**
3. Select your phone number

### 3. Configure Voice Settings

In the **Voice Configuration** section:

| Setting | Value |
|---------|-------|
| **A call comes in** | Webhook |
| **URL** | `https://<your-ngrok-subdomain>.ngrok-free.app/incoming` |
| **HTTP** | HTTP POST |

![Twilio Voice Configuration](https://console.twilio.com - Voice Configuration section)

**Important:** The URL must end with `/incoming` — this is the endpoint where the incaller server receives the Twilio webhook.

### 4. Leave Other Settings Default

| Setting | Recommended Value |
|---------|-------------------|
| **Primary handler fails** | Webhook (leave URL empty) |
| **Call status changes** | (leave empty) |
| **Caller Name Lookup** | Disabled |

### 5. Save Configuration

Click **Save configuration** at the bottom of the page.

## Verification

### Test the Webhook

Before making a real call, verify the endpoint is reachable:

```bash
curl -X POST "https://<your-ngrok-subdomain>.ngrok-free.app/incoming" \
  -d "From=+1234567890" \
  -d "To=+358454913431" \
  -d "CallSid=TEST123"
```

Expected response (TwiML):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://<your-ngrok-subdomain>.ngrok-free.app/voice" />
    </Connect>
</Response>
```

### Make a Test Call

1. Start the incaller:
   ```bash
   VOICE_STREAM_URL="https://<your-ngrok-subdomain>.ngrok-free.app" \
   yamlgraph graph run projects/incaller/graph.yaml \
     --var 'targets=caller_name:Your full name' \
     --full
   ```

2. Dial your Twilio phone number from any phone

3. The bot should greet you: "Thank you for calling..."

## Troubleshooting

### "No application to handle call"

- Verify the webhook URL is correct (ends with `/incoming`)
- Check ngrok is running and the URL is publicly accessible
- Look for errors in ngrok's web interface (http://localhost:4040)

### Call connects but no audio

- Check `VOICE_STREAM_URL` environment variable is set
- Verify the WebSocket URL in TwiML uses `wss://` (not `ws://`)
- Check incaller logs for WebSocket connection errors

### "CallNotAnsweredError" in incaller

- The incaller timed out waiting for a call (default: 300s)
- Verify Twilio webhook configuration points to your ngrok URL
- Try the curl test above to verify the endpoint responds

## Regional Considerations

The screenshot shows **US1 Region** routing. If your users are in a different region:

1. Click **Go to other configurations** in Twilio Console
2. Add regional voice URLs for lower latency

## Security Notes

- ngrok URLs are temporary — they change each time you restart ngrok
- For production, use a stable public URL (e.g., cloud deployment)
- Consider Twilio's [Request Validation](https://www.twilio.com/docs/usage/security#validating-requests) for production

## Related

- [Incaller README](./README.md) — Full setup and usage guide
- [Twilio Media Streams](https://www.twilio.com/docs/voice/media-streams) — WebSocket protocol docs
- [TwiML `<Connect>` verb](https://www.twilio.com/docs/voice/twiml/connect) — Stream configuration reference
