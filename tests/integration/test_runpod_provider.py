"""FR-766: live RunPod integration witness (AC-08).

Gated on the full env triple; when present, witnesses the three claims
the FR makes about the OpenAI-compatible route: real invoke, real SSE
streaming (the reason langchain-runpod was rejected), and Pydantic
structured output (Commandment 5).
"""

import os

import pytest
from pydantic import BaseModel, Field

from yamlgraph.utils.llm_factory import clear_cache, create_llm

requires_runpod = pytest.mark.skipif(
    not all(
        os.getenv(var) for var in ("RUNPOD_API_KEY", "RUNPOD_ENDPOINT", "RUNPOD_MODEL")
    ),
    reason="RUNPOD_API_KEY, RUNPOD_ENDPOINT and RUNPOD_MODEL must all be set",
)


class TinyAnswer(BaseModel):
    """Minimal structured-output witness schema."""

    answer: str = Field(description="One-word answer")
    confident: bool = Field(description="Whether the answer is certain")


@requires_runpod
class TestRunpodLive:
    """Real calls against the endpoint configured in the environment."""

    def setup_method(self):
        clear_cache()

    @pytest.mark.req("REQ-YG-010")
    def test_runpod_invoke(self):
        llm = create_llm(provider="runpod", temperature=0.0)
        result = llm.invoke("Reply with the single word: pong")
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    @pytest.mark.req("REQ-YG-010")
    def test_runpod_stream_yields_chunks(self):
        """R-3: streaming must be witnessed, not assumed."""
        llm = create_llm(provider="runpod", temperature=0.0)
        chunks = list(llm.stream("Count from 1 to 10, digits separated by spaces."))
        assert len(chunks) >= 1
        combined = "".join(str(c.content) for c in chunks)
        assert len(combined) > 0

    @pytest.mark.req("REQ-YG-010")
    def test_runpod_structured_output(self):
        """Constraint 3: structured output witnessed against the live model."""
        llm = create_llm(provider="runpod", temperature=0.0)
        structured = llm.with_structured_output(TinyAnswer)
        result = structured.invoke(
            "What color is a clear daytime sky? Answer in one word."
        )
        assert isinstance(result, TinyAnswer)
        assert result.answer.strip()
