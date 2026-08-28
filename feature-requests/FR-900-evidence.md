# FR-900 Evidence — raw price-sheet and report observations (promoted from tmp/fr900-raw/, 2026-08-28)

## billing-blocks.json (raw billing blocks, newest models.json)
```json
{
  "source": "/Users/sami.j.p.heikkinen/Library/Application Support/Code/User/workspaceStorage/152c28e905ea7afa3341c4a1f4daf141/GitHub.copilot-chat/debug-logs/1c67ea71-4e33-4771-99e8-8634a1014c0c/models.json",
  "claude-fable-5": {
    "restricted_to": [
      "pro_plus",
      "business",
      "enterprise",
      "max"
    ],
    "token_prices": {
      "batch_size": 1000000,
      "default": {
        "cache_read_price": 100,
        "cache_write_1h_price": 2000,
        "cache_write_price": 1250,
        "input_price": 1000,
        "max_prompt_tokens": 200000,
        "output_price": 5000
      },
      "long_context": {
        "cache_read_price": 100,
        "cache_write_1h_price": 2000,
        "cache_write_price": 1250,
        "input_price": 1000,
        "max_prompt_tokens": 936000,
        "output_price": 5000
      }
    }
  },
  "claude-sonnet-5": {
    "auto_discount": 0.3,
    "restricted_to": [
      "pro",
      "pro_plus",
      "business",
      "enterprise",
      "max"
    ],
    "token_prices": {
      "batch_size": 1000000,
      "default": {
        "cache_read_price": 20,
        "cache_write_1h_price": 400,
        "cache_write_price": 250,
        "input_price": 200,
        "max_prompt_tokens": 200000,
        "output_price": 1000
      },
      "long_context": {
        "cache_read_price": 20,
        "cache_write_1h_price": 400,
        "cache_write_price": 250,
        "input_price": 200,
        "max_prompt_tokens": 936000,
        "output_price": 1000
      }
    }
  },
  "gpt-5.6-sol": {
    "auto_discount": 0.3,
    "restricted_to": [
      "pro_plus",
      "business",
      "enterprise",
      "max"
    ],
    "token_prices": {
      "batch_size": 1000000,
      "default": {
        "cache_read_price": 20,
        "cache_write_price": 250,
        "input_price": 200,
        "max_prompt_tokens": 272000,
        "output_price": 1000
      },
      "long_context": {
        "cache_read_price": 40,
        "cache_write_price": 500,
        "input_price": 400,
        "max_prompt_tokens": 922000,
        "output_price": 1500
      }
    }
  }
}```

## old-parser-prices.txt (load_prices() output under the cache_price bug — cache: 0 for all 34 families)
```
claude-fable-5                 {'in': 1000, 'out': 5000, 'cache': 0}
claude-haiku-4.5               {'in': 100, 'out': 500, 'cache': 0}
claude-opus-4.5                {'in': 500, 'out': 2500, 'cache': 0}
claude-opus-4.6                {'in': 500, 'out': 2500, 'cache': 0}
claude-opus-4.7                {'in': 500, 'out': 2500, 'cache': 0}
claude-opus-4.8                {'in': 500, 'out': 2500, 'cache': 0}
claude-opus-4.8-fast           {'in': 1000, 'out': 5000, 'cache': 0}
claude-opus-5                  {'in': 500, 'out': 2500, 'cache': 0}
claude-sonnet-4.5              {'in': 300, 'out': 1500, 'cache': 0}
claude-sonnet-4.6              {'in': 300, 'out': 1500, 'cache': 0}
claude-sonnet-5                {'in': 200, 'out': 1000, 'cache': 0}
gemini-3.1-pro-preview         {'in': 200, 'out': 1200, 'cache': 0}
gemini-3.5-flash               {'in': 150, 'out': 900, 'cache': 0}
gemini-3.6-flash               {'in': 75, 'out': 375, 'cache': 0}
gemini-3.7-flash               {'in': 75, 'out': 375, 'cache': 0}
gpt-3.5-turbo                  {'in': 0, 'out': 0, 'cache': 0}
gpt-4                          {'in': 250, 'out': 1000, 'cache': 0}
gpt-4-turbo                    {'in': 1000, 'out': 3000, 'cache': 0}
gpt-4.1                        {'in': 0, 'out': 0, 'cache': 0}
gpt-4o                         {'in': 0, 'out': 0, 'cache': 0}
gpt-4o-mini                    {'in': 0, 'out': 0, 'cache': 0}
gpt-5-mini                     {'in': 25, 'out': 200, 'cache': 0}
gpt-5.3-codex                  {'in': 175, 'out': 1400, 'cache': 0}
gpt-5.4                        {'in': 250, 'out': 1500, 'cache': 0}
gpt-5.4-mini                   {'in': 75, 'out': 450, 'cache': 0}
gpt-5.5                        {'in': 500, 'out': 3000, 'cache': 0}
gpt-5.6-luna                   {'in': 20, 'out': 120, 'cache': 0}
gpt-5.6-sol                    {'in': 200, 'out': 1000, 'cache': 0}
gpt-5.6-terra                  {'in': 200, 'out': 1200, 'cache': 0}
grok-4.5                       {'in': 200, 'out': 600, 'cache': 0}
oswe-vscode-modelD             {'in': 75, 'out': 450, 'cache': 0}
text-embedding-3-small         {'in': 0, 'out': 0, 'cache': 0}
text-embedding-ada-002         {'in': 0, 'out': 0, 'cache': 0}
trajectory-compaction          {'in': 0, 'out': 0, 'cache': 0}```

## aug-report-corrected.txt (August 2026 repo×model report with corrected pricing)
```
August 2026-08 — estimated credits (1 cr = $0.01); range = 98%-cached .. all-fresh

repo                             model                          req      promptTok     outTok    cr best     cr worst
customer-service-agent-platform  claude-fable-5                 753  1,709,858,356  3,455,840  261,788.9  1,727,137.6
yamlgraph                        claude-fable-5                 256    674,601,965  1,827,568  105,605.9    683,739.8
yamlgraph-hva-bulletin           claude-fable-5                  24     85,232,842    140,118   12,888.9     85,933.4
yamlgraph                        claude-sonnet-5                 29    119,229,251    352,147    3,762.1     24,198.0
yamlgraph-hva-bulletin           gpt-5.6-sol                     36     55,427,729    171,190    1,756.4     11,256.7
customer-service-agent-platform  gpt-5.6-sol                     50     50,110,784    200,677    1,633.8     10,222.8
yamlgraph                        gpt-5.6-sol                     22     47,457,499    150,807    1,508.1      9,642.3
customer-service-agent-platform  claude-sonnet-5                  8     42,969,656     87,193    1,316.1      8,681.1
yamlgraph                        claude-opus-5                   15     13,881,149     88,390    1,213.5      7,161.5
shared-enterprise-architecture   claude-fable-5                   7      2,005,804     67,316      623.4      2,342.4
customer-service-agent-platform  gpt-5.5                         12      7,667,591     32,644      550.3      3,931.7
kertomus-yamlgraph               claude-opus-4.6                  1         66,396        714        6.5         35.0

Per-repo totals:
customer-service-agent-platform    823 req   265,289.2 ..  1,749,973.2 cr   ($2,653 .. $17,500)
yamlgraph                          322 req   112,089.6 ..    724,741.7 cr   ($1,121 .. $7,247)
yamlgraph-hva-bulletin              60 req    14,645.3 ..     97,190.2 cr   ($146 .. $972)
shared-enterprise-architecture       7 req       623.4 ..      2,342.4 cr   ($6 .. $23)
kertomus-yamlgraph                   1 req         6.5 ..         35.0 cr   ($0 .. $0)

TOTAL: 1213 req, 392,654.1 .. 2,574,282.4 cr  ($3,927 .. $25,743)
```

## External anchor

Actual August 2026 invoice: $7,500 across two devices (~50% each).
Corrected best-bound this device: $3,927 → ≈$7.9K total, within ~5%.
Old (bugged) best-bound this device: $796 — ~10% of actual.

**Prior art:** dispositioned in FR-900 body — evidence artifact only.
