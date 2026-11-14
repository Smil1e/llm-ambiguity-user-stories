"""Step 1: load stories, keep presumed-clean ones, inject ambiguity indicators, write the datasets.

Design (one fixed rule per type, all inside the "I want" part = the functional commitment):
  vague_qualifier  : adverb before the main verb      "I want to quickly export ..."
  vague_quantifier : replaces "the" before a plural   "I want to export several of the records"
  escape_clause    : appended to the "I want" part    "I want to export the records, if possible, so that ..."
Stories that do not fit every rule are excluded (no fallback positions). Every variant is
verified automatically: it still matches the template, the term occurs exactly once, the term
lies inside the "I want" part, and removing the edit gives back the original text.

Input  : a folder of Dalpiaz project files. Each .txt file = one project, one user story per line.
         A .csv file with a 'story' column (and optional 'project' column) also works.
Output : data/base_stories.csv, data/stories_full.csv, data/stories_pilot.csv,
         data/fewshot_examples.json, data/filter_report.txt

Usage  : python prepare.py --data path/to/dalpiaz_folder
"""
import argparse
import csv
import json
import os
import random
import re
from collections import Counter, defaultdict

import config
from prompts import SYSTEM_PROMPT
from wordlists import ALL_BASELINE_RE, ALL_OUT_RE, FEWSHOT, IN_VOCAB, OUT_VOCAB, term_regex

STORY_RE = re.compile(
    r"^\s*As\s+(?:an?|the)\s+(?P<role>[^,]+?)\s*,?\s*I\s+(?:want|would like|need|wish)\s+"
    r"(?P<want>.+?)\s*,?\s+so\s+that\s+(?P<benefit>.+?)\s*\.?\s*$",
    re.IGNORECASE,
)
THE_RE = re.compile(r"\bthe\s+(?=\w)", re.IGNORECASE)
COMPOUND_RE = re.compile(r"\b(and|or)\b|[;/&]", re.IGNORECASE)
STOP_WORDS = {"of", "by", "for", "to", "in", "on", "at", "with", "from", "that", "which", "so"}
POSITION = {"vague_qualifier": "before_main_verb", "vague_quantifier": "want_object",
            "escape_clause": "after_want"}


def is_plural_np(text_after_the):
    """True if the noun phrase right after 'the' looks plural (e.g. 'the pending orders').

    KNOWN LIMITATION (kept unchanged so that the reported data set is reproduced exactly):
    any word ending in "s" counts, so "the draw has" or "the FABS file" are taken as plural.
    Together with objects preceded by "all", this produced 14 flawed quantifier variants;
    sensitivity.py identifies them with spaCy and reports the results without them (Appendix A)."""
    for w in re.findall(r"[A-Za-z'-]+|[^\sA-Za-z]", text_after_the)[:4]:
        if not w[0].isalpha() or w.lower() in STOP_WORDS:
            break
        lw = w.lower()
        if lw.endswith("s") and not lw.endswith(("ss", "us", "is")):
            return True
    return False


def plural_the_hits(want):
    return [h.start() for h in THE_RE.finditer(want) if is_plural_np(want[h.end():])]


# ---------------------------------------------------------------- loading
def load_stories(folder):
    stories = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        stem, ext = os.path.splitext(name)
        if ext.lower() == ".txt":
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                for line in f:
                    line = " ".join(line.strip().split())
                    if line:
                        stories.append({"project": stem, "text": line})
        elif ext.lower() == ".csv":
            with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
                for row in csv.DictReader(f):
                    text = " ".join((row.get("story") or "").split())
                    if text:
                        stories.append({"project": row.get("project") or stem, "text": text})
    return stories


# ---------------------------------------------------------------- filtering
def check(text):
    """Return (match, None) if the story is presumed clean and fits every injection rule."""
    m = STORY_RE.match(text)
    if not m:
        return None, "not_template"
    if not 8 <= len(text.split()) <= 40:
        return None, "length"
    if any(r.search(text) for r in ALL_BASELINE_RE) or any(r.search(text) for r in ALL_OUT_RE):
        return None, "contains_vague_term"
    want = m.group("want")
    if COMPOUND_RE.search(want):
        return None, "compound_want"
    if not want.lower().startswith("to "):
        return None, "want_not_infinitive"
    if not plural_the_hits(want):
        return None, "no_plural_object_in_want"
    return m, None


# ---------------------------------------------------------------- injection
def inject(text, m, typ, term):
    """Apply the single rule for this type. Returns (new_text, inserted_segment)."""
    w0, w1 = m.span("want")
    if typ == "vague_qualifier":
        seg = term + " "
        k = w0 + (14 if m.group("want").lower().startswith("to be able to ") else 3); return text[:k] + seg + text[k:], seg
    if typ == "vague_quantifier":
        idx = w0 + plural_the_hits(m.group("want"))[0]
        return text[:idx] + term + " " + text[idx + 4:], term + " "  # "the " -> "<term> "
    if typ == "escape_clause":
        seg = ", " + term
        return text[:w1] + seg + text[w1:], seg
    raise ValueError(typ)


def verify(original, new, typ, term, seg):
    """Automatic check that the edit produced the targeted case (not only a grammatical one)."""
    m = STORY_RE.match(new)
    if not m:
        return False
    if len(term_regex(term).findall(new)) != 1:
        return False
    if not term_regex(term).search(m.group("want")):
        return False
    undo = new.replace(seg, "the ", 1) if typ == "vague_quantifier" else new.replace(seg, "", 1)
    return undo == original


def variants_for(b, i):
    """One variant per type, balanced vocab group and term rotation. None if any check fails."""
    m = STORY_RE.match(b["text"])
    rows = [{**b, "id": f"{b['base_id']}_orig", "injected_type": "none", "vocab": "",
             "position": "", "term": "", "segment": ""}]
    for t_idx, typ in enumerate(config.TYPES):
        k = i + t_idx
        vocab = config.VOCAB_GROUPS[k % 2]
        terms = (IN_VOCAB if vocab == "in" else OUT_VOCAB)[typ]
        term = terms[(k // 2) % len(terms)]
        text, seg = inject(b["text"], m, typ, term)
        if not verify(b["text"], text, typ, term, seg):
            return None
        rows.append({**b, "id": f"{b['base_id']}_{typ}", "text": text, "injected_type": typ,
                     "vocab": vocab, "position": POSITION[typ], "term": term, "segment": seg.strip(" ,")})
    return rows


def fits_every_term(s):
    """A story is usable only if every possible test term passes verification for its type."""
    m = STORY_RE.match(s["text"])
    for typ in config.TYPES:
        for term in IN_VOCAB[typ] + OUT_VOCAB[typ]:
            text, seg = inject(s["text"], m, typ, term)
            if not verify(s["text"], text, typ, term, seg):
                return False
    return True


# ---------------------------------------------------------------- few-shot and leakage
def build_fewshot(stories):
    examples = []
    for s in stories[:2]:
        examples.append({"story": s["text"], "labels": {t: "No" for t in config.TYPES}, "evidence": [],
                         "rationale": "No vague qualifier, vague quantifier or escape clause."})
    for j, typ in enumerate(config.TYPES):
        s = stories[2 + j]
        text, _ = inject(s["text"], STORY_RE.match(s["text"]), typ, FEWSHOT[typ])
        labels = {t: ("Yes" if t == typ else "No") for t in config.TYPES}
        examples.append({"story": text, "labels": labels, "evidence": [FEWSHOT[typ]],
                         "rationale": f"'{FEWSHOT[typ]}' makes the story ambiguous ({typ.replace('_', ' ')})."})
    return examples


def check_leakage(fewshot):
    """No test term (or its stem, e.g. 'smooth' for 'smoothly') may appear in any instruction
    or example text the model sees."""
    seen = (SYSTEM_PROMPT + " " + " ".join(e["story"] + " " + e["rationale"] for e in fewshot)).lower()
    leaks = []
    for groups in (IN_VOCAB, OUT_VOCAB):
        for terms in groups.values():
            for t in terms:
                core = re.sub(r"\b(of the|the)\b", "", t).strip()
                stems = {core, core[:-2] if core.endswith("ly") else core}
                if any(re.search(r"\b" + re.escape(s), seen) for s in stems if len(s) > 2):
                    leaks.append(t)
    if leaks:
        raise SystemExit(f"Test terms leak into the prompt or few-shot examples: {leaks}")


# ---------------------------------------------------------------- main
COLS = ["id", "base_id", "project", "text", "injected_type", "vocab", "position", "term", "segment"]


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder with the Dalpiaz files")
    ap.add_argument("--projects", nargs="*", help="optional: test projects (file names without extension)")
    ap.add_argument("--fewshot-project", help="optional: held-out project for few-shot examples")
    ap.add_argument("--pool-all", action="store_true",
                    help="sample the base stories from ALL projects (except the few-shot project) "
                         "instead of a balanced draw from a few projects")
    args = ap.parse_args()

    rng = random.Random(config.SEED)
    os.makedirs(config.DATA_DIR, exist_ok=True)

    raw = load_stories(args.data)
    seen, eligible, reasons = set(), defaultdict(list), Counter()
    for s in raw:
        key = s["text"].lower()
        if key in seen:
            reasons["duplicate"] += 1
            continue
        seen.add(key)
        m, why = check(s["text"])
        if why:
            reasons[why] += 1
        else:
            eligible[s["project"]].append(s)

    # rank projects by the number of stories that fit EVERY injection rule (not just the filters)
    usable = {p: [s for s in eligible[p] if fits_every_term(s)] for p in eligible}
    ranked = sorted(eligible, key=lambda p: len(usable[p]), reverse=True)
    rejected = sum(len(eligible[p]) - len(usable[p]) for p in eligible)
    picked = []

    if args.pool_all:
        # few-shot project: the given one, else the smallest project that still has >= 5 usable stories
        fs_project = args.fewshot_project or min((p for p in ranked if len(usable[p]) >= 5),
                                                 key=lambda p: len(usable[p]))
        test_projects = [p for p in ranked if p != fs_project and usable[p]]
        pool = [s for p in test_projects for s in usable[p]]
        if len(pool) < config.N_BASE:
            raise SystemExit(f"Only {len(pool)} usable stories outside the few-shot project, "
                             f"needs {config.N_BASE}. Lower N_BASE in config.py.")
        rng.shuffle(pool)
        picked = pool[: config.N_BASE]
        test_projects = sorted({s["project"] for s in picked})
    else:
        test_projects = args.projects or ranked[: config.N_TEST_PROJECTS]
        fs_project = args.fewshot_project or next(p for p in ranked if p not in test_projects)
        per = [config.N_BASE // len(test_projects)] * len(test_projects)
        for i in range(config.N_BASE - sum(per)):
            per[i] += 1
        for p, n in zip(test_projects, per):
            pool = usable[p][:]
            rng.shuffle(pool)
            if len(pool) < n:
                raise SystemExit(f"Project {p} has only {len(pool)} usable stories, needs {n}. "
                                 f"Use --pool-all, lower N_BASE in config.py, or choose other projects with --projects.")
            picked += pool[:n]
    if len(usable[fs_project]) < 5:
        raise SystemExit(f"Few-shot project {fs_project} needs at least 5 usable stories.")
    rng.shuffle(picked)

    full, base = [], []
    for i, s in enumerate(picked):
        b = {**s, "base_id": f"B{i + 1:02d}"}
        rows = variants_for(b, i)
        if rows is None:  # cannot happen after the check above, kept as a guard
            raise SystemExit(f"Verification failed for {b['base_id']}")
        base.append(b)
        full += rows
    pilot_ids = {b["base_id"] for b in base[: config.N_PILOT]}
    pilot = [r for r in full if r["base_id"] in pilot_ids]

    fs_pool = usable[fs_project][:]
    rng.shuffle(fs_pool)
    fewshot = build_fewshot(fs_pool)
    check_leakage(fewshot)

    write_csv(os.path.join(config.DATA_DIR, "base_stories.csv"),
              [{**b, "id": b["base_id"], "injected_type": "none"} for b in base])
    write_csv(os.path.join(config.DATA_DIR, "stories_full.csv"), full)
    write_csv(os.path.join(config.DATA_DIR, "stories_pilot.csv"), pilot)
    with open(os.path.join(config.DATA_DIR, "fewshot_examples.json"), "w", encoding="utf-8") as f:
        json.dump({"project": fs_project, "examples": fewshot}, f, indent=2, ensure_ascii=False)

    lines = [f"Stories loaded: {len(raw)}", "Removed by filter:"]
    lines += [f"  {k}: {v}" for k, v in reasons.most_common()]
    lines += ["Eligible (usable) per project:"] + [f"  {p}: {len(eligible[p])} ({len(usable[p])})" for p in ranked]
    lines += [f"Rejected by injection verification: {rejected}",
              f"Test projects: {test_projects}", f"Few-shot project: {fs_project}",
              f"Base stories: {len(base)}  Full set: {len(full)}  Pilot set: {len(pilot)}",
              "Injected per type/vocab: " +
              str(dict(Counter((r['injected_type'], r['vocab']) for r in full if r['vocab']))),
              "Leakage check: passed (no test term or stem in the system prompt or few-shot examples)"]
    report = "\n".join(lines)
    with open(os.path.join(config.DATA_DIR, "filter_report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
