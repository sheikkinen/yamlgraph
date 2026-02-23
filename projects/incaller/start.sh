#!/bin/bash
# Incaller start script
# Starts ngrok, updates Twilio webhook, and runs the incaller graph

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment
if [[ -f .env ]]; then
    export $(grep -v '^#' .env | xargs)
fi

# Required environment variables
: "${TWILIO_PHONE_NUMBER:?Set TWILIO_PHONE_NUMBER in .env (e.g., +358454913431)}"
: "${TWILIO_ACCOUNT_SID:?Set TWILIO_ACCOUNT_SID in .env}"
: "${TWILIO_AUTH_TOKEN:?Set TWILIO_AUTH_TOKEN in .env}"
: "${ELEVENLABS_API_KEY:?Set ELEVENLABS_API_KEY in .env}"

PORT=${PORT:-8080}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting incaller...${NC}"

# Check for required tools
command -v ngrok >/dev/null 2>&1 || { echo -e "${RED}ngrok not found. Install: brew install ngrok${NC}"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}jq not found. Install: brew install jq${NC}"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo -e "${RED}curl not found${NC}"; exit 1; }

# Kill any existing ngrok on this port
pkill -f "ngrok http $PORT" 2>/dev/null || true
sleep 1

# Start ngrok in background
echo -e "${YELLOW}📡 Starting ngrok on port $PORT...${NC}"
ngrok http $PORT --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
echo -n "Waiting for ngrok..."
for i in {1..30}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[] | select(.proto=="https") | .public_url' 2>/dev/null | head -1)
    if [[ -n "$NGROK_URL" && "$NGROK_URL" != "null" ]]; then
        break
    fi
    echo -n "."
    sleep 1
done
echo

if [[ -z "$NGROK_URL" || "$NGROK_URL" == "null" ]]; then
    echo -e "${RED}❌ Failed to start ngrok. Check /tmp/ngrok.log${NC}"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ ngrok URL: $NGROK_URL${NC}"
export VOICE_STREAM_URL="$NGROK_URL"

# Update Twilio webhook
echo -e "${YELLOW}📞 Updating Twilio webhook for $TWILIO_PHONE_NUMBER...${NC}"
WEBHOOK_URL="${NGROK_URL}/incoming"

# Use Twilio API directly (no CLI dependency)
RESPONSE=$(curl -s -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json" \
    -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
    -d "PhoneNumber=${TWILIO_PHONE_NUMBER}" \
    --data-urlencode "VoiceUrl=${WEBHOOK_URL}" \
    --data-urlencode "VoiceMethod=POST" 2>&1)

# Check if it's a list response (phone number exists)
SID=$(echo "$RESPONSE" | jq -r '.incoming_phone_numbers[0].sid // .sid' 2>/dev/null)

if [[ -z "$SID" || "$SID" == "null" ]]; then
    # Try to find the phone number SID first
    PHONE_LIST=$(curl -s "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json?PhoneNumber=${TWILIO_PHONE_NUMBER}" \
        -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}")
    SID=$(echo "$PHONE_LIST" | jq -r '.incoming_phone_numbers[0].sid' 2>/dev/null)

    if [[ -n "$SID" && "$SID" != "null" ]]; then
        # Update the phone number by SID
        RESPONSE=$(curl -s -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers/${SID}.json" \
            -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
            --data-urlencode "VoiceUrl=${WEBHOOK_URL}" \
            --data-urlencode "VoiceMethod=POST")
    fi
fi

# Verify update
UPDATED_URL=$(echo "$RESPONSE" | jq -r '.voice_url' 2>/dev/null)
if [[ "$UPDATED_URL" == "$WEBHOOK_URL" ]]; then
    echo -e "${GREEN}✓ Twilio webhook updated: $WEBHOOK_URL${NC}"
else
    echo -e "${RED}⚠ Could not verify Twilio update. Response:${NC}"
    echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
    echo -e "${YELLOW}You may need to update manually in Twilio Console${NC}"
fi

# Cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down...${NC}"
    kill $NGROK_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Stopped ngrok${NC}"
}
trap cleanup EXIT

# Print ready message
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Incaller ready!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ngrok URL:     ${NGROK_URL}"
echo -e "  Webhook:       ${WEBHOOK_URL}"
echo -e "  Twilio number: ${TWILIO_PHONE_NUMBER}"
echo ""
echo -e "  ${YELLOW}Dial ${TWILIO_PHONE_NUMBER} to test the voicebot${NC}"
echo ""

# Run the graph
echo -e "${YELLOW}🎙️  Starting voicebot graph...${NC}"
echo ""

# Default to targets mode if no args provided
if [[ $# -eq 0 ]]; then
    yamlgraph graph run graph.yaml \
        --var 'prompts_dir=projects/incaller/prompts' \
        --var 'targets=caller_name:Your full name|reason:Why are you calling' \
        --full
else
    yamlgraph graph run graph.yaml --var 'prompts_dir=projects/incaller/prompts' "$@" --full
fi
