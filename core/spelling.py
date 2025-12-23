"""Spelling support for the writing helper (offline, pyspellchecker)."""
import re

_spell = None


def _checker():
    global _spell
    if _spell is None:
        from spellchecker import SpellChecker
        _spell = SpellChecker(language="en")
    return _spell


def check(text: str):
    """Return list of (word, [suggestions]) for likely misspellings."""
    sp = _checker()
    words = re.findall(r"[A-Za-z']+", text)
    unknown = sp.unknown([w.lower() for w in words if len(w) > 1 and not w.isupper()])
    out, seen = [], set()
    for w in words:
        lw = w.lower()
        if lw in unknown and lw not in seen:
            seen.add(lw)
            cands = sp.candidates(lw) or set()
            best = sp.correction(lw)
            sugg = ([best] if best else []) + sorted(c for c in cands if c != best)
            out.append((w, sugg[:4]))
    return out


def apply_fix(text: str, wrong: str, right: str) -> str:
    def rep(m):
        w = m.group(0)
        return right.capitalize() if w[0].isupper() else right
    return re.sub(rf"\b{re.escape(wrong)}\b", rep, text)


def tidy(text: str) -> str:
    """Capitalise sentence starts and 'i', add a final full stop."""
    t = re.sub(r"\s+", " ", text).strip()
    t = re.sub(r"\bi\b", "I", t)
    t = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
    if t and t[-1] not in ".!?":
        t += "."
    return t
