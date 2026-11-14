"""Figure 2 of the report: localized detection inside and outside the dictionary.

Reads results/full/metrics.csv (written by evaluate.py) and saves results/full/fig2_in_out.png.
Usage: python make_figures.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import config  # noqa: E402

LABELS = {"rule": "Dictionary\nbaseline", "claude/zero": "Claude Haiku\nzero-shot", "claude/few": "Claude Haiku\nfew-shot",
          "openai/zero": "GPT-6 Luna\nzero-shot", "openai/few": "GPT-6 Luna\nfew-shot"}


def key(cond):
    model, strategy = cond.split(" ")[0], cond.split("/ ")[-1]
    return "rule" if model == "rule" else f"{model}/{strategy}"


def main():
    path = os.path.join(config.RESULTS_DIR, "full", "metrics.csv")
    rows = {key(r["condition"]): r for r in csv.DictReader(open(path, encoding="utf-8"))}
    order = [k for k in LABELS if k in rows]
    inn = [100 * float(rows[k]["locdet_ALL_in_mean"]) for k in order]
    out = [100 * float(rows[k]["locdet_ALL_out_mean"]) for k in order]
    fig, ax = plt.subplots(figsize=(9.6, 4.5), dpi=150)
    x = range(len(order))
    w = 0.38
    b1 = ax.bar([i - w / 2 - 0.01 for i in x], inn, w, color="#2a78d6", label="In-dictionary terms", zorder=3)
    b2 = ax.bar([i + w / 2 + 0.01 for i in x], out, w, color="#eb6834", label="Out-of-dictionary terms", zorder=3)
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{b.get_height():.1f}%",
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([LABELS[k] for k in order], fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Localized detection rate")
    ax.yaxis.grid(True, color="#e4e3dd", zorder=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2, frameon=False)
    plt.tight_layout()
    out_path = os.path.join(config.RESULTS_DIR, "full", "fig2_in_out.png")
    fig.savefig(out_path, facecolor="white")
    print("Saved", out_path)


if __name__ == "__main__":
    main()
