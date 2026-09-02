#!/usr/bin/env python3
"""PermissionRequest is a decision hook, not an observability event.

Condemning test (Rite of Correction): FR-743 A2 registered the
plain-text session-probe on all 16 hook events, including
PermissionRequest. PermissionRequest is fail-closed: the platform
expects a structured decision on stdout, and a plain-text marker
fails the contract — every permission in a non-interactive child CLI
session (judge/review adapters) is denied with "PermissionRequest
hook failed". Witnessed 2026-07-24: FR-758 judge run rendered its
verdict but could not persist tmp/draft-judgement.md; zero
PermissionRequest entries in audit.jsonl across all history while the
probe fired for Stop/SessionEnd/PostToolUseFailure in the same child
session.

The cure: observability probes may register only on fail-open
notification events. Decision hooks (PermissionRequest) must not
carry a handler whose stdout is not a structured decision.
"""

from __future__ import annotations

import json
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
PROBE_CONFIG = HOOKS_ROOT / "session-probe.json"

# Hook events where a non-decision (plain stdout) handler is unsafe:
# the platform interprets handler output as a verdict and fails closed.
DECISION_EVENTS = {"PermissionRequest"}

PROBE_SCRIPT = "session-probe.sh"


def test_probe_not_registered_on_decision_hooks():
    """The plain-text probe must not sit on fail-closed decision hooks."""
    config = json.loads(PROBE_CONFIG.read_text(encoding="utf-8"))
    offenders = [
        event
        for event, handlers in config["hooks"].items()
        if event in DECISION_EVENTS
        and any(PROBE_SCRIPT in h.get("command", "") for h in handlers)
    ]
    assert not offenders, (
        f"session-probe.sh registered on decision hook(s) {offenders}: "
        "PermissionRequest is fail-closed — a plain-text probe denies "
        "every permission in non-interactive child sessions "
        "(witnessed 2026-07-24, FR-758 judge run)"
    )


def test_probe_still_observes_notification_events():
    """Removing the decision hook must not strip the observability probe."""
    config = json.loads(PROBE_CONFIG.read_text(encoding="utf-8"))
    for event in ("SessionStart", "UserPromptSubmit", "Stop", "SessionEnd"):
        handlers = config["hooks"].get(event, [])
        assert any(
            PROBE_SCRIPT in h.get("command", "") for h in handlers
        ), f"probe missing from fail-open event {event}"
