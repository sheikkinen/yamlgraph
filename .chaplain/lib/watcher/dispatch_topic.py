#!/usr/bin/env python3
"""Select next watcher2 topic and emit normalized project routing context."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from project_contract import (
    load_ninchat_voice_manifest,
    yamlgraph_project_context,
)

NINCHAT_MANIFEST = Path("projects/ninchat_voice/chaplain.yaml")


def _pick_topic(inbox_dir: Path) -> tuple[Path, str]:
    yamlgraph_topics = sorted(inbox_dir.glob("*.md"))
    if yamlgraph_topics:
        return yamlgraph_topics[0], "yamlgraph"

    ninchat_dir = inbox_dir / "ninchat_voice"
    ninchat_dir.mkdir(parents=True, exist_ok=True)
    ninchat_topics = sorted(ninchat_dir.glob("*.md"))
    if ninchat_topics:
        return ninchat_topics[0], "ninchat_voice"

    raise FileNotFoundError("No topic files found in configured inbox lanes")


def _context_for_project(project: str) -> dict[str, str]:
    if project == "ninchat_voice":
        return load_ninchat_voice_manifest(NINCHAT_MANIFEST).model_dump()
    return yamlgraph_project_context().model_dump()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inbox-dir", required=True)
    parser.add_argument("--processing-dir", required=True)
    args = parser.parse_args()

    inbox_dir = Path(args.inbox_dir)
    processing_dir = Path(args.processing_dir)
    processing_dir.mkdir(parents=True, exist_ok=True)

    topic_path, project = _pick_topic(inbox_dir)
    destination = processing_dir / topic_path.name
    shutil.move(str(topic_path), str(destination))

    payload = {"topic_file": str(destination), **_context_for_project(project)}
    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
