#!/usr/bin/env python3
"""FR-731: compile a yamlgraph prompt YAML to a WebLLM prompt.json.

Spike-local compiler — an example consuming the installed yamlgraph
package, not new framework surface. Loads the reflexion critique prompt
(native inline schema), builds the Pydantic model through the existing
schema_loader path, and emits the portable contract WebLLM needs:

    {name, system, user_template, json_schema}

F3 (judgement): no model_id — deployment config lives in the page.
F5 (judgement): sort_keys serialization — rebuild on an unchanged
prompt is a byte-level no-op, drift is visible in git diff.

Usage:
    python examples/webllm-demo/build.py            # write artifact
    python examples/webllm-demo/build.py --check    # verify no drift
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from yamlgraph.schema_loader import build_pydantic_model

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_YAML = (
    REPO_ROOT / "examples" / "demos" / "reflexion" / "prompts" / "critique.yaml"
)
ARTIFACT = REPO_ROOT / "docs" / "demos" / "webllm" / "prompt.json"


def build_prompt_json() -> dict:
    """Compile the critique prompt YAML to the WebLLM contract dict."""
    config = yaml.safe_load(PROMPT_YAML.read_text())
    model = build_pydantic_model(config["schema"])
    return {
        "name": config["schema"]["name"],
        "system": config["system"],
        "user_template": config["user"],
        "json_schema": model.model_json_schema(),
    }


def serialize(payload: dict) -> str:
    """Deterministic serialization (F5): sorted keys, stable indent."""
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def main() -> int:
    text = serialize(build_prompt_json())
    if "--check" in sys.argv:
        if ARTIFACT.read_text() != text:
            print(f"✗ drift: {ARTIFACT} differs from rebuild", file=sys.stderr)
            return 1
        print(f"✓ {ARTIFACT} is current")
        return 0
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(text)
    print(f"✓ wrote {ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
