"""Readability scores, chunking and text simplification."""
import re

SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def sentences(text: str):
    return [s.strip() for s in SENT_RE.split(text.strip()) if s.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def syllables(word: str) -> int:
    """Heuristic English syllable count (no external data needed)."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|[^laeiouy]ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def flesch(text: str):
    words = re.findall(r"[A-Za-z0-9']+", text)
    n_s = max(1, len(sentences(text)))
    n_w = max(1, len(words))
    syl = sum(syllables(w) for w in words)
    ease = 206.835 - 1.015 * (n_w / n_s) - 84.6 * (syl / n_w)
    grade = 0.39 * (n_w / n_s) + 11.8 * (syl / n_w) - 15.59
    return ease, max(0.0, grade)


def scores(text: str) -> dict:
    if word_count(text) < 3:
        return {"Reading ease": None, "Grade level": None, "Words": word_count(text), "Avg sentence length": None}
    sents = sentences(text) or [text]
    return {
        "Reading ease": round(flesch(text)[0], 1),
        "Grade level": round(flesch(text)[1], 1),
        "Words": word_count(text),
        "Avg sentence length": round(word_count(text) / len(sents), 1),
    }


def chunk_text(text: str, target_words: int = 80):
    """Split into chunks of roughly target_words, keeping whole sentences and paragraphs."""
    chunks = []
    for para in [p for p in re.split(r"\n\s*\n", text) if p.strip()]:
        cur, n = [], 0
        for s in sentences(para) or [para]:
            w = word_count(s)
            if cur and n + w > target_words:
                chunks.append(" ".join(cur)); cur, n = [], 0
            cur.append(s); n += w
        if cur:
            if chunks and n < target_words * 0.3 and word_count(chunks[-1]) + n <= target_words * 1.4:
                chunks[-1] += " " + " ".join(cur)
            else:
                chunks.append(" ".join(cur))
    return chunks


# Plain-English substitutions (subset inspired by the Plain English Campaign A–Z of alternative words)
SIMPLE_WORDS = {
    "approximately": "about", "utilize": "use", "utilized": "used", "utilised": "used", "utilizes": "uses", "utilise": "use", "utilization": "use",
    "commence": "start", "commenced": "started", "terminate": "end", "terminated": "ended",
    "purchase": "buy", "purchased": "bought", "assist": "help", "assistance": "help",
    "sufficient": "enough", "insufficient": "not enough", "numerous": "many",
    "demonstrate": "show", "demonstrated": "showed", "obtain": "get", "obtained": "got",
    "require": "need", "requires": "needs", "required": "needed", "additional": "extra",
    "subsequently": "later", "prior to": "before", "in order to": "to", "however": "but",
    "therefore": "so", "consequently": "so", "nevertheless": "still", "furthermore": "also",
    "moreover": "also", "individuals": "people", "individual": "person", "residence": "home",
    "facilitate": "help", "endeavour": "try", "endeavor": "try", "inform": "tell",
    "indicate": "show", "indicates": "shows", "majority": "most", "objective": "aim",
    "participate": "take part", "possess": "have", "possesses": "has", "regarding": "about",
    "sustain": "keep up", "comprehend": "understand", "construct": "build", "constructed": "built",
    "observe": "see", "observed": "saw", "inquire": "ask", "attempt": "try", "attempted": "tried",
    "accomplish": "do", "accomplished": "did", "beneficial": "helpful", "modify": "change",
    "modified": "changed", "frequently": "often", "initial": "first", "initially": "at first",
    "remainder": "rest", "transmit": "send", "visualize": "picture", "enormous": "huge",
    "rapidly": "quickly", "rapid": "fast", "commonly": "often", "magnitude": "size",
    "consume": "eat", "consumed": "ate", "reside": "live", "resides": "lives",
    "approximate": "rough", "components": "parts", "component": "part", "fundamental": "basic",
    "significant": "big", "significantly": "a lot", "illuminate": "light up", "vehicle": "car",
    "physician": "doctor", "currently": "now", "located": "found", "eliminate": "remove",
}

_PHRASES = sorted(SIMPLE_WORDS, key=len, reverse=True)
_SPLIT_CONJ = re.compile(r",?\s+\b(and|but|so|because|although|whereas)\b\s+", re.I)


def _swap_words(s: str) -> str:
    for p in _PHRASES:
        def rep(m, p=p):
            r = SIMPLE_WORDS[p]
            return r[0].upper() + r[1:] if m.group(0)[0].isupper() else r
        s = re.sub(rf"\b{re.escape(p)}\b", rep, s, flags=re.I)
    return s


def _split_long(s: str, max_words: int):
    if word_count(s) <= max_words:
        return [s]
    s = re.sub(r"\s*\([^)]*\)", "", s)              # drop brackets
    s = re.sub(r",\s+(?:which|who)\s[^,.;]+,", "", s)  # drop extra-detail clauses ", which ..., "
    if word_count(s) <= max_words:
        return [s]
    parts = re.split(r"\s*;\s*|\s+[–—-]\s+", s)
    out = []
    for p in parts:
        if word_count(p) > max_words:
            m = list(_SPLIT_CONJ.finditer(p))
            # split at the conjunction nearest the middle
            if m:
                mid = len(p) / 2
                best = min(m, key=lambda x: abs(x.start() - mid))
                a, b = p[:best.start()], p[best.end():]
                conj = best.group(1).lower()
                lead = {"because": "This is because", "which": "This", "although": "But",
                        "while": "Also,", "whereas": "But", "and": "", "but": "But", "so": "So"}[conj]
                b = (lead + " " + b) if lead else b
                out += _split_long(a, max_words) + _split_long(b, max_words)
                continue
            commas = [m.start() for m in re.finditer(r",\s+", p)]
            commas = [c for c in commas if word_count(p[:c]) >= 4 and word_count(p[c:]) >= 4]
            if commas:
                c = min(commas, key=lambda x: abs(x - len(p) / 2))
                out += _split_long(p[:c], max_words) + _split_long(p[c + 1:], max_words)
                continue
        out.append(p)
    fixed = []
    for p in out:
        p = p.strip(" ,")
        if not p:
            continue
        p = p[0].upper() + p[1:]
        if p[-1] not in ".!?":
            p += "."
        fixed.append(p)
    return fixed


LEVELS = {  # label -> (max sentence words, target grade)
    "Very easy (age 7–9)": (10, 3),
    "Easy (age 9–11)": (14, 5),
    "Standard (age 11–14)": (20, 8),
    "Original": (999, 99),
}


def simplify_rule_based(text: str, level: str) -> str:
    max_words, _ = LEVELS.get(level, (14, 5))
    if max_words >= 999:
        return text
    paras = []
    for para in re.split(r"\n\s*\n", text):
        out = []
        for s in sentences(para):
            out += _split_long(_swap_words(s), max_words)
        if out:
            paras.append(" ".join(out))
    return "\n\n".join(paras)


def simplify_llm(text: str, level: str, provider: str, api_key: str) -> str:
    from core.llm import chat
    _, grade = LEVELS.get(level, (14, 5))
    prompt = (f"Rewrite the text below so a reader at US grade {grade} level can read it easily. "
              "Use short sentences and common words, keep every important fact, do not add new facts, "
              "keep paragraphs. Return only the rewritten text.\n\nTEXT:\n" + text)
    return chat(provider, api_key, prompt)
