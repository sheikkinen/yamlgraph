"""Offline RED tests for FR-949 issue-delegate skill (REQ-YG-637).

Covers the offline seams frozen in FR-949 rev 5 / third judgement:
models.py (request boundary, closed status enums, precedence),
worker.py (YAML-block extraction, payload grammar, redaction, chunking,
artifact verification, timeout truth). No network, no gh, no runner,
no secret, no host mutation (AC-15).

Committed RED first per Commandment 7; GREEN lands in follow-up commits.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Dash in the skill dir name; load via importlib (lan-delegate precedent).
_SKILL_DIR = (
    Path(__file__).parent.parent.parent / ".github" / "skills" / "issue-delegate"
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        f"issue_delegate_{name}",
        _SKILL_DIR / f"{name}.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"issue_delegate_{name}"] = module
    spec.loader.exec_module(module)
    return module


models = _load("models")
worker = _load("worker")

VALID_SHA = "a" * 40


def _request_body(**overrides) -> str:
    fields = {
        "schema_version": 1,
        "task": "judge",
        "sha": VALID_SHA,
        "payload": "feature-requests/FR-900-example.md",
        "max_reported_credits": 60,
    }
    fields.update(overrides)
    lines = "\n".join(f"{k}: {v}" for k, v in fields.items() if v is not None)
    return f"Delegation request.\n\n```yaml\n{lines}\n```\n"


# --- DelegationRequest boundary (AC-04) ---


@pytest.mark.req("REQ-YG-637")
def test_valid_request_parses():
    req = worker.parse_issue_body(_request_body())
    assert req.task == models.Task.JUDGE
    assert req.sha == VALID_SHA
    assert req.repo == "sheikkinen/yamlgraph"  # O-1 default


@pytest.mark.req("REQ-YG-637")
def test_repo_field_is_free_form_owner_name():
    """O-1 as amended: syntactic validation only, no allowlist."""
    req = worker.parse_issue_body(_request_body(repo="sheikkinen/some-extracted-repo"))
    assert req.repo == "sheikkinen/some-extracted-repo"


@pytest.mark.req("REQ-YG-637")
@pytest.mark.parametrize(
    "bad_repo",
    ["noslash", "a/b/c", "owner/", "/name", "owner/na me", "owner/$(cmd)", "-x/y"],
)
def test_repo_field_rejects_non_owner_name_shapes(bad_repo):
    with pytest.raises(models.RequestValidationError):
        worker.parse_issue_body(_request_body(repo=bad_repo))


@pytest.mark.req("REQ-YG-637")
@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": 2},
        {"task": "deploy"},
        {"sha": "A" * 40},  # uppercase
        {"sha": "a" * 39},
        {"sha": None},
        {"max_reported_credits": 0},
        {"max_reported_credits": 61},  # worker max 60 is authoritative
        {"max_reported_credits": -5},
    ],
)
def test_invalid_field_values_fail_before_checkout(overrides):
    with pytest.raises(models.RequestValidationError):
        worker.parse_issue_body(_request_body(**overrides))


@pytest.mark.req("REQ-YG-637")
def test_unknown_key_fails_extra_forbid():
    body = _request_body().replace("```\n", "surprise: extra\n```\n", 1)
    with pytest.raises(models.RequestValidationError):
        worker.parse_issue_body(body)


@pytest.mark.req("REQ-YG-637")
def test_duplicate_key_fails():
    body = _request_body().replace("task: judge", "task: judge\ntask: research")
    with pytest.raises(models.RequestValidationError):
        worker.parse_issue_body(body)


@pytest.mark.req("REQ-YG-637")
@pytest.mark.parametrize(
    "body",
    [
        "no yaml block at all",
        "```yaml\ntask: judge\n```\n```yaml\ntask: judge\n```",  # two blocks
        "```\ntask: judge\n```",  # unfenced language
    ],
)
def test_exactly_one_fenced_yaml_block_required(body):
    with pytest.raises(models.RequestValidationError):
        worker.parse_issue_body(body)


# --- Payload grammar (AC-05) ---


@pytest.mark.req("REQ-YG-637")
@pytest.mark.parametrize(
    "payload",
    [
        "/etc/passwd",
        "../escape.md",
        "feature-requests/../../x.md",
        "feature-requests\\FR-1.md",
        "feature-requests/FR-1\x00.md",
        "-rf.md",
        "feature-requests/FR-900-example.judgement.md",  # judge excludes judgements
        "yamlgraph/cli.py",  # wrong directory/type for judge
    ],
)
def test_judge_payload_grammar_rejects(payload):
    with pytest.raises(models.RequestValidationError):
        worker.validate_payload(models.Task.JUDGE, payload)


@pytest.mark.req("REQ-YG-637")
def test_judge_payload_accepts_fr_markdown():
    worker.validate_payload(models.Task.JUDGE, "feature-requests/FR-900-example.md")


# --- Status enums and precedence (AC-13, § 8) ---


@pytest.mark.req("REQ-YG-637")
def test_delegation_status_precedence_is_total():
    enum_values = set(models.DelegationStatus)
    precedence_values = set(models._PRECEDENCE)
    assert enum_values == precedence_values
    assert len(models._PRECEDENCE) == len(set(models._PRECEDENCE))


@pytest.mark.req("REQ-YG-637")
def test_status_enum_reflects_third_judgement():
    names = {s.name for s in models.DelegationStatus}
    assert "CREDENTIAL_ISOLATION_FAIL" in names  # added per R-2/R-4
    assert "COMMENT_POST_FAIL" not in names  # moved to PublicationStatus per R-2
    assert "UNTRUSTED_AUTHOR" not in names  # removed per R-5


@pytest.mark.req("REQ-YG-637")
def test_publication_status_is_separate_and_closed():
    assert {s.name for s in models.PublicationStatus} == {
        "NOT_ATTEMPTED",
        "OK",
        "COMMENT_POST_FAIL",
        "TERMINAL_MUTATION_FAIL",
    }


@pytest.mark.req("REQ-YG-637")
def test_token_leak_outranks_everything():
    for other in models.DelegationStatus:
        if other is models.DelegationStatus.TOKEN_LEAK_DETECTED:
            continue
        assert (
            models.resolve_status([other, models.DelegationStatus.TOKEN_LEAK_DETECTED])
            is models.DelegationStatus.TOKEN_LEAK_DETECTED
        )


@pytest.mark.req("REQ-YG-637")
def test_kill_fail_outranks_timeout():
    assert (
        models.resolve_status(
            [
                models.DelegationStatus.TIMEOUT,
                models.DelegationStatus.PROCESS_TREE_KILL_FAIL,
            ]
        )
        is models.DelegationStatus.PROCESS_TREE_KILL_FAIL
    )


@pytest.mark.req("REQ-YG-637")
def test_empty_observations_resolve_ok():
    assert models.resolve_status([]) is models.DelegationStatus.OK


# --- Timeout truth (R-1, AC-11) ---


@pytest.mark.req("REQ-YG-637")
def test_inner_deadline_is_25_minutes_and_not_issue_controlled():
    assert models.INNER_DEADLINE_SECONDS == 25 * 60
    assert "timeout" not in models.DelegationRequest.model_fields
    assert "deadline" not in models.DelegationRequest.model_fields


@pytest.mark.req("REQ-YG-637")
def test_timeout_requires_empty_job_and_absent_pids():
    """TIMEOUT only with job empty + all recorded PIDs absent; else KILL_FAIL."""
    ok = worker.resolve_timeout_truth(
        inner_deadline_fired=True, job_active_processes=0, surviving_pids=[]
    )
    assert ok is models.DelegationStatus.TIMEOUT
    survivor = worker.resolve_timeout_truth(
        inner_deadline_fired=True, job_active_processes=0, surviving_pids=[4242]
    )
    assert survivor is models.DelegationStatus.PROCESS_TREE_KILL_FAIL
    active = worker.resolve_timeout_truth(
        inner_deadline_fired=True, job_active_processes=1, surviving_pids=[]
    )
    assert active is models.DelegationStatus.PROCESS_TREE_KILL_FAIL


# --- Redaction (R-4, AC-09) ---


@pytest.mark.req("REQ-YG-637")
def test_redactor_strips_configured_secret_fixtures():
    secret = "ghp_" + "x" * 36
    out = worker.redact(f"before {secret} after", secrets=[secret])
    assert secret not in out
    assert "before" in out and "after" in out


@pytest.mark.req("REQ-YG-637")
def test_literal_leak_in_artifact_yields_token_leak_status():
    secret = "github_pat_" + "y" * 22
    status = worker.check_artifact_for_leak("body with " + secret, secrets=[secret])
    assert status is models.DelegationStatus.TOKEN_LEAK_DETECTED


# --- Chunking and full-output publication (O-2, AC-12) ---


@pytest.mark.req("REQ-YG-637")
def test_chunks_respect_github_limit_and_reassemble_byte_identical():
    payload = ("é" * 30000 + "\n") * 5  # multibyte across boundaries
    chunks = worker.chunk_output(payload, header_template="part {i}/{n} run 1 ")
    for chunk in chunks:
        assert len(chunk.encode("utf-8")) <= 60_000
    reassembled = worker.reassemble(chunks)
    assert reassembled == payload  # O-2: full output, nothing trimmed


@pytest.mark.req("REQ-YG-637")
def test_chunking_never_splits_a_code_point():
    payload = "🜏" * 40_000  # 4-byte code points
    for chunk in worker.chunk_output(payload, header_template="p {i}/{n} "):
        chunk.encode("utf-8")  # would raise on a split surrogate


@pytest.mark.req("REQ-YG-637")
def test_invalid_utf8_replaced_and_final_line_retained():
    raw = b"line1\nline2 \xff\xfe tail-without-newline"
    text = worker.decode_capture(raw)
    assert "\ufffd" in text
    assert text.endswith("tail-without-newline")


# --- Artifact verification (AC-12, § 7) ---


@pytest.mark.req("REQ-YG-637")
def test_judge_artifact_requires_verdict_line(tmp_path):
    good = tmp_path / "draft-judgement.md"
    good.write_text("# J\n\n**Verdict:** APPROVED\n")
    worker.verify_artifact(models.Task.JUDGE, good)  # no raise
    bad = tmp_path / "empty.md"
    bad.write_text("")
    with pytest.raises(models.ArtifactError):
        worker.verify_artifact(models.Task.JUDGE, bad)


@pytest.mark.req("REQ-YG-637")
def test_missing_artifact_fails_even_on_exit_zero(tmp_path):
    with pytest.raises(models.ArtifactError):
        worker.verify_artifact(models.Task.JUDGE, tmp_path / "absent.md")
