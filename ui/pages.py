"""All app screens. UI only: logic lives in core/."""
import random
from datetime import datetime

import pandas as pd
import streamlit as st

from core import adaptive, homework, library, progress, quiz, readability, report, spelling, store, textio
from core.config import brand
from core.display import FONTS, THEMES, tts_mp3
from core.llm import PROVIDERS
from ui import components as C
from ui.state import llm, load_profile, once, save_settings, settings

NAV = {}  # filled by app.py: name -> st.Page


def go(name):
    st.switch_page(NAV[name])


def need_profile():
    if not st.session_state.get("profile"):
        st.info("👋 First, tell me who is reading.")
        if st.button("Start here ▶", type="primary"):
            go("home")
        st.stop()


def events():
    p = store.get_profile(st.session_state["profile"]) if st.session_state.get("profile") else None
    return (p or {}).get("sessions", []), p


def set_text(text, title):
    ss = st.session_state
    ss["text"], ss["title"] = text.strip(), title
    ss["original"] = text.strip()
    ss["chunks"] = readability.chunk_text(ss["text"], 60 if settings().get("level", "").startswith("Very") else 80)
    ss["ci"], ss["quiz"] = 0, None
    ss.pop("simplified_from", None)


# ======================================================================= HOME
def home():
    b = brand()
    ss = st.session_state
    if not ss.get("profile"):
        st.title(f"{b['icon']} {b['app_name']}")
        st.markdown(f"### {b['tagline']}")
        C.listen_button(f"Welcome to {b['app_name']}. Type your name, then press Let's go.", "welcome_say", "🔊 Hear this")
        profiles = store.list_profiles()
        if profiles:
            st.markdown("#### Who is reading?")
            cols = st.columns(min(4, len(profiles)))
            for i, name in enumerate(profiles):
                if cols[i % len(cols)].button(f"🙂 {name}", key=f"pick_{name}", use_container_width=True):
                    load_profile(name)
                    st.rerun()
            st.markdown("#### …or someone new")
        with st.form("new"):
            name = st.text_input("Your name", placeholder="e.g. Sam")
            age = st.number_input("Age (optional)", 8, 99, 12)
            st.markdown("**Pick the colour that feels easiest to read:**")
            theme = st.radio("Colour", list(THEMES)[:6], horizontal=True, label_visibility="collapsed")
            if st.form_submit_button("Let's go ▶", type="primary"):
                if not name.strip():
                    st.error("Please type your name.")
                else:
                    store.create_profile(name, int(age))
                    load_profile(name.strip())
                    ss["settings"]["theme"] = theme
                    save_settings()
                    ss["welcome"] = True
                    st.rerun()
        st.caption("🔒 Everything stays on this device/app. No account, no ads.")
        return

    ev, p = events()
    name = ss["profile"]
    st.title(f"Hi {name}! 👋")
    if ss.pop("welcome", False):
        C.say(f"Hi {name}! Let's read together.", "hi_say", beep=660)
        st.markdown("**Quick tour:** 📖 *Read* your own text · 📚 *Library* has practice stories · "
                    "🔤 *Practice* drills tricky words · 📝 *Homework* reads worksheets · ✍️ *Write* lets you speak to type.")
    goal = p.get("daily_goal", 10)
    mins = progress.today_minutes(ev)
    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Streak", f"{progress.streak(ev)} day" + ("" if progress.streak(ev) == 1 else "s"))
    c2.metric("🎯 Today", f"{mins:.0f} / {goal} min")
    c3.metric("🏅 Badges", len(progress.earned_badges(ev, sum(1 for _, e in store.struggle_words(name, True) if e.get('mastered')), goal)))
    st.progress(min(1.0, mins / max(goal, 1)), text="Daily goal" + (" ✅ done!" if mins >= goal else ""))
    st.markdown("### What do you want to do?")
    a, b2 = st.columns(2)
    if a.button("📖  Read my text", use_container_width=True, type="primary"):
        go("read")
    if b2.button("📚  Practice stories", use_container_width=True):
        go("library")
    a, b2 = st.columns(2)
    if a.button("🔤  Word practice", use_container_width=True):
        go("practice")
    if b2.button("📝  Homework helper", use_container_width=True):
        go("homework")
    a, b2 = st.columns(2)
    if a.button("✍️  Speak & write", use_container_width=True):
        go("write")
    if b2.button("📊  My progress", use_container_width=True):
        go("progress")
    tricky = store.struggle_words(name)
    if tricky:
        st.markdown(f"💡 You have **{len(tricky)} tricky words** to practise.")
    if st.button("🔁 Switch reader"):
        ss["profile"] = None
        st.rerun()


# ======================================================================= READ
def _input_area():
    tabs = st.tabs(["✏️ Type / paste", "📄 File", "📷 Photo"])
    with tabs[0]:
        t = st.text_area("Paste or type text", height=180, key="paste", label_visibility="collapsed",
                         placeholder="Paste any text here…")
        if st.button("Use this text ▶", type="primary", key="use_paste") and t.strip():
            set_text(t, "My text"); st.rerun()
    with tabs[1]:
        f = st.file_uploader("PDF, Word or TXT", type=["pdf", "docx", "txt", "md"])
        if f and st.button("Open file ▶", type="primary"):
            try:
                t = textio.extract_file(f.name, f.getvalue())
                if not t.strip():
                    st.warning("I couldn't find text in that file. If it's a scan, try the 📷 Photo tab.")
                else:
                    set_text(t, f.name); st.rerun()
            except Exception as e:
                st.error(f"Sorry, I couldn't open that file ({e}).")
    with tabs[2]:
        t = _photo_text("read")
        if t:
            set_text(t, "Photo"); st.rerun()


def _photo_text(key):
    src = st.radio("Photo from", ["Upload", "Camera"], horizontal=True, key=f"src_{key}", label_visibility="collapsed")
    img = st.camera_input("Take a photo of the page", key=f"cam_{key}") if src == "Camera" else \
        st.file_uploader("Photo of a page", type=["png", "jpg", "jpeg", "webp"], key=f"img_{key}")
    if img and st.button("Read the photo ▶", type="primary", key=f"ocr_{key}"):
        with st.spinner("Reading the photo…"):
            try:
                t = textio.ocr_image(img.getvalue(), keep_lines=(key == "hw"))
            except Exception as e:
                st.error(f"Photo reading failed ({e})."); return None
        if not t.strip():
            st.warning("I couldn't see any words. Try a brighter, closer, straighter photo.")
            return None
        return t
    return None


def _look_controls(compact=True):
    s = settings()
    with st.expander("🎨 Change how text looks", expanded=not compact):
        c1, c2 = st.columns(2)
        s["font"] = c1.selectbox("Font", list(FONTS), index=list(FONTS).index(s.get("font", "Lexend")))
        s["theme"] = c2.selectbox("Colours", list(THEMES), index=list(THEMES).index(s.get("theme", "Cream (BDA)")))
        s["size"] = st.slider("Text size", 16, 44, int(s.get("size", 22)))
        c1, c2, c3 = st.columns(3)
        s["letter"] = c1.slider("Letter gap", 0.0, 0.3, float(s.get("letter", 0.05)), 0.01)
        s["word"] = c2.slider("Word gap", 0.0, 1.0, float(s.get("word", 0.16)), 0.02)
        s["line"] = c3.slider("Line gap", 1.2, 3.0, float(s.get("line", 1.6)), 0.1)
        c1, c2 = st.columns(2)
        s["ruler"] = c1.toggle("Reading ruler", s.get("ruler", True))
        s["bionic"] = c2.toggle("Bold word starts", s.get("bionic", False))
        if st.button("💾 Save my look"):
            save_settings(); st.toast("Saved ✓")


def read():
    need_profile()
    ss, s = st.session_state, settings()
    st.title("📖 Read")
    if not ss["text"]:
        st.markdown("Add some text to read, or pick a story from the 📚 Library.")
        _input_area()
        if st.button("📚 Pick a practice story"):
            go("library")
        return

    top = st.columns([3, 1])
    top[0].markdown(f"### {ss['title']}")
    if top[1].button("➕ New text"):
        ss["text"], ss["chunks"] = "", []; st.rerun()

    # --- level & simplify
    with st.expander("🪄 Make it easier", expanded=False):
        lvl = st.select_slider("Reading level", adaptive.LEVEL_ORDER, value=s.get("level", "Easy (age 9–11)"))
        prov, key = llm()
        use_ai = st.toggle("Use AI to rewrite (better)", value=bool(key), disabled=not key,
                           help=None if key else "Add an AI key in ⚙️ Settings to switch this on.")
        if st.button("Simplify ✨", type="primary"):
            src = ss.get("original", ss["text"])
            with st.spinner("Rewriting…"):
                try:
                    new = readability.simplify_llm(src, lvl, prov, key) if use_ai and key else readability.simplify_rule_based(src, lvl)
                except Exception as e:
                    st.warning(f"AI didn't work ({e}). Using the built-in simplifier.")
                    new = readability.simplify_rule_based(src, lvl)
            s["level"] = lvl; save_settings()
            ss["text"] = new
            ss["chunks"] = readability.chunk_text(new, 60 if lvl.startswith("Very") else 80)
            ss["ci"], ss["quiz"], ss["simplified_from"] = 0, None, src
            st.rerun()
        if ss.get("simplified_from"):
            b, a = readability.scores(ss["simplified_from"]), readability.scores(ss["text"])
            st.dataframe(pd.DataFrame({"Before": b, "After": a}).astype(str), use_container_width=True)
            if st.button("↩ Back to original"):
                set_text(ss["simplified_from"], ss["title"]); st.rerun()
        else:
            sc = readability.scores(ss["text"])
            st.caption(f"Grade level {sc['Grade level']} · reading ease {sc['Reading ease']} (higher = easier)")

    _look_controls()
    c1, c2, c3 = st.columns(3)
    mode = c1.radio("View", ["📄 Page", "🔦 Focus"], horizontal=True,
                    help="Focus shows one sentence at a time.")
    s["quiz_on"] = c2.toggle("Quiz me", s.get("quiz_on", True))
    s["autoread"] = c3.toggle("Auto-read (Focus)", s.get("autoread", True))

    chunks = ss["chunks"] or [ss["text"]]
    ci = min(ss["ci"], len(chunks) - 1)
    st.progress((ci) / len(chunks), text=f"Part {ci + 1} of {len(chunks)}")

    # --- quiz stage
    if ss.get("quiz") is not None:
        _quiz(chunks, ci)
        return

    done = C.reader(chunks[ci], s, key=f"rd_{hash(ss['text'])}_{ci}_{mode}", mode="focus" if "Focus" in mode else "flow")
    with st.expander("🔈 Can't hear anything? Play as an audio file"):
        if st.button("Make audio file"):
            try:
                st.audio(tts_mp3(chunks[ci], slow=s.get("rate", 1) < 0.8), format="audio/mp3")
            except Exception as e:
                st.error(f"Audio needs internet ({e}).")
    if once(done, "chunk"):
        _finish_chunk(done, chunks, ci)
        st.rerun()
    _coach()


def _finish_chunk(done, chunks, ci):
    ss, s = st.session_state, settings()
    words = readability.word_count(chunks[ci])
    wpm = adaptive.chunk_wpm(words, done["seconds"])
    ev = {"kind": "chunk", "title": ss["title"], "words": words, "seconds": round(done["seconds"], 1), "wpm": wpm,
          "replays": done.get("replays", 0), "lookups": len(done.get("lookups", [])), "rate": done.get("rate"),
          "readaloud": bool(done.get("mic")), "level": s.get("level")}
    store.log_event(ss["profile"], ev)
    ss["history"].append(ev)
    tricky = done.get("lookups", []) + done.get("replayed", []) + done.get("misread", [])
    store.add_struggle_words(ss["profile"], tricky, ss["title"])
    if done.get("misread") is not None and done.get("misread"):
        ss["last_misread"] = done["misread"]
    s["rate"] = done.get("rate", s.get("rate", 1.0))
    rate, level, reasons = adaptive.recommend(ss["history"], s["rate"], s.get("level", "Easy (age 9–11)"))
    ss["coach"] = {"rate": rate, "level": level, "reasons": reasons, "wpm": wpm}
    if s.get("quiz_on", True):
        prov, key = llm()
        qs = []
        if key:
            try:
                qs = quiz.llm_questions(chunks[ci], prov, key)
            except Exception:
                qs = []
        qs = qs or quiz.cloze_questions(chunks[ci], n=2, seed=ci)
        ss["quiz"] = qs if qs else None
        if not qs:
            ss["ci"] = ci + 1
    else:
        ss["ci"] = ci + 1


def _coach():
    ss, s = st.session_state, settings()
    c = ss.get("coach")
    if not c:
        return
    with st.container(border=True):
        st.markdown(f"**🧭 Reading coach** · last part: **{c['wpm'] or '–'} words/min**")
        for r in c["reasons"]:
            st.markdown(f"- {r}")
        if (c["rate"], c["level"]) != (s.get("rate"), s.get("level")):
            st.markdown(f"Suggested: voice **{c['rate']:.2f}×**, level **{c['level']}**")
            if st.button("👍 Use the suggestion", type="primary"):
                s["rate"] = c["rate"]
                if c["level"] != s.get("level"):
                    s["level"] = c["level"]
                    src = ss.get("simplified_from", ss.get("original", ss["text"]))
                    new = readability.simplify_rule_based(src, c["level"])
                    done_words = sum(readability.word_count(x) for x in ss["chunks"][:ss["ci"]])
                    ss["text"], ss["simplified_from"] = new, src
                    ss["chunks"] = readability.chunk_text(new, 60 if c["level"].startswith("Very") else 80)
                    acc, k = 0, 0
                    while k < len(ss["chunks"]) and acc < done_words:
                        acc += readability.word_count(ss["chunks"][k]); k += 1
                    ss["ci"] = min(k, len(ss["chunks"]) - 1)
                save_settings(); ss["coach"] = None; st.rerun()
    if ss.get("last_misread"):
        st.markdown("🟠 Words to check: " + ", ".join(ss["last_misread"][:10]) + " (added to your 🔤 practice list)")
    if ss["ci"] >= len(ss["chunks"]):
        _finished()


def _finished():
    st.balloons()
    C.say("Well done! You finished the whole text.", f"fin_{st.session_state['title']}", beep=880)
    st.success("🎉 You finished the whole text!")
    c1, c2 = st.columns(2)
    if c1.button("📚 Another story", type="primary"):
        go("library")
    if c2.button("🔤 Practise tricky words"):
        go("practice")


def _quiz(chunks, ci):
    ss = st.session_state
    qs = ss["quiz"]
    st.markdown("### 🤔 Quick check")
    answers = []
    for i, q in enumerate(qs):
        with st.container(border=True):
            st.markdown(f"**{q['question']}**")
            C.listen_button(q["question"].replace("_____", "blank") + ". " + ". ".join(q["options"]), f"q_say_{ci}_{i}", "🔊")
            answers.append(st.radio("Answer", q["options"], index=None, key=f"q_{hash(ss['text'])}_{ci}_{i}",
                                    label_visibility="collapsed"))
    if st.button("Check ✓", type="primary", disabled=any(a is None for a in answers)):
        sc = quiz.grade(qs, answers)
        store.log_event(ss["profile"], {"kind": "quiz", "title": ss["title"], "score": sc, "seconds": 0})
        if ss["history"]:
            ss["history"][-1]["quiz"] = sc
        ss["quiz_result"] = (sc, [(q["question"], q["answer"], a) for q, a in zip(qs, answers)])
        ss["quiz"] = None
        ss["ci"] = ci + 1
        st.rerun()
    if st.button("Skip ⏭"):
        ss["quiz"], ss["ci"] = None, ci + 1; st.rerun()


def quiz_feedback():
    ss = st.session_state
    r = ss.pop("quiz_result", None)
    if not r:
        return
    sc, items = r
    if sc == 1:
        st.success("⭐ All correct! Brilliant.")
        C.say("All correct! Brilliant.", "qfb", beep=880)
    elif sc >= 0.5:
        st.info(f"👍 Good try: {round(sc * 100)}% right.")
        C.say("Good try!", "qfb", beep=660)
    else:
        st.warning("That was tricky. Let's keep going, you're learning!")
        C.say("That was tricky. Let's keep going.", "qfb", beep=440)
    for q, ans, a in items:
        if a != ans:
            st.markdown(f"- The answer was **{ans}**")


# ======================================================================= LIBRARY
def library_page():
    need_profile()
    st.title("📚 Practice library")
    c1, c2 = st.columns(2)
    lvl = c1.radio("Level", ["All"] + library.LEVELS, horizontal=True)
    kind = c2.radio("Type", ["All", "Short story", "Everyday text", "Science", "History"], horizontal=True)
    items = library.by_level(lvl, kind)
    badge = {"Beginner": "🟢", "Elementary": "🔵", "Intermediate": "🟠", "Advanced": "🔴"}
    for i, p in enumerate(items):
        with st.container(border=True):
            a, b = st.columns([4, 1])
            a.markdown(f"**{badge[p['level']]} {p['title']}** · {p['type']} · {readability.word_count(p['text'])} words")
            a.caption(p["text"][:110] + "…")
            if b.button("Read ▶", key=f"lib_{i}", type="primary", use_container_width=True):
                set_text(p["text"], p["title"]); go("read")


# ======================================================================= PRACTICE
def practice():
    need_profile()
    st.title("🔤 Word practice")
    t1, t2, t3 = st.tabs(["⭐ My tricky words", "🔡 Phonics", "👀 Sight words"])
    with t1:
        _tricky()
    with t2:
        pat = st.selectbox("Sound pattern", list(library.PHONICS))
        _drill(library.PHONICS[pat], f"ph_{pat}", pat)
    with t3:
        sset = st.radio("Set", list(library.SIGHT_WORDS), horizontal=True)
        _flash(library.SIGHT_WORDS[sset], f"sw_{sset}")


def _tricky():
    name = st.session_state["profile"]
    items = store.struggle_words(name)
    if not items:
        st.markdown("No tricky words yet. When you tap a word, repeat a sentence, or the mic hears a word you skipped, "
                    "it shows up here for practice.")
        return
    st.markdown(f"**{len(items)} words** · get one right 3 times in a row to master it 💪")
    _drill([w for w, _ in items[:12]], "tricky", "My words", track=True)
    with st.expander("See the list"):
        st.dataframe(pd.DataFrame([{"word": w, "times": e["count"], "from": ", ".join(e["sources"][:2])} for w, e in items]),
                     use_container_width=True, hide_index=True)


def _drill(words, key, title, track=False):
    """Hear it → spell it. Also shows the word split into chunks for decoding."""
    ss = st.session_state
    k = f"drill_{key}"
    if k not in ss or ss[k]["words"] != words:
        ss[k] = {"words": words, "i": 0, "right": 0}
    d = ss[k]
    if d["i"] >= len(words):
        st.success(f"🎉 Done! {d['right']} / {len(words)} right.")
        store.log_event(ss["profile"], {"kind": "drill", "title": title, "score": d["right"] / len(words), "seconds": len(words) * 15})
        C.say("Great work!", f"drdone_{key}", beep=880)
        if st.button("Go again 🔁", key=f"again_{key}"):
            random.shuffle(words); ss[k] = {"words": words, "i": 0, "right": 0}; st.rerun()
        ss[k]["i"] = -999  # log once
        return
    if d["i"] < 0:
        if st.button("Go again 🔁", key=f"again2_{key}"):
            ss[k] = {"words": words, "i": 0, "right": 0}; st.rerun()
        return
    w = words[d["i"]]
    st.progress(d["i"] / len(words), text=f"Word {d['i'] + 1} of {len(words)}")
    c1, c2 = st.columns([1, 2])
    with c1:
        C.listen_button(w, f"say_{key}_{d['i']}", "🔊 Hear word", rate=0.75)
    show = c2.toggle("Show me the word", key=f"show_{key}_{d['i']}")
    if show:
        st.markdown(f"<div class='big' style='letter-spacing:.15em'>{' · '.join(_syllables(w))}</div>", unsafe_allow_html=True)
    with st.form(f"f_{key}_{d['i']}", clear_on_submit=True):
        ans = st.text_input("Type the word you hear", key=f"in_{key}_{d['i']}")
        ok = st.form_submit_button("Check ✓", type="primary")
    if ok:
        right = ans.strip().lower() == w.lower()
        if track:
            store.practise_word(ss["profile"], w, right)
        if right:
            d["right"] += 1
            st.toast("✅ Correct!")
            C.say("Correct!", f"ok_{key}_{d['i']}", beep=880)
        else:
            st.toast(f"The word was: {w}")
            C.say(f"Not quite. It's {w}. {' '.join(w)}", f"no_{key}_{d['i']}", beep=330)
        d["i"] += 1
        st.rerun()


def _syllables(w):
    import re
    parts = re.findall(r"[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$|[^aeiouy](?=[^aeiouy]))?", w.lower())
    return parts if "".join(parts) == w.lower() and parts else [w]


def _flash(words, key):
    ss = st.session_state
    k = f"flash_{key}"
    ss.setdefault(k, 0)
    i = ss[k] % len(words)
    w = words[i]
    st.markdown(f"<div class='card' style='text-align:center;font-size:64px;font-weight:700'>{w}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        C.listen_button(w, f"fl_{key}_{i}", "🔊 Hear it", rate=0.8)
    if c2.button("✅ I know it", key=f"know_{key}", use_container_width=True, type="primary"):
        ss[k] += 1
        store.log_event(ss["profile"], {"kind": "drill", "title": f"Sight words {key}", "score": 1, "seconds": 5})
        st.rerun()
    if c3.button("🔁 Practise later", key=f"later_{key}", use_container_width=True):
        store.add_struggle_words(ss["profile"], [w], "Sight words")
        ss[k] += 1; st.rerun()
    st.caption(f"{i + 1} / {len(words)}")


# ======================================================================= HOMEWORK
def homework_page():
    need_profile()
    ss = st.session_state
    st.title("📝 Homework helper")
    st.markdown("Snap your worksheet. I'll read each question to you, and you can **say** your answer.")
    if not ss.get("hw_qs"):
        t = _photo_text("hw")
        txt = st.text_area("…or paste the questions", height=120, key="hw_paste")
        if st.button("Use pasted questions ▶", disabled=not txt.strip()):
            t = txt
        if t:
            ss["hw_qs"] = homework.split_questions(t) or [t]
            ss["hw_ans"] = [""] * len(ss["hw_qs"])
            st.rerun()
        return
    qs = ss["hw_qs"]
    i = st.session_state.setdefault("hw_i", 0)
    i = min(i, len(qs) - 1)
    st.progress((i + 1) / len(qs), text=f"Question {i + 1} of {len(qs)}")
    C.reader(qs[i], settings(), key=f"hwr_{i}_{hash(qs[i])}", readalong=False, done_label="✅ Got it")
    spoken = C.dictation(f"hwd_{i}", "Say my answer")
    if once(spoken, f"hw{i}"):
        ss["hw_ans"][i] = (ss["hw_ans"][i] + " " + spoken["text"]).strip()
        ss[f"hw_ta_{i}"] = ss["hw_ans"][i]
    ss["hw_ans"][i] = st.text_area("My answer", value=ss["hw_ans"][i], key=f"hw_ta_{i}", height=110)
    if ss["hw_ans"][i]:
        for w, sug in spelling.check(ss["hw_ans"][i])[:5]:
            st.caption(f"✏️ Check spelling: **{w}** → {', '.join(sug) or '?'}")
    c1, c2, c3 = st.columns(3)
    if c1.button("◀ Back", disabled=i == 0, use_container_width=True):
        ss["hw_i"] = i - 1; st.rerun()
    if c2.button("Next ▶", disabled=i >= len(qs) - 1, type="primary", use_container_width=True):
        ss["hw_i"] = i + 1; st.rerun()
    if c3.button("🗑 New worksheet", use_container_width=True):
        for k in ("hw_qs", "hw_ans", "hw_i"):
            ss.pop(k, None)
        st.rerun()
    out = "\n\n".join(f"{n + 1}. {q}\nAnswer: {a}" for n, (q, a) in enumerate(zip(qs, ss["hw_ans"])))
    st.download_button("⬇️ Save my answers", out, file_name="homework_answers.txt", use_container_width=True)


# ======================================================================= WRITE
def write():
    need_profile()
    ss = st.session_state
    st.title("✍️ Speak & write")
    st.markdown("Press the mic and say what you want to write. Then fix spellings with one tap.")
    ss.setdefault("draft", "")
    spoken = C.dictation("wr_mic", "Speak")
    if once(spoken, "write"):
        ss["draft"] = (ss["draft"] + " " + spoken["text"]).strip()
        ss["draft_box"] = ss["draft"]
    ss.setdefault("draft_box", ss["draft"])
    ss["draft"] = st.text_area("My writing", key="draft_box", height=200)
    issues = spelling.check(ss["draft"]) if ss["draft"] else []
    if issues:
        st.markdown("**✏️ Spelling help**")
        for j, (w, sug) in enumerate(issues[:8]):
            cols = st.columns([2] + [1] * max(1, len(sug)))
            cols[0].markdown(f"**{w}**")
            for c, sgt in zip(cols[1:], sug):
                if c.button(sgt, key=f"fix_{j}_{sgt}"):
                    ss["draft"] = spelling.apply_fix(ss["draft"], w, sgt)
                    ss["draft_box"] = ss["draft"]
                    store.add_struggle_words(ss["profile"], [sgt], "My writing")
                    st.rerun()
    elif ss["draft"]:
        st.success("No spelling problems found ✓")
    c1, c2, c3 = st.columns(3)
    if c1.button("✨ Tidy capitals & full stops", use_container_width=True) and ss["draft"]:
        ss["draft"] = spelling.tidy(ss["draft"]); ss["draft_box"] = ss["draft"]; st.rerun()
    with c2:
        if ss["draft"]:
            C.listen_button(ss["draft"], "wr_listen", "🔊 Read it back", rate=settings().get("rate", 1.0))
    c3.download_button("⬇️ Save", ss["draft"] or "", file_name="my_writing.txt", use_container_width=True)
    if st.button("🗑 Clear"):
        ss["draft"] = ""; ss["draft_box"] = ""; st.rerun()


# ======================================================================= PROGRESS
def progress_page():
    need_profile()
    ss = st.session_state
    name = ss["profile"]
    ev, p = events()
    st.title(f"📊 {name}'s progress")
    s = report.summary(ev)
    c = st.columns(4)
    c[0].metric("Speed now", f"{s['recent_wpm'] or '–'} wpm", None if not s["first_wpm"] or not s["recent_wpm"] else f"{s['recent_wpm'] - s['first_wpm']:+.0f} since start")
    c[1].metric("Quiz average", f"{s['quiz_avg'] if s['quiz_avg'] is not None else '–'}%")
    c[2].metric("Words read", s["words"])
    c[3].metric("🔥 Streak", f"{s['streak']} day" + ("" if s['streak'] == 1 else "s"))

    goal = p.get("daily_goal", 10)
    ng = st.slider("🎯 Daily goal (minutes)", 5, 60, goal, 5)
    if ng != goal:
        store.set_goal(name, ng); st.rerun()

    mastered = sum(1 for _, e in store.struggle_words(name, True) if e.get("mastered"))
    got = {b[0] for b in progress.earned_badges(ev, mastered, goal)}
    st.markdown("### 🏅 Badges")
    cols = st.columns(5)
    for i, (bid, icon, title, desc) in enumerate(progress.BADGES):
        on = bid in got
        cols[i % 5].markdown(f"<div class='card' style='text-align:center;opacity:{1 if on else .35}'>"
                             f"<div style='font-size:40px'>{icon if on else '🔒'}</div><b>{title}</b><br><small>{desc}</small></div>",
                             unsafe_allow_html=True)
    df = store.events_dataframe(name)
    if df.empty:
        st.info("Read something and your charts will appear here.")
    else:
        ch = df[df["kind"] == "chunk"].dropna(subset=["wpm"]) if "wpm" in df else pd.DataFrame()
        if not ch.empty:
            st.markdown("### Reading speed (words per minute)")
            st.line_chart(ch.set_index("time")["wpm"])
        qz = df[df["kind"] == "quiz"] if "kind" in df else pd.DataFrame()
        if not qz.empty:
            st.markdown("### Quiz scores (%)")
            st.line_chart((qz.set_index("time")["score"] * 100))
        mins = pd.Series(progress.minutes_by_day(ev)).sort_index()
        st.markdown("### Minutes per day")
        st.bar_chart(mins)

    st.markdown("### 📤 Share with a teacher or parent")
    st.download_button("⬇️ Download report (opens in any browser)", report.html_report(p, brand()["app_name"]),
                       file_name=f"{name}_reading_report.html", mime="text/html", type="primary", use_container_width=True)
    if not df.empty:
        st.download_button("⬇️ Download all data (CSV)", df.to_csv(index=False), file_name=f"{name}_reading_data.csv",
                           mime="text/csv", use_container_width=True)


# ======================================================================= SETTINGS
def settings_page():
    need_profile()
    ss = st.session_state
    st.title("⚙️ Settings")
    _look_controls(compact=False)
    s = settings()
    s["rate"] = st.slider("Voice speed", 0.5, 1.8, float(s.get("rate", 1.0)), 0.05)
    if st.button("💾 Save", type="primary"):
        save_settings(); st.toast("Saved ✓")
    if brand().get("show_llm_settings", True):
        with st.expander("🤖 AI helper (optional)"):
            st.markdown("The app works fully without AI. With a free key from Groq or Google Gemini, "
                        "simplifying and quiz questions get smarter. The key is used only for this session.")
            ss["llm_provider"] = st.selectbox("Provider", list(PROVIDERS))
            ss["llm_key"] = st.text_input("API key", type="password", value=ss.get("llm_key", ""))
    with st.expander("🔒 Privacy"):
        st.markdown("""- Profiles and progress are saved in a file inside this app, not in any account. On a shared online demo,
other people using the same link could see profile names, so use a first name or nickname.
- Read-aloud and voice typing use your browser's built-in speech features. Some browsers (like Chrome) send voice to their own speech service.
- Tapping a word looks up its meaning on the free dictionaryapi.dev service (just the word is sent).
- The optional AI helper sends the text you simplify to the AI provider you choose.
- Photos are read on the app server and not stored.""")
    with st.expander("🗑 Delete my profile"):
        if st.button(f"Delete {ss['profile']} and all their progress"):
            store.delete_profile(ss["profile"]); ss["profile"] = None; st.rerun()
