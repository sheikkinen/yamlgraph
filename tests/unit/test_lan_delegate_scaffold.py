"""Offline scaffold-layer tests for FR-948 lan-delegate skill.

REQ-YG-636. This module covers models.py (schema validity, enum totality,
precedence resolution) and errors.py (typed pre-launch exception classes).
Wire-level tests (WinRM client construction, wrapper JSON parsing,
delegate.py CLI) land alongside their production surfaces in follow-up
commits.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# The skill directory lives at .github/skills/lan-delegate/ (dash in the
# package name so we cannot use plain `import`). Load via importlib so
# tests stay hermetic and pytest doesn't have to be reconfigured.
_SKILL_DIR = Path(__file__).parent.parent.parent / ".github" / "skills" / "lan-delegate"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        f"lan_delegate_{name}",
        _SKILL_DIR / f"{name}.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"lan_delegate_{name}"] = module
    spec.loader.exec_module(module)
    return module


models = _load("models")
errors = _load("errors")


@pytest.mark.req("REQ-YG-636")
def test_delegation_policy_status_precedence_is_total():
    """Every enum value appears exactly once in the precedence table."""
    enum_values = set(models.DelegationPolicyStatus)
    precedence_values = set(models._PRECEDENCE)
    assert enum_values == precedence_values, (
        f"Missing from precedence: {enum_values - precedence_values}; "
        f"Extra in precedence: {precedence_values - enum_values}"
    )
    assert len(models._PRECEDENCE) == len(
        set(models._PRECEDENCE)
    ), "Precedence table has duplicate entries"


@pytest.mark.req("REQ-YG-636")
def test_resolve_status_returns_highest_severity():
    """resolve_status picks TIMEOUT over COPILOT_NONZERO (higher severity)."""
    result = models.resolve_status(
        [
            models.DelegationPolicyStatus.COPILOT_NONZERO,
            models.DelegationPolicyStatus.TIMEOUT,
            models.DelegationPolicyStatus.ARTIFACT_COPY_FAIL,
        ]
    )
    assert result == models.DelegationPolicyStatus.TIMEOUT


@pytest.mark.req("REQ-YG-636")
def test_resolve_status_empty_list_is_ok():
    """Empty observed list -> OK (nothing failed)."""
    assert models.resolve_status([]) == models.DelegationPolicyStatus.OK


@pytest.mark.req("REQ-YG-636")
def test_token_leak_outranks_all_other_failures():
    """TOKEN_LEAK_DETECTED is the highest severity; must win against any other."""
    for other in models.DelegationPolicyStatus:
        if other == models.DelegationPolicyStatus.TOKEN_LEAK_DETECTED:
            continue
        assert (
            models.resolve_status(
                [other, models.DelegationPolicyStatus.TOKEN_LEAK_DETECTED]
            )
            == models.DelegationPolicyStatus.TOKEN_LEAK_DETECTED
        )


@pytest.mark.req("REQ-YG-636")
def test_process_tree_kill_fail_outranks_timeout():
    """Kill failure means we cannot prove termination; ranks above plain TIMEOUT."""
    result = models.resolve_status(
        [
            models.DelegationPolicyStatus.TIMEOUT,
            models.DelegationPolicyStatus.PROCESS_TREE_KILL_FAIL,
        ]
    )
    assert result == models.DelegationPolicyStatus.PROCESS_TREE_KILL_FAIL


@pytest.mark.req("REQ-YG-636")
def test_prerequisites_all_ok_requires_node_major_ge_22():
    """RemoteCopilotPrerequisites.all_ok() rejects Node 20 even when everything else is present."""
    prereqs = models.RemoteCopilotPrerequisites(
        git=models.ToolInfo(
            present=True, path="C:\\Program Files\\Git\\cmd\\git.exe", version="2.40.1"
        ),
        node=models.ToolInfo(
            present=True, path="C:\\Program Files\\nodejs\\node.exe", version="v20.16.1"
        ),
        copilot=models.ToolInfo(
            present=True,
            path="C:\\Program Files\\nodejs\\copilot.cmd",
            version="1.0.82",
        ),
        canonical_clone=models.RepoInfo(
            path="C:\\Users\\copilot\\yamlgraph", exists=True, contains_sha=True
        ),
        run_worktree_free=True,
        smb_destination_free=True,
    )
    assert prereqs.all_ok() is False, "Node major 20 must fail all_ok()"


@pytest.mark.req("REQ-YG-636")
def test_prerequisites_all_ok_accepts_node_major_ge_22():
    prereqs = models.RemoteCopilotPrerequisites(
        git=models.ToolInfo(present=True, path="git", version="2.40.1"),
        node=models.ToolInfo(present=True, path="node", version="v24.19.0"),
        copilot=models.ToolInfo(present=True, path="copilot.cmd", version="1.0.82"),
        canonical_clone=models.RepoInfo(path="clone", exists=True, contains_sha=True),
        run_worktree_free=True,
        smb_destination_free=True,
    )
    assert prereqs.all_ok() is True


@pytest.mark.req("REQ-YG-636")
def test_prerequisites_all_ok_rejects_missing_sha():
    prereqs = models.RemoteCopilotPrerequisites(
        git=models.ToolInfo(present=True, version="2.40.1"),
        node=models.ToolInfo(present=True, version="v24.19.0"),
        copilot=models.ToolInfo(present=True, version="1.0.82"),
        canonical_clone=models.RepoInfo(path="clone", exists=True, contains_sha=False),
        run_worktree_free=True,
        smb_destination_free=True,
    )
    assert prereqs.all_ok() is False


@pytest.mark.req("REQ-YG-636")
def test_pre_launch_exceptions_tuple_lists_all_typed_classes():
    """PRE_LAUNCH_EXCEPTIONS must enumerate every typed exception in errors.py."""
    expected = {
        errors.DirtyLocalTreeError,
        errors.MissingReconError,
        errors.StaleReconError,
        errors.ReconDisqualifyingFieldError,
        errors.MissingCredentialError,
        errors.UnsafeHostError,
        errors.PromptFileError,
        errors.UnsafeRunIdError,
        errors.LocalPathCollisionError,
        errors.RecursiveDelegationError,
    }
    assert set(errors.PRE_LAUNCH_EXCEPTIONS) == expected


@pytest.mark.req("REQ-YG-636")
def test_pre_launch_exceptions_all_inherit_lan_delegate_error():
    """Every typed exception must be catchable via LanDelegateError."""
    for exc_cls in errors.PRE_LAUNCH_EXCEPTIONS:
        assert issubclass(
            exc_cls, errors.LanDelegateError
        ), f"{exc_cls.__name__} does not inherit LanDelegateError"


@pytest.mark.req("REQ-YG-636")
def test_missing_credential_error_names_variable():
    """MissingCredentialError message must name the missing variable."""
    exc = errors.MissingCredentialError("GH_TOKEN")
    assert "GH_TOKEN" in str(exc)


@pytest.mark.req("REQ-YG-636")
def test_recursive_delegation_error_mentions_marker():
    """RecursiveDelegationError message must name YAMLGRAPH_LAN_DELEGATED so operators can diagnose."""
    exc = errors.RecursiveDelegationError()
    assert "YAMLGRAPH_LAN_DELEGATED" in str(exc)


@pytest.mark.req("REQ-YG-636")
def test_stale_recon_error_names_ages():
    exc = errors.StaleReconError(
        host="Huutokauppakone.local", age_min=42.0, max_age_min=10.0
    )
    assert "Huutokauppakone.local" in str(exc)
    assert "42" in str(exc)
    assert "10" in str(exc)
