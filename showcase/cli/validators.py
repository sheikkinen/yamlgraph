"""CLI validation functions.

Provides argument validation for CLI commands.
"""

from showcase.config import MAX_WORD_COUNT, MIN_WORD_COUNT
from showcase.utils.sanitize import sanitize_topic


def validate_route_args(args) -> bool:
    """Validate route command arguments.

    Args:
        args: Parsed arguments namespace

    Returns:
        True if valid, False otherwise (prints error message)
    """
    message = args.message.strip() if args.message else ""
    if not message:
        print("❌ Message cannot be empty")
        return False
    return True


def validate_refine_args(args) -> bool:
    """Validate refine command arguments.

    Args:
        args: Parsed arguments namespace

    Returns:
        True if valid, False otherwise (prints error message)
    """
    topic = args.topic.strip() if args.topic else ""
    if not topic:
        print("❌ Topic cannot be empty")
        return False
    return True


def validate_run_args(args) -> bool:
    """Validate and sanitize run command arguments.

    Args:
        args: Parsed arguments namespace

    Returns:
        True if valid, False otherwise (prints error message)
    """
    # Sanitize topic
    result = sanitize_topic(args.topic)
    if not result.is_safe:
        for warning in result.warnings:
            print(f"❌ {warning}")
        return False

    # Update args with sanitized value
    args.topic = result.value

    # Print any warnings (e.g., truncation)
    for warning in result.warnings:
        print(f"⚠️  {warning}")

    if args.word_count < MIN_WORD_COUNT or args.word_count > MAX_WORD_COUNT:
        print(f"❌ Word count must be between {MIN_WORD_COUNT} and {MAX_WORD_COUNT}")
        return False

    return True
