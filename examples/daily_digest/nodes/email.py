"""Email sending node using Resend API."""

import logging
import os

import resend

logger = logging.getLogger(__name__)

# Configure Resend API key from environment
resend.api_key = os.environ.get("RESEND_API_KEY", "")

# Default sender (Resend test domain - no verification needed)
DEFAULT_FROM = os.environ.get(
    "DIGEST_FROM_EMAIL", "YAMLGraph <yamlgraph-no-reply@resend.dev>"
)


def send_email(state: dict) -> dict:
    """Send via Resend API. Skip if dry run."""
    # Support dry-run mode
    if state.get("_dry_run"):
        logger.info("🔕 Dry run - skipping email send")
        return {"email_sent": False}

    recipient = state.get("recipient_email", "")
    if not recipient:
        logger.info("🔕 No recipient - skipping email send")
        return {"email_sent": False}

    today = state.get("today", "")
    digest_html = state.get("digest_html", "")

    resend.Emails.send(
        {
            "from": DEFAULT_FROM,
            "to": [recipient],
            "subject": f"🗞️ Daily Tech Digest - {today}",
            "html": digest_html,
        }
    )

    logger.info(f"📬 Email sent to {recipient}")
    return {"email_sent": True}
