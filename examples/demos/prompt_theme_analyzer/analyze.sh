#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <source_dir>" >&2
  exit 1
fi

SOURCE_DIR="$1"

python - "$SOURCE_DIR" <<'PY'
from __future__ import annotations

import statistics
import sys
from collections import Counter
from pathlib import Path

source_dir = Path(sys.argv[1])
if not source_dir.exists() or not source_dir.is_dir():
    raise SystemExit(f"source_dir must be an existing directory: {source_dir}")

theme_keywords: dict[str, tuple[str, ...]] = {
    "portrait": ("portrait", "close-up", "headshot", "face"),
    "fantasy": ("fantasy", "myth", "dragon", "sorcerer"),
    "sci-fi": ("cyberpunk", "futuristic", "android", "neon"),
    "nature": ("forest", "mountain", "ocean", "flora"),
    "horror": ("gothic", "horror", "macabre", "haunted"),
    "fashion": ("fashion", "couture", "runway", "editorial"),
}

artists = (
    "moebius",
    "greg rutkowski",
    "alphonse mucha",
    "h.r. giger",
    "frank frazetta",
)

files = sorted(source_dir.glob("*/prompts.txt"))
lengths: list[int] = []
theme_counts: Counter[str] = Counter()
artist_counts: Counter[str] = Counter()

for prompts_file in files:
    text = prompts_file.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        continue
    lengths.append(len(text))
    lowered = text.lower()

    for theme, words in theme_keywords.items():
        if any(word in lowered for word in words):
            theme_counts[theme] += 1

    for artist in artists:
        if artist in lowered:
            artist_counts[artist] += 1

print("Prompt Theme Analyzer (non-LLM pre-analysis)")
print(f"Source dir: {source_dir}")
print(f"Prompt files: {len(files)}")

if lengths:
    print(
        "Length stats: "
        f"min={min(lengths)} avg={int(statistics.fmean(lengths))} max={max(lengths)} chars"
    )

print("\nTop themes:")
for name, count in theme_counts.most_common(10):
    print(f"- {name}: {count}")

print("\nTop artist references:")
for name, count in artist_counts.most_common(10):
    print(f"- {name}: {count}")
PY
