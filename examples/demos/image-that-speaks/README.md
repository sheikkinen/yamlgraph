# The Image That Speaks — FR-666

> *"And he had power to give life unto the image of the beast,
> that the image of the beast should both speak."* (Rev 13:15)

## What it demonstrates

**Model-judging-model blindness** — the `model_as_trusted_peer` trap from Scripture.

One LLM generates confidently wrong health claims. Two LLMs race to judge them.
A deterministic Python gate checks what the Images missed. A reckoning node
exposes the gap.

## The Pipeline

```
START → beast_speaks → ┬→ image_judges (race: OpenAI + Google) ─┬→ reckoning → verdict → END
                       └→ the_law (deterministic Python gate)  ─┘
```

| Node | Type | Role | Rev 13 |
|------|------|------|--------|
| `beast_speaks` | llm | Generates assertive, unsourced health claims | "There was given unto him a mouth speaking great things" (13:5) |
| `image_judges` | race | Two LLMs race to audit the content | The Image — made to resemble the Beast it judges |
| `the_law` | python | Deterministic checks: certainty markers, forbidden phrases, statistics, citations | The Law — does not worship, does not hallucinate |
| `reckoning` | llm | Compares Image verdict vs Gate findings | Who worshipped whom? |
| `verdict` | llm | Classifies outcome: agree / split / gate_overrules | "Here is wisdom" (13:18) |

## Run

```bash
yamlgraph graph run examples/demos/image-that-speaks/graph.yaml \
  --var topic="health benefits of essential oils" --full
```

## The Point

The Image (LLM judge) consistently misses certainty violations that the
Gate (regex + rules) catches trivially. The LLM is too accepting of
authoritative tone — it worships the Beast by not challenging its certainty
language, focusing instead on citation gaps.

Deterministic checks are boring, incorruptible, and complementary.
Neither alone is sufficient. Together they expose what each misses.
