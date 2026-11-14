# Detecting Injected Lexical Ambiguity in User Stories with LLMs

Replication package for the MSCS811 project report (Taibah University, 2026).

**Research question.** To what extent do LLMs detect and localize injected lexical ambiguity
indicators in Agile user stories, inside and outside the coverage of a specified dictionary?

**Design in brief.** 50 real user stories from the Dalpiaz data set were filtered and given one
injected indicator per type (vague qualifier, vague quantifier, escape clause) with fixed,
reversible rules, giving 200 texts (50 originals + 150 variants). Half of the injected terms are
in the dictionary of a rule-based baseline and half are not. Claude Haiku 5.5 and GPT-6 Luna were
run zero-shot and few-shot, twice per condition (1,600 responses), and had to quote the phrase
behind each detection.

## Main results (from `results/full/`)

| Condition | Localized detection (all) | Outside the dictionary | Flag rate on originals |
|---|---|---|---|
| Dictionary baseline | 50.0% | 0% | 0% |
| Claude Haiku, zero-shot | 99.3% | 98.7% | 31% |
| Claude Haiku, few-shot | 97.3% | 94.7% | 19% |
| GPT-6 Luna, zero-shot | 98.7% | 97.3% | 65% |
| GPT-6 Luna, few-shot | 99.7% | 99.3% | 29% |

The labels are synthetic: they record which indicator was injected, not a human judgement that a
story is ambiguous. The results show detection beyond this particular dictionary on the tested
set; they do not show reliable judgement of real ambiguity in general.

## Repository structure

| Path | Content |
|---|---|
| `config.py` | Settings (seed, number of stories and runs, model names) |
| `wordlists.py` | Baseline dictionary, injection terms (in / out of dictionary), few-shot terms |
| `prepare.py` | Filtering, injection rules, automated validity checks, leakage check |
| `prompts.py` | System prompt and few-shot message builder |
| `detectors.py` | Dictionary baseline, Claude and OpenAI callers, output parsing |
| `run_experiment.py` | Sends every text to every detector and saves raw replies (resumable) |
| `evaluate.py` | All metrics: localized detection, localization precision, P / R / F1, validity, confusion |
| `check_grammar.py` | LanguageTool check that injection added no grammar issues |
| `analyze_originals.py` | Post-hoc exploratory analysis of flags on original stories (Table 7) |
| `sensitivity.py` | Sensitivity analyses of Appendix A (flawed variants, evidence-matching rules) |
| `make_figures.py` | Figure 2 (localized detection inside and outside the dictionary) |
| `data/` | `base_stories.csv` (50 originals) and `stories_full.csv` (200 evaluated texts) |
| `results/full/` | Raw model replies (`raw_*.jsonl`) and all computed tables |
| `notebooks/run_in_colab.ipynb` | Re-evaluation and full rerun in Google Colab |

## Where each result of the report comes from

| Report | Produced by | Output file |
|---|---|---|
| Section 5.1 (validity, ungrounded evidence) | `evaluate.py`, `check_grammar.py` | `results/full/summary.md` (Table D), `data/grammar_check_full.csv` |
| Table 4 (overall results) | `evaluate.py` | `summary.md` (Table A) |
| Figure 2 (inside / outside the dictionary) | `evaluate.py` + `make_figures.py` | `fig2_in_out.png` |
| Table 5 (per type) | `evaluate.py` | `summary.md` (Table B) |
| Table 6 (P / R / F1) | `evaluate.py` | `summary.md` (Table C) |
| Cross-type flags (Section 5.4) | `evaluate.py` | `summary.md` (Table E), `confusion.csv` |
| Section 5.5 and Table 7 (flags on originals, Fisher test) | `analyze_originals.py` | `originals_analysis.md` |
| Appendix A (Tables A1, A2) | `sensitivity.py` | `sensitivity.md` |

## How to reproduce

Re-evaluate the saved outputs (no API key needed):

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python evaluate.py --set full          # Tables 4-6, results/full/summary.md
python analyze_originals.py --flags results/full/flagged_originals.csv --stories data/base_stories.csv --out results/full
python sensitivity.py                  # Appendix A, results/full/sensitivity.md
python make_figures.py                 # Figure 2
```

Rerun the whole experiment (requires the Dalpiaz data set and API keys set as environment
variables `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`; never commit keys):

```bash
export CLAUDE_MODEL=claude-haiku-5-5 OPENAI_MODEL=gpt-6-luna
python prepare.py --data path/to/dalpiaz --pool-all --fewshot-project g21-badcamp
python check_grammar.py --set full
python run_experiment.py --set full --models rule claude openai --strategies zero few --runs 2
python evaluate.py --set full
```

`prepare.py` is deterministic (seed 42) and also writes the few-shot examples and a filter report.
The models were run on 13 November 2026; model outputs can differ between requests and versions.

## Known limitation

The plural heuristic in `prepare.py` produced 10 quantifier variants before a singular noun, and
4 more variants placed the quantifier after "all" in the original. The code is left unchanged so
that the reported data set is reproduced exactly; `sensitivity.py` identifies these 14 variants and
shows that excluding them does not change the main conclusions.

## Data and licence

User stories: F. Dalpiaz, *Requirements data sets (user stories)*, Mendeley Data, v2,
doi:10.17632/7zbk8zsd8y, licensed CC BY 4.0. The derived texts in `data/` keep that licence.
Code: MIT licence (see `LICENSE`).
