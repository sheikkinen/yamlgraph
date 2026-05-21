# Reflection: Gibberish Output from Simple Code Generation

**Date:** 2026-05-21
**Context:** Copilot chat/agent session — simple code generation returned garbled output
**Trap:** `plausible_wrong_answer` → output passes no shape check at all; pure noise

---

## I. The Observation

A simple code generation request — the kind that should be trivially correct — returned gibberish. Not a wrong answer. Not a hallucination. Not a subtly incorrect implementation. Gibberish: tokens that don't compose into coherent language or code.

## II. The Hypothesis: Vectorization/Tokenization Error

The hypothesis: the model's internal representation computed the "right" answer, but an error in the early inference pipeline — tokenization, embedding lookup, or the first few attention layers — corrupted the computation. The output is not wrong in intent; it is wrong in *transport*.

This is analogous to a correct SQL query returning garbled results because of a character encoding mismatch at the connection layer. The logic is sound; the boundary between representation and output is not.

### Why this hypothesis fits

1. **The task was trivially simple.** The model has generated equivalent code thousands of times in training. A semantic failure (wrong algorithm, wrong API) is unlikely for this class of request. A mechanical failure is more parsimonious.

2. **The output is not "creative wrong" — it's incoherent.** Hallucinations have structure: they look right but are wrong. This output doesn't look right. That points to a failure below the semantic layer — in the machinery that converts internal representations to token sequences.

3. **Non-determinism in inference.** Modern LLM inference stacks are complex: quantization, KV-cache management, speculative decoding, batched attention across requests. Any of these can introduce numerical errors that compound through layers. A single corrupted attention head in an early layer can cascade.

### The vectorization angle

Transformer inference is heavily vectorized — matrix multiplications across GPU cores with reduced-precision arithmetic (FP16, BF16, INT8). Known failure modes:

- **NaN/Inf propagation:** A single NaN in an attention score propagates through softmax, corrupting the entire attention distribution for that head. Downstream layers receive garbage context.
- **Quantization clipping:** INT8 or FP8 quantized weights occasionally clip extreme activations, which in early layers can shift the entire representation space for that inference pass.
- **KV-cache corruption:** Speculative decoding or continuous batching can, under load, serve a stale or misaligned KV-cache entry, making the model "attend" to tokens from a different request or conversation turn.
- **Tokenizer edge cases:** BPE merge rules can interact badly with certain byte sequences (especially in multilingual or code contexts), producing token IDs that map to unrelated subwords.

## III. Implications for YAMLGraph

### Boundary: `schema` and `provider`

This is exactly the `schema` boundary from the Knowledge Graph: LLM output entering Pydantic validation. If structured output (JSON mode, tool_use) was used and the tokenization error occurs, the output would fail JSON parsing — which is actually the *correct* behavior. The Pydantic schema acts as a corruption detector.

For unstructured text output (raw code generation), there is no such gate. The gibberish passes through as a valid string.

### Defensive pattern: Output coherence assertion

The current `plausible_wrong_answer` trap assumes the output *looks right* but *is wrong*. This is a new failure mode: the output *looks wrong* and *is wrong*. Paradoxically, this is easier to detect but currently unguarded:

```
if output is coherent → check semantic correctness (existing trap)
if output is incoherent → retry or escalate (unguarded)
```

A simple coherence check (parseable code? valid sentences? entropy below threshold?) at the `schema` boundary would catch this class of failure mechanically.

### Retry semantics

If the hypothesis is correct — transient numerical error in inference — then a simple retry should succeed. This aligns with the existing `on_error: retry` pattern in YAML graph nodes. The failure is not in the prompt or the model's knowledge; it's in the infrastructure serving the inference.

## IV. The Broader Pattern

This is a *The One Law* violation at a boundary we don't control: the provider's inference infrastructure. We normalize at the `provider` boundary for type differences (`content: str` vs `content: list`), but we don't normalize for *coherence*. The assumption has been: if the API returns 200 OK with valid JSON structure, the content is semantically valid. That assumption is false under infrastructure faults.

**The fix:** Normalize coherence at the `schema` boundary. For code outputs: attempt AST parse. For text outputs: basic entropy/perplexity check or at minimum length sanity. For structured outputs: Pydantic already handles this.

## V. Seed

**Seed:** Can we build a lightweight "output coherence gate" that detects garbled LLM responses without requiring a second LLM call? AST parsing for code, regex structure checks for JSON, Shannon entropy for prose — and auto-retry on failure? This would be a universal guard against transient inference infrastructure faults, applicable across all providers.
