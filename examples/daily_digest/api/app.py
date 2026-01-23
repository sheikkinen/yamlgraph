"""FastAPI application with authentication and rate limiting.

This API is designed to be triggered by a GitHub Actions cron job.
It runs the digest pipeline in the background and sends an email with the results.
"""

import logging
import os
import sys
from datetime import date
from pathlib import Path
from typing import Annotated

# Add /app to path for Fly.io deployment (nodes.* imports)
APP_DIR = Path(__file__).parent.parent.resolve()
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi import (  # noqa: E402
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from slowapi import Limiter, _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402
from slowapi.util import get_remote_address  # noqa: E402

from yamlgraph.graph_loader import load_and_compile  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title="Daily Digest API",
    description="Trigger daily tech digest pipeline",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()
API_TOKEN = os.environ.get("DIGEST_API_TOKEN", "")


class RunRequest(BaseModel):
    """Request body for /run endpoint."""

    topics: list[str] = ["AI", "Python", "LangGraph"]
    recipient_email: str | None = None


class AcceptedResponse(BaseModel):
    """Response when pipeline is accepted for processing."""

    status: str
    message: str


def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Verify bearer token."""
    if not API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API token not configured",
        )
    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    return credentials.credentials


def run_pipeline(topics: list[str], recipient_email: str | None = None) -> None:
    """Run the digest pipeline (blocking). Called as background task."""
    try:
        logger.info(f"🚀 Starting digest pipeline with topics: {topics}")

        # Load graph
        graph_path = Path(__file__).parent.parent / "graph.yaml"
        state_graph = load_and_compile(str(graph_path))
        compiled = state_graph.compile()

        # Get recipient from request or environment
        recipient = recipient_email or os.environ.get("RECIPIENT_EMAIL", "")

        # Run pipeline
        result = compiled.invoke(
            {
                "topics": topics,
                "recipient_email": recipient,
                "today": date.today().isoformat(),
            }
        )

        # Log results
        ranked = result.get("ranked_stories", [])
        if hasattr(ranked, "stories"):
            ranked = ranked.stories

        logger.info(
            f"✅ Pipeline completed: "
            f"{len(result.get('raw_articles', []))} fetched, "
            f"{len(result.get('filtered_articles', []))} filtered, "
            f"{len(ranked) if ranked else 0} ranked, "
            f"email_sent={result.get('email_sent', False)}"
        )

    except Exception as e:
        logger.exception(f"❌ Pipeline failed: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/run", response_model=AcceptedResponse, status_code=202)
@limiter.limit("2/hour")
async def run_digest(
    request: Request,
    body: RunRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token),
):
    """Trigger the daily digest pipeline.

    Returns 202 Accepted immediately and runs pipeline in background.
    Requires Bearer token authentication.
    Rate limited to 2 requests per hour.
    """
    # Schedule pipeline to run in background
    background_tasks.add_task(run_pipeline, body.topics, body.recipient_email)

    logger.info(f"📬 Digest pipeline triggered with topics: {body.topics}")

    return AcceptedResponse(
        status="accepted",
        message="Digest pipeline started in background",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
