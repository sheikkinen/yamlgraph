"""Probe: does claude-sonnet-4-5 return list[str] as a JSON string under forced tool calling,
and does method="json_schema" (constrained decoding) fix it? Same prompt as spike run 1."""

import json
import sys
from pathlib import Path

import yaml
from langchain_core.messages import HumanMessage, SystemMessage

from yamlgraph.schema_loader import build_pydantic_model
from yamlgraph.utils.llm_factory import create_llm

SPIKE = Path("/Users/sheikki/Documents/src/outsider-spike-llm")
prompt = yaml.safe_load((SPIKE / "prompts/outsider.yaml").read_text())
schema = prompt["schema"]
# restore run-1 shape: the two list fields declared as lists
for f in ("unclear", "needs"):
    schema["fields"][f]["type"] = "list[str]"
    schema["fields"][f]["description"] = (
        schema["fields"][f]["description"]
        .replace("one item per line", "one item per element")
        .replace("Empty string if", "Empty list if")
    )
Model = build_pydantic_model(schema)
text = (SPIKE / "inputs/positive.md").read_text()
msgs = [
    SystemMessage(content=prompt["system"]),
    HumanMessage(content=prompt["user"].replace("{pr_text}", text)),
]
llm = create_llm(provider="anthropic", model="claude-sonnet-4-5", temperature=0.0)

method = sys.argv[1]
structured = llm.with_structured_output(Model, method=method, include_raw=True)
out = structured.invoke(msgs)
raw = out["raw"]
err = out["parsing_error"]
if method == "function_calling":
    args = raw.tool_calls[0]["args"]
    print(
        f"[{method}] unclear arg type={type(args['unclear']).__name__} "
        f"needs arg type={type(args['needs']).__name__}"
    )
    print("raw unclear[:120] =", json.dumps(args["unclear"])[:120])
else:
    print(f"[{method}] content[:120] =", str(raw.content)[:120])
print(f"[{method}] parsing_error =", repr(err)[:200])
if out["parsed"] is not None:
    p = out["parsed"]
    print(f"[{method}] parsed OK: unclear={len(p.unclear)} needs={len(p.needs)}")
