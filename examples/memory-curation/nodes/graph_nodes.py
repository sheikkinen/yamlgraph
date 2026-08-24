"""Graph glue for the FR-875 memory-curation example."""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def load_memory_notes(state: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(str(state["out_dir"]))
    manifest_path = out_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    notes = [
        {
            "path": path,
            "body": (out_dir / "notes" / path).read_text(encoding="utf-8"),
        }
        for path in sorted(manifest["notes"])
    ]
    return {
        "manifest_path": str(manifest_path),
        "notes": notes,
        "note_count": len(notes),
        "today": date.today().isoformat(),
    }


def reconcile_memory_dispositions(state: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(str(state["out_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    dispositions_path = out_dir / "dispositions.json"
    dispositions = [_jsonable(item) for item in state["dispositions"]]
    dispositions_path.write_text(
        json.dumps(dispositions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "python",
            "examples/memory-curation/nodes/reconcile.py",
            "--manifest",
            str(state["manifest_path"]),
            "--dispositions",
            str(dispositions_path),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "reconcile_summary": {
            "stdout": result.stdout.strip(),
            "dispositions_path": str(dispositions_path),
            "disposition_json": str(out_dir / "disposition.json"),
            "disposition_md": str(out_dir / "disposition.md"),
        }
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
