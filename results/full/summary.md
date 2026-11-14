# Results: full set (200 stories)

Labels are synthetic (injected indicators). Detection rates use ALL injected variants as the denominator; invalid replies count as not detected.

## Table A. Localized detection of injected indicators (primary)

| Condition | Valid outputs | Localized detection (all) | In-dictionary | Out-of-dictionary | Detection (all) | Localization precision | Flag rate on originals |
|---|---|---|---|---|---|---|---|
| claude (claude-haiku-5-5) / few | 1.00 ± 0.00 | 0.97 ± 0.01 | 1.00 ± 0.00 | 0.95 ± 0.02 | 0.97 ± 0.01 | 1.00 ± 0.00 | 0.19 ± 0.01 |
| claude (claude-haiku-5-5) / zero | 1.00 ± 0.00 | 0.99 ± 0.01 | 1.00 ± 0.00 | 0.99 ± 0.02 | 0.99 ± 0.01 | 1.00 ± 0.00 | 0.31 ± 0.01 |
| openai (gpt-6-luna) / few | 1.00 ± 0.00 | 1.00 ± 0.01 | 1.00 ± 0.00 | 0.99 ± 0.01 | 1.00 ± 0.01 | 1.00 ± 0.00 | 0.29 ± 0.04 |
| openai (gpt-6-luna) / zero | 1.00 ± 0.00 | 0.99 ± 0.00 | 1.00 ± 0.00 | 0.97 ± 0.00 | 0.99 ± 0.00 | 1.00 ± 0.00 | 0.65 ± 0.07 |
| rule (rule-based) / none | 1.00 ± 0.00 | 0.50 ± 0.00 | 1.00 ± 0.00 | 0.00 ± 0.00 | 0.50 ± 0.00 | 1.00 ± 0.00 | 0.00 ± 0.00 |

## Table B. Localized detection per type (all / in-dictionary / out-of-dictionary)

| Condition | vague_qualifier | vague_quantifier | escape_clause |
|---|---|---|---|
| claude (claude-haiku-5-5) / few | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.92 / 1.00 / 0.84 |
| claude (claude-haiku-5-5) / zero | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.98 / 1.00 / 0.96 |
| openai (gpt-6-luna) / few | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.99 / 1.00 / 0.98 |
| openai (gpt-6-luna) / zero | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.96 / 1.00 / 0.92 |
| rule (rule-based) / none | 0.50 / 1.00 / 0.00 | 0.50 / 1.00 / 0.00 | 0.50 / 1.00 / 0.00 |

## Table C. Agreement with synthetic labels per type, over all valid outputs (F1; P / R)

| Condition | vague_qualifier | vague_quantifier | escape_clause |
|---|---|---|---|
| claude (claude-haiku-5-5) / few | 0.80 (0.66 / 1.00) | 0.96 (0.92 / 1.00) | 0.96 (1.00 / 0.92) |
| claude (claude-haiku-5-5) / zero | 0.73 (0.57 / 1.00) | 0.89 (0.81 / 1.00) | 0.99 (1.00 / 0.98) |
| openai (gpt-6-luna) / few | 0.79 (0.65 / 1.00) | 0.94 (0.89 / 1.00) | 0.98 (0.97 / 0.99) |
| openai (gpt-6-luna) / zero | 0.68 (0.52 / 1.00) | 0.70 (0.54 / 1.00) | 0.90 (0.85 / 0.96) |
| rule (rule-based) / none | 0.67 (1.00 / 0.50) | 0.67 (1.00 / 0.50) | 0.67 (1.00 / 0.50) |

## Table D. Output validity

| Condition | Valid | Invalid JSON | Missing field | Bad value | Retries used | Ungrounded evidence |
|---|---|---|---|---|---|---|
| claude (claude-haiku-5-5) / few | 1.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0 | 0.00 ± 0.00 |
| claude (claude-haiku-5-5) / zero | 1.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0 | 0.00 ± 0.00 |
| openai (gpt-6-luna) / few | 1.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0 | 0.02 ± 0.01 |
| openai (gpt-6-luna) / zero | 1.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0 | 0.01 ± 0.00 |
| rule (rule-based) / none | 1.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0 | 0.00 ± 0.00 |

## Table E. Confusion among valid outputs: share flagged for each label

| Condition | Injected type | vague_qualifier | vague_quantifier | escape_clause |
|---|---|---|---|---|
| claude (claude-haiku-5-5) / few | none | 0.14 | 0.07 | 0.00 |
| claude (claude-haiku-5-5) / few | vague_qualifier | 1.00 | 0.00 | 0.00 |
| claude (claude-haiku-5-5) / few | vague_quantifier | 0.19 | 1.00 | 0.00 |
| claude (claude-haiku-5-5) / few | escape_clause | 0.18 | 0.02 | 0.92 |
| claude (claude-haiku-5-5) / zero | none | 0.22 | 0.11 | 0.00 |
| claude (claude-haiku-5-5) / zero | vague_qualifier | 1.00 | 0.08 | 0.00 |
| claude (claude-haiku-5-5) / zero | vague_quantifier | 0.23 | 1.00 | 0.00 |
| claude (claude-haiku-5-5) / zero | escape_clause | 0.29 | 0.05 | 0.98 |
| openai (gpt-6-luna) / few | none | 0.20 | 0.09 | 0.01 |
| openai (gpt-6-luna) / few | vague_qualifier | 1.00 | 0.02 | 0.02 |
| openai (gpt-6-luna) / few | vague_quantifier | 0.21 | 1.00 | 0.00 |
| openai (gpt-6-luna) / few | escape_clause | 0.12 | 0.02 | 0.99 |
| openai (gpt-6-luna) / zero | none | 0.33 | 0.52 | 0.07 |
| openai (gpt-6-luna) / zero | vague_qualifier | 1.00 | 0.19 | 0.03 |
| openai (gpt-6-luna) / zero | vague_quantifier | 0.31 | 1.00 | 0.07 |
| openai (gpt-6-luna) / zero | escape_clause | 0.29 | 0.13 | 0.96 |
| rule (rule-based) / none | none | 0.00 | 0.00 | 0.00 |
| rule (rule-based) / none | vague_qualifier | 0.50 | 0.00 | 0.00 |
| rule (rule-based) / none | vague_quantifier | 0.00 | 0.50 | 0.00 |
| rule (rule-based) / none | escape_clause | 0.00 | 0.00 | 0.50 |
