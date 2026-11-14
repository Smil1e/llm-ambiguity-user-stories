"""Step 3: compute the metrics from the saved replies.

What the metrics can and cannot claim (state this in the report):
- The labels are SYNTHETIC. They record which indicator was injected, not a human judgement
  that a story is or is not ambiguous. The original stories are only presumed clean.
- Therefore the PRIMARY metric needs no negatives:
    localized detection rate = injected variants for which the detector set the injected type
    to "Yes" AND reported evidence containing the injected term, divided by ALL injected
    variants of that group. Invalid replies count as not detected (strict).
- Secondary metrics:
    detection rate            the same without the evidence condition
    localization precision    among variants where the injected type was detected, the share
                              whose evidence contains the injected term
    flag rate on originals    share of VALID replies on original stories with any "Yes"
                              (descriptive; a flag may point to real ambiguity, see
                              flagged_originals.csv)
    synthetic-label agreement per type T, over ALL valid replies: positive = injected with T,
                              negative = everything else (originals AND variants injected with
                              other types). Reported as agreement with the synthetic labels,
                              not as accuracy of detecting real ambiguity.
    valid-output rate, failure categories, ungrounded evidence rate (evidence not in the story)
- Every metric is computed per run and reported as mean and standard deviation over runs.

Usage: python evaluate.py --set pilot
Writes results/<set>/metrics.csv, confusion.csv, flagged_originals.csv and summary.md
"""
import argparse
import csv
import glob
import json
import os
import statistics
from collections import Counter, defaultdict

import config

GROUPS = [("all", lambda r: True), ("in", lambda r: r["vocab"] == "in"), ("out", lambda r: r["vocab"] == "out")]


def prf(y_true, y_pred):
    tp = sum(t and p for t, p in zip(y_true, y_pred))
    fp = sum((not t) and p for t, p in zip(y_true, y_pred))
    fn = sum(t and (not p) for t, p in zip(y_true, y_pred))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1


def has_term(term, evidence):
    t = term.lower()
    return any(t in e.lower() or (len(e) > 3 and e.lower() in t) for e in evidence)


def ratio(a, b):
    return a / b if b else 0.0


def metrics_for_run(rows, rec):
    """rec: id -> {"labels": dict|None, "evidence": list, "status": str}"""
    out = {}
    valid = {i for i, x in rec.items() if x["status"] == "ok"}
    out["valid_rate"] = ratio(len(valid), len(rows))
    for s in ("invalid_json", "missing_field", "bad_value"):
        out[f"fail_{s}"] = ratio(sum(x["status"] == s for x in rec.values()), len(rows))

    injected = [r for r in rows if r["injected_type"] != "none"]

    def detected(r):
        return r["id"] in valid and rec[r["id"]]["labels"][r["injected_type"]] == "Yes"

    def localized(r):
        return detected(r) and has_term(r["term"], rec[r["id"]]["evidence"])

    for t in ["ALL"] + config.TYPES:
        for g, sel in GROUPS:
            sub = [r for r in injected if sel(r) and (t == "ALL" or r["injected_type"] == t)]
            det = [r for r in sub if detected(r)]
            out[f"locdet_{t}_{g}"] = ratio(sum(localized(r) for r in sub), len(sub))
            out[f"det_{t}_{g}"] = ratio(len(det), len(sub))
            out[f"locprec_{t}_{g}"] = ratio(sum(localized(r) for r in det), len(det))

    orig_valid = [r for r in rows if r["injected_type"] == "none" and r["id"] in valid]
    out["flag_rate_on_originals"] = ratio(
        sum(any(v == "Yes" for v in rec[r["id"]]["labels"].values()) for r in orig_valid), len(orig_valid))

    vrows = [r for r in rows if r["id"] in valid]
    for t in config.TYPES:
        y = [r["injected_type"] == t for r in vrows]
        p = [rec[r["id"]]["labels"][t] == "Yes" for r in vrows]
        out[f"agree_{t}_P"], out[f"agree_{t}_R"], out[f"agree_{t}_F1"] = prf(y, p)

    reporting = [r for r in vrows if any(v == "Yes" for v in rec[r["id"]]["labels"].values())]
    ungrounded = [r for r in reporting
                  if any(e.lower() not in r["text"].lower() for e in rec[r["id"]]["evidence"])
                  or not rec[r["id"]]["evidence"]]
    out["ungrounded_evidence_rate"] = ratio(len(ungrounded), len(reporting))
    return out


def confusion_for_run(rows, rec):
    """Among VALID replies: share of stories of each injected type flagged for each label."""
    table = {}
    for src in ["none"] + config.TYPES:
        sub = [r for r in rows if r["injected_type"] == src and rec[r["id"]]["status"] == "ok"]
        table[src] = {t: ratio(sum(rec[r["id"]]["labels"][t] == "Yes" for r in sub), len(sub)) for t in config.TYPES}
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["pilot", "full"], default="pilot")
    args = ap.parse_args()

    with open(os.path.join(config.DATA_DIR, f"stories_{args.set}.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = {r["id"] for r in rows}
    by_id = {r["id"]: r for r in rows}
    res_dir = os.path.join(config.RESULTS_DIR, args.set)

    per_cond = {}
    for path in sorted(glob.glob(os.path.join(res_dir, "raw_*.jsonl"))):
        runs, name = defaultdict(dict), None
        with open(path, encoding="utf-8") as f:
            for line in f:
                x = json.loads(line)
                if x["id"] in ids:
                    status = x.get("status") or ("ok" if x.get("parse_ok") else "invalid_json")
                    runs[x["run"]][x["id"]] = {"labels": x["labels"], "evidence": x.get("evidence") or [],
                                               "status": status, "attempts": x.get("attempts", 1)}
                    name = f"{x['model']} ({x['model_name']}) / {x['strategy']}"
        complete = {k: v for k, v in runs.items() if len(v) == len(ids)}
        if len(complete) < len(runs):
            print(f"WARNING {os.path.basename(path)}: {len(runs) - len(complete)} incomplete run(s) skipped")
        if complete:
            per_cond[name] = complete
    if not per_cond:
        raise SystemExit("No complete runs found. Run run_experiment.py first.")

    metric_rows, conf_rows, flagged = [], [], []
    for cond, runs in per_cond.items():
        ms = [metrics_for_run(rows, rec) for rec in runs.values()]
        agg = {"condition": cond, "n_runs": len(ms),
               "retries_used": sum(x["attempts"] - 1 for rec in runs.values() for x in rec.values())}
        for key in ms[0]:
            vals = [m[key] for m in ms]
            agg[key + "_mean"] = round(statistics.mean(vals), 3)
            agg[key + "_sd"] = round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0
        metric_rows.append(agg)

        confs = [confusion_for_run(rows, rec) for rec in runs.values()]
        for src in ["none"] + config.TYPES:
            conf_rows.append({"condition": cond, "injected_type": src,
                              **{t: round(statistics.mean(c[src][t] for c in confs), 3) for t in config.TYPES}})
        for k, rec in runs.items():
            for i, x in rec.items():
                if by_id[i]["injected_type"] == "none" and x["status"] == "ok" and any(v == "Yes" for v in x["labels"].values()):
                    flagged.append({"condition": cond, "run": k, "id": i,
                                    "flagged_types": ", ".join(t for t in config.TYPES if x["labels"][t] == "Yes"),
                                    "evidence": " | ".join(x["evidence"]), "text": by_id[i]["text"]})

    def write(name, fields, data):
        with open(os.path.join(res_dir, name), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(data)
    write("metrics.csv", list(metric_rows[0].keys()), metric_rows)
    write("confusion.csv", ["condition", "injected_type"] + config.TYPES, conf_rows)
    write("flagged_originals.csv", ["condition", "run", "id", "flagged_types", "evidence", "text"], flagged)

    def ms(a, k):
        return f"{a[k + '_mean']:.2f} ± {a[k + '_sd']:.2f}"

    s = [f"# Results: {args.set} set ({len(rows)} stories)\n",
         "Labels are synthetic (injected indicators). Detection rates use ALL injected variants as the "
         "denominator; invalid replies count as not detected.\n",
         "## Table A. Localized detection of injected indicators (primary)\n",
         "| Condition | Valid outputs | Localized detection (all) | In-dictionary | Out-of-dictionary | Detection (all) | Localization precision | Flag rate on originals |",
         "|---|---|---|---|---|---|---|---|"]
    for a in metric_rows:
        s.append(f"| {a['condition']} | {ms(a,'valid_rate')} | {ms(a,'locdet_ALL_all')} | {ms(a,'locdet_ALL_in')} | "
                 f"{ms(a,'locdet_ALL_out')} | {ms(a,'det_ALL_all')} | {ms(a,'locprec_ALL_all')} | {ms(a,'flag_rate_on_originals')} |")
    s += ["\n## Table B. Localized detection per type (all / in-dictionary / out-of-dictionary)\n",
          "| Condition | " + " | ".join(config.TYPES) + " |", "|---|" + "---|" * len(config.TYPES)]
    for a in metric_rows:
        s.append(f"| {a['condition']} | " + " | ".join(
            f"{a[f'locdet_{t}_all_mean']:.2f} / {a[f'locdet_{t}_in_mean']:.2f} / {a[f'locdet_{t}_out_mean']:.2f}"
            for t in config.TYPES) + " |")
    s += ["\n## Table C. Agreement with synthetic labels per type, over all valid outputs (F1; P / R)\n",
          "| Condition | " + " | ".join(config.TYPES) + " |", "|---|" + "---|" * len(config.TYPES)]
    for a in metric_rows:
        s.append(f"| {a['condition']} | " + " | ".join(
            f"{a[f'agree_{t}_F1_mean']:.2f} ({a[f'agree_{t}_P_mean']:.2f} / {a[f'agree_{t}_R_mean']:.2f})"
            for t in config.TYPES) + " |")
    s += ["\n## Table D. Output validity\n",
          "| Condition | Valid | Invalid JSON | Missing field | Bad value | Retries used | Ungrounded evidence |",
          "|---|---|---|---|---|---|---|"]
    for a in metric_rows:
        s.append(f"| {a['condition']} | {ms(a,'valid_rate')} | {ms(a,'fail_invalid_json')} | {ms(a,'fail_missing_field')} | "
                 f"{ms(a,'fail_bad_value')} | {a['retries_used']} | {ms(a,'ungrounded_evidence_rate')} |")
    s += ["\n## Table E. Confusion among valid outputs: share flagged for each label\n",
          "| Condition | Injected type | " + " | ".join(config.TYPES) + " |", "|---|---|" + "---|" * len(config.TYPES)]
    for c in conf_rows:
        s.append(f"| {c['condition']} | {c['injected_type']} | " + " | ".join(f"{c[t]:.2f}" for t in config.TYPES) + " |")
    text = "\n".join(s) + "\n"
    with open(os.path.join(res_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
