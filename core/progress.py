"""Streaks, daily goals and badges computed from a learner's logged events."""
from datetime import date, datetime, timedelta


def _day(e):
    return datetime.fromisoformat(e["time"]).date()


def minutes_by_day(events):
    out = {}
    for e in events:
        out[_day(e)] = out.get(_day(e), 0) + (e.get("seconds") or 0) / 60
    return out


def streak(events, today: date = None):
    today = today or date.today()
    days = set(_day(e) for e in events)
    d = today if today in days else today - timedelta(days=1)
    n = 0
    while d in days:
        n += 1
        d -= timedelta(days=1)
    return n


def best_streak(events):
    days = sorted(set(_day(e) for e in events))
    best = cur = 0
    prev = None
    for d in days:
        cur = cur + 1 if prev and d - prev == timedelta(days=1) else 1
        best, prev = max(best, cur), d
    return best


BADGES = [
    ("first_read", "🌱", "First steps", "Finish your first reading"),
    ("words_500", "📗", "500 words", "Read 500 words"),
    ("words_5000", "📚", "Bookworm", "Read 5,000 words"),
    ("streak_3", "🔥", "3-day streak", "Practise 3 days in a row"),
    ("streak_7", "🏆", "Week warrior", "Practise 7 days in a row"),
    ("quiz_ace", "⭐", "Quiz star", "Get 100% on a quiz"),
    ("readaloud", "🎤", "Brave reader", "Read out loud with the mic"),
    ("drill_10", "🔤", "Word builder", "Finish 10 word drills"),
    ("mastered_10", "💪", "Tricky words tamed", "Master 10 of your tricky words"),
    ("goal_5", "🎯", "Goal getter", "Hit your daily goal on 5 days"),
]


def earned_badges(events, mastered_count=0, goal_minutes=10):
    words = sum(e.get("words", 0) for e in events if e.get("kind") == "chunk")
    got = set()
    if any(e.get("kind") == "chunk" for e in events):
        got.add("first_read")
    if words >= 500:
        got.add("words_500")
    if words >= 5000:
        got.add("words_5000")
    bs = best_streak(events)
    if bs >= 3:
        got.add("streak_3")
    if bs >= 7:
        got.add("streak_7")
    if any(e.get("kind") == "quiz" and e.get("score") == 1 for e in events):
        got.add("quiz_ace")
    if any(e.get("readaloud") for e in events):
        got.add("readaloud")
    if sum(1 for e in events if e.get("kind") == "drill") >= 10:
        got.add("drill_10")
    if mastered_count >= 10:
        got.add("mastered_10")
    if sum(1 for m in minutes_by_day(events).values() if m >= goal_minutes) >= 5:
        got.add("goal_5")
    return [b for b in BADGES if b[0] in got]


def today_minutes(events, today: date = None):
    return minutes_by_day(events).get(today or date.today(), 0)
