# Chapter 4: When the Pattern Breaks the Parser

> *"May I kill the cheapest bug — the one in the spec."*
> — Agents' Prayer, The Scripture

## I. The Comma That Knew Too Much

Here is a function that maps YAML type annotations to JSON Schema. It lives in `discovery.py`, the module that decides what a graph expects as input:

```python
parts = re.split(r"\[", type_str, maxsplit=1)
base = parts[0].strip()
params_str = parts[1].rstrip("]") if len(parts) > 1 else ""
params = (
    [p.strip() for p in params_str.split(",") if p.strip()]
    if params_str else []
)
```

Feed it `str`. It returns `{"type": "string"}`. Correct.

Feed it `list[str]`. The bracket split gives `["list", "str]"]`. The rstrip peels the closing bracket. `params` becomes `["str"]`. The code dispatches to the array case, recurses on `"str"`, and produces `{"type": "array", "items": {"type": "string"}}`. Correct.

Feed it `dict[str, str]`. The bracket split gives `["dict", "str, str]"]`. The rstrip peels the bracket. The comma split gives `["str", "str"]`. The code dispatches to the object case, takes `params[1]` as the value type, and produces `{"type": "object", "additionalProperties": {"type": "string"}}`. Correct.

Three cases. Three successes. The developer feels the warm glow of a working pattern. The regex is clean, readable, tested. Why would you change it?

Now feed it `dict[str, list[int]]`.

The bracket split, with `maxsplit=1`, produces `["dict", "str, list[int]]]"]`. The rstrip doesn't strip the *last* bracket. It strips all trailing characters that appear in the argument set. Both `]` characters vanish. `params_str` becomes `"str, list[int"`. The comma split produces `["str", "list[int"]`. The code takes `params[1]` — `"list[int"` — as the value type and recurses. The double bracket has been swallowed. The nesting information is lost. The output is structurally wrong.

But feed it `dict[str, dict[str, list[int]]]`.

Now `rstrip("]")` strips *three* closing brackets. `params_str` becomes `"str, dict[str, list[int"`. The comma split produces `["str", "dict[str", "list[int"]`. Three fragments. Gibberish. The code takes `params[1]` — `"dict[str"` — as the value type and recurses on a syntactically broken string. No crash. No warning. A silent production of wrong output: a plausible JSON Schema that validates the wrong structure.

The FR-355 diary records what finally replaced this:

> `_split_top_level_args` bracket-aware parser replacing `re.split` avoids the `regex_fourth_exclusion` trap for nested generics like `dict[str, list[int]]`.

A bracket-aware parser. Not a more clever regex. Not a special case. A different tool — one that understands the recursive structure it is being asked to decompose.

The name in the Scripture for this moment — the moment when the fourth special case arrives and the developer reaches for another `if` clause instead of a different formalism — is `regex_fourth_exclusion`. *Fourth special case → switch to proper parser.*

---

## II. The Boundary Between Type Classes

The seduction of `regex_fourth_exclusion` is not technical. It is psychological. Each working case *trains* the developer to trust the tool. Case 1 works. Case 2 works. Case 3 works. The cost of switching feels enormous — you'd have to learn a new API, or write a recursive descent function, or import a parsing library. The cost of one more rule feels negligible — just handle the brackets. One more `if`. One more special case.

But the fourth case doesn't *extend* the pattern. It *breaks the frame*.

Consider what the comma split is being asked to do. "Split on commas." Simple. But `dict[str, list[int]]` contains a comma *inside* a nested type parameter. The comma at the top level separates arguments; the comma inside brackets signals nesting. To split correctly, you need to track bracket depth. A counter makes your tool *stateful*. A stateful pattern matcher is a parser pretending to be a regex.

This is not pedantry. The Chomsky hierarchy describes a genuine boundary: regular expressions (Type 3) match patterns without memory. Context-free grammars (Type 2) match patterns with a stack — they can count opening brackets and match them to closing brackets. The gap is not quantitative (more rules) but qualitative (different computational model). You are not adding a rule to a regex. You are asking a finite automaton to simulate a pushdown automaton. It cannot. It will produce plausible output that silently diverges from correct output as nesting increases.

The FR-166 diary entry shows the same shape. A verification evaluator extracted match groups from a regex into bare `int` locals:

> The evaluator previously extracted `min_count` and `max_count` from a regex match into bare variables with no validation — an inverted range like "10-3 items" was silently parsed and created an impossible check.

The regex matched. The output was plausible. The bug was silent. The cure: wrap extracted groups in a Pydantic model immediately. The model becomes both the validator and the documentation of what the regex is expected to produce.

Each patch is small, local, testable. The compounding cost is invisible. You write one more special case. It works for `dict[str, list[int]]`. Then someone writes `dict[str, dict[str, list[int]]]`. The fifth special case arrives. The regex is now twenty lines long, has nested lookaheads, tracks something that looks suspiciously like bracket depth but is expressed as negative character classes, and no one can read it anymore. The function that started as three lines of readable string manipulation has become a fragile, untestable approximation of a parser — a parser that doesn't know it's a parser.

The funeral was always scheduled. Three successes just hid the date.

---

## III. Normalize at the Boundary

The Scripture's knowledge graph contains a law called `the_one_law`:

> *Normalize at the boundary where external data enters, not downstream where it manifests.*

The regex in `discovery.py` is a *downstream fix*. It receives a type string — `dict[str, list[int]]` — that is already structured, recursive, and context-sensitive. The string is a *serialized syntax tree*. Brackets encode nesting. Commas encode argument boundaries at specific depths. The regex operates downstream, at the point where this structure has been flattened into a linear sequence of characters, and tries to reconstruct the structure it lost.

The boundary where type annotations enter the system — the point where a YAML `state:` block is parsed — should have produced a proper representation: a recursive data structure, a token tree, even just a recursive function that walks the string and tracks bracket depth. Instead, the annotation was passed through as a raw string, and every downstream consumer had to re-derive the structure from the flat representation.

The diary shows the inverse in FR-184. The Philosopher graph needed to match extracted diary patterns against existing Scripture keys — a task that is deterministic, exact, and finite. The initial design delegated this to an LLM:

> LLM-based exact matching against structured YAML keys is non-deterministic. An LLM could silently judge `downstream_fix` as "not present" when the Scripture spells it `downstream_fix:` with a colon, or vice versa.

The cure was to parse deterministically at the Python boundary. A `_load_scripture_keys()` function reads Scripture once, extracts identifiers with a simple regex, and filters against the resulting set. O(1) lookup, zero hallucination risk.

Both errors are wrong for the same reason — the tool's computational class doesn't match the input's structural class. Type annotations are recursive; they need a parser. YAML keys are flat; they need an exact lookup. The One Law doesn't say "always use a parser" or "always use a regex." It says: *normalize at the boundary*. Understand the structure of your input *where it enters*, and choose the tool that matches that structure's complexity class.

---

## IV. The Spec You Didn't Write

The Scripture's cure for `regex_fourth_exclusion` is `spec_kill`: *The cheapest bug is the one killed in the spec.*

This is not advice about documentation. It is advice about *thinking*.

The cure for the `discovery.py` bug is not "write a parser." A parser is the *implementation* of the cure. The cure itself is: **ask the question earlier**. If the specification for the type-annotation mapper had said — before any code was written — "type annotations form a recursive grammar with arbitrarily nested bracket pairs; the parser must handle depth N+1 as correctly as depth N," then the regex would never have been written. The solution would begin with a bracket-depth walker because the spec *requires* one.

The bug was born not in the code but in the *unstated assumption that the input was flat*.

We infer the complexity class of the input from the first examples we see. `str` is flat. `list[str]` has one level of nesting. `dict[str, str]` has one level with two parameters. The mind generalizes: "this is a simple parameterized format." The generalization is plausible. It handles every case in the test suite. It matches every example in the YAML files the developer has seen.

But the generalization is wrong. `list[dict[str, list[int]]]` is a valid type annotation. The grammar permits arbitrary nesting. We just hadn't seen deep enough to notice. The first three examples were drawn from a biased sample — the simple cases that happen to dominate any real codebase — and we mistook the sample for the population.

`spec_kill` says: invest the thinking *before* the code. Ask about the input's structure *before* you choose the tool. What is the grammar? Is it regular, context-free, or context-sensitive? Can the input nest? Can it recurse? The answers determine the tool's minimum computational class.

---

## Seed

How many regexes in production right now are one nesting level away from this trap? How would you audit for it?

The audit pattern might look like this: for every regex in the codebase, identify the input's grammar class. If the input can nest — if brackets appear, if delimiters exist inside nested structures, if the grammar is self-referencing — the regex is a latent `regex_fourth_exclusion` waiting for the fourth case. The audit produces not a list of bugs but a list of *risks*: places where the tool's computational class is lower than the input's structural class.

The question is not whether the fourth case will arrive. It always arrives. The question is whether the spec will name it before the code encounters it.
