"""Adaptive pacing: turn reading behaviour into recommended speed and reading level."""
from core.readability import LEVELS

LEVEL_ORDER = ["Very easy (age 7–9)", "Easy (age 9–11)", "Standard (age 11–14)", "Original"]


def chunk_wpm(words: int, seconds: float):
    if seconds <= 1 or words <= 0:
        return None
    wpm = words / (seconds / 60)
    return round(min(wpm, 600), 1)


def recommend(history, current_rate: float = 1.0, current_level: str = "Easy (age 9–11)"):
    """history: list of dicts with wpm, replays, lookups, words (recent chunks), plus optional quiz score.
    Returns (rate, level, reasons)."""
    reasons = []
    recent = [h for h in history if h.get("wpm")][-5:]
    rate, level = current_rate, current_level
    if current_level not in LEVEL_ORDER:
        level = "Easy (age 9–11)"
    idx = LEVEL_ORDER.index(level)
    if not recent:
        return rate, level, ["Read a few sections and I'll start suggesting a speed and level."]
    avg_wpm = sum(h["wpm"] for h in recent) / len(recent)
    words = sum(h.get("words", 0) for h in recent) or 1
    struggle = sum(h.get("replays", 0) + h.get("lookups", 0) for h in recent) / words * 100  # per 100 words
    quiz = [h["quiz"] for h in history[-5:] if h.get("quiz") is not None]
    quiz_avg = sum(quiz) / len(quiz) if quiz else None

    if struggle >= 3 or avg_wpm < 60 or (quiz_avg is not None and quiz_avg < 0.5):
        rate = max(0.5, round(rate - 0.1, 2))
        idx = max(0, idx - 1)
        reasons.append("You replayed or looked up quite a few words, or found questions hard, so I slowed the voice and made the text easier.")
    elif struggle < 1 and avg_wpm > 150 and (quiz_avg is None or quiz_avg >= 0.8):
        rate = min(1.6, round(rate + 0.1, 2))
        idx = min(len(LEVEL_ORDER) - 1, idx + 1)
        reasons.append("You're reading smoothly with good understanding, so I sped up a little and raised the level.")
    else:
        reasons.append("Your pace looks comfortable, so I kept the speed and level the same.")
    reasons.append(f"Average speed over the last {len(recent)} section(s): {avg_wpm:.0f} words per minute.")
    if quiz_avg is not None:
        reasons.append(f"Recent quiz score: {quiz_avg*100:.0f}%.")
    return rate, LEVEL_ORDER[idx], reasons
