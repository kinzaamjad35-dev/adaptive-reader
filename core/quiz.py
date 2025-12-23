"""Comprehension checks: free auto-generated cloze questions, or LLM questions with a key."""
import json
import random
import re

from core.readability import sentences

STOP = set("""a an the and or but if then so of to in on at by for with from as is are was were be been
being it its this that these those he she they we you i his her their our your my me him them us not no
do does did have has had will would can could should may might must there here what which who whom when
where why how all any each few more most other some such than too very just also into over under about up
down out off again once only own same both one two""".split())


def _keywords(sent: str):
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", sent)
    return [w for w in words if w.lower() not in STOP and len(w) > 3]


def cloze_questions(text: str, n: int = 3, seed: int = 0):
    """Fill-in-the-blank questions with 4 options drawn from the passage."""
    rng = random.Random(seed)
    sents = [s for s in sentences(text) if 5 <= len(s.split()) <= 40]
    pool = sorted({w for s in sentences(text) for w in _keywords(s)}, key=str.lower)
    rng.shuffle(sents)
    qs, used = [], set()
    for s in sents:
        kws = [w for w in _keywords(s) if w.lower() not in used]
        if not kws:
            continue
        answer = max(kws, key=len)
        distract = [w for w in pool if w.lower() != answer.lower() and w.lower() not in s.lower()]
        rng.shuffle(distract)
        opts = list(dict.fromkeys([answer] + distract[:3]))
        if len(opts) < 3:
            continue
        rng.shuffle(opts)
        q = re.sub(rf"\b{re.escape(answer)}\b", "_____", s, count=1)
        qs.append({"question": f"Fill the gap: {q}", "options": opts, "answer": answer})
        used.add(answer.lower())
        if len(qs) >= n:
            break
    return qs


def llm_questions(text: str, provider: str, api_key: str, n: int = 3):
    from core.llm import chat
    prompt = (f"Write {n} simple multiple-choice comprehension questions about the passage. "
              'Reply with JSON only: [{"question": str, "options": [4 strings], "answer": str}]. '
              "The answer must be one of the options.\n\nPASSAGE:\n" + text)
    raw = chat(provider, api_key, prompt)
    m = re.search(r"\[.*\]", raw, re.S)
    data = json.loads(m.group(0) if m else raw)
    out = []
    for q in data[:n]:
        if q.get("answer") in q.get("options", []):
            out.append({"question": q["question"], "options": q["options"], "answer": q["answer"]})
    return out


def grade(questions, responses) -> float:
    if not questions:
        return 0.0
    right = sum(1 for q, r in zip(questions, responses) if r == q["answer"])
    return right / len(questions)
