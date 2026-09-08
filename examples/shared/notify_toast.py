"""Shared desktop-toast notification tool (FR-1030, CAP-268).

Submits a native desktop notification through the facility each OS already
provides. It carries already-rendered strings and has no opinion about what
they say; composing the title and message belongs to the caller.

Contract: ``send_toast(title, message) -> {"submitted": True, "backend": ...}``.

**submitted, not delivered.** A zero exit status proves the OS notification
facility accepted the request. It does not prove a human saw anything —
macOS presentation depends on the user's Notifications settings, Windows
honours Focus Assist and per-app policy, and a freedesktop notification
daemon may drop or queue. The return value says only what was proven.

**No caller text ever becomes code.** The AppleScript and PowerShell sources
are frozen module constants; the title and message travel as ``argv`` or as
child-process environment and never enter a command string, a script body,
or markup. ``shlex.quote()`` is deliberately absent: no shell is invoked
anywhere, and quoting a value nothing will parse would misplace the boundary.

Every failure raises ``ToastError`` — unsupported platform, blank input,
missing binary, non-zero exit, timeout — so an unattended caller cannot
report green while notifying nobody.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS = ("darwin", "win32", "linux")
TIMEOUT_SECONDS = 10

# Frozen AppleScript. The text arrives as `argv`, so there is no AppleScript
# string literal to escape.
MACOS_SCRIPT = """on run argv
    display notification (item 2 of argv) with title (item 1 of argv)
end run
"""

# Frozen PowerShell driving WinRT. The text arrives as child environment and
# reaches the XML through CreateTextNode, so XML metacharacters are data by
# construction. Microsoft requires a desktop app to present the AppUserModelID
# of a Start-menu shortcut; the in-box Windows PowerShell AUMID is used, so the
# toast is attributed to Windows PowerShell in Action Center.
WINDOWS_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$aumid = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
    [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$nodes = $xml.GetElementsByTagName('text')
$nodes.Item(0).AppendChild($xml.CreateTextNode($env:YG_TOAST_TITLE)) | Out-Null
$nodes.Item(1).AppendChild($xml.CreateTextNode($env:YG_TOAST_MESSAGE)) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($aumid).Show($toast)
"""


class ToastError(RuntimeError):
    """The notification could not be submitted."""


def _macos(title: str, message: str) -> tuple[list[str], dict]:
    return ["osascript", "-", title, message], {"input": MACOS_SCRIPT}


def _windows(title: str, message: str) -> tuple[list[str], dict]:
    env = dict(os.environ)
    env["YG_TOAST_TITLE"] = title
    env["YG_TOAST_MESSAGE"] = message
    argv = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        WINDOWS_SCRIPT,
    ]
    return argv, {"env": env}


def _linux(title: str, message: str) -> tuple[list[str], dict]:
    # The `--` terminator is what stops a leading-hyphen title becoming a flag.
    return ["notify-send", "--", title, message], {}


_BACKENDS = {
    "darwin": ("osascript", _macos),
    "win32": ("powershell", _windows),
    "linux": ("notify-send", _linux),
}


def send_toast(title: str, message: str) -> dict:
    """Submit a desktop notification; raise ``ToastError`` if it cannot be.

    Returns ``{"submitted": True, "backend": <backend name>}`` — acceptance by
    the OS notification facility, never proof that a human saw it.
    """
    if not title.strip() and not message.strip():
        raise ToastError(
            "refusing to submit a notification with no title and no message"
        )

    entry = _BACKENDS.get(sys.platform)
    if entry is None:
        raise ToastError(
            f"unsupported platform {sys.platform!r}: "
            f"supported platforms are {', '.join(SUPPORTED_PLATFORMS)}"
        )
    backend, build = entry
    argv, extra = build(title, message)

    try:
        result = subprocess.run(  # noqa: S603 — frozen argv, shell=False, text never in argv[0]
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            **extra,
        )
    except FileNotFoundError as exc:
        raise ToastError(f"{backend} not found on this system: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ToastError(
            f"{backend} did not return within {TIMEOUT_SECONDS} seconds"
        ) from exc

    if result.returncode != 0:
        raise ToastError(
            f"{backend} exited {result.returncode}: {(result.stderr or '').strip()}"
        )

    logger.info("Notification submitted via %s", backend)
    return {"submitted": True, "backend": backend}
