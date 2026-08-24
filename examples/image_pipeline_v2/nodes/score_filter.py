"""score_filter node (FR-879 AC-08/AC-09): scores candidate prompts via
the deviant-daily critic subprocess and selects top-k survivors.

Fail-fast contract: missing clone/venv/ckpt/calibration stops the run
with retrain commands; zero survivors is an explicit failure — there is
no unfiltered rendering path.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from pathlib import Path

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

RETRAIN_HELP = (
    "set DEVIANT_DAILY_DIR to a sheikkinen/deviant-daily clone with a "
    "trained critic:\n"
    "  git clone https://github.com/sheikkinen/deviant-daily.git\n"
    "  cd deviant-daily && python3.11 -m venv .venv && source .venv/bin/activate\n"
    '  pip install -e ".[training]"\n'
    "  python -m training.prepare prompts/corpus.jsonl training/data --seed 7\n"
    "  python -m training.train --seed 42 --steps 5000 --out training/ckpt\n"
    "  python -m training.score --calibrate"
)


class ScoreRow(BaseModel):
    prompt_sha: str
    register: str
    nll_per_char: float
    truncated: bool
    band: str
    boundary: str
    boundary_reason: str
    verdict: str
    ckpt_sha: str
    corpus_sha: str
    git_sha: str


def _critic_paths() -> tuple[Path, Path]:
    dd = os.environ.get("DEVIANT_DAILY_DIR")
    if not dd:
        raise RuntimeError(f"DEVIANT_DAILY_DIR is not set — {RETRAIN_HELP}")
    root = Path(dd)
    python = root / ".venv" / "bin" / "python"
    for required in (
        root,
        python,
        root / "training" / "ckpt" / "model.pt",
        root / "training" / "ckpt" / "calibration.json",
    ):
        if not required.exists():
            raise RuntimeError(f"missing {required} — {RETRAIN_HELP}")
    return root, python


def score_filter_node(state: dict) -> dict:
    candidates = state.get("candidates") or {}
    prompts = list(candidates.get("prompts") or [])
    if not prompts:
        raise RuntimeError("no candidate prompts in state.candidates.prompts")
    top_k = int(state.get("top_k") or 3)

    root, python = _critic_paths()
    payload = "\n".join(json.dumps({"prompt": p}) for p in prompts)
    completed = subprocess.run(
        [str(python), "-m", "training.score"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=root,
        timeout=600,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"scorer failed (exit {completed.returncode}): {completed.stderr[-500:]}"
        )

    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != len(prompts):
        raise ValueError(
            f"scorer returned {len(lines)} rows for {len(prompts)} prompts"
        )

    scored: list[dict] = []
    for prompt, line in zip(prompts, lines, strict=False):
        try:
            row = ScoreRow.model_validate_json(line)
        except ValidationError as e:
            raise ValueError(f"malformed scorer row: {e}") from e
        expected = hashlib.sha1(prompt.encode(), usedforsecurity=False).hexdigest()[:12]
        if row.prompt_sha != expected:
            raise ValueError(f"prompt sha mismatch: {row.prompt_sha} != {expected}")
        scored.append({"prompt": prompt, **row.model_dump()})

    survivors = sorted(
        (r for r in scored if r["verdict"] == "pass"),
        key=lambda r: r["nll_per_char"],
    )[:top_k]
    for row in scored:
        row["selected"] = any(s["prompt_sha"] == row["prompt_sha"] for s in survivors)

    counts: dict[str, int] = {}
    for row in scored:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    logger.info(f"🧪 critic verdicts: {counts}")
    if not survivors:
        raise RuntimeError(f"zero survivors from {len(prompts)} candidates: {counts}")

    return {"scored": scored, "prompts": [s["prompt"] for s in survivors]}
