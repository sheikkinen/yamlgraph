"""Integration test for the shared vision tool (FR-769, CAP-217).

Runs only when GOOGLE_API_KEY is present; exercises the real multimodal
provider path with a generated fixture image.
"""

import base64
import os

import pytest

from examples.shared.vision_tool import ImageDescription, describe_image

pytestmark = [
    pytest.mark.process,
    pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set — vision integration test skipped",
    ),
]

# 1x1 red PNG
RED_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


@pytest.mark.req("REQ-YG-575")
def test_describe_image_live_google(tmp_path):
    png = tmp_path / "pixel.png"
    png.write_bytes(RED_PIXEL_PNG)

    result = describe_image(
        png,
        "Describe this image in one sentence and give two tags.",
        provider="google",
    )

    assert isinstance(result, ImageDescription)
    assert result.title
    assert result.description
    assert result.tags
