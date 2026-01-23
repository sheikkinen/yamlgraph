"""Tests for email sending node."""


class TestSendEmail:
    """Tests for send_email node."""

    def test_sends_email_with_resend(self, mock_resend):
        """send_email calls Resend API."""
        from examples.daily_digest.nodes.email import send_email

        state = {
            "recipient_email": "test@example.com",
            "today": "2026-01-23",
            "digest_html": "<html>Test</html>",
        }

        result = send_email(state)

        assert result["email_sent"] is True
        mock_resend.assert_called_once()

    def test_skips_when_dry_run(self, mock_resend):
        """send_email skips sending when _dry_run is True."""
        from examples.daily_digest.nodes.email import send_email

        state = {
            "recipient_email": "test@example.com",
            "today": "2026-01-23",
            "digest_html": "<html>Test</html>",
            "_dry_run": True,
        }

        result = send_email(state)

        assert result["email_sent"] is False
        mock_resend.assert_not_called()

    def test_skips_when_no_recipient(self, mock_resend):
        """send_email skips when recipient_email is empty."""
        from examples.daily_digest.nodes.email import send_email

        state = {
            "recipient_email": "",
            "today": "2026-01-23",
            "digest_html": "<html>Test</html>",
        }

        result = send_email(state)

        assert result["email_sent"] is False
        mock_resend.assert_not_called()

    def test_includes_date_in_subject(self, mock_resend):
        """Email subject includes the date."""
        from examples.daily_digest.nodes.email import send_email

        state = {
            "recipient_email": "test@example.com",
            "today": "2026-01-23",
            "digest_html": "<html>Test</html>",
        }

        send_email(state)

        call_args = mock_resend.call_args[0][0]
        assert "2026-01-23" in call_args["subject"]
