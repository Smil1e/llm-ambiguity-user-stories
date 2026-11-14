"""Post-hoc sensitivity analyses reported in Appendix A (no API calls).

Table A1  The key measures recomputed without the flawed quantifier variants:
          (a) the plural heuristic of prepare.py placed the quantifier before a singular noun
              (detected with the spaCy part-of-speech tagger), and
          (b) the quantifier directly follows "all" in the injected text ("all a good chunk of the").
Table A2  Localized detection under the planned evidence-matching rule and three stricter rules:
          full injected phrase as whole words; without the trailing "of the";
          without "of the" and the leading article.

Usage: python sensitivity.py            (reads data/stories_full.csv and results/full/raw_*.jsonl)
Output: results/full/sensitivity.md
"""
import csv
import glob
import json
import os
import re
import statistics
from collections import defaultdict

import config
from evaluate import has_term, metrics_for_run
from prepare import STORY_RE, plural_the_hits


def flawed_quantifier_bases(rows):
    import spacy
    nlp = spacy.load("en_core_web_sm")
    bad = {}
    for r in rows:
        if r["injected_type"] == "none":
            m = STORY_RE.match(r["text"])
            idx = m.start("want") + plural_the_hits(m.group("want"))[0]
            the = [t for t in nlp(r["text"]) if t.idx == idx]
            if not the or the[0].head.tag_ not in ("NNS", "NNPS"):
                bad[r["base_id"]] = "quantifier before a singular noun"
    for r in rows:
        if r["injected_type"] == "vague_quantifier" and re.search(r"\ball " + re.escape(r["term"]), r["text"], re.I):
            bad[r["base_id"]] = 'quantifier after "all"'
    return bad


def load_runs(res_dir, ids):
    out = {}
    for path in sorted(glob.glob(os.path.join(res_dir, "raw_*.jsonl"))):
        runs, name = defaultdict(dict), None
        for line in open(path, encoding="utf-8"):
            x = json.loads(line)
            if x["id"] in ids:
                runs[x["run"]][x["id"]] = {"labels": x["labels"], "evidence": x.get("evidence") or [],
                                           "status": x.get("status") or ("ok" if x.get("parse_ok") else "invalid_json")}
                name = f"{x['model']} ({x['model_name']}) / {x['strategy']}"
        out[name] = {k: v for k, v in runs.items() if len(v) == len(ids)}
    return out


def words_rx(p):
    return re.compile(r"(?<![\w-])" + re.escape(p) + r"(?![\w-])", re.I)


RULES = {
    "Planned rule (reported)": lambda t, ev: has_term(t, ev),
    "Full injected phrase, whole words": lambda t, ev: any(words_rx(t).search(e) for e in ev),
    'Without trailing "of the"': lambda t, ev: any(words_rx(re.sub(r"\s+of the$", "", t)).search(e) for e in ev),
    'Without "of the" and article': lambda t, ev: any(
        words_rx(re.sub(r"^(a|an)\s+", "", re.sub(r"\s+of the$", "", t))).search(e) for e in ev),
}


def main():
    rows = list(csv.DictReader(open(os.path.join(config.DATA_DIR, "stories_full.csv"), encoding="utf-8")))
    res_dir = os.path.join(config.RESULTS_DIR, "full")
    bad = flawed_quantifier_bases(rows)
    kept = [r for r in rows if not (r["injected_type"] == "vague_quantifier" and r["base_id"] in bad)]
    lines = ["# Sensitivity analyses (Appendix A)\n",
             f"Flawed quantifier variants excluded ({len(bad)}): " +
             ", ".join(f"{b} ({why})" for b, why in sorted(bad.items())) + "\n",
             "## Table A1. Key results without the flawed quantifier variants\n",
             "| Condition | Localized, all | Localized, out-of-dictionary | Quantifier localized | Quantifier F1 |",
             "|---|---|---|---|---|"]
    for name, runs in load_runs(res_dir, {r["id"] for r in kept}).items():
        ms = [metrics_for_run(kept, rec) for rec in runs.values()]
        avg = lambda k: statistics.mean(m[k] for m in ms)
        lines.append(f"| {name} | {100 * avg('locdet_ALL_all'):.1f}% | {100 * avg('locdet_ALL_out'):.1f}% | "
                     f"{100 * avg('locdet_vague_quantifier_all'):.1f}% | {avg('agree_vague_quantifier_F1'):.2f} |")
    inj = [r for r in rows if r["injected_type"] != "none"]
    lines += ["\n## Table A2. Localized detection under different evidence-matching rules\n",
              "| Condition | " + " | ".join(RULES) + " | Evidence items copying >= 80% of the story |",
              "|---|" + "---|" * (len(RULES) + 1)]
    for name, runs in load_runs(res_dir, {r["id"] for r in rows}).items():
        cells = []
        for rule in RULES.values():
            vals = [sum(rec[r["id"]]["status"] == "ok" and rec[r["id"]]["labels"][r["injected_type"]] == "Yes"
                        and rule(r["term"], rec[r["id"]]["evidence"]) for r in inj) / len(inj) for rec in runs.values()]
            cells.append(f"{100 * statistics.mean(vals):.1f}%")
        by_id = {r["id"]: r for r in rows}
        copies = sum(len(e.split()) >= 0.8 * len(by_id[i]["text"].split())
                     for rec in runs.values() for i, x in rec.items() for e in x["evidence"])
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {copies} |")
    longest = 0
    for name, runs in load_runs(res_dir, {r["id"] for r in rows}).items():
        for rec in runs.values():
            for r in inj:
                for e in rec[r["id"]]["evidence"]:
                    if has_term(r["term"], [e]):
                        longest = max(longest, len(re.findall(r"[\w'-]+", e)))
    lines.append(f"\nLongest evidence item matching an injected term: {longest} words")
    text = "\n".join(lines) + "\n"
    open(os.path.join(res_dir, "sensitivity.md"), "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
