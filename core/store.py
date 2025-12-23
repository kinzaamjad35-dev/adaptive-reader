"""Learner profiles and sessions stored locally in a JSON file (no cloud, no accounts)."""
import json
import os
import threading
from datetime import datetime

DATA_PATH = os.environ.get("ADAPTIVE_READER_DATA", os.path.join(os.path.dirname(__file__), "..", "data", "profiles.json"))
_lock = threading.Lock()

DEFAULT_SETTINGS = {
    "font": "Lexend", "size": 22, "letter": 0.05, "word": 0.16, "line": 1.6,
    "theme": "Cream (BDA)", "bionic": False, "ruler": True, "rate": 1.0, "level": "Easy (age 9–11)",
}


def _load(path=None):
    path = path or DATA_PATH
    if not os.path.exists(path):
        return {"profiles": {}}
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"profiles": {}}


def _save(data, path=None):
    path = path or DATA_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


def list_profiles(path=None):
    return sorted(_load(path)["profiles"].keys())


def get_profile(name, path=None):
    p = _load(path)["profiles"].get(name)
    if p:
        p["settings"] = {**DEFAULT_SETTINGS, **p.get("settings", {})}
    return p


def create_profile(name, age=None, path=None):
    name = name.strip()
    if not name:
        raise ValueError("Name required")
    with _lock:
        data = _load(path)
        if name not in data["profiles"]:
            data["profiles"][name] = {"name": name, "age": age, "created": datetime.now().isoformat(timespec="seconds"),
                                      "settings": dict(DEFAULT_SETTINGS), "sessions": []}
            _save(data, path)
    return get_profile(name, path)


def delete_profile(name, path=None):
    with _lock:
        data = _load(path)
        data["profiles"].pop(name, None)
        _save(data, path)


def save_settings(name, settings, path=None):
    with _lock:
        data = _load(path)
        if name in data["profiles"]:
            data["profiles"][name]["settings"] = {**DEFAULT_SETTINGS, **settings}
            _save(data, path)


def log_event(name, event: dict, path=None):
    """event: {kind: 'chunk'|'quiz'|'drill', words, seconds, wpm, replays, lookups, score, title}"""
    with _lock:
        data = _load(path)
        if name not in data["profiles"]:
            return
        event = {"time": datetime.now().isoformat(timespec="seconds"), **event}
        data["profiles"][name]["sessions"].append(event)
        _save(data, path)


def events_dataframe(name, path=None):
    import pandas as pd
    p = get_profile(name, path)
    df = pd.DataFrame(p["sessions"] if p else [])
    if not df.empty:
        df["time"] = pd.to_datetime(df["time"])
    return df


# ---------------- struggle words (personal practice list)
def add_struggle_words(name, words, source, path=None):
    words = [w.strip(" .,!?;:\"'()").lower() for w in words if w and len(w.strip()) > 1]
    if not words:
        return
    with _lock:
        data = _load(path)
        p = data["profiles"].get(name)
        if not p:
            return
        sw = p.setdefault("struggle_words", {})
        for w in words:
            e = sw.setdefault(w, {"count": 0, "sources": [], "mastered": False, "correct": 0})
            e["count"] += 1
            e["mastered"] = False
            if source not in e["sources"]:
                e["sources"].append(source)
            e["last"] = datetime.now().isoformat(timespec="seconds")
        _save(data, path)


def struggle_words(name, include_mastered=False, path=None):
    p = get_profile(name, path) or {}
    sw = p.get("struggle_words", {})
    items = [(w, e) for w, e in sw.items() if include_mastered or not e.get("mastered")]
    return sorted(items, key=lambda x: (-x[1]["count"], x[0]))


def practise_word(name, word, correct, path=None):
    """Record a practice attempt; 3 correct in a row marks the word mastered."""
    with _lock:
        data = _load(path)
        p = data["profiles"].get(name)
        if not p or word not in p.get("struggle_words", {}):
            return
        e = p["struggle_words"][word]
        e["correct"] = e.get("correct", 0) + 1 if correct else 0
        if e["correct"] >= 3:
            e["mastered"] = True
        _save(data, path)


def set_goal(name, minutes, path=None):
    with _lock:
        data = _load(path)
        if name in data["profiles"]:
            data["profiles"][name]["daily_goal"] = int(minutes)
            _save(data, path)
