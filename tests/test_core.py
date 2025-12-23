import os, sys, io
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core import readability, quiz, adaptive, store, progress, library, align, homework, spelling, report, display, textio

LONG = ("The scientists utilized approximately forty instruments in order to observe the storm, and they subsequently "
        "demonstrated that the rapid winds, which were enormous, could terminate the power supply although the town was prepared.")


def test_scores_and_chunks():
    s = readability.scores(LONG)
    assert s["Words"] > 20 and s["Grade level"] is not None
    chunks = readability.chunk_text(" ".join(p["text"] for p in library.PASSAGES[:3]), 60)
    assert len(chunks) >= 3 and all(readability.word_count(c) < 120 for c in chunks)


def test_simplify_makes_easier():
    out = readability.simplify_rule_based(LONG, "Very easy (age 7–9)")
    assert "used" in out and "about" in out and "utilized" not in out
    assert max(readability.word_count(x) for x in readability.sentences(out)) <= 14
    assert readability.scores(out)["Grade level"] < readability.scores(LONG)["Grade level"]
    assert readability.simplify_rule_based(LONG, "Original") == LONG


def test_cloze_quiz():
    t = library.PASSAGES[2]["text"]
    qs = quiz.cloze_questions(t, n=3, seed=1)
    assert qs and all(q["answer"] in q["options"] and "_____" in q["question"] for q in qs)
    assert quiz.grade(qs, [q["answer"] for q in qs]) == 1.0


def test_adaptive():
    assert adaptive.chunk_wpm(100, 60) == 100
    slow = [{"wpm": 50, "words": 80, "replays": 3, "lookups": 2}]
    r, lvl, _ = adaptive.recommend(slow, 1.0, "Standard (age 11–14)")
    assert r < 1.0 and lvl == "Easy (age 9–11)"
    fast = [{"wpm": 200, "words": 80, "replays": 0, "lookups": 0, "quiz": 1.0}] * 3
    r, lvl, _ = adaptive.recommend(fast, 1.0, "Easy (age 9–11)")
    assert r > 1.0 and lvl == "Standard (age 11–14)"


def test_store_and_progress(tmp_path):
    path = str(tmp_path / "p.json")
    store.create_profile("Ana", 10, path=path)
    store.log_event("Ana", {"kind": "chunk", "words": 80, "seconds": 60, "wpm": 80}, path=path)
    store.add_struggle_words("Ana", ["Enormous", "enormous", "x"], "t", path=path)
    sw = store.struggle_words("Ana", path=path)
    assert sw[0][0] == "enormous" and sw[0][1]["count"] == 2
    for _ in range(3):
        store.practise_word("Ana", "enormous", True, path=path)
    assert store.struggle_words("Ana", path=path) == []
    p = store.get_profile("Ana", path=path)
    assert "Ana" in report.html_report(p)
    today = datetime.now()
    ev = [{"time": (today - timedelta(days=d)).isoformat(), "kind": "chunk", "words": 200, "seconds": 600} for d in range(3)]
    assert progress.streak(ev) == 3
    ids = [b[0] for b in progress.earned_badges(ev)]
    assert "streak_3" in ids and "words_500" in ids


def test_align_flags_skipped():
    exp = "the big brown dog jumped over the fence".split()
    pos, missed = align.align(exp, "the big dog jumped over the fence".split())
    assert pos == len(exp) and missed == [2]


def test_homework_split():
    qs = homework.split_questions("Worksheet\n1. What is a frog?\n2) Where do tadpoles live?\nQ3: Name one bug.")
    assert len(qs) >= 3 and "frog" in qs[1]
    assert len(homework.split_questions("What is two plus two? Why is the sky blue?")) == 2


def test_spelling():
    issues = dict(spelling.check("I went to scool becuase it was fun"))
    assert "scool" in issues and "school" in issues["scool"]
    assert spelling.tidy("i like cats. they are fun") == "I like cats. They are fun."


def test_bionic_and_library():
    assert display.bionic_word("reading,") == "<b>read</b>ing,"
    assert {p["level"] for p in library.PASSAGES} == set(library.LEVELS)
    assert all(len(v) >= 8 for v in library.PHONICS.values())


def test_text_extract():
    import docx
    d = docx.Document(); d.add_paragraph("Hello reader."); b = io.BytesIO(); d.save(b)
    assert "Hello reader." in textio.extract_file("a.docx", b.getvalue())
    assert textio.extract_file("a.txt", b"line one\nline two") == "line one line two"


def test_syllables():
    assert [readability.syllables(w) for w in ["cat", "table", "reading", "elephant"]] == [1, 2, 2, 3]


def test_ocr_worksheet():
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1000, 300), "white"); d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 36)
    except OSError:
        f = ImageFont.load_default(size=36)
    d.text((30, 40), "1. What do frogs eat?", fill="black", font=f)
    d.text((30, 130), "2. Where do tadpoles live?", fill="black", font=f)
    b = io.BytesIO(); img.save(b, "PNG")
    qs = homework.split_questions(textio.ocr_image(b.getvalue(), keep_lines=True))
    assert len(qs) == 2 and "frogs" in qs[0].lower()
    assert homework.split_questions("1. What? 2. Why is it so?") == ["What?", "Why is it so?"]
