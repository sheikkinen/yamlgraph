"""Tests for the shared vision tool (image → structured text).

FR-769: `examples/shared/vision_tool.py` — `describe_image()` sends an
image plus instruction through a `create_llm()` chat model and returns a
validated `ImageDescription`. Provider allowlist enforced before any LLM
invocation; no success-shaped fallbacks.

RED contract: `examples.shared.vision_tool` does not exist yet.
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from examples.shared.vision_tool import (
    SUPPORTED_PROVIDERS,
    ImageDescription,
    describe_image,
)

# FR-756: imports from examples/ cross the process boundary
pytestmark = pytest.mark.process

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def image_file(tmp_path):
    """A tiny valid PNG on disk."""
    import base64

    png = tmp_path / "sample.png"
    # 1x1 transparent PNG
    png.write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
            "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
    )
    return png


@pytest.fixture
def described():
    return ImageDescription(
        title="Misty Forest",
        description="A forest at dawn.",
        tags=["forest", "dawn"],
    )


def make_llm(result):
    """Mock chat model whose structured pipeline returns `result`."""
    llm = MagicMock()
    llm.with_structured_output.return_value.invoke.return_value = result
    return llm


# ---------------------------------------------------------------------------
# Case 1 + 3: local path → multimodal message → validated ImageDescription
# ---------------------------------------------------------------------------


class TestLocalPath:
    @pytest.mark.req("REQ-YG-575")
    def test_local_path_encodes_image_and_returns_description(
        self, image_file, described
    ):
        llm = make_llm(described)
        with patch("examples.shared.vision_tool.create_llm", return_value=llm):
            result = describe_image(image_file, "Describe this.", provider="google")

        assert isinstance(result, ImageDescription)
        assert result.title == "Misty Forest"
        # The invoked message must carry a base64 data URL content part
        (messages,), _ = llm.with_structured_output.return_value.invoke.call_args
        content = messages[0].content
        image_parts = [
            p for p in content if isinstance(p, dict) and p.get("type") == "image_url"
        ]
        assert image_parts, "no image content part in message"
        assert image_parts[0]["image_url"]["url"].startswith("data:image/png;base64,")

    @pytest.mark.req("REQ-YG-575")
    def test_instruction_travels_as_text_part(self, image_file, described):
        llm = make_llm(described)
        with patch("examples.shared.vision_tool.create_llm", return_value=llm):
            describe_image(image_file, "Eight DeviantArt tags.", provider="google")

        (messages,), _ = llm.with_structured_output.return_value.invoke.call_args
        text_parts = [
            p
            for p in messages[0].content
            if isinstance(p, dict) and p.get("type") == "text"
        ]
        assert text_parts and "DeviantArt" in text_parts[0]["text"]


# ---------------------------------------------------------------------------
# Case 2: URL input passes through without local file reads
# ---------------------------------------------------------------------------


class TestUrlInput:
    @pytest.mark.req("REQ-YG-575")
    def test_url_is_passed_as_url_content_part(self, described):
        llm = make_llm(described)
        url = "https://example.com/art.png"
        with patch("examples.shared.vision_tool.create_llm", return_value=llm):
            result = describe_image(url, "Describe.", provider="anthropic")

        assert isinstance(result, ImageDescription)
        (messages,), _ = llm.with_structured_output.return_value.invoke.call_args
        image_parts = [
            p
            for p in messages[0].content
            if isinstance(p, dict) and p.get("type") == "image_url"
        ]
        assert image_parts[0]["image_url"]["url"] == url


# ---------------------------------------------------------------------------
# Case 4: missing local path
# ---------------------------------------------------------------------------


class TestMissingFile:
    @pytest.mark.req("REQ-YG-575")
    def test_missing_path_raises_naming_the_path(self, tmp_path):
        missing = tmp_path / "nope.png"
        with (
            patch("examples.shared.vision_tool.create_llm") as factory,
            pytest.raises((FileNotFoundError, ValueError), match="nope.png"),
        ):
            describe_image(missing, "Describe.", provider="google")
        factory.assert_not_called()


# ---------------------------------------------------------------------------
# Case 5: provider allowlist enforced before invocation
# ---------------------------------------------------------------------------


class TestProviderAllowlist:
    @pytest.mark.req("REQ-YG-575")
    def test_unsupported_provider_raises_before_invocation(self, image_file):
        with (
            patch("examples.shared.vision_tool.create_llm") as factory,
            pytest.raises(ValueError) as exc,
        ):
            describe_image(image_file, "Describe.", provider="mistral")
        factory.assert_not_called()
        message = str(exc.value)
        assert "mistral" in message
        for supported in SUPPORTED_PROVIDERS:
            assert supported in message

    @pytest.mark.req("REQ-YG-575")
    def test_supported_providers_are_google_and_anthropic(self):
        assert set(SUPPORTED_PROVIDERS) == {"google", "anthropic"}


# ---------------------------------------------------------------------------
# Case 6: malformed model output → validation error, no fallback
# ---------------------------------------------------------------------------


class TestMalformedOutput:
    @pytest.mark.req("REQ-YG-575")
    def test_malformed_output_raises_validation_error(self, image_file):
        llm = make_llm({"title": "x"})  # missing required fields
        with (
            patch("examples.shared.vision_tool.create_llm", return_value=llm),
            pytest.raises(ValidationError),
        ):
            describe_image(image_file, "Describe.", provider="google")

    @pytest.mark.req("REQ-YG-575")
    def test_none_output_raises_not_returns(self, image_file):
        llm = make_llm(None)
        with (
            patch("examples.shared.vision_tool.create_llm", return_value=llm),
            pytest.raises((ValidationError, ValueError)),
        ):
            describe_image(image_file, "Describe.", provider="google")
