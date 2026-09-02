"""Deterministic tools for the disposable diary discourse instrument."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

TARGET_CHARS = 60_000
MAX_PRIMARY_CHUNKS = 96
MAX_REDUCTION_BATCHES = 12
MAX_MEMOS_PER_BATCH = 8
CONTROL_PATHS = (
    "docs/FR-884-session-task-shapes.md",
    "docs/FR-884-raw-read-log.md",
)


def collect_corpus(state: dict[str, Any]) -> dict[str, Any]:
    """Collect diary corpus files and prepare exact-coverage chunk payloads."""
    corpus_dir = _required_path(state, "corpus_dir")
    include_legacy = _parse_bool(state.get("include_legacy", True))

    source_paths = _source_paths(corpus_dir, include_legacy)
    if not source_paths:
        raise ValueError(f"no diary markdown files found under {corpus_dir}")

    manifest: list[dict[str, Any]] = []
    non_empty: list[dict[str, Any]] = []
    empty_files: list[dict[str, Any]] = []
    for path in source_paths:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        record = {
            "path": _repo_relative(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "chars": len(text),
        }
        manifest.append(record)
        if raw:
            non_empty.append({**record, "text": text})
        else:
            empty_files.append(record)

    chunks = _build_chunks(non_empty, TARGET_CHARS)
    if len(chunks) > MAX_PRIMARY_CHUNKS:
        raise ValueError(
            f"primary chunk bound exceeded: {len(chunks)} > {MAX_PRIMARY_CHUNKS}"
        )

    run_budget = {
        "target_chunk_chars": TARGET_CHARS,
        "primary_chunks": len(chunks),
        "max_primary_chunks": MAX_PRIMARY_CHUNKS,
        "estimated_reduction_batches": _ceil_div(len(chunks), MAX_MEMOS_PER_BATCH),
        "max_reduction_batches": MAX_REDUCTION_BATCHES,
        "estimated_llm_calls": len(chunks)
        + _ceil_div(len(chunks), MAX_MEMOS_PER_BATCH),
        "max_llm_calls": MAX_PRIMARY_CHUNKS + MAX_REDUCTION_BATCHES,
    }
    return {
        "corpus_manifest": manifest,
        "empty_files": empty_files,
        "primary_chunks": chunks,
        "control_documents": _read_control_documents(),
        "collection_summary": {
            "source_files": len(source_paths),
            "non_empty_files": len(non_empty),
            "empty_files": len(empty_files),
            "source_bytes": sum(item["bytes"] for item in manifest),
            "covered_non_empty_bytes": sum(item["bytes"] for item in non_empty),
        },
        "run_budget": run_budget,
    }


def batch_memoranda(state: dict[str, Any]) -> dict[str, Any]:
    """Validate primary map results and group memoranda for reduction."""
    chunks = _by_chunk_id(state.get("primary_chunks"))
    raw_memoranda = state.get("chunk_memoranda")
    if not isinstance(raw_memoranda, list):
        raise ValueError("chunk_memoranda must be a list")

    memoranda = _ordered_clean_memoranda(raw_memoranda, chunks)
    batches: list[dict[str, Any]] = []
    for offset in range(0, len(memoranda), MAX_MEMOS_PER_BATCH):
        batch_items = memoranda[offset : offset + MAX_MEMOS_PER_BATCH]
        source_paths = sorted(
            {
                path
                for memo in batch_items
                for path in chunks[memo["chunk_id"]]["source_paths"]
            }
        )
        batches.append(
            {
                "batch_id": f"b{len(batches) + 1:02d}",
                "chunk_ids": [memo["chunk_id"] for memo in batch_items],
                "source_paths": source_paths,
                "memoranda_block": _render_memoranda_block(batch_items),
            }
        )

    if len(batches) > MAX_REDUCTION_BATCHES:
        raise ValueError(
            f"reduction batch bound exceeded: {len(batches)} > {MAX_REDUCTION_BATCHES}"
        )

    return {
        "normalized_memoranda": memoranda,
        "reduction_batches": batches,
        "run_budget": {
            **(state.get("run_budget") or {}),
            "actual_reduction_batches": len(batches),
            "actual_llm_calls": len(memoranda) + len(batches),
        },
    }


def write_dossier(state: dict[str, Any]) -> dict[str, Any]:
    """Write the full JSON dossier and compact markdown index."""
    output_dir = _required_path(state, "output_dir")
    output_dir.mkdir(parents=True, exist_ok=True)

    chunks = _by_chunk_id(state.get("primary_chunks"))
    memoranda = state.get("normalized_memoranda")
    if not isinstance(memoranda, list):
        memoranda = _ordered_clean_memoranda(state.get("chunk_memoranda"), chunks)
    batches = _by_batch_id(state.get("reduction_batches"))
    distillations = _ordered_clean_distillations(
        state.get("batch_distillations"), batches
    )
    coverage = _coverage_reconciliation(
        state.get("corpus_manifest"),
        state.get("empty_files"),
        chunks,
        memoranda,
        batches,
        distillations,
    )
    dossier = {
        "collection_summary": state.get("collection_summary") or {},
        "run_budget": state.get("run_budget") or {},
        "corpus_manifest": state.get("corpus_manifest") or [],
        "empty_files": state.get("empty_files") or [],
        "primary_chunks": list(chunks.values()),
        "chunk_memoranda": memoranda,
        "reduction_batches": list(batches.values()),
        "batch_distillations": distillations,
        "control_documents": state.get("control_documents") or [],
        "coverage_reconciliation": coverage,
    }

    json_path = output_dir / "dossier.json"
    md_path = output_dir / "dossier.md"
    json_path.write_text(json.dumps(dossier, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown_index(dossier), encoding="utf-8")
    print(f"wrote {json_path} and {md_path}")
    return {
        "dossier": dossier,
        "coverage_reconciliation": coverage,
        "dossier_json_path": str(json_path),
        "dossier_md_path": str(md_path),
        "written": True,
    }


def _required_path(state: dict[str, Any], key: str) -> Path:
    value = state.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return Path(value)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ValueError(f"include_legacy must be boolean-like, got {value!r}")


def _source_paths(corpus_dir: Path, include_legacy: bool) -> list[Path]:
    if not corpus_dir.is_dir():
        raise FileNotFoundError(f"corpus_dir does not exist: {corpus_dir}")

    if _repo_relative(corpus_dir) == "docs/diary":
        paths = _tracked_paths(["docs/diary/*.md"])
        if include_legacy:
            paths.extend(_tracked_paths(["docs/diary-*.md"]))
        return sorted(dict.fromkeys(path for path in paths if path.is_file()))

    paths = sorted(corpus_dir.glob("*.md"))
    if include_legacy:
        docs_dir = Path("docs")
        paths.extend(sorted(docs_dir.glob("diary-*.md")))
    return sorted(dict.fromkeys(path for path in paths if path.is_file()))


def _tracked_paths(patterns: list[str]) -> list[Path]:
    return [
        Path(path)
        for path in _git_index_paths()
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
    ]


def _git_index_paths() -> list[str]:
    index = Path(".git/index")
    if not index.is_file():
        raise FileNotFoundError(
            ".git/index not found; committed corpus scan requires git"
        )
    data = index.read_bytes()
    if data[:4] != b"DIRC":
        raise ValueError(".git/index has an unexpected header")
    version, entries = struct.unpack(">II", data[4:12])
    if version not in {2, 3}:
        raise ValueError(f"unsupported git index version for corpus scan: {version}")

    offset = 12
    paths: list[str] = []
    for _ in range(entries):
        if offset + 62 > len(data):
            raise ValueError("truncated git index entry")
        flags = struct.unpack(">H", data[offset + 60 : offset + 62])[0]
        path_length = flags & 0x0FFF
        path_start = offset + 62
        if path_length < 0x0FFF:
            path_end = path_start + path_length
        else:
            path_end = data.index(b"\x00", path_start)
        paths.append(data[path_start:path_end].decode("utf-8"))
        entry_len = (path_end - offset) + 1
        offset += (entry_len + 7) & ~7
    return paths


def _read_control_documents() -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    for name in CONTROL_PATHS:
        path = Path(name)
        if not path.is_file():
            raise FileNotFoundError(f"control document missing: {name}")
        raw = path.read_bytes()
        controls.append(
            {
                "path": name,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "text": raw.decode("utf-8"),
            }
        )
    return controls


def _build_chunks(
    records: list[dict[str, Any]], target_chars: int
) -> list[dict[str, Any]]:
    file_segments: list[dict[str, Any]] = []
    for record in records:
        file_segments.extend(_split_record(record, target_chars))

    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for segment in file_segments:
        if current and current_chars + segment["chars"] > target_chars:
            chunks.append(_make_chunk(len(chunks) + 1, current))
            current = []
            current_chars = 0
        current.append(segment)
        current_chars += segment["chars"]
    if current:
        chunks.append(_make_chunk(len(chunks) + 1, current))
    return chunks


def _split_record(record: dict[str, Any], target_chars: int) -> list[dict[str, Any]]:
    text = record["text"]
    if len(text) <= target_chars:
        return [_segment(record, 0, len(text))]

    boundaries = _split_boundaries(text, target_chars)
    return [_segment(record, start, end) for start, end in boundaries]


def _split_boundaries(text: str, target_chars: int) -> list[tuple[int, int]]:
    boundaries: list[tuple[int, int]] = []
    start = 0
    while start < len(text):
        hard_end = min(len(text), start + target_chars)
        if hard_end == len(text):
            end = hard_end
        else:
            window = text[start:hard_end]
            candidates = [
                window.rfind("\n## "),
                window.rfind("\n# "),
                window.rfind("\n\n"),
            ]
            best = max(candidates)
            end = start + best if best > max(1000, target_chars // 3) else hard_end
        if end <= start:
            end = hard_end
        boundaries.append((start, end))
        start = end
    return boundaries


def _segment(record: dict[str, Any], start_char: int, end_char: int) -> dict[str, Any]:
    text = record["text"]
    start_byte = len(text[:start_char].encode("utf-8"))
    end_byte = len(text[:end_char].encode("utf-8"))
    return {
        "path": record["path"],
        "start_char": start_char,
        "end_char": end_char,
        "start_byte": start_byte,
        "end_byte": end_byte,
        "chars": end_char - start_char,
        "bytes": end_byte - start_byte,
        "text": text[start_char:end_char],
    }


def _make_chunk(index: int, segments: list[dict[str, Any]]) -> dict[str, Any]:
    chunk_id = f"c{index:03d}"
    source_paths = sorted({segment["path"] for segment in segments})
    span_summary = [
        {
            "path": segment["path"],
            "start_byte": segment["start_byte"],
            "end_byte": segment["end_byte"],
            "start_char": segment["start_char"],
            "end_char": segment["end_char"],
        }
        for segment in segments
    ]
    blocks = [
        (
            f"--- SOURCE {segment['path']} "
            f"bytes={segment['start_byte']}..{segment['end_byte']} ---\n"
            f"{segment['text']}"
        )
        for segment in segments
    ]
    return {
        "chunk_id": chunk_id,
        "source_paths": source_paths,
        "span_summary": span_summary,
        "char_count": sum(segment["chars"] for segment in segments),
        "byte_count": sum(segment["bytes"] for segment in segments),
        "text": "\n\n".join(blocks),
    }


def _by_chunk_id(raw_chunks: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw_chunks, list):
        raise ValueError("primary_chunks must be a list")
    chunks: dict[str, dict[str, Any]] = {}
    for chunk in raw_chunks:
        if not isinstance(chunk, dict) or not isinstance(chunk.get("chunk_id"), str):
            raise ValueError("each primary chunk must be a dict with chunk_id")
        chunk_id = chunk["chunk_id"]
        if chunk_id in chunks:
            raise ValueError(f"duplicate chunk_id: {chunk_id}")
        chunks[chunk_id] = chunk
    return chunks


def _by_batch_id(raw_batches: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw_batches, list):
        raise ValueError("reduction_batches must be a list")
    batches: dict[str, dict[str, Any]] = {}
    for batch in raw_batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("batch_id"), str):
            raise ValueError("each reduction batch must be a dict with batch_id")
        batch_id = batch["batch_id"]
        if batch_id in batches:
            raise ValueError(f"duplicate batch_id: {batch_id}")
        batches[batch_id] = batch
    return batches


def _ordered_clean_memoranda(
    raw_items: Any, chunks: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        raise ValueError("chunk_memoranda must be a list")
    ordered_chunk_ids = list(chunks)
    memoranda: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(raw_items, key=lambda value: value.get("_map_index", 0)):
        if not isinstance(item, dict):
            raise ValueError(f"memorandum item must be a dict, got {type(item)}")
        if "_error" in item:
            raise ValueError(f"map memorandum failed: {item['_error']}")
        index = item.get("_map_index")
        if not isinstance(index, int) or not 0 <= index < len(ordered_chunk_ids):
            raise ValueError(f"memorandum has invalid _map_index: {index}")
        payload = _plain_dict(item.get("memorandum") or item)
        chunk_id = payload.get("chunk_id") or ordered_chunk_ids[index]
        if chunk_id != ordered_chunk_ids[index]:
            raise ValueError(
                f"memorandum chunk_id mismatch at index {index}: {chunk_id} != "
                f"{ordered_chunk_ids[index]}"
            )
        if chunk_id in seen:
            raise ValueError(f"duplicate memorandum for chunk_id: {chunk_id}")
        seen.add(chunk_id)
        cleaned = {key: value for key, value in payload.items() if key != "_map_index"}
        cleaned["chunk_id"] = chunk_id
        memoranda.append(cleaned)
    missing = sorted(set(chunks) - seen)
    if missing:
        raise ValueError("missing memoranda for chunks: " + ", ".join(missing))
    return memoranda


def _ordered_clean_distillations(
    raw_items: Any, batches: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        raise ValueError("batch_distillations must be a list")
    ordered_batch_ids = list(batches)
    distillations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(raw_items, key=lambda value: value.get("_map_index", 0)):
        if not isinstance(item, dict):
            raise ValueError(f"distillation item must be a dict, got {type(item)}")
        if "_error" in item:
            raise ValueError(f"map distillation failed: {item['_error']}")
        index = item.get("_map_index")
        if not isinstance(index, int) or not 0 <= index < len(ordered_batch_ids):
            raise ValueError(f"distillation has invalid _map_index: {index}")
        payload = _plain_dict(item.get("distillation") or item)
        batch_id = payload.get("batch_id") or ordered_batch_ids[index]
        if batch_id != ordered_batch_ids[index]:
            raise ValueError(
                f"distillation batch_id mismatch at index {index}: {batch_id} != "
                f"{ordered_batch_ids[index]}"
            )
        if batch_id in seen:
            raise ValueError(f"duplicate distillation for batch_id: {batch_id}")
        seen.add(batch_id)
        cleaned = {key: value for key, value in payload.items() if key != "_map_index"}
        cleaned["batch_id"] = batch_id
        distillations.append(cleaned)
    missing = sorted(set(batches) - seen)
    if missing:
        raise ValueError("missing distillations for batches: " + ", ".join(missing))
    return distillations


def _plain_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if not isinstance(value, dict):
        raise ValueError(f"expected dict payload, got {type(value)}")
    return value


def _render_memoranda_block(memoranda: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for memo in memoranda:
        blocks.append(
            "\n".join(
                [
                    f"## {memo['chunk_id']}",
                    f"Central tension: {memo.get('central_tension', '')}",
                    f"Durable lesson: {memo.get('durable_lesson', '')}",
                    "Correction or contradiction: "
                    + str(memo.get("correction_or_contradiction", "")),
                    f"Unresolved question: {memo.get('unresolved_question', '')}",
                    "Memorandum:",
                    str(memo.get("interpretive_memorandum", "")),
                    "Evidence excerpts:",
                    json.dumps(
                        memo.get("evidence_excerpts") or [],
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                ]
            )
        )
    return "\n\n".join(blocks)


def _coverage_reconciliation(
    manifest: Any,
    empty_files: Any,
    chunks: dict[str, dict[str, Any]],
    memoranda: list[dict[str, Any]],
    batches: dict[str, dict[str, Any]],
    distillations: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(manifest, list) or not isinstance(empty_files, list):
        raise ValueError("manifest and empty_files must be lists")
    manifest_by_path = {item["path"]: item for item in manifest}
    empty_paths = {item["path"] for item in empty_files}
    non_empty_paths = set(manifest_by_path) - empty_paths

    spans_by_path: dict[str, list[tuple[int, int]]] = {
        path: [] for path in non_empty_paths
    }
    for chunk in chunks.values():
        for span in chunk.get("span_summary") or []:
            path = span["path"]
            spans_by_path.setdefault(path, []).append(
                (span["start_byte"], span["end_byte"])
            )

    path_coverage: list[dict[str, Any]] = []
    for path in sorted(non_empty_paths):
        spans = sorted(spans_by_path.get(path) or [])
        expected_end = 0
        for start, end in spans:
            if start != expected_end or end <= start:
                raise ValueError(
                    f"non-contiguous coverage for {path} at {start}..{end}"
                )
            expected_end = end
        expected_bytes = manifest_by_path[path]["bytes"]
        if expected_end != expected_bytes:
            raise ValueError(
                f"byte coverage mismatch for {path}: {expected_end} != {expected_bytes}"
            )
        path_coverage.append(
            {"path": path, "bytes": expected_bytes, "span_count": len(spans)}
        )

    memo_chunk_ids = [memo["chunk_id"] for memo in memoranda]
    batched_chunk_ids = [
        chunk_id
        for batch in batches.values()
        for chunk_id in batch.get("chunk_ids", [])
    ]
    if sorted(memo_chunk_ids) != sorted(chunks):
        raise ValueError("memorandum coverage does not match primary chunks")
    if sorted(batched_chunk_ids) != sorted(memo_chunk_ids):
        raise ValueError("batch coverage does not match memoranda")
    if len(distillations) != len(batches):
        raise ValueError("distillation count does not match reduction batches")

    return {
        "source_files": len(manifest),
        "non_empty_source_files": len(non_empty_paths),
        "empty_files_reported": len(empty_paths),
        "source_bytes": sum(item["bytes"] for item in manifest),
        "non_empty_source_bytes": sum(
            manifest_by_path[path]["bytes"] for path in non_empty_paths
        ),
        "chunk_count": len(chunks),
        "memorandum_count": len(memoranda),
        "reduction_batch_count": len(batches),
        "distillation_count": len(distillations),
        "every_non_empty_source_byte_covered_once": True,
        "every_primary_chunk_has_one_memorandum": True,
        "every_memorandum_belongs_to_one_reduction_batch": True,
        "map_errors_skipped": False,
        "path_coverage": path_coverage,
    }


def _render_markdown_index(dossier: dict[str, Any]) -> str:
    coverage = dossier["coverage_reconciliation"]
    lines = [
        "# Diary Discourse Dossier Index",
        "",
        "This compact index points to the full raw dossier in `dossier.json`.",
        "",
        "## Counts",
        "",
        f"- Source files: {coverage['source_files']}",
        f"- Empty files reported: {coverage['empty_files_reported']}",
        f"- Primary chunks: {coverage['chunk_count']}",
        f"- Memoranda: {coverage['memorandum_count']}",
        f"- Reduction batches: {coverage['reduction_batch_count']}",
        f"- Batch distillations: {coverage['distillation_count']}",
        f"- Source bytes: {coverage['source_bytes']}",
        f"- Non-empty source bytes covered: {coverage['non_empty_source_bytes']}",
        "",
        "## Primary chunks",
        "",
    ]
    for chunk in dossier["primary_chunks"]:
        lines.append(
            f"- `{chunk['chunk_id']}`: {chunk['char_count']} chars, "
            f"{chunk['byte_count']} bytes, {len(chunk['source_paths'])} paths"
        )
    lines.extend(["", "## Reduction batches", ""])
    for batch in dossier["reduction_batches"]:
        lines.append(
            f"- `{batch['batch_id']}`: {len(batch['chunk_ids'])} memoranda, "
            f"{len(batch['source_paths'])} paths"
        )
    lines.extend(["", "## Control documents packaged separately", ""])
    for control in dossier["control_documents"]:
        lines.append(f"- `{control['path']}` ({control['bytes']} bytes)")
    return "\n".join(lines).rstrip() + "\n"


def _ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor if value else 0


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()
