"""sample_candidates node (FR-881 AC-05/AC-06): samples candidate
prompts from the deviant-daily trained local model via the frozen
`training/generate.py --json` JSONL contract, and selects the first
top_k boundary-passing candidates in generation order.

Fail-fast contract: missing clone/venv/ckpt/corpus or malformed JSONL
stops the run with setup/train commands. There is deliberately NO LLM
fallback — the demo's headline is that no LLM is needed (C-4).
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

SETUP_HELP = (
    "set DEVIANT_DAILY_DIR to a sheikkinen/deviant-daily clone with a "
    "trained model:\n"
    "  git clone https://github.com/sheikkinen/deviant-daily.git\n"
    "  cd deviant-daily && python3.11 -m venv .venv && source .venv/bin/activate\n"
    '  pip install -e ".[training]"\n'
    "  python -m training.prepare prompts/corpus.jsonl training/data --seed 7\n"
    "  python -m training.train --seed 42 --steps 5000 --out training/ckpt"
)


class CandidateRow(BaseModel):
    record: str
    ordinal: int
    prompt: str
    attempts_for_candidate: int
    verdict_counts: dict
    seed: int
    temp: float
    top_k: int
    cond: str
    start: str
    ckpt_sha: str
    corpus_sha: str
    git_sha: str


class SummaryRow(BaseModel):
    record: str
    attempts: int
    verdict_counts: dict
    ckpt_sha: str
    corpus_sha: str
    git_sha: str


def _generator_paths() -> tuple[Path, Path]:
    dd = os.environ.get("DEVIANT_DAILY_DIR")
    if not dd:
        raise RuntimeError(f"DEVIANT_DAILY_DIR is not set — {SETUP_HELP}")
    root = Path(dd)
    python = root / ".venv" / "bin" / "python"
    for required in (
        root,
        python,
        root / "training" / "ckpt" / "model.pt",
        root / "prompts" / "corpus.jsonl",
    ):
        if not required.exists():
            raise RuntimeError(f"missing {required} — {SETUP_HELP}")
    return root, python


def sample_candidates_node(state: dict) -> dict:
    n_candidates = int(state.get("n_candidates") or 10)
    top_k = int(state.get("top_k") or 3)
    root, python = _generator_paths()

    cmd = [
        str(python),
        "-m",
        "training.generate",
        "--json",
        "--n",
        str(n_candidates),
        "--temp",
        str(state.get("temp") or "0.8"),
        "--cond",
        str(state.get("cond") or "prose"),
        "--seed",
        str(state.get("seed") or "42"),
    ]
    start = str(state.get("start") or "")
    if start:
        cmd += ["--start", start]

    completed = subprocess.run(
        cmd, capture_output=True, text=True, cwd=root, timeout=1800
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"generator failed (exit {completed.returncode}): "
            f"{completed.stderr.strip()[:500]} — {SETUP_HELP}"
        )

    candidates: list[CandidateRow] = []
    summary: SummaryRow | None = None
    for line in completed.stdout.strip().splitlines():
        try:
            data = json.loads(line)
            if data.get("record") == "candidate":
                candidates.append(CandidateRow(**data))
            elif data.get("record") == "summary":
                summary = SummaryRow(**data)
            else:
                raise ValueError(f"unknown record type: {data.get('record')}")
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            raise RuntimeError(f"malformed generator JSONL line: {e}") from e
    if summary is None or not candidates:
        raise RuntimeError(
            "generator JSONL missing candidates or summary record — "
            f"got {len(candidates)} candidates"
        )

    # Selection (judgement R-2/AC-06): first top_k passers in generation
    # order — the boundary already gated inside the generator.
    scored = []
    prompts = []
    for row in candidates:
        selected = row.ordinal <= top_k
        if selected:
            prompts.append(row.prompt)
        scored.append(
            {
                "ordinal": row.ordinal,
                "prompt": row.prompt,
                "prompt_sha": hashlib.sha1(
                    row.prompt.encode(), usedforsecurity=False
                ).hexdigest()[:12],
                "attempts_for_candidate": row.attempts_for_candidate,
                "verdict_counts": row.verdict_counts,
                "selected": selected,
                "ckpt_sha": row.ckpt_sha,
                "corpus_sha": row.corpus_sha,
                "git_sha": row.git_sha,
            }
        )
    logger.info(
        "🎲 %d candidates in %d attempts; selected first %d",
        len(candidates),
        summary.attempts,
        len(prompts),
    )
    return {
        "scored": scored,
        "prompts": prompts,
        "gen_summary": summary.model_dump(),
    }
