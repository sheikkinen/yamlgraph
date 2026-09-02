"""Unit tests for inquisitor.sh --propose flag (FR-118).

Tests the flag parsing and propose gating logic in inquisitor.sh.
The propose mode detects persistent violations in diary entries and
writes fix proposals to .chaplain/inbox/.

The flag parsing and gating logic is pure shell, so tests exercise it
via subprocess with temporary directory structures (same pattern as
test_watch_enforce_spawn.py).
"""

import os
import subprocess
import textwrap

# Shell snippet that mirrors the flag-parsing logic to be added to inquisitor.sh.
# We test this in isolation so we don't need copilot or the full script.
import pytest

pytestmark = pytest.mark.process

_FLAG_PARSE_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail

    PROPOSE=""
    if [[ "${1:-}" == "--propose" ]]; then
        PROPOSE="true"
    fi

    if [[ -n "$PROPOSE" ]]; then
        echo "PROPOSE_MODE"
    else
        echo "AUDIT_ONLY"
    fi
""")

# Shell snippet that tests the dedup/gating for proposal file creation.
# Simulates what the copilot propose call would check before writing.
_DEDUP_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$TEST_DIR"

    SLUG="$SLUG"
    INBOX=".chaplain/inbox"
    TARGET="$INBOX/inquisitor-${SLUG}.md"

    if [[ -f "$TARGET" ]]; then
        echo "SKIP_DUP:$TARGET"
    else
        echo "# Fix: test violation" > "$TARGET"
        echo "WROTE:$TARGET"
    fi
""")


def _run_flag_parse(args: list[str] | None = None) -> str:
    """Run the flag parsing script and return stdout."""
    cmd = ["bash", "-c", _FLAG_PARSE_SCRIPT, "--"] + (args or [])
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


def _run_dedup(test_dir: str, slug: str) -> str:
    """Run the dedup script and return stdout."""
    result = subprocess.run(
        ["bash", "-c", _DEDUP_SCRIPT],
        env={
            **os.environ,
            "TEST_DIR": str(test_dir),
            "SLUG": slug,
        },
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


@pytest.mark.req("REQ-YG-118")
class TestProposeFlagParsing:
    """Tests for --propose flag parsing in inquisitor.sh."""

    def test_no_flag_is_audit_only(self):
        """Without --propose, script stays in audit-only mode."""
        output = _run_flag_parse()
        assert output == "AUDIT_ONLY"

    def test_propose_flag_enables_propose_mode(self):
        """--propose flag activates propose mode."""
        output = _run_flag_parse(["--propose"])
        assert output == "PROPOSE_MODE"

    def test_unknown_flag_is_audit_only(self):
        """Unknown flags do not activate propose mode."""
        output = _run_flag_parse(["--unknown"])
        assert output == "AUDIT_ONLY"

    def test_empty_string_arg_is_audit_only(self):
        """Empty string argument does not activate propose mode."""
        output = _run_flag_parse([""])
        assert output == "AUDIT_ONLY"


@pytest.mark.req("REQ-YG-118")
class TestProposalFileDedup:
    """Tests for filename-based dedup of proposal files."""

    def test_writes_proposal_when_no_existing_file(self, tmp_path):
        """Proposal file is created when inbox has no same-named file."""
        inbox = tmp_path / ".chaplain" / "inbox"
        inbox.mkdir(parents=True)

        output = _run_dedup(str(tmp_path), "architecture-count")
        assert "WROTE:.chaplain/inbox/inquisitor-architecture-count.md" in output
        assert (inbox / "inquisitor-architecture-count.md").exists()

    def test_skips_proposal_when_file_exists(self, tmp_path):
        """Duplicate proposal is skipped when same-named file exists."""
        inbox = tmp_path / ".chaplain" / "inbox"
        inbox.mkdir(parents=True)
        existing = inbox / "inquisitor-fr-status-draft.md"
        existing.write_text("# Existing proposal\n", encoding="utf-8")

        output = _run_dedup(str(tmp_path), "fr-status-draft")
        assert "SKIP_DUP:" in output
        # Existing file content not overwritten
        assert existing.read_text(encoding="utf-8") == "# Existing proposal\n"


@pytest.mark.req("REQ-YG-118")
class TestInquisitorShellIntegration:
    """Integration test verifying inquisitor.sh contains the propose logic."""

    def test_inquisitor_sh_has_propose_flag_parsing(self):
        """inquisitor.sh parses --propose flag."""
        content = _read_inquisitor_sh()
        assert "--propose" in content

    def test_inquisitor_sh_has_propose_variable(self):
        """inquisitor.sh sets PROPOSE variable."""
        content = _read_inquisitor_sh()
        assert "PROPOSE=" in content

    def test_inquisitor_sh_gates_propose_on_flag(self):
        """inquisitor.sh conditionally runs propose block."""
        content = _read_inquisitor_sh()
        assert 'if [[ -n "$PROPOSE" ]]' in content

    def test_inquisitor_sh_propose_reads_diary(self):
        """Propose prompt instructs reading diary audit entries."""
        content = _read_inquisitor_sh()
        assert "diary" in content.lower()
        assert "Inquisitor Audit" in content

    def test_inquisitor_sh_propose_detects_persistence(self):
        """Propose prompt instructs detecting persistent violations."""
        content = _read_inquisitor_sh()
        assert "consecutive" in content.lower()

    def test_inquisitor_sh_propose_writes_to_inbox(self):
        """Propose prompt instructs writing to .chaplain/inbox/."""
        content = _read_inquisitor_sh()
        assert ".chaplain/inbox/" in content

    def test_inquisitor_sh_propose_uses_filename_dedup(self):
        """Propose prompt instructs filename-based dedup."""
        content = _read_inquisitor_sh()
        assert "inquisitor-" in content
        assert "kebab-case" in content

    def test_inquisitor_sh_audit_block_unchanged(self):
        """Original audit copilot call is preserved unchanged."""
        content = _read_inquisitor_sh()
        assert "**Inquisit.**" in content
        assert "You are the Inquisitor. Your duty: audit" in content

    def test_inquisitor_sh_header_documents_propose(self):
        """Script header documents the --propose flag."""
        content = _read_inquisitor_sh()
        # Header should mention --propose usage
        header_lines = content.split("\n")[:10]
        header = "\n".join(header_lines)
        assert "--propose" in header


def _read_inquisitor_sh() -> str:
    """Read the current inquisitor.sh content."""
    inquisitor_path = os.path.join(
        os.path.dirname(__file__), "..", "..", ".chaplain", "inquisitor.sh"
    )
    with open(inquisitor_path, encoding="utf-8") as f:
        return f.read()
