"""Storyboard-specific wrappers for image generation.

Re-exports from examples.shared.replicate_tool.
"""

from examples.shared.replicate_tool import (
    ImageResult,
    edit_image,
    generate_image,
    generate_storyboard_images,
)

# Re-export for backward compatibility
__all__ = [
    "ImageResult",
    "generate_image",
    "edit_image",
    "generate_storyboard_images",
]
