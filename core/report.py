"""Shareable progress report (self-contained HTML a learner can send to a teacher or parent)."""
import html
from datetime import date

from core import progress


def summary(events):
    chunks = [e for e in events if e.get("kind") == "chunk" and e.get("wpm")]
    quizzes = [e for e in events if e.get("kind") == "quiz"]
    return {
        "sessions_days": len(progress.minutes_by_day(events)),
        "minutes": round(sum((e.get("seconds") or 0) for e in events) / 60, 1),
        "words": sum(e.get("words", 0) for e in chunks),
        "avg_wpm": round(sum(e["wpm"] for e in chunks) / len(chunks), 1) if chunks else None,
        "recent_wpm": round(sum(e["wpm"] for e in chunks[-5:]) / len(chunks[-5:]), 1) if chunks else None,
        "first_wpm": round(sum(e["wpm"] for e in chunks[:5]) / len(chunks[:5]), 1) if chunks else None,
        "quiz_avg": round(100 * sum(e["score"] for e in quizzes) / len(quizzes)) if quizzes else None,
        "streak": progress.streak(events),
    }


def html_report(profile, brand_name="Adaptive Reader"):
    ev = profile.get("sessions", [])
    s = summary(ev)
    sw = sorted(profile.get("struggle_words", {}).items(), key=lambda x: -x[1]["count"])
    rows = "".join(
        f"<tr><td>{html.escape(e['time'][:16].replace('T', ' '))}</td><td>{html.escape(e.get('kind', ''))}</td>"
        f"<td>{html.escape(str(e.get('title', '')))}</td><td>{e.get('words', '')}</td><td>{e.get('wpm', '') or ''}</td>"
        f"<td>{'' if e.get('score') is None else str(round(e['score'] * 100)) + '%'}</td></tr>" for e in ev[-60:][::-1])
    words = ", ".join(f"{html.escape(w)}{' ✓' if e.get('mastered') else ''}" for w, e in sw[:40]) or "None yet"
    fmt = lambda v, suf="": "–" if v is None else f"{v}{suf}"
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(profile['name'])} – reading report</title>
<style>body{{font-family:Verdana,sans-serif;background:#FAF6E9;color:#2B2B2B;max-width:900px;margin:auto;padding:24px;line-height:1.6}}
.cards{{display:flex;flex-wrap:wrap;gap:12px}}.c{{border:2px solid #2F5D8A;border-radius:12px;padding:12px 16px;min-width:150px}}
.c b{{font-size:1.6em;display:block}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border-bottom:1px solid #ccc;padding:6px;text-align:left}}</style>
</head><body><h1>📖 Reading report: {html.escape(profile['name'])}</h1>
<p>Made with {html.escape(brand_name)} on {date.today().isoformat()}. This report was created on the learner's device.</p>
<div class="cards">
<div class="c"><b>{fmt(s['recent_wpm'])}</b>words/min now (started at {fmt(s['first_wpm'])})</div>
<div class="c"><b>{fmt(s['quiz_avg'], '%')}</b>average quiz score</div>
<div class="c"><b>{s['words']}</b>words read</div>
<div class="c"><b>{s['minutes']}</b>minutes practised</div>
<div class="c"><b>{s['sessions_days']}</b>days practised</div>
<div class="c"><b>{s['streak']}</b>day streak</div></div>
<h2>Tricky words</h2><p>{words}</p><p><small>✓ = mastered in practice</small></p>
<h2>Recent activity</h2><table><tr><th>When</th><th>Activity</th><th>Text</th><th>Words</th><th>WPM</th><th>Score</th></tr>{rows}</table>
</body></html>"""
