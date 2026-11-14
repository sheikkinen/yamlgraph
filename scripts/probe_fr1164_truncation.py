"""FR-1164 live probe: what a reply cut at the output-token limit looks like.

Operator-approved 2026-11-14: at most 4 requests, at most $0.05.
Needs ANTHROPIC_API_KEY (read from the environment or a .env above this
file; never printed). Writes sanitized evidence to
feature-requests/evidence/FR-1164-truncation-probe.json.

    python scripts/probe_fr1164_truncation.py [OUT.json]

Requests (max_tokens=16, claude-haiku-4-5-20251001):
  1. plain invoke                                -> raw response_metadata
  2. with_structured_output(json_schema, include_raw=True)
                                                 -> the raw envelope
  3. yamlgraph invoke_structured (today's path)  -> what it raises/returns;
     may cost a 4th request if FR-998 earns its second attempt.
"""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel

from yamlgraph.utils.content import normalize_content
from yamlgraph.utils.llm_factory import create_llm
from yamlgraph.utils.structured_output import invoke_structured

REPO = Path(__file__).resolve().parent.parent

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 16
OUT = REPO / "feature-requests" / "evidence" / "FR-1164-truncation-probe.json"
PROMPT = "List fifty countries of the world, one per entry, nothing else."
KEPT_METADATA = ("model", "model_name", "stop_reason", "finish_reason", "usage")


class Countries(BaseModel):
    countries: list[str]


def _meta(message) -> dict:
    meta = getattr(message, "response_metadata", {}) or {}
    return {
        "response_metadata": {k: meta[k] for k in KEPT_METADATA if k in meta},
        "response_metadata_keys": sorted(meta),
        "usage_metadata": getattr(message, "usage_metadata", None),
        "content_block_types": (
            [b.get("type") for b in message.content if isinstance(b, dict)]
            if isinstance(message.content, list)
            else ["str"]
        ),
        "visible_text": normalize_content(message.content),
    }


def _error(err: BaseException) -> dict:
    return {
        "type": f"{type(err).__module__}.{type(err).__qualname__}",
        "message": str(err)[:500],
    }


def main() -> int:
    load_dotenv(find_dotenv(str(Path(__file__).resolve())))
    llm = create_llm(
        provider="anthropic", model=MODEL, max_tokens=MAX_TOKENS, temperature=0
    )
    messages = [("user", PROMPT)]
    result: dict = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "prompt": PROMPT,
        "git_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
        ).stdout.strip(),
        "packages": {
            p: importlib.metadata.version(p)
            for p in (
                "langchain-core",
                "langchain-anthropic",
                "anthropic",
                "langchain-openai",
                "langchain-google-genai",
            )
        },
    }

    try:
        result["plain"] = _meta(llm.invoke(messages))
    except Exception as err:  # evidence, not handling
        result["plain"] = {"error": _error(err)}

    try:
        out = llm.with_structured_output(
            Countries, method="json_schema", include_raw=True
        ).invoke(messages)
        result["structured_include_raw"] = {
            "envelope_keys": sorted(out),
            "raw": _meta(out["raw"]) if out.get("raw") is not None else None,
            "parsed": repr(out.get("parsed")),
            "parsing_error": _error(out["parsing_error"])
            if out.get("parsing_error")
            else None,
        }
    except Exception as err:
        result["structured_include_raw"] = {"error": _error(err)}

    try:
        parsed = invoke_structured(llm, Countries, messages)
        result["structured_today"] = {"returned": repr(parsed)}
    except Exception as err:
        result["structured_today"] = {"error": _error(err)}

    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    out_path.write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
