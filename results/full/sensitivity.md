# Sensitivity analyses (Appendix A)

Flawed quantifier variants excluded (14): B09 (quantifier before a singular noun), B16 (quantifier before a singular noun), B18 (quantifier before a singular noun), B19 (quantifier before a singular noun), B21 (quantifier before a singular noun), B25 (quantifier before a singular noun), B26 (quantifier before a singular noun), B30 (quantifier before a singular noun), B31 (quantifier after "all"), B32 (quantifier before a singular noun), B34 (quantifier after "all"), B39 (quantifier after "all"), B46 (quantifier before a singular noun), B49 (quantifier after "all")

## Table A1. Key results without the flawed quantifier variants

| Condition | Localized, all | Localized, out-of-dictionary | Quantifier localized | Quantifier F1 |
|---|---|---|---|---|
| claude (claude-haiku-5-5) / few | 97.1% | 94.1% | 100.0% | 0.94 |
| claude (claude-haiku-5-5) / zero | 99.3% | 98.5% | 100.0% | 0.86 |
| openai (gpt-6-luna) / few | 99.6% | 99.3% | 100.0% | 0.92 |
| openai (gpt-6-luna) / zero | 98.5% | 97.1% | 100.0% | 0.63 |
| rule (rule-based) / none | 50.0% | 0.0% | 50.0% | 0.67 |

## Table A2. Localized detection under different evidence-matching rules

| Condition | Planned rule (reported) | Full injected phrase, whole words | Without trailing "of the" | Without "of the" and article | Evidence items copying >= 80% of the story |
|---|---|---|---|---|---|
| claude (claude-haiku-5-5) / few | 97.3% | 78.7% | 95.0% | 96.7% | 0 |
| claude (claude-haiku-5-5) / zero | 99.3% | 81.3% | 97.7% | 99.3% | 0 |
| openai (gpt-6-luna) / few | 99.7% | 81.3% | 95.3% | 97.7% | 0 |
| openai (gpt-6-luna) / zero | 98.7% | 76.7% | 93.7% | 98.3% | 0 |
| rule (rule-based) / none | 50.0% | 33.3% | 50.0% | 50.0% | 0 |

Longest evidence item matching an injected term: 12 words
