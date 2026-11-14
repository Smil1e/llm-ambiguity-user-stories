"""Word lists.

BASELINE  : the dictionary of the rule-based detector. It follows the approach of the Smella
            tool (Femmer et al., "Rapid quality assurance with Requirements Smells"), which
            detects ISO/IEC/IEEE 29148 language smells by dictionary lookup:
              - vague_qualifier <- ISO 29148 "subjective language" and
                                   "ambiguous adverbs and adjectives"
              - escape_clause   <- ISO 29148 "loopholes" and "open-ended, non-verifiable terms"
              - vague_quantifier<- not a separate ISO/Smella category; take the terms from a
                                   published ambiguity source (e.g. Berry et al., Ambiguity
                                   Handbook) and cite it.
            Smella does not publish its full dictionaries, so the report must say this is a
            re-implementation of its approach with documented lists. VERIFY every term against
            the source you cite before the full run, then freeze the list.
            Matching covers the listed word forms only (no lemmatiser), so list each form.
IN_VOCAB  : injection terms that ARE in BASELINE (the rule-based detector should catch them).
OUT_VOCAB : injection terms that are NOT in BASELINE (tests whether LLMs generalise beyond lists).
FEWSHOT   : terms used only in few-shot examples. They are in BASELINE but never used for
            injection, so the prompt never leaks a test term to the LLM.
"""
import re

BASELINE = {
    "vague_qualifier": [
        # subjective language
        "user-friendly", "user friendly", "easy to use", "cost-effective", "cost effective",
        "easy", "easily", "simple", "simply", "intuitive", "seamless", "seamlessly", "flexible",
        "robust", "efficient", "efficiently", "effective", "effectively",
        # ambiguous adverbs and adjectives
        "quick", "quickly", "fast", "timely", "adequate", "adequately", "appropriate",
        "appropriately", "significant", "significantly", "minimal", "sufficient", "reasonable",
        "normal", "almost always",
    ],
    "vague_quantifier": [
        "some", "several", "many", "few", "a few", "various", "numerous", "most",
        "a lot of", "lots of", "multiple",
    ],
    "escape_clause": [
        # loopholes
        "if possible", "as appropriate", "as applicable", "as needed", "as required",
        "where possible", "if necessary", "when necessary", "if feasible", "to the extent possible",
        # open-ended, non-verifiable terms
        "but not limited to", "as a minimum", "etc",
    ],
}

IN_VOCAB = {
    "vague_qualifier": ["quickly", "easily", "efficiently", "seamlessly"],
    "vague_quantifier": ["some of the", "several of the", "many of the", "a few of the"],
    "escape_clause": ["if possible", "as needed", "where possible", "if necessary"],
}

OUT_VOCAB = {
    "vague_qualifier": ["snappily", "smoothly", "painlessly", "effortlessly"],
    "vague_quantifier": ["a handful of the", "a bunch of the", "a decent number of the", "a good chunk of the"],
    "escape_clause": ["where it makes sense", "when convenient", "within reason", "if it is doable"],
}

FEWSHOT = {
    "vague_qualifier": "adequately",
    "vague_quantifier": "most of the",
    "escape_clause": "as appropriate",
}


def term_regex(term: str) -> re.Pattern:
    return re.compile(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", re.IGNORECASE)


BASELINE_RE = {t: [term_regex(w) for w in ws] for t, ws in BASELINE.items()}
ALL_BASELINE_RE = [r for rs in BASELINE_RE.values() for r in rs]
ALL_OUT_RE = [term_regex(w) for ws in OUT_VOCAB.values() for w in ws]


def _self_check():
    """Fail loudly if the lists break the design assumptions."""
    for t in IN_VOCAB:
        for w in IN_VOCAB[t]:
            assert any(r.search(w) for r in BASELINE_RE[t]), f"IN_VOCAB term not caught by baseline: {w}"
        for w in OUT_VOCAB[t]:
            assert not any(r.search(w) for r in ALL_BASELINE_RE), f"OUT_VOCAB term leaks into baseline: {w}"
        assert any(r.search(FEWSHOT[t]) for r in BASELINE_RE[t]), f"FEWSHOT term not in baseline: {FEWSHOT[t]}"
        assert FEWSHOT[t] not in IN_VOCAB[t] + OUT_VOCAB[t], f"FEWSHOT term reused for injection: {FEWSHOT[t]}"


_self_check()
