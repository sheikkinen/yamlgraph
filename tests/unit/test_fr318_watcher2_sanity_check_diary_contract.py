from pathlib import Path

import pytest

pytestmark = pytest.mark.process

PROMPT_FILE = Path(".chaplain/graphs/watcher-enforce/prompts/sanity-check-session.yaml")


def _read_prompt() -> str:
    assert PROMPT_FILE.exists(), f"Prompt file {PROMPT_FILE} not found"
    return PROMPT_FILE.read_text()


@pytest.mark.req("REQ-YG-316")
def test_ac01_no_hardcoded_fr316_diary_filename():
    """AC-01: prompt no longer contains hardcoded fr-316 diary filename text."""
    content = _read_prompt()

    assert (
        "fr-316-watcher2-sanity-check-state" not in content
    ), "Prompt still contains hardcoded fr-316 diary filename"


@pytest.mark.req("REQ-YG-316")
def test_ac02_diary_filename_is_derived_from_fr_path_instruction():
    """AC-02: Prompt explicitly instructs deriving diary filename from {{ fr_path }}."""
    content = _read_prompt()

    assert (
        "Derive the FR slug from `{{ fr_path }}`" in content
    ), "Prompt must explicitly instruct deriving diary filename from {{ fr_path }}"
    assert (
        "reflection-<derived-fr-slug>-watcher2-sanity-check-state.md" in content
    ), "Prompt must use FR-derived diary filename template"


@pytest.mark.req("REQ-YG-316")
def test_ac03_prompt_requires_stage_and_commit_for_diary():
    """AC-03: Prompt explicitly instructs staging and committing the created diary file."""
    content = _read_prompt()

    assert "7. **STAGE + COMMIT**" in content
    assert (
        "git add docs/diary/YYYY-MM-DD-reflection-<derived-fr-slug>-watcher2-sanity-check-state.md"
        in content
    )
    assert "git commit -m" in content


@pytest.mark.req("REQ-YG-316")
def test_ac04_prompt_keeps_pass_warn_output_contract():
    """AC-04: Prompt still returns exactly PASS or WARN for FSM routing."""
    content = _read_prompt()

    assert "- `PASS`" in content, "Prompt must return exactly PASS"
    assert "- `WARN`" in content, "Prompt must return exactly WARN"
    assert "- `FAIL`" not in content, "Prompt should not introduce FAIL routing output"
