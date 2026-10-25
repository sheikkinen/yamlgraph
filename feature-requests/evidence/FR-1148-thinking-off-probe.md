# FR-1148 evidence: the thinking-off probe (2026-10-25)

**Prior art:** [FR-1048-opencode-cli-probe.md](FR-1048-opencode-cli-probe.md), [FR-960-claude-judge-witness.md](FR-960-claude-judge-witness.md) and the FR-960 run drafts — judge/CLI backend witnesses that share the words "thinking" and "probe", not this provider rule; dismissed. The FR this evidence serves dispositions its own prior art: [../FR-1148-anthropic-thinking-off.md](../FR-1148-anthropic-thinking-off.md). (Added by the FR author at filing to satisfy the FR-738 gate.)

Direct `anthropic==1.3.0` SDK calls from the yamlgraph venv, key from `.env`
(never printed). Raw console output, unedited except one cp1252 byte (the
superscript two in Probe B's text heads) re-encoded as UTF-8 `²`. Scripts kept below so the
probe can be re-run.

## Probe A — which `thinking` form each listed model accepts

Prompt: "Name three primary colours, one per line, nothing else.", `max_tokens=512`.

```text
MODELS ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5", "claude-fable-5-1", "claude-opus-5", "claude-sonnet-5", "claude-fable-5", "claude-opus-4-8", "claude-opus-4-7", "claude-sonnet-4-6", "claude-opus-4-6", "claude-opus-4-5-20251101", "claude-haiku-4-5-20251001", "claude-sonnet-4-5-20250929"]
claude-sonnet-5-5            absent         OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-sonnet-5-5            disabled       400 To turn thinking off on this model, send "thinking": {"type": "between_tools"} instead of {"type": "disabled"}. The model does not think before responding. The short updates it writes between tool calls come back as thinking blocks.
claude-sonnet-5-5            between_tools  OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-opus-5-5              absent         OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-opus-5-5              disabled       400 "thinking.type.disabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.
claude-opus-5-5              between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-fable-5-1             absent         OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-fable-5-1             disabled       400 "thinking.type.disabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.
claude-fable-5-1             between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-sonnet-5              absent         OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-sonnet-5              disabled       OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-sonnet-5              between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-opus-5                absent         OK stop=end_turn blocks=['thinking', 'text'] out=78 text='Red\nYellow\nBlue'
claude-opus-5                disabled       OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-opus-5                between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-fable-5               absent         OK stop=end_turn blocks=['thinking', 'text'] out=34 text='Red\nBlue\nYellow'
claude-fable-5               disabled       400 "thinking.type.disabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.
claude-fable-5               between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-opus-4-8              absent         OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-opus-4-8              disabled       OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-opus-4-8              between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-opus-4-7              absent         OK stop=end_turn blocks=['text'] out=15 text='Red\nBlue\nYellow'
claude-opus-4-7              disabled       OK stop=end_turn blocks=['text'] out=15 text='Red\nBlue\nYellow'
claude-opus-4-7              between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-sonnet-4-6            absent         OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-sonnet-4-6            disabled       OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-sonnet-4-6            between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-haiku-4-5-20251001    absent         OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-haiku-4-5-20251001    disabled       OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-haiku-4-5-20251001    between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-haiku-5-5             absent         OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-haiku-5-5             disabled       OK stop=end_turn blocks=['text'] out=13 text='Red\nBlue\nYellow'
claude-haiku-5-5             between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-opus-4-6              absent         OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-opus-4-6              disabled       OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-opus-4-6              between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-opus-4-5-20251101     absent         OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-opus-4-5-20251101     disabled       OK stop=end_turn blocks=['text'] out=8 text='Red\nBlue\nYellow'
claude-opus-4-5-20251101     between_tools  400 "thinking.type.between_tools" is not supported for this model.
claude-sonnet-4-5-20250929   absent         OK stop=end_turn blocks=['text'] out=8 text='Red\nYellow\nBlue'
claude-sonnet-4-5-20250929   disabled       OK stop=end_turn blocks=['text'] out=8 text='Red\nYellow\nBlue'
claude-sonnet-4-5-20250929   between_tools  400 "thinking.type.between_tools" is not supported for this model.
```

## Probe B — Sonnet 5.5 default thinking eats `max_tokens`

One arithmetic-then-write prompt, `max_tokens=1500`, `claude-sonnet-5-5`, two runs per form.

```text
absent         run1 stop=max_tokens blocks=['thinking'] out=1500 thinking_chars=0 text_chars=0 text_head=''
absent         run2 stop=max_tokens blocks=['thinking'] out=1500 thinking_chars=0 text_chars=0 text_head=''
between_tools  run1 stop=end_turn blocks=['text'] out=1084 thinking_chars=0 text_chars=2491 text_head='I need to compute the sum of i² mod 41 for i = 1 t'
between_tools  run2 stop=end_turn blocks=['text'] out=884 thinking_chars=0 text_chars=2265 text_head='I need to compute the sum of i² mod 41 for i = 1 t'
```

## Probe scripts

```python
"""FR-1148 evidence probe: which `thinking` form each Anthropic model accepts.

Prints request shape, status, error message or stop_reason/block types/usage.
Never prints keys. Run with the yamlgraph venv from C:/src/yamlgraph.
"""

import json
import sys

from dotenv import load_dotenv

load_dotenv("C:/src/yamlgraph/.env")
import anthropic  # noqa: E402

client = anthropic.Anthropic()

ids = [m.id for m in client.models.list(limit=100)]
print("MODELS", json.dumps(ids))

FORMS = {
    "absent": None,
    "disabled": {"type": "disabled"},
    "between_tools": {"type": "between_tools"},
}
MODELS = sys.argv[1:] or [
    "claude-sonnet-5-5",
    "claude-opus-5-5",
    "claude-fable-5-1",
    "claude-sonnet-5",
    "claude-opus-5",
    "claude-fable-5",
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
]
PROMPT = "Name three primary colours, one per line, nothing else."

for model in MODELS:
    for name, thinking in FORMS.items():
        kwargs = {"model": model, "max_tokens": 512, "messages": [{"role": "user", "content": PROMPT}]}
        if thinking is not None:
            kwargs["thinking"] = thinking
        try:
            r = client.messages.create(**kwargs)
            types = [b.type for b in r.content]
            text = "".join(getattr(b, "text", "") for b in r.content if b.type == "text")
            print(
                f"{model:28} {name:14} OK stop={r.stop_reason} blocks={types} "
                f"out={r.usage.output_tokens} text={text.strip()[:40]!r}"
            )
        except anthropic.APIStatusError as e:
            msg = e.body.get("error", {}).get("message") if isinstance(e.body, dict) else str(e)
            print(f"{model:28} {name:14} {e.status_code} {msg}")
```

```python
"""FR-1148 evidence probe: does Sonnet 5.5's default thinking eat max_tokens?

Same demanding prompt, small max_tokens, thinking absent vs between_tools.
Never prints keys.
"""

from dotenv import load_dotenv

load_dotenv("C:/src/yamlgraph/.env")
import anthropic  # noqa: E402

client = anthropic.Anthropic()
PROMPT = (
    "A ledger has 37 entries. Each entry i (1-based) is i*i mod 41. "
    "Work out the sum of all entries, then write a 300-word story whose "
    "first word is that sum spelled out."
)
for name, thinking in (("absent", None), ("between_tools", {"type": "between_tools"})):
    for run in (1, 2):
        kwargs = {
            "model": "claude-sonnet-5-5",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": PROMPT}],
        }
        if thinking is not None:
            kwargs["thinking"] = thinking
        r = client.messages.create(**kwargs)
        types = [b.type for b in r.content]
        text = "".join(getattr(b, "text", "") for b in r.content if b.type == "text")
        think = "".join(getattr(b, "thinking", "") or "" for b in r.content if b.type == "thinking")
        print(
            f"{name:14} run{run} stop={r.stop_reason} blocks={types} out={r.usage.output_tokens} "
            f"thinking_chars={len(think)} text_chars={len(text)} text_head={text.strip()[:50]!r}"
        )
```
