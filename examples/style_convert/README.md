# Style-Convert Pipeline

Restyle an existing file of image prompts into a single target art style.

`style_convert` is the inverse-front twin of
[`image_pipeline`](../image_pipeline/): instead of *inventing* prompts from a
style, it takes a file of prompts you already have and *re-skins* each one into
a target style — preserving the subject, composition, pose, and action, and
replacing only the medium/style/artist references.

```
START → load_prompts (python) → convert_styles (map, LLM/Mistral) → save_prompts (python, reused) → END
```

## Usage

```bash
yamlgraph graph run examples/style_convert/graph.yaml \
  --var input_file="/path/to/prompts.txt" \
  --var target_style="John William Waterhouse, romantic Pre-Raphaelite oil painting" \
  --full
```

### Required variables

| Variable | Description |
|----------|-------------|
| `input_file` | Path to a UTF-8 text file, one prompt per nonblank line. A leading `N. ` enumerator (e.g. `1. a cat on a wall`) is stripped; all other text is preserved. |
| `target_style` | Free-form target art style string (artist, movement, medium). No named-style registry — write the style you want. |

## Input contract

`load_prompts` reads `input_file` as UTF-8 text and treats **each nonblank line
as one prompt**. It strips only a leading decimal enumerator of the form `N. `
and preserves everything else verbatim. It raises `ValueError` if the file is
missing or produces zero prompts, and it **never writes to the input file**.

Blank-line paragraph parsing, multi-line prompts, and named-style lookup tables
are intentionally out of scope.

## Output

`convert_styles` pins **Mistral** on the graph map sub-node
(`convert_styles.node.provider` in `graph.yaml` — the executor resolves the
provider from node config, not from prompt metadata) and returns a structured
`prompt_text` per prompt, so the flattened map output is compatible with the
reused `save_prompts_node`. A `validate_conversions` gate then runs **before**
the sink: if any conversion branch failed, it raises so the run aborts and no
partial prompt file is written (R-3/C-4 — N in == N out or nothing written).
The pipeline reuses
[`image_pipeline`'s `save_prompts_node`](../image_pipeline/nodes/save_prompts.py)
**unchanged**: it writes a timestamped `outputs/image_pipeline/<ts>/prompts.txt`
with one restyled prompt per line and returns `prompt_file` / `output_dir`.

The conversion is **count-preserving**: on success, N input prompts produce
exactly N output lines. There is no `on_error: skip` — a failing conversion
branch surfaces on the error channel and is retained as an error entry rather
than being silently dropped.

## Round-trip with image_pipeline

Because the output format is identical to `image_pipeline`'s prompt sink, the
two compose in both directions:

- Feed `image_pipeline`'s generated `prompts.txt` into `style_convert` to
  re-skin a whole batch into one coherent voice.
- Feed `style_convert`'s output back into `image_pipeline`'s `generate_images`
  node to render the restyled prompts.
