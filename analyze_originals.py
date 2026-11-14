"""Supplementary analysis: do LLM flags on the original stories point to recognised
ambiguity indicators outside the three studied types?

The extended categories are closed word classes taken from ISO/IEC/IEEE 29148 (superlatives,
comparative phrases, negative statements) and from Berry et al. (universal
quantifiers). They are defined by fixed patterns, not by looking at the flags, and they do not
overlap with the BASELINE dictionary. Vague pronouns are left out here: they are a
referential problem, and the dummy "it" in "it is possible" would be counted wrongly. Matching is automatic, so the share is a lower bound:
subjective terms outside these closed classes (e.g. "necessary", "full details") are not counted.

Usage:
  python analyze_originals.py --flags results/full/flagged_originals.csv \
                              [--stories data/base_stories.csv] [--out results/full]
"""
import argparse, csv, os, re
from collections import defaultdict

EST_STOP = {"rest", "best", "test", "tests", "request", "requests", "interest", "interests",
            "forest", "honest", "digest", "harvest", "suggest", "manifest", "invest", "contest",
            "protest", "guest", "west", "nest", "quest", "chest", "pest", "latest", "modest",
            "arrest", "attest", "detest", "ingest", "invest", "lest", "vest", "zest", "crest"}
ER_STOP = {"user", "users", "manager", "member", "members", "researcher", "researchers",
           "order", "folder", "number", "other", "others", "under", "over", "after", "never",
           "either", "whether", "rather", "together", "server", "provider", "owner", "officer",
           "filter", "register", "paper", "player", "data", "layer", "customer", "partner",
           "reviewer", "worker", "helper", "teacher", "developer", "power", "water", "later",
           "offer", "answer", "cover", "enter", "transfer", "header", "footer", "cluster",
           "computer", "parameter", "letter", "matter", "chapter", "corner", "border", "trigger",
           "member's", "visitor", "per"}

CATEGORIES = {
    # ISO/IEC/IEEE 29148: superlatives
    "superlative": lambda w, ws, i: (w in {"most", "least", "best", "worst"}
                                      or (len(w) > 4 and w.endswith("est") and w not in EST_STOP)),
    # ISO/IEC/IEEE 29148: comparative phrases
    "comparative": lambda w, ws, i: (w in {"more", "less", "better", "worse", "fewer", "greater"}
                                      or (i + 1 < len(ws) and ws[i + 1] == "than")
                                      or (len(w) > 4 and w.endswith("er") and w not in ER_STOP
                                          and w[:-2] in {"fast", "slow", "high", "low", "easi",
                                                          "simpl", "quick", "larg", "small",
                                                          "short", "long", "clos", "clear",
                                                          "great", "smart", "strong"})),
    # ISO/IEC/IEEE 29148: negative statements
    "negative": lambda w, ws, i: w in {"not", "no", "never", "without", "cannot", "don't",
                                       "doesn't", "isn't", "aren't", "won't", "can't", "nor"},
    # Berry et al.: universal quantifiers (scope ambiguity)
    "universal_quantifier": lambda w, ws, i: w in {"all", "every", "each", "any", "always"},
}


def tokens(s):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", s.lower())


def categories_in(phrase):
    ws = tokens(phrase)
    return {c for c, f in CATEGORIES.items() for i, w in enumerate(ws) if f(w, ws, i)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flags", required=True)
    ap.add_argument("--stories")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.flags, encoding="utf-8-sig")))

    # evidence level: one row = one (condition, run, original story) with >= 1 flag
    per_cond = defaultdict(lambda: {"n": 0, "hit": 0, "cats": defaultdict(int)})
    detail = []
    for r in rows:
        phrases = [p.strip() for p in r["evidence"].split("|") if p.strip()]
        cats = set().union(*[categories_in(p) for p in phrases]) if phrases else set()
        d = per_cond[r["condition"]]
        d["n"] += 1
        d["hit"] += bool(cats)
        for c in cats:
            d["cats"][c] += 1
        detail.append({**r, "extended_categories": ";".join(sorted(cats))})

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "flagged_originals_categories.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0].keys()))
        w.writeheader(); w.writerows(detail)

    lines = ["# Supplementary analysis of flags on original stories", "",
             "## Table F. Flagged original stories whose evidence contains an extended indicator",
             "", "| Condition | Flagged (story-runs) | With extended indicator | "
             + " | ".join(CATEGORIES) + " |", "|---|---|---|" + "---|" * len(CATEGORIES)]
    for cond in sorted(per_cond):
        d = per_cond[cond]
        lines.append(f"| {cond} | {d['n']} | {d['hit']} ({d['hit'] / d['n']:.0%}) | "
                     + " | ".join(str(d["cats"][c]) for c in CATEGORIES) + " |")

    # story level (needs all base stories)
    if a.stories:
        stories = list(csv.DictReader(open(a.stories, encoding="utf-8-sig")))
        text_col = "text" if "text" in stories[0] else list(stories[0].keys())[1]
        id_col = "id" if "id" in stories[0] else list(stories[0].keys())[0]
        has = {}
        for s in stories:
            sid = s[id_col] if s[id_col].endswith("_orig") else s[id_col] + "_orig"
            has[sid] = categories_in(s[text_col])
        n_with = sum(1 for v in has.values() if v)
        lines += ["", f"## Table G. Flag rate on originals with and without an extended indicator",
                  "", f"{n_with} of {len(has)} original stories contain at least one extended "
                  "indicator (" + ", ".join(f"{c}: {sum(1 for v in has.values() if c in v)}"
                                          for c in CATEGORIES) + ").", "",
                  "| Condition | Flag rate, with indicator | Flag rate, without indicator |",
                  "|---|---|---|"]
        runs = sorted({r["run"] for r in rows})
        for cond in sorted(per_cond):
            flagged = {(r["run"], r["id"]) for r in rows if r["condition"] == cond}
            def rate(group):
                ids = [k for k, v in has.items() if bool(v) == group]
                if not ids:
                    return float("nan")
                return sum((run, i) in flagged for run in runs for i in ids) / (len(ids) * len(runs))
            lines.append(f"| {cond} | {rate(True):.0%} | {rate(False):.0%} |")

    # flag counts across conditions (Section 5.5)
    by_model = defaultdict(set)
    by_cond = defaultdict(set)
    for r in rows:
        by_model[r["condition"].split(" ")[0]].add(r["id"])
        by_cond[r["condition"]].add(r["id"])
    models = sorted(by_model)
    lines += ["", "## Flagged original stories (both runs)", ""]
    for m in models:
        lines.append(f"- {m}: {len(by_model[m])} distinct original stories flagged at least once")
    if len(models) == 2:
        lines.append(f"- flagged by both models: {len(by_model[models[0]] & by_model[models[1]])}")
    llm_conds = [c for c in by_cond if not c.startswith("rule")]
    if llm_conds:
        allc = set.intersection(*[by_cond[c] for c in llm_conds])
        lines.append(f"- flagged in all {len(llm_conds)} LLM conditions: {len(allc)} ({', '.join(sorted(allc))})")

    # Fisher's exact test: stories flagged in at least one run, with vs without an extended indicator
    if a.stories:
        from scipy.stats import fisher_exact
        lines += ["", "## Fisher's exact test (stories flagged in at least one run)", "",
                  "| Condition | With indicator flagged | Without indicator flagged | p |", "|---|---|---|---|"]
        n_with = sum(1 for v in has.values() if v)
        n_without = len(has) - n_with
        for cond in sorted(per_cond):
            f = by_cond[cond]
            a1 = sum(1 for k, v in has.items() if v and k in f)
            c1 = sum(1 for k, v in has.items() if not v and k in f)
            p = fisher_exact([[a1, n_with - a1], [c1, n_without - c1]])[1]
            lines.append(f"| {cond} | {a1}/{n_with} | {c1}/{n_without} | {p:.2f} |")

    out = "\n".join(lines) + "\n"
    open(os.path.join(a.out, "originals_analysis.md"), "w", encoding="utf-8").write(out)
    print(out)


if __name__ == "__main__":
    main()
