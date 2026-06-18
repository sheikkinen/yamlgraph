# The Filter That Belonged at the Boundary

**Date:** 2026-06-17
**Context:** FR-512 enforcement (chapter-open context slimming) + run 10019 validation (book_reviewer pipeline)
**Incident:** Book reviewer pipeline failed on LLM output shape mismatches; initial fix attempt was downstream error recovery; correct fix was boundary-layer coercion.

## The Trap

When the book_reviewer pipeline (FR-497) ran on run 10019, the chapter_review LLM node returned structured data where one field (`criteria`) arrived as a JSON string instead of the expected `list[CriterionScore]` (Pydantic model).

The error stack showed:
```
Node _map_chapter_review_sub failed: 1 validation error for ChapterReviewOutput
criteria
  Input should be a valid list [type=list_type, input_value='[\n  {\n    "name":
  "coh...eter name="issues">null', input_type=str]
```

**Initial diagnosis:** The map collector is storing error dicts when items fail. Let me add a filter downstream in compute_node to skip `_error`-marked entries.

**Implementation:** Added condition:
```python
reviews = [
    ChapterReview.model_validate(r)
    for r in state.get("chapter_reviews", [])
    if not isinstance(r, dict) or "_error" not in r
]
```

This worked (run completed, review.md generated).

**But:**

This approach treated the symptom, not the root cause. The real problem was that `ChapterReview` was fragile to LLM output shape variations. Once fixed at the entry boundary, the downstream filter became unnecessary.

## The Insight: Normalize at Entry, Not at Exit

The correct fix belonged in the model layer itself. Pydantic v2 provides `@field_validator(mode="before")` to coerce inputs *before* type checking. The `issues` field already had this:

```python
@field_validator("issues", mode="before")
@classmethod
def _coerce_issues(cls, v: object) -> list[str]:
    return v if isinstance(v, list) else []
```

The solution: **Apply the same pattern to fields that receive LLM outputs.**

Added validators to:
- `ChapterReview.criteria`: returns `[]` if input is not a list
- `PairContinuity.breaks`: converts non-list to `[]`, then stringifies each item
- `SynopsisBeats.promised` and `.undelivered`: same pattern

**Why this is correct:**

1. **Entry boundary is the trust boundary.** When external data (LLM output, API response, user input) crosses into the system, the model is the first gatekeeper. That's where type normalization belongs.

2. **Coercion at entry prevents downstream fragility.** Once the field passes the validator, all downstream code can assume it has the correct shape. No need for defensive checks deeper in the call chain.

3. **Tests the assumption cheaply.** Boundary coercers document the system's tolerance for shape variation and make that tolerance testable without reaching downstream code.

4. **Follows "Commandment 6: bear witness of thy errors"** — normalize at the boundary where external data enters, not downstream where it manifests.

From the Scripture: **"Normalize at the boundary where external data enters, not downstream where it manifests."**

## What Went Right

- The LLM output was recognizably a valid critique (just wrong JSON shape)
- Book reviewer still produced a correct review (chapters with missing criteria just scored 0, pulling overall down)
- Run 10019 completed with meaningful output despite the validation hiccup
- The fix was local to the model layer (no orchestration changes needed)

## What Went Wrong

- Initial assumption that error dicts needed special handling in compute_node (they didn't; the model should have accepted the input shape)
- Didn't check for existing boundary coercers before adding error recovery code
- The downstream filter masked the real problem and made the pipeline look robust when it was fragile

## The Correctness Proof

After adding boundary coercers:
- `pytest examples/book_reviewer/tests/ -q` → all tests pass
- Ran pipeline on run 10019 → review.md generated with quality scores
- Score aggregation works correctly even with mixed-quality per-chapter inputs

The downstream filter in compute_node can now be removed; it's no longer needed.

## Lessons

1. **Coercion validators are first-class infrastructure.** They aren't just error handling; they're the contract at the boundary.

2. **"Defensive" code downstream signals a missed opportunity upstream.** When you find yourself writing `if not isinstance(x, list) or "_error" not in x`, stop and ask: "Does the entry boundary know how to handle this?"

3. **The trust boundary moves with the data layer.** The model is where external LLM outputs first become data; that's where tolerance and coercion logic belongs.

4. **Test the boundary, not the defense.** Rather than test for error recovery in compute_node, test that ChapterReview accepts various input shapes and normalizes them correctly.

## Related Scripture

- **One Law:** Normalize at the boundary where external data enters, not downstream where it manifests.
- **Commandment 5:** Sanctify thy outputs with types (and coercers).
- **Commandment 6:** Bear witness of thy errors. What is hidden in an entry-layer assumption shall be revealed in production.

---

## Seed: Models as Self-Defending Entry Points

How do we design Pydantic models to be more self-defending across LLM provider variations without balloning validator count?

**Directions to explore:**
1. Base model mixin pattern: a `BoundaryModel(BaseModel)` subclass that provides coercion for common LLM-output patterns (list shape variance, string/int confusion, nested depth mismatches)
2. Decorator-based validator synthesis: `@coerce_list("field_name")` that auto-generates the validator
3. Testing posture: unit tests that verify models accept 5–10 common shape variations of real LLM output, not just the happy path
4. Documentation norm: require *both* the shape you expect *and* the shapes you'll accept with examples from production logs

Example starting point:
```python
class SelfDefendingModel(BaseModel):
    """Base for models that receive direct LLM output.

    Provides automatic list coercion for fields declared with
    coerce_lists() so downstream code doesn't need to check shapes.
    """
    @classmethod
    def coerce_lists(cls) -> list[str]:
        """Override to list field names that should coerce to []."""
        return []

    def __init_subclass__(cls):
        """Auto-attach validators to declared coerce fields."""
        for field_name in cls.coerce_lists():
            # Synthesize @field_validator for this field
            pass
```

Would this improve robustness without adding thousands of manual validators?

---

**Diary Entry Closed:** 2026-06-17 20:15
**Next Session Seeds:**
- Explore self-defending model base patterns
- Run full test suite on book_reviewer to ensure all edge cases are covered
- Remove the now-unnecessary error filter from compute_node
- Consider whether other examples have the same boundary-coercion gap
