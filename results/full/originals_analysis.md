# Supplementary analysis of flags on original stories

## Table F. Flagged original stories whose evidence contains an extended indicator

| Condition | Flagged (story-runs) | With extended indicator | superlative | comparative | negative | universal_quantifier |
|---|---|---|---|---|---|---|
| claude (claude-haiku-5-5) / few | 19 | 8 (42%) | 1 | 3 | 2 | 2 |
| claude (claude-haiku-5-5) / zero | 31 | 10 (32%) | 2 | 4 | 2 | 2 |
| openai (gpt-6-luna) / few | 29 | 10 (34%) | 1 | 4 | 2 | 3 |
| openai (gpt-6-luna) / zero | 65 | 17 (26%) | 2 | 4 | 3 | 8 |

## Table G. Flag rate on originals with and without an extended indicator

14 of 50 original stories contain at least one extended indicator (superlative: 1, comparative: 2, negative: 4, universal_quantifier: 7).

| Condition | Flag rate, with indicator | Flag rate, without indicator |
|---|---|---|
| claude (claude-haiku-5-5) / few | 29% | 15% |
| claude (claude-haiku-5-5) / zero | 50% | 24% |
| openai (gpt-6-luna) / few | 43% | 24% |
| openai (gpt-6-luna) / zero | 75% | 61% |

## Flagged original stories (both runs)

- claude: 18 distinct original stories flagged at least once
- openai: 39 distinct original stories flagged at least once
- flagged by both models: 17
- flagged in all 4 LLM conditions: 8 (B16_orig, B18_orig, B22_orig, B24_orig, B25_orig, B42_orig, B43_orig, B45_orig)

## Fisher's exact test (stories flagged in at least one run)

| Condition | With indicator flagged | Without indicator flagged | p |
|---|---|---|---|
| claude (claude-haiku-5-5) / few | 5/14 | 7/36 | 0.28 |
| claude (claude-haiku-5-5) / zero | 7/14 | 10/36 | 0.19 |
| openai (gpt-6-luna) / few | 7/14 | 10/36 | 0.19 |
| openai (gpt-6-luna) / zero | 12/14 | 27/36 | 0.71 |
