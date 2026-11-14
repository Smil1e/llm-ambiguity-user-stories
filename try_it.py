"""Hands-on test: inject one ambiguity into your own story, then see who detects it.

Usage (from the project folder):
    python try_it.py                      # dictionary baseline only (no API keys needed)
    python try_it.py --models claude openai   # also ask the LLMs (needs API keys in env vars)
    python try_it.py --story "As a nurse, I want to print the shift reports, so that I can hand them over."
Keys are read only from the environment: ANTHROPIC_API_KEY, OPENAI_API_KEY.
"""
import argparse, os, sys

import config, detectors, prepare, prompts
from evaluate import has_term

DEFAULT = "As a librarian, I want to export the loan records, so that I can share them with the finance office."
TESTS = [  # (type, term, in the dictionary?)
    ("vague_qualifier", "quickly", True),
    ("vague_qualifier", "snappily", False),
    ("vague_quantifier", "a handful of the", False),
    ("escape_clause", "if possible", True),
    ("escape_clause", "where it makes sense", False),
]

ap = argparse.ArgumentParser()
ap.add_argument("--story", default=DEFAULT)
ap.add_argument("--models", nargs="*", default=[], choices=["claude", "openai"])
a = ap.parse_args()

m = prepare.STORY_RE.match(a.story)
if not m:
    sys.exit('The story must follow: "As a <role>, I want to <action>, so that <benefit>."')
if "claude" in a.models: os.environ.setdefault("CLAUDE_MODEL", "claude-haiku-5-5")
if "openai" in a.models: os.environ.setdefault("OPENAI_MODEL", "gpt-6-luna")
import importlib; importlib.reload(config); importlib.reload(detectors)

print("ORIGINAL:", a.story)
def ask(name, story):
    raw = detectors.rule_based(story) if name == "dictionary" else \
        detectors.LLM_CALLERS[name](prompts.SYSTEM_PROMPT, prompts.build_messages(story, "zero"))
    labels, evidence, status = detectors.parse_output(raw)
    return {"evidence": evidence or [], **(labels or {})}

print("  dictionary flags:", ask("dictionary", a.story)["evidence"] or "nothing", "\n")
score = {k: [0, 0] for k in ["dictionary"] + a.models}
for typ, term, indict in TESTS:
    try:
        new, seg = prepare.inject(a.story, m, typ, term)
    except Exception as e:
        print(f"[{typ}: '{term}'] cannot inject into this story ({e})\n"); continue
    print(f"[{typ}: '{term}' | {'IN' if indict else 'OUT of'} the dictionary]\n  {new}")
    results = {name: ask(name, new) for name in ["dictionary"] + a.models}
    for name, r in results.items():
        ok = r.get(typ) == "Yes" and has_term(term, r.get("evidence", []))
        score[name][0] += ok; score[name][1] += 1
        print(f"    {name:<10} {'FOUND' if ok else 'missed':<7} type={r.get(typ)}  evidence={r.get('evidence')}")
    print()
print("SUMMARY (localized detection):", {k: f"{v[0]}/{v[1]}" for k, v in score.items()})
