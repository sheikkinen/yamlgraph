"""Tests for the shared desktop-toast tool (FR-1030, REQ-YG-672).

`examples/shared/notify_toast.py` — `send_toast(title, message)` submits a
native desktop notification through the facility each OS already provides
and returns `{"submitted": True, "backend": ...}`.

Two things these tests exist to pin, both of which a passing "it works on
my mac" run would hide:

1. **No caller text ever becomes code.** On every backend the title and
   message travel as `argv` or as child-process environment, never
   interpolated into a command string, script source, or XML. The tests
   assert the frozen script literals are byte-identical regardless of what
   the caller passes.
2. **No success-shaped return on any failure path.** Missing binary,
   non-zero exit, timeout, and unsupported platform all raise.

No test spawns a real notification process; the suite passes headless.

RED contract: `examples.shared.notify_toast` does not exist yet.
"""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from examples.shared.notify_toast import (
    MACOS_SCRIPT,
    SUPPORTED_PLATFORMS,
    TIMEOUT_SECONDS,
    WINDOWS_SCRIPT,
    ToastError,
    send_toast,
)

# FR-756: imports from examples/ cross the process boundary
pytestmark = pytest.mark.process

# Payloads that would break a naive implementation on at least one backend.
HOSTILE = [
    '"; rm -rf / #',
    "$(id)",
    "`whoami`",
    "</text><image src='x'/><text>",
    "--title=pwned",
    "line one\nline two",
    "100% & <done>",
    'it\'s "quoted"',
]


@pytest.fixture
def run():
    """Patch subprocess.run; default to a clean exit."""
    with patch("examples.shared.notify_toast.subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield mock


def call_of(mock):
    """(argv, kwargs) of the single subprocess invocation."""
    assert mock.call_count == 1, (
        f"expected exactly one subprocess call, got {mock.call_count}"
    )
    args, kwargs = mock.call_args
    return args[0], kwargs


# ---------------------------------------------------------------------------
# Backend dispatch
# ---------------------------------------------------------------------------


class TestDispatch:
    @pytest.mark.req("REQ-YG-672")
    def test_darwin_selects_osascript(self, run):
        with patch.object(sys, "platform", "darwin"):
            result = send_toast("Title", "Message")

        argv, _ = call_of(run)
        assert result == {"submitted": True, "backend": "osascript"}
        assert argv[0] == "osascript"

    @pytest.mark.req("REQ-YG-672")
    def test_win32_selects_powershell(self, run):
        with patch.object(sys, "platform", "win32"):
            result = send_toast("Title", "Message")

        argv, _ = call_of(run)
        assert result == {"submitted": True, "backend": "powershell"}
        assert argv[0] == "powershell.exe"

    @pytest.mark.req("REQ-YG-672")
    def test_linux_selects_notify_send(self, run):
        with patch.object(sys, "platform", "linux"):
            result = send_toast("Title", "Message")

        argv, _ = call_of(run)
        assert result == {"submitted": True, "backend": "notify-send"}
        assert argv[0] == "notify-send"

    @pytest.mark.req("REQ-YG-672")
    def test_unsupported_platform_raises_before_any_subprocess(self, run):
        with patch.object(sys, "platform", "aix"), pytest.raises(ToastError) as exc:
            send_toast("Title", "Message")

        assert run.call_count == 0, (
            "no subprocess may be spawned on an unsupported platform"
        )
        for platform in SUPPORTED_PLATFORMS:
            assert platform in str(exc.value)
        assert "aix" in str(exc.value)


# ---------------------------------------------------------------------------
# Process construction — argv, stdin, env, shell, timeout
# ---------------------------------------------------------------------------


class TestMacOSProcess:
    @pytest.mark.req("REQ-YG-672")
    def test_text_travels_as_argv_after_stdin_script(self, run):
        with patch.object(sys, "platform", "darwin"):
            send_toast("The Title", "The Message")

        argv, kwargs = call_of(run)
        assert argv == ["osascript", "-", "The Title", "The Message"]
        assert kwargs["input"] == MACOS_SCRIPT
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == TIMEOUT_SECONDS

    @pytest.mark.req("REQ-YG-672")
    @pytest.mark.parametrize("payload", HOSTILE)
    def test_hostile_text_stays_data(self, run, payload):
        with patch.object(sys, "platform", "darwin"):
            send_toast(payload, payload)

        argv, kwargs = call_of(run)
        assert argv[2] == payload and argv[3] == payload
        assert kwargs["input"] == MACOS_SCRIPT, "the AppleScript source must never vary"
        assert payload not in kwargs["input"]


class TestWindowsProcess:
    @pytest.mark.req("REQ-YG-672")
    def test_text_travels_as_child_environment(self, run):
        with patch.object(sys, "platform", "win32"):
            send_toast("The Title", "The Message")

        argv, kwargs = call_of(run)
        assert argv[0] == "powershell.exe"
        assert "-NoProfile" in argv and "-NonInteractive" in argv
        assert argv[-1] == WINDOWS_SCRIPT
        assert kwargs["env"]["YG_TOAST_TITLE"] == "The Title"
        assert kwargs["env"]["YG_TOAST_MESSAGE"] == "The Message"
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == TIMEOUT_SECONDS

    @pytest.mark.req("REQ-YG-672")
    def test_child_environment_inherits_parent(self, run, monkeypatch):
        monkeypatch.setenv("SYSTEMROOT", "C:\\Windows")
        with patch.object(sys, "platform", "win32"):
            send_toast("T", "M")

        _, kwargs = call_of(run)
        assert kwargs["env"]["SYSTEMROOT"] == "C:\\Windows"

    @pytest.mark.req("REQ-YG-672")
    def test_script_reaches_xml_through_create_text_node(self):
        # Judgement AC-06: text nodes, not string-built XML.
        assert "CreateTextNode" in WINDOWS_SCRIPT
        assert "$env:YG_TOAST_TITLE" in WINDOWS_SCRIPT
        assert "$env:YG_TOAST_MESSAGE" in WINDOWS_SCRIPT
        # The AUMID is the documented desktop-app requirement (FR-1030).
        assert "CreateToastNotifier" in WINDOWS_SCRIPT
        assert "WindowsPowerShell\\v1.0\\powershell.exe" in WINDOWS_SCRIPT

    @pytest.mark.req("REQ-YG-672")
    @pytest.mark.parametrize("payload", HOSTILE)
    def test_hostile_text_stays_data(self, run, payload):
        with patch.object(sys, "platform", "win32"):
            send_toast(payload, payload)

        argv, kwargs = call_of(run)
        assert kwargs["env"]["YG_TOAST_TITLE"] == payload
        assert kwargs["env"]["YG_TOAST_MESSAGE"] == payload
        assert argv[-1] == WINDOWS_SCRIPT, "the PowerShell source must never vary"
        assert payload not in " ".join(argv)


class TestLinuxProcess:
    @pytest.mark.req("REQ-YG-672")
    def test_text_travels_as_argv_after_terminator(self, run):
        with patch.object(sys, "platform", "linux"):
            send_toast("The Title", "The Message")

        argv, kwargs = call_of(run)
        assert argv == ["notify-send", "--", "The Title", "The Message"]
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == TIMEOUT_SECONDS

    @pytest.mark.req("REQ-YG-672")
    @pytest.mark.parametrize("payload", HOSTILE)
    def test_hostile_text_stays_data(self, run, payload):
        with patch.object(sys, "platform", "linux"):
            send_toast(payload, payload)

        argv, _ = call_of(run)
        # The `--` terminator is what keeps "--title=pwned" from becoming a flag.
        assert argv[1] == "--"
        assert argv[2] == payload and argv[3] == payload


# ---------------------------------------------------------------------------
# Failure paths — never success-shaped (Commandment 6)
# ---------------------------------------------------------------------------


class TestFailures:
    @pytest.mark.req("REQ-YG-672")
    def test_missing_binary_raises(self, run):
        run.side_effect = FileNotFoundError("no such file")
        with patch.object(sys, "platform", "darwin"), pytest.raises(ToastError) as exc:
            send_toast("T", "M")

        assert "osascript" in str(exc.value)

    @pytest.mark.req("REQ-YG-672")
    def test_non_zero_exit_raises_with_stderr(self, run):
        run.return_value = MagicMock(
            returncode=1, stdout="", stderr="execution error: -1743"
        )
        with patch.object(sys, "platform", "darwin"), pytest.raises(ToastError) as exc:
            send_toast("T", "M")

        assert "-1743" in str(exc.value)

    @pytest.mark.req("REQ-YG-672")
    def test_timeout_raises(self, run):
        run.side_effect = subprocess.TimeoutExpired(
            cmd="osascript", timeout=TIMEOUT_SECONDS
        )
        with patch.object(sys, "platform", "darwin"), pytest.raises(ToastError) as exc:
            send_toast("T", "M")

        assert str(TIMEOUT_SECONDS) in str(exc.value)

    @pytest.mark.req("REQ-YG-672")
    @pytest.mark.parametrize(
        "failure",
        [
            FileNotFoundError("gone"),
            subprocess.TimeoutExpired(cmd="notify-send", timeout=1),
        ],
    )
    def test_no_failure_path_returns_a_submitted_mapping(self, run, failure):
        run.side_effect = failure
        with patch.object(sys, "platform", "linux"), pytest.raises(ToastError):
            send_toast("T", "M")

    @pytest.mark.req("REQ-YG-672")
    def test_blank_title_and_message_refused_before_subprocess(self, run):
        with patch.object(sys, "platform", "darwin"), pytest.raises(ToastError):
            send_toast("", "")

        assert run.call_count == 0
