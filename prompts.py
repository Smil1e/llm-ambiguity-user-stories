"""Prompts. The same system prompt and output format are used for every model and strategy;
the only difference between zero-shot and few-shot is the example turns.

The type definitions deliberately contain NO example words: any example could leak a test
term (or its stem) into the prompt. prepare.py checks this automatically.
"""
import json

import config

SYSTEM_PROMPT = """You are a requirements quality reviewer in an Agile team.
You check one user story at a time for three kinds of lexical ambiguity:

1. vague_qualifier: an adverb or adjective that describes a desired quality of the behaviour
   without a measurable criterion.
2. vague_quantifier: a word or phrase that refers to an unspecified amount or subset of items,
   so the exact number or selection of items is not defined.
3. escape_clause: a phrase that makes the requirement optional or conditional without stating
   when it applies.

Judge only these three kinds. A story can have none, one, or more than one.
In "evidence", copy the exact word or phrase from the story that causes each ambiguity you report.
Use an empty list if you report none.

Reply with ONLY a JSON object, no other text, in exactly this form:
{"rationale": "<one short sentence>", "evidence": ["<exact phrase>"], "vague_qualifier": "Yes" or "No", "vague_quantifier": "Yes" or "No", "escape_clause": "Yes" or "No"}"""


def user_msg(story):
    return f"User story:\n{story}"


def assistant_msg(rationale, labels, evidence):
    return json.dumps({"rationale": rationale, "evidence": evidence, **{t: labels[t] for t in config.TYPES}})


def build_messages(story, strategy, fewshot_examples=None):
    msgs = []
    if strategy == "few":
        for ex in fewshot_examples:
            msgs.append({"role": "user", "content": user_msg(ex["story"])})
            msgs.append({"role": "assistant",
                         "content": assistant_msg(ex["rationale"], ex["labels"], ex.get("evidence", []))})
    elif strategy != "zero":
        raise ValueError(strategy)
    msgs.append({"role": "user", "content": user_msg(story)})
    return msgs
