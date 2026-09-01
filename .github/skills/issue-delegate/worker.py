"""Typed worker entrypoints for issue-queue delegation (FR-949, REQ-YG-637).

The workflow steps call these same functions the unit tests call — no
duplicated shell logic. All worker-controlled bytes cross redact() before
any publication API or runner stdout (third judgement R-4).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml

_HERE = Path(__file__).parent


def _load_models():
    if "issue_delegate_models" in sys.modules:
        return sys.modules["issue_delegate_models"]
    spec = importlib.util.spec_from_file_location(
        "issue_delegate_models", _HERE / "models.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["issue_delegate_models"] = module
    spec.loader.exec_module(module)
    return module


models = _load_models()

REDACTION_MARK = "[REDACTED]"
MAX_COMMENT_BYTES = 60_000

_YAML_BLOCK = re.compile(r"^```yaml\s*$(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys."""


def _strict_mapping(loader: _StrictLoader, node: yaml.MappingNode, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise models.RequestValidationError(f"duplicate key: {key!r}")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _strict_mapping
)


def parse_issue_body(body: str):
    """Extract exactly one fenced YAML mapping and validate it (AC-04)."""
    blocks = _YAML_BLOCK.findall(body)
    if len(blocks) != 1:
        raise models.RequestValidationError(
            f"expected exactly one ```yaml block, found {len(blocks)}"
        )
    try:
        data = yaml.load(blocks[0], Loader=_StrictLoader)  # noqa: S506  # SafeLoader subclass
    except models.RequestValidationError:
        raise
    except yaml.YAMLError as exc:
        raise models.RequestValidationError(f"YAML parse failure: {exc}") from exc
    if not isinstance(data, dict):
        raise models.RequestValidationError("YAML block is not a mapping")
    try:
        return models.DelegationRequest.model_validate(data)
    except ValueError as exc:
        raise models.RequestValidationError(str(exc)) from exc


_JUDGE_PAYLOAD = re.compile(r"^feature-requests/FR-[A-Za-z0-9._-]+\.md$")
_RESEARCH_PAYLOAD = re.compile(r"^[A-Za-z0-9._/-]+\.md$")


def validate_payload(task, payload: str) -> None:
    """Mechanical payload grammar (AC-05); rejects before checkout or launch."""
    if (
        not payload
        or payload.startswith(("/", "-"))
        or "\\" in payload
        or ".." in payload.split("/")
        or any(ord(c) < 32 for c in payload)
    ):
        raise models.RequestValidationError(f"payload shape refused: {payload!r}")
    if task is models.Task.JUDGE:
        if payload.endswith(".judgement.md") or not _JUDGE_PAYLOAD.match(payload):
            raise models.RequestValidationError(
                f"judge payload must be feature-requests/FR-*.md: {payload!r}"
            )
    elif task is models.Task.RESEARCH:
        if not _RESEARCH_PAYLOAD.match(payload) or payload.startswith("-"):
            raise models.RequestValidationError(
                f"research payload must be a committed .md brief: {payload!r}"
            )
    else:  # pragma: no cover - Task is a closed enum
        raise models.RequestValidationError(f"unknown task: {task!r}")


def resolve_timeout_truth(
    *, inner_deadline_fired: bool, job_active_processes: int, surviving_pids: list[int]
):
    """TIMEOUT only with the job empty AND every recorded PID absent (R-1/AC-11)."""
    if not inner_deadline_fired:
        return models.DelegationStatus.OK
    if job_active_processes == 0 and not surviving_pids:
        return models.DelegationStatus.TIMEOUT
    return models.DelegationStatus.PROCESS_TREE_KILL_FAIL


def redact(text: str, *, secrets: list[str]) -> str:
    """Single redaction boundary for worker-controlled bytes (R-4/AC-09)."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, REDACTION_MARK)
    return text


def check_artifact_for_leak(body: str, *, secrets: list[str]):
    """Literal configured secret in an artifact => TOKEN_LEAK_DETECTED."""
    for secret in secrets:
        if secret and secret in body:
            return models.DelegationStatus.TOKEN_LEAK_DETECTED
    return None


def decode_capture(raw: bytes) -> str:
    """Invalid UTF-8 becomes U+FFFD; the final unterminated line is retained."""
    return raw.decode("utf-8", errors="replace")


def chunk_output(text: str, *, header_template: str) -> list[str]:
    """Split into GitHub-postable chunks: header + '\\n' + slice.

    O-2: the full text is published — chunking is mechanical, never trims.
    Each chunk is <= MAX_COMMENT_BYTES UTF-8 bytes including its header and
    never splits a code point.
    """
    # Reserve header space using a generous width so n is stable.
    header_budget = len(header_template.format(i=99999, n=99999).encode()) + 1
    body_budget = MAX_COMMENT_BYTES - header_budget
    encoded = text.encode()
    slices: list[str] = []
    pos = 0
    while pos < len(encoded):
        end = min(pos + body_budget, len(encoded))
        # Back off to a UTF-8 code-point boundary (continuation bytes are 10xxxxxx).
        while end > pos and end < len(encoded) and (encoded[end] & 0xC0) == 0x80:
            end -= 1
        slices.append(encoded[pos:end].decode())
        pos = end
    n = len(slices)
    return [
        header_template.format(i=i, n=n) + "\n" + body
        for i, body in enumerate(slices, start=1)
    ]


def reassemble(chunks: list[str]) -> str:
    """Ordered reassembly, byte-identical to the original text."""
    return "".join(chunk.split("\n", 1)[1] for chunk in chunks)


_VERDICT_LINE = re.compile(r"\*\*Verdict:\*\*", re.MULTILINE)


def verify_artifact(task, path: Path) -> None:
    """Fresh, non-empty, task-shaped artifact — or ArtifactError even on exit 0."""
    if not path.is_file():
        raise models.ArtifactError(f"artifact missing: {path}")
    body = path.read_text(encoding="utf-8")
    if not body.strip():
        raise models.ArtifactError(f"artifact empty: {path}")
    if task is models.Task.JUDGE and not _VERDICT_LINE.search(body):
        raise models.ArtifactError(f"judge artifact has no verdict line: {path}")


# ---------------------------------------------------------------------------
# CLI — the workflow steps and submit.sh call these same entrypoints (AC-15)
# ---------------------------------------------------------------------------


def _cmd_validate_payload(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: worker.py validate-payload <task> <payload>", file=sys.stderr)
        return 2
    try:
        task = models.Task(argv[0])
        validate_payload(task, argv[1])
    except (ValueError, models.RequestValidationError) as exc:
        print(f"payload refused: {exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_parse_issue(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: worker.py parse-issue <event.json>", file=sys.stderr)
        return 2
    event = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    try:
        request = parse_issue_body(event["issue"]["body"])
        validate_payload(request.task, request.payload)
    except (KeyError, models.RequestValidationError) as exc:
        print(f"INVALID_REQUEST: {exc}", file=sys.stderr)
        return 1
    print(f"task={request.task.value}")
    print(f"repo={request.repo}")
    print(f"sha={request.sha}")
    print(f"payload={request.payload}")
    print(f"max_reported_credits={request.max_reported_credits}")
    return 0


_COMMANDS = {
    "validate-payload": _cmd_validate_payload,
    "parse-issue": _cmd_parse_issue,
    "resolve": None,  # bound below
}


_ARTIFACTS = {
    "judge": "tmp/draft-judgement.md",
    "research": "tmp/draft-alternatives.md",
}

_CHUNK_HEADER = "<!-- delegation output part {i}/{n} -->"


def _cmd_resolve(argv: list[str]) -> int:
    """Cleanup-side resolution: verify, redact, credits, status precedence.

    Runs after payload termination and before any publication (AC-13);
    writes redacted comment chunks and the final status for the workflow's
    publication steps — the single redaction boundary (R-4).
    """
    import argparse
    import os

    ap = argparse.ArgumentParser(prog="worker.py resolve")
    ap.add_argument("--task", required=True)
    ap.add_argument("--result-json", required=True)
    ap.add_argument("--capture", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--target-dir", default="target")
    a = ap.parse_args(argv)
    task = models.Task(a.task)

    result_path = Path(a.result_json)
    job = json.loads(result_path.read_text()) if result_path.is_file() else {}
    capture_path = Path(a.capture)
    raw_text = (
        decode_capture(capture_path.read_bytes()) if capture_path.is_file() else ""
    )
    secrets = [
        v
        for k, v in os.environ.items()
        if v and (k.startswith("DELEGATE_") or k in ("GH_TOKEN", "GITHUB_TOKEN"))
    ]
    observed: list[models.DelegationStatus] = []

    timeout_status = resolve_timeout_truth(
        inner_deadline_fired=bool(job.get("inner_deadline_fired")),
        job_active_processes=int(job.get("job_active_processes", 0)),
        surviving_pids=list(job.get("surviving_pids", [])),
    )
    if timeout_status is not models.DelegationStatus.OK:
        observed.append(timeout_status)
    if job.get("exit_code", 1) != 0:
        observed.append(models.DelegationStatus.PAYLOAD_NONZERO)

    artifact_path = Path(a.target_dir) / _ARTIFACTS[task.value]
    artifact_body: str | None = None
    if not artifact_path.is_file():
        observed.append(models.DelegationStatus.ARTIFACT_MISSING)
    else:
        try:
            verify_artifact(task, artifact_path)
            artifact_body = artifact_path.read_text(encoding="utf-8")
        except models.ArtifactError:
            observed.append(models.DelegationStatus.ARTIFACT_INVALID)

    credits = job.get("reported_credits")
    if credits is not None:
        try:
            if float(credits) > models.MAX_REPORTED_CREDITS:
                observed.append(models.DelegationStatus.CREDIT_FAIL_HIGH)
        except (TypeError, ValueError):
            observed.append(models.DelegationStatus.CREDIT_FAIL_UNPARSEABLE)

    # Literal configured secret in worker-controlled output (pre-redaction).
    leak = check_artifact_for_leak(raw_text + (artifact_body or ""), secrets=secrets)
    if leak is not None:
        observed.append(leak)
        artifact_body = None  # artifact is never posted on a leak

    status = models.resolve_status(observed)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    redacted = redact(raw_text, secrets=secrets)
    index = 0
    for chunk in chunk_output(redacted, header_template=_CHUNK_HEADER):
        (out / f"comment-{index:03d}.md").write_text(chunk, encoding="utf-8")
        index += 1
    if artifact_body is not None and status is models.DelegationStatus.OK:
        for chunk in chunk_output(
            redact(artifact_body, secrets=secrets),
            header_template="<!-- delegation artifact part {i}/{n} -->",
        ):
            (out / f"comment-{index:03d}.md").write_text(chunk, encoding="utf-8")
            index += 1
    (out / "status.txt").write_text(status.value, encoding="utf-8")
    print(f"status={status.value}")
    return 0


_COMMANDS["resolve"] = _cmd_resolve


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in _COMMANDS:
        print(f"usage: worker.py {{{'|'.join(_COMMANDS)}}} ...", file=sys.stderr)
        return 2
    return _COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
