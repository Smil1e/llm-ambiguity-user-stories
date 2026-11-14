"""Detectors: dictionary baseline, Claude, OpenAI (and Gemini, not used in the reported run), and a mock used only to test the pipeline."""
import json
import random
import re
import time

import config
from wordlists import BASELINE_RE

JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


# ---------------------------------------------------------------- parsing
def parse_output(raw):
    """Return (labels, evidence, status).

    status is one of:
      ok            valid JSON with Yes/No for every type
      invalid_json  no parseable JSON object in the reply
      missing_field a type field is absent
      bad_value     a type field is present but not Yes/No
    A missing or malformed 'evidence' field does not make the reply invalid; it is stored as
    an empty list, and evaluate.py reports separately whether evidence is grounded in the story."""
    if raw is None:
        return None, [], "invalid_json"
    m = JSON_RE.search(raw)
    if not m:
        return None, [], "invalid_json"
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, [], "invalid_json"
    if not isinstance(obj, dict):
        return None, [], "invalid_json"
    labels = {}
    for t in config.TYPES:
        if t not in obj:
            return None, [], "missing_field"
        v = str(obj[t]).strip().capitalize()
        if v not in ("Yes", "No"):
            return None, [], "bad_value"
        labels[t] = v
    ev = obj.get("evidence", [])
    if isinstance(ev, str):
        ev = [ev]
    evidence = [str(e) for e in ev if str(e).strip()] if isinstance(ev, list) else []
    return labels, evidence, "ok"


# ---------------------------------------------------------------- rule-based
def rule_based(story):
    """Dictionary baseline inspired by selected Smella categories: reports every matched term."""
    labels, evidence = {}, []
    for t in config.TYPES:
        hits = [h.group(0) for r in BASELINE_RE[t] for h in r.finditer(story)]
        labels[t] = "Yes" if hits else "No"
        evidence += hits
    return json.dumps({"rationale": "dictionary match", "evidence": evidence, **labels})


# ---------------------------------------------------------------- LLM clients
_clients = {}


def _with_retries(fn, attempts=4):
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # network / rate-limit errors
            if i == attempts - 1:
                raise
            wait = 2 ** (i + 1)
            print(f"    retry in {wait}s after error: {type(e).__name__}: {str(e)[:120]}")
            time.sleep(wait)


def call_claude(system, messages):
    import anthropic
    if "claude" not in _clients:
        _clients["claude"] = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    client = _clients["claude"]

    def go():
        kw = dict(model=config.CLAUDE_MODEL, max_tokens=config.MAX_TOKENS, system=system, messages=messages)
        try:
            r = client.messages.create(temperature=config.TEMPERATURE, **kw)
        except TypeError:
            r = client.messages.create(**kw)  # this SDK/model does not accept temperature
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    return _with_retries(go)


def call_gemini(system, messages):
    from google import genai
    from google.genai import types
    if not config.GEMINI_MODEL:
        raise SystemExit("Set GEMINI_MODEL to a current Gemini model name first (see README).")
    if "gemini" not in _clients:
        _clients["gemini"] = genai.Client()  # reads GEMINI_API_KEY
    client = _clients["gemini"]
    contents = [types.Content(role="user" if m["role"] == "user" else "model",
                              parts=[types.Part(text=m["content"])]) for m in messages]
    cfg = types.GenerateContentConfig(system_instruction=system, temperature=config.TEMPERATURE,
                                      max_output_tokens=config.MAX_TOKENS,
                                      response_mime_type="application/json")

    def go():
        return client.models.generate_content(model=config.GEMINI_MODEL, contents=contents, config=cfg).text
    return _with_retries(go)


def call_openai(system, messages):
    """OpenAI chat completions with JSON mode. Some newer models reject 'temperature' or
    'max_tokens'; the call falls back to the accepted parameters and the report must say
    which settings were actually used (printed once to the log)."""
    import openai
    if not config.OPENAI_MODEL:
        raise SystemExit("Set OPENAI_MODEL to a current OpenAI model name first.")
    if "openai" not in _clients:
        _clients["openai"] = openai.OpenAI()  # reads OPENAI_API_KEY
        _clients["openai_kw"] = {"temperature": config.TEMPERATURE}
        if config.OPENAI_REASONING:  # e.g. "none": no hidden reasoning, comparable to Claude without thinking
            _clients["openai_kw"]["reasoning_effort"] = config.OPENAI_REASONING
    client = _clients["openai"]
    msgs = [{"role": "system", "content": system}] + messages

    def go():
        kw = dict(model=config.OPENAI_MODEL, messages=msgs, response_format={"type": "json_object"},
                  max_completion_tokens=config.MAX_TOKENS, **_clients["openai_kw"])
        try:
            r = client.chat.completions.create(**kw)
        except openai.BadRequestError as e:
            dropped = [p for p in ("temperature", "reasoning_effort") if p in str(e) and p in _clients["openai_kw"]]
            if not dropped:
                raise
            for p in dropped:
                _clients["openai_kw"].pop(p)
                kw.pop(p)
                print(f"    note: this OpenAI model does not accept '{p}'; using its default")
            r = client.chat.completions.create(**kw)
        return r.choices[0].message.content
    return _with_retries(go)


def call_mock(system, messages, _rng=random.Random(0)):
    """Fake LLM for testing the pipeline only: keyword baseline with random noise."""
    story = messages[-1]["content"].split("\n", 1)[1]
    labels = json.loads(rule_based(story))
    if _rng.random() < 0.5:
        labels["evidence"] = [w for w in story.split()[:2]]  # simulate wrong or missing evidence
    for t in config.TYPES:
        if _rng.random() < 0.15:
            labels[t] = "No" if labels[t] == "Yes" else "Yes"
    if _rng.random() < 0.03:
        return "Sorry, I cannot answer that."  # simulate an unparseable reply
    return json.dumps(labels)


LLM_CALLERS = {"claude": call_claude, "gemini": call_gemini, "openai": call_openai, "mock": call_mock}


def model_name(model):
    return {"claude": config.CLAUDE_MODEL, "gemini": config.GEMINI_MODEL, "openai": config.OPENAI_MODEL,
            "mock": "mock", "rule": "rule-based"}[model]
