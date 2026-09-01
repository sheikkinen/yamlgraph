"""Typed worker entrypoints for issue-queue delegation (FR-949, REQ-YG-637).

The workflow steps call these same functions the unit tests call — no
duplicated shell logic. All worker-controlled bytes cross redact() before
any publication API or runner stdout (third judgement R-4).
"""

from __future__ import annotations

import importlib.util
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
