"""Homework mode: find the questions in worksheet text."""
import re

Q_START = re.compile(r"^\s*(?:Q\s*)?(\d{1,2}|[a-hA-H])\s*[.)\]:-]\s+")


def split_questions(text: str):
    """Split worksheet text into questions. Uses numbering (1. 2) a) Q3:) or question marks."""
    text = re.sub(r"(?<=[?.!])\s+(?=(?:Q\s*)?\d{1,2}\s*[.)\]:])", "\n", text)  # inline numbering
    lines = [l.strip() for l in re.split(r"\n+", text) if l.strip()]
    qs, cur = [], None
    for l in lines:
        if Q_START.match(l):
            if cur:
                qs.append(cur)
            cur = Q_START.sub("", l, count=1)
        elif cur is not None:
            cur += " " + l
        else:
            cur = l
    if cur:
        qs.append(cur)
    if len(qs) <= 1:  # no numbering: split on question marks
        parts = re.findall(r"[^?]+\?", text.replace("\n", " "))
        if parts:
            qs = [p.strip() for p in parts]
    return [re.sub(r"\s+", " ", q).strip() for q in qs if len(q.strip()) > 2]
