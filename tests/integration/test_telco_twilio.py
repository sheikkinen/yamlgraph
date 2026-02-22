"""Integration tests for Twilio + WebSocket streaming.

Tests the Twilio REST API and WebSocket server independently of ElevenLabs.
Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, CLIENT_PHONE_NUMBER

Run with: pytest tests/integration/test_telco_twilio.py -v -s
"""

import os
import time

import pytest

# Skip all tests if Twilio credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("TWILIO_ACCOUNT_SID"),
    reason="TWILIO_ACCOUNT_SID not set",
)


@pytest.fixture
def twilio_client():
    """Create Twilio client."""
    from twilio.rest import Client

    return Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
    )


class TestTwilioConnection:
    """Test Twilio REST API connectivity."""

    @pytest.mark.req("REQ-YG-078")
    def test_account_info(self, twilio_client):
        """Verify Twilio credentials are valid.

        REQ-YG-078: Twilio REST API connectivity.
        """
        account = twilio_client.api.accounts(os.getenv("TWILIO_ACCOUNT_SID")).fetch()
        assert account.status == "active"
        print(f"✓ Account: {account.friendly_name}")

    @pytest.mark.req("REQ-YG-078")
    def test_phone_number_exists(self, twilio_client):
        """Verify outbound phone number exists.

        REQ-YG-078: Twilio phone number configured.
        """
        phone = os.getenv("TWILIO_PHONE_NUMBER")
        numbers = twilio_client.incoming_phone_numbers.list(phone_number=phone)
        assert len(numbers) > 0, f"Phone number {phone} not found in account"
        print(f"✓ Phone number: {numbers[0].phone_number}")


class TestWebSocketServer:
    """Test in-process WebSocket server."""

    @pytest.mark.req("REQ-YG-081")
    def test_server_starts_and_stops(self):
        """Verify TelcoSession server lifecycle.

        REQ-YG-081: WebSocket coordinator lifecycle.
        """
        from projects.outcaller.nodes.coordinator import TelcoSession

        session = TelcoSession()
        session.start()
        time.sleep(0.5)  # Give uvicorn time to bind

        # Check server is listening
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 8080))
        sock.close()
        assert result == 0, "Server not listening on port 8080"
        print("✓ Server listening on port 8080")

        session.shutdown()
        print("✓ Server shutdown cleanly")

    @pytest.mark.req("REQ-YG-081")
    def test_server_health_endpoint(self):
        """Verify /health endpoint responds.

        REQ-YG-081: WebSocket server health check.
        """
        import httpx

        from projects.outcaller.nodes.coordinator import TelcoSession

        session = TelcoSession()
        session.start()
        time.sleep(0.5)

        try:
            response = httpx.get("http://127.0.0.1:8080/health", timeout=5.0)
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            print("✓ Health endpoint OK")
        finally:
            session.shutdown()


class TestTwilioOutboundCall:
    """Test actual outbound call (EXPENSIVE - calls real phone)."""

    @pytest.mark.req("REQ-YG-078")
    @pytest.mark.skip(reason="Expensive: makes real phone call")
    def test_outbound_call_connects(self, twilio_client):
        """Make outbound call and verify WebSocket connects.

        REQ-YG-078: YAMLGraph orchestrates outbound Twilio voice call.

        This test:
        1. Starts local WebSocket server
        2. Starts ngrok tunnel (must be running externally)
        3. Makes outbound call via Twilio
        4. Waits for WebSocket connection
        """
        from projects.outcaller.nodes.coordinator import (
            TelcoSession,
            set_active_session,
        )

        ngrok_url = os.getenv("NGROK_URL")
        client_phone = os.getenv("CLIENT_PHONE_NUMBER")
        assert ngrok_url, "NGROK_URL not set"
        assert client_phone, "CLIENT_PHONE_NUMBER not set"

        session = TelcoSession()
        session.start()
        set_active_session(session)
        time.sleep(1.0)

        try:
            # Convert to wss:// for Twilio
            ws_url = ngrok_url.replace("https://", "wss://")
            twiml = f"""
            <Response>
                <Connect>
                    <Stream url="{ws_url}/voice" />
                </Connect>
            </Response>
            """

            call = twilio_client.calls.create(
                to=client_phone,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                twiml=twiml.strip(),
            )
            print(f"✓ Call initiated: {call.sid}")

            # Wait for WebSocket connection (answer the phone!)
            session.wait_for_ws_connect(timeout=30.0)
            print(f"✓ WebSocket connected: {session.stream_sid}")

            # Send a test silence frame
            silence = bytes([0xFF] * 640)
            session.put_outbound_sync(silence)
            print("✓ Outbound audio queued")

            # Hang up
            twilio_client.calls(call.sid).update(status="completed")
            print("✓ Call ended")

        finally:
            session.shutdown()
