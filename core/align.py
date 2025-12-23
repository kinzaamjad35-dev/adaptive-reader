"""Read-along alignment: compare what the learner said with the expected words."""
import re
from difflib import SequenceMatcher


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))


def similar(a: str, b: str) -> bool:
    a, b = norm(a), norm(b)
    if not a or not b:
        return False
    if a == b:
        return True
    return len(a) > 3 and SequenceMatcher(None, a, b).ratio() >= 0.8


def align(expected, spoken, lookahead: int = 3):
    """Walk the spoken words along the expected words.
    Returns (position reached, list of expected-word indexes that were skipped or misread)."""
    pos, missed = 0, []
    for s in spoken:
        for k in range(lookahead + 1):
            if pos + k < len(expected) and similar(expected[pos + k], s):
                missed += list(range(pos, pos + k))
                pos += k + 1
                break
    return pos, missed
