# Session Continuation Test - FR-105

Tests whether Copilot's `--continue` session flag actually preserves conversation context.

## The Experiment

1. **Node 1** (`create_characters`): Creates two original characters with specific names/traits
2. **Interrupt** (`ask_place`): Pauses for user to specify meeting location
3. **Node 3** (`write_meeting`): Writes how they met using `continue_session: true`

**Key insight**: Node 3's prompt does NOT include character information. It relies entirely on session continuation to know the characters. The place IS passed explicitly (hybrid test).

## Expected Results

### If session continuation works:
- Node 3 correctly references the character names from Node 1
- Story uses the specific traits (profession, quirk, secret) from Node 1
- Meeting happens at the user-specified location
- "Session verification" line shows the same names

### If session continuation fails:
- Node 3 invents new characters OR
- Node 3 is confused about which characters to use OR
- Generic story without the specific traits

## Run the Test

### Automated (mock input for interrupt):
```bash
cd examples/demos/session-test
chmod +x runner.sh
./runner.sh noir "a smoke-filled jazz club"
```

Or with Python directly:
```bash
python run_demo.py --genre sci-fi --place "a derelict space station cafeteria"
```

### Interactive (real user input):
```bash
# Requires manual input at interrupt
yamlgraph graph run examples/demos/session-test/graph.yaml --var genre="fantasy" --full
```

Try different genres: `sci-fi`, `fantasy`, `romance`, `thriller`, `noir`

## Implementation Details

- `create_characters` node: No special flags
- `ask_place` node: `type: interrupt` with `resume_key: meeting_place`
- `write_meeting` node: Uses `cli_flags.continue_session: true` (translates to `--continue`)
- FR-105 continuation uses `--continue` (last session) not `--resume <id>` (specific session)
- Checkpointer required for interrupt nodes: `type: sqlite, path: :memory:`
