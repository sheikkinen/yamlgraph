"""Graph-local tools for the requirement-witness audit demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_BATCHES_DIR = "tmp/req-audit/batches"
DEFAULT_RAW_DIR = "tmp/req-audit/raw"


def _state_path(state: dict[str, Any], key: str, default: str) -> Path:
    value = state.get(key) or default
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string path")
    return Path(value)


def list_batches(state: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Load batch files in deterministic order for map fan-out."""
    batches_dir = _state_path(state, "batches_dir", DEFAULT_BATCHES_DIR)
    if not batches_dir.is_dir():
        raise FileNotFoundError(f"batches_dir does not exist: {batches_dir}")

    paths = sorted(batches_dir.glob("batch-*.json"))
    if not paths:
        raise FileNotFoundError(f"no batch-*.json files found in {batches_dir}")

    batch_files: list[dict[str, Any]] = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)
        if not isinstance(payload, list):
            raise ValueError(f"{path} must contain a JSON list")
        req_ids = [_require_req_id(path, item) for item in payload]
        batch_files.append(
            {
                "stem": path.stem,
                "path": str(path),
                "content": content,
                "req_ids": req_ids,
                "count": len(payload),
            }
        )
    return {"batch_files": batch_files}


def _require_req_id(path: Path, item: Any) -> str:
    if not isinstance(item, dict):
        raise ValueError(f"{path} contains a non-object question payload")
    req_id = item.get("req_id")
    if not isinstance(req_id, str) or not req_id:
        raise ValueError(f"{path} contains a question payload without req_id")
    return req_id


def write_raw_results(state: dict[str, Any]) -> dict[str, list[str]]:
    """Persist each mapped LLM result under the matching batch stem."""
    raw_dir = _state_path(state, "raw_dir", DEFAULT_RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)

    batch_files = state.get("batch_files")
    audit_results = state.get("audit_results")
    if not isinstance(batch_files, list):
        raise TypeError("batch_files must be a list")
    if not isinstance(audit_results, list):
        raise TypeError("audit_results must be a list")

    batches_by_index = {
        index: batch
        for index, batch in enumerate(batch_files)
        if isinstance(batch, dict) and isinstance(batch.get("stem"), str)
    }
    written: list[str] = []
    for result in sorted(audit_results, key=_map_index):
        if not isinstance(result, dict):
            raise ValueError("mapped audit result must be an object")
        if "_error" in result:
            raise ValueError(f"mapped audit result failed: {result['_error']}")

        index = _map_index(result)
        batch = batches_by_index.get(index)
        if batch is None:
            raise ValueError(f"no input batch found for map index {index}")

        structured = {
            key: value for key, value in result.items() if key != "_map_index"
        }
        if not isinstance(structured.get("verdicts"), list):
            raise ValueError(f"batch {batch['stem']} result missing verdicts list")

        output_path = raw_dir / f"{batch['stem']}.json"
        output_path.write_text(
            json.dumps(structured, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(str(output_path))
    return {"raw_files": written}


def _map_index(result: dict[str, Any]) -> int:
    index = result.get("_map_index")
    if not isinstance(index, int):
        raise ValueError("mapped audit result missing integer _map_index")
    return index
