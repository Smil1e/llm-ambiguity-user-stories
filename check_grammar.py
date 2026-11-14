"""Automatic check that injection did not add grammar errors (replaces human validation).

For every injected story, it counts grammar/spelling issues reported by LanguageTool and
compares them with the issues in its original story. An injection "adds errors" if the
injected story has more issues than its original.

Requires Java (available in Google Colab) and: pip install language-tool-python
Usage : python check_grammar.py --set full
Output: data/grammar_check_<set>.csv and a short summary printed on screen.
"""
import argparse
import csv
import os
from collections import Counter

import config

# Rules that would fire on the injected terms by design (style, not grammar).
IGNORED_CATEGORIES = {"STYLE", "REDUNDANCY", "TYPOGRAPHY", "CASING"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["pilot", "full"], default="full")
    args = ap.parse_args()

    import language_tool_python
    tool = language_tool_python.LanguageTool("en-US")

    with open(os.path.join(config.DATA_DIR, f"stories_{args.set}.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    def issues(text):
        return [m for m in tool.check(text) if (m.category or "").upper() not in IGNORED_CATEGORIES]

    orig_n = {r["base_id"]: len(issues(r["text"])) for r in rows if r["injected_type"] == "none"}
    out, added = [], Counter()
    for r in rows:
        if r["injected_type"] == "none":
            continue
        found = issues(r["text"])
        extra = len(found) - orig_n[r["base_id"]]
        if extra > 0:
            added[r["injected_type"]] += 1
        out.append({"id": r["id"], "injected_type": r["injected_type"], "position": r["position"],
                    "term": r["term"], "issues_original": orig_n[r["base_id"]],
                    "issues_injected": len(found), "added_errors": max(extra, 0),
                    "messages": " | ".join(f"{getattr(m, 'rule_id', None) or getattr(m, 'ruleId', '')}: {m.message}" for m in found),
                    "text": r["text"]})
    tool.close()

    path = os.path.join(config.DATA_DIR, f"grammar_check_{args.set}.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    total = Counter(r["injected_type"] for r in out)
    print(f"Injected stories checked: {len(out)}")
    for t in config.TYPES:
        print(f"  {t}: {added[t]}/{total[t]} with added grammar issues")
    print(f"Overall clean injections: {100 * (1 - sum(added.values()) / len(out)):.1f}%")
    print(f"Details: {path}  (fix or report every story listed with added_errors > 0)")


if __name__ == "__main__":
    main()
