"""Step 2: send every story to every detector and save the raw replies.

Results go to results/<set>/raw_<model>_<strategy>.jsonl, one line per (story, run).
The script resumes: lines already saved are skipped, so you can stop and restart safely.

Usage examples:
  python run_experiment.py --set pilot --models rule claude gemini
  python run_experiment.py --set full  --models rule claude gemini --strategies zero few --runs 3
"""
import argparse
import csv
import json
import os
from datetime import datetime, timezone

import config
from detectors import LLM_CALLERS, model_name, parse_output, rule_based
from prompts import SYSTEM_PROMPT, build_messages


def load_rows(set_name):
    with open(os.path.join(config.DATA_DIR, f"stories_{set_name}.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def done_keys(path):
    keys = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                keys.add((r["id"], r["run"]))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["pilot", "full"], default="pilot")
    ap.add_argument("--models", nargs="+", default=["rule", "claude", "gemini"],
                    choices=["rule", "claude", "gemini", "openai", "mock"])
    ap.add_argument("--strategies", nargs="+", default=["zero", "few"], choices=["zero", "few"])
    ap.add_argument("--runs", type=int, default=config.N_RUNS)
    args = ap.parse_args()

    rows = load_rows(args.set)
    with open(os.path.join(config.DATA_DIR, "fewshot_examples.json"), encoding="utf-8") as f:
        fewshot = json.load(f)["examples"]
    out_dir = os.path.join(config.RESULTS_DIR, args.set)
    os.makedirs(out_dir, exist_ok=True)

    for model in args.models:
        strategies = ["none"] if model == "rule" else args.strategies
        runs = 1 if model == "rule" else args.runs  # rule-based is deterministic
        for strategy in strategies:
            path = os.path.join(out_dir, f"raw_{model}_{strategy}.jsonl")
            done = done_keys(path)
            todo = [(r, k) for k in range(1, runs + 1) for r in rows if (r["id"], k) not in done]
            print(f"{model}/{strategy}: {len(todo)} calls to make ({len(done)} already saved)")
            with open(path, "a", encoding="utf-8") as out:
                for n, (r, k) in enumerate(todo, 1):
                    attempts, failed = 0, False
                    if model == "rule":
                        raw = rule_based(r["text"])
                        attempts = 1
                        labels, evidence, status = parse_output(raw)
                    else:
                        msgs = build_messages(r["text"], strategy, fewshot)
                        # retry policy fixed in config.RETRY_INVALID: re-ask only for invalid replies
                        while attempts < 1 + config.RETRY_INVALID:
                            attempts += 1
                            try:
                                raw = LLM_CALLERS[model](SYSTEM_PROMPT, msgs)
                            except SystemExit:
                                raise
                            except Exception as e:
                                # API error: not saved, so the next run of the script retries it
                                print(f"    failed {r['id']} run {k} (will retry next time): {e}")
                                failed = True
                                break
                            labels, evidence, status = parse_output(raw)
                            if status == "ok":
                                break
                    if failed:
                        continue
                    out.write(json.dumps({
                        "id": r["id"], "run": k, "model": model, "model_name": model_name(model),
                        "strategy": strategy, "raw": raw, "labels": labels, "evidence": evidence,
                        "status": status, "parse_ok": status == "ok", "attempts": attempts,
                        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    }, ensure_ascii=False) + "\n")
                    out.flush()
                    if n % 25 == 0:
                        print(f"    {n}/{len(todo)}")


if __name__ == "__main__":
    main()
