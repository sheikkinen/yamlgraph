"""RED acceptance tests for FR-425 Phase B — hook emit script + redaction.

Tests cover:
- Command redaction (KEY=, TOKEN=, SECRET=, PASSWORD=, PASSPHRASE= → REDACTED)
- classify-emit.sh graceful exit when socket absent
- classify-emit.sh JSON parsing of hook input
- classify-emit.json config schema
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EMIT_SCRIPT = REPO_ROOT / ".github" / "hooks" / "scripts" / "classify-emit.sh"
EMIT_CONFIG = REPO_ROOT / ".github" / "hooks" / "classify-emit.json"


# ─── Redaction via sed ───────────────────────────────────────────────────────


def _redact(command: str) -> str:
    """Run the same sed redaction that classify-emit.sh uses."""
    result = subprocess.run(
        ["sed", "-E", "s/(KEY|TOKEN|SECRET|PASSWORD|PASSPHRASE)=[^ ]*/\\1=REDACTED/gi"],
        input=command,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.req("REQ-YG-411")
class TestRedaction:
    """Command redaction before LLM transmission."""

    def test_api_key_redacted(self) -> None:
        assert (
            _redact("ANTHROPIC_API_KEY=sk-ant-foo123 curl")
            == "ANTHROPIC_API_KEY=REDACTED curl"
        )

    def test_token_redacted(self) -> None:
        assert (
            _redact("export GITHUB_TOKEN=ghp_abc123") == "export GITHUB_TOKEN=REDACTED"
        )

    def test_secret_redacted(self) -> None:
        assert _redact("AWS_SECRET=wJalrXUtnFEMI") == "AWS_SECRET=REDACTED"

    def test_password_redacted(self) -> None:
        assert _redact("DB_PASSWORD=hunter2 psql") == "DB_PASSWORD=REDACTED psql"

    def test_passphrase_redacted(self) -> None:
        assert _redact("SSH_PASSPHRASE=my_pass ssh") == "SSH_PASSPHRASE=REDACTED ssh"

    def test_multiple_secrets_redacted(self) -> None:
        cmd = "API_KEY=abc TOKEN=xyz SECRET=123"
        redacted = _redact(cmd)
        assert "API_KEY=REDACTED" in redacted
        assert "TOKEN=REDACTED" in redacted
        assert "SECRET=REDACTED" in redacted

    def test_case_insensitive(self) -> None:
        assert _redact("api_key=foo") == "api_key=REDACTED"
        assert _redact("Api_Key=foo") == "Api_Key=REDACTED"

    def test_no_secrets_unchanged(self) -> None:
        cmd = "ls -la /tmp"
        assert _redact(cmd) == cmd

    def test_partial_match_not_redacted(self) -> None:
        """KEY without = should not be redacted."""
        cmd = "echo KEY is important"
        assert _redact(cmd) == cmd


# ─── classify-emit.sh behavior ──────────────────────────────────────────────


@pytest.mark.req("REQ-YG-411")
class TestEmitScript:
    """classify-emit.sh script behavior."""

    def test_script_exists_and_executable(self) -> None:
        assert EMIT_SCRIPT.exists()
        assert EMIT_SCRIPT.stat().st_mode & 0o111  # executable

    def test_graceful_exit_no_socket(self) -> None:
        """Script exits 0 when classifier socket doesn't exist."""
        hook_input = json.dumps(
            {
                "toolName": "run_in_terminal",
                "toolInput": {"command": "ls -la"},
                "sessionId": "test-session",
            }
        )
        result = subprocess.run(
            ["bash", str(EMIT_SCRIPT)],
            input=hook_input,
            capture_output=True,
            text=True,
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin",
                "HOME": str(Path.home()),
                "HOOK_CLASSIFIER_SOCK": "/tmp/nonexistent-test-sock-fr425.sock",
            },
        )
        assert result.returncode == 0


# ─── classify-emit.json config ───────────────────────────────────────────────


@pytest.mark.req("REQ-YG-411")
class TestEmitConfig:
    """classify-emit.json hook config schema."""

    def test_config_exists(self) -> None:
        assert EMIT_CONFIG.exists()

    def test_config_valid_json(self) -> None:
        config = json.loads(EMIT_CONFIG.read_text(encoding="utf-8"))
        assert "hooks" in config

    def test_config_is_post_tool_use(self) -> None:
        config = json.loads(EMIT_CONFIG.read_text(encoding="utf-8"))
        assert "PostToolUse" in config["hooks"]

    def test_config_references_emit_script(self) -> None:
        config = json.loads(EMIT_CONFIG.read_text(encoding="utf-8"))
        entries = config["hooks"]["PostToolUse"]
        assert len(entries) == 1
        assert entries[0]["command"] == ".github/hooks/scripts/classify-emit.sh"
        assert entries[0]["type"] == "command"
        assert entries[0]["timeout"] == 5
