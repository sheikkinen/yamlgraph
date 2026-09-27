"""Spike: what does Anthropic constrained decoding do with an unconstrained object?

Question. The daily digest's ranker prompt types its result as
``stories: list[dict]`` (FR-1121, chosen because the Anthropic SDK transform
does not raise on it). The first production run on yamlgraph 0.6.1 returned
zero stories (run 36335550129). Offline, the SDK transform rewrites
``{type: object, additionalProperties: true}`` into
``{type: object, properties: {}, additionalProperties: false}`` — a schema
only ``{}`` satisfies. Is that what the model sees, and is that why it
answered ``[]``? And which declared form carries a story through?

Method. The digest's real prompt (``prompts/rank_stories.yaml``) rendered with
three analysed articles, four schema forms, two binding methods, through the
same libraries the digest uses (langchain-anthropic → ``anthropic.transform_schema``
for ``json_schema``; forced tool call for ``function_calling``). Raw content,
parsed output and the wire schema are recorded per run. Model: the default
yamlgraph resolves for ``provider: anthropic`` with no model named, exactly
as the digest workflow does.

Run:  python docs/spikes/constrained-object-2026-09-27/probe.py > docs/spikes/constrained-object-2026-09-27/probe-output.txt
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import jinja2
import yaml
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from langchain_anthropic.chat_models import (  # noqa: E402
    _convert_to_anthropic_output_config_format,
    convert_to_anthropic_tool,
)

from yamlgraph.config import DEFAULT_MODELS  # noqa: E402
from yamlgraph.schema_loader import (  # noqa: E402
    build_pydantic_model,
    build_pydantic_model_from_json_schema,
)
from yamlgraph.utils.llm_factory import create_llm  # noqa: E402

DIGEST = Path("C:/src/yamlgraph-daily-digest")
PROMPT = yaml.safe_load((DIGEST / "prompts/rank_stories.yaml").read_text(encoding="utf-8"))
OUT = Path(__file__).resolve().parent / "results.json"

ANALYZED = [
    {
        "title": "Rust 2.0 announced with a stable ABI",
        "url": "https://example.com/rust-2",
        "summary": "The Rust team announced a stable ABI and a 2.0 edition timeline.",
        "relevance_score": 0.9,
    },
    {
        "title": "Python 3.15 free-threading becomes default",
        "url": "https://example.com/py315",
        "summary": "CPython 3.15 ships with the GIL disabled by default.",
        "relevance_score": 0.8,
    },
    {
        "title": "LangGraph adds durable map fan-out",
        "url": "https://example.com/langgraph-map",
        "summary": "LangGraph's Send API gains per-branch accounting and failure lists.",
        "relevance_score": 0.7,
    },
]

DESC = "Top 5-8 stories, each with title, url, summary, relevance, reason"

FORMS: dict[str, Any] = {
    # A. production today (FR-1121): `fields` form, list[dict]
    "A_fields_list_dict": ("fields", {"name": "RankedStories", "fields": {"stories": {"type": "list[dict]", "description": DESC}}}),
    # B. production before FR-1121: list[Any] (expected: transform raises)
    "B_fields_list_any": ("fields", {"name": "RankedStories", "fields": {"stories": {"type": "list[Any]", "description": DESC}}}),
    # C. FR-1054 JSON-schema form with declared item properties
    "C_output_schema_nested": (
        "output_schema",
        {
            "type": "object",
            "properties": {
                "stories": {
                    "type": "array",
                    "description": DESC,
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                            "summary": {"type": "string"},
                            "relevance": {"type": "number"},
                            "reason": {"type": "string"},
                        },
                        "required": ["title", "url", "summary", "relevance", "reason"],
                    },
                }
            },
            "required": ["stories"],
        },
    ),
    # D. a single unconstrained object field (the other FR-1123 migration target)
    "D_fields_dict": ("fields", {"name": "RankedStories", "fields": {"stories": {"type": "dict", "description": "map of url -> reason"}}}),
}


def build(form: str, spec: dict) -> type:
    if form == "fields":
        return build_pydantic_model(spec)
    return build_pydantic_model_from_json_schema(spec, "RankedStories")


def messages() -> list:
    user = jinja2.Template(PROMPT["user"]).render(analyzed=ANALYZED, topics=["AI", "Python", "LangGraph"])
    return [SystemMessage(content=PROMPT["system"]), HumanMessage(content=user)]


def wire_schema(method: str, model: type) -> Any:
    if method == "json_schema":
        return _convert_to_anthropic_output_config_format(model)["schema"]
    return convert_to_anthropic_tool(model)["input_schema"]


def run_one(llm: Any, method: str, model: type) -> dict:
    bound = llm.with_structured_output(model, method=method, include_raw=True)
    out = bound.invoke(messages())
    raw = out.get("raw")
    content = getattr(raw, "content", None)
    tool_calls = getattr(raw, "tool_calls", None)
    parsed = out.get("parsed")
    return {
        "raw_content": content if isinstance(content, str) else json.dumps(content, default=str),
        "raw_tool_calls": json.dumps(tool_calls, default=str) if tool_calls else None,
        "parsed": parsed.model_dump() if parsed is not None else None,
        "parsing_error": repr(out.get("parsing_error")) if out.get("parsing_error") else None,
        "usage": getattr(raw, "usage_metadata", None),
    }


def main() -> int:
    llm = create_llm(provider="anthropic")
    print(f"model: {DEFAULT_MODELS['anthropic']}  (create_llm default for provider=anthropic)")
    results: dict[str, Any] = {"model": DEFAULT_MODELS["anthropic"], "runs": []}
    for name, (form, spec) in FORMS.items():
        Model = build(form, spec)
        for method in ("json_schema", "function_calling"):
            reps = 2 if name == "A_fields_list_dict" and method == "json_schema" else 1
            for rep in range(reps):
                rec: dict[str, Any] = {"form": name, "method": method, "rep": rep}
                print(f"\n=== {name} / {method} / rep {rep} ===")
                try:
                    ws = wire_schema(method, Model)
                    rec["wire_schema_stories"] = copy.deepcopy(ws.get("properties", {}).get("stories"))
                    if "$defs" in ws:
                        rec["wire_defs"] = ws["$defs"]
                    print("wire schema (stories):", json.dumps(rec["wire_schema_stories"])[:400])
                    if "$defs" in ws:
                        print("wire $defs:", json.dumps(ws["$defs"])[:400])
                except Exception as e:  # the transform itself may raise (list[Any])
                    rec["wire_error"] = f"{type(e).__name__}: {e}"
                    print("wire schema ERROR:", rec["wire_error"])
                    results["runs"].append(rec)
                    continue
                try:
                    rec.update(run_one(llm, method, Model))
                    stories = (rec["parsed"] or {}).get("stories")
                    n = len(stories) if isinstance(stories, (list, dict)) else None
                    print("raw content[:300]:", (rec["raw_content"] or "")[:300])
                    if rec["raw_tool_calls"]:
                        print("raw tool_calls[:300]:", rec["raw_tool_calls"][:300])
                    print("parsed stories count:", n, "| first:", json.dumps(stories[0] if isinstance(stories, list) and stories else stories, default=str)[:200])
                    print("parsing_error:", rec["parsing_error"])
                except Exception as e:
                    rec["invoke_error"] = f"{type(e).__name__}: {e}"
                    print("invoke ERROR:", rec["invoke_error"][:400])
                results["runs"].append(rec)
    OUT.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nresults written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
