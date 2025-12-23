"""Smoke tests: onboarding works and every screen renders without errors."""
import os
import pytest
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv("ADAPTIVE_READER_DATA", str(tmp_path / "p.json"))
    monkeypatch.setenv("AR_ROOT", ROOT)
    import core.store
    monkeypatch.setattr(core.store, "DATA_PATH", str(tmp_path / "p.json"))


def test_onboarding():
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60)
    at.run()
    assert not at.exception
    at.text_input[0].input("Testy")
    at.button[0].click()
    at.run()
    assert not at.exception
    assert "Hi Testy" in at.title[0].value


def page_script(page_name, text):
    import os, sys
    sys.path.insert(0, os.environ["AR_ROOT"])
    import streamlit as st
    from core import store
    from ui import pages as P
    from ui.state import init, load_profile
    init()
    if not store.get_profile("Testy"):
        store.create_profile("Testy", 12)
        store.log_event("Testy", {"kind": "chunk", "words": 80, "seconds": 50, "wpm": 96, "title": "t"})
        store.log_event("Testy", {"kind": "quiz", "score": 1.0, "seconds": 0, "title": "t"})
        store.add_struggle_words("Testy", ["enormous", "habitat"], "t")
    if not st.session_state.get("profile"):
        load_profile("Testy")
    if text and not st.session_state.get("text"):
        P.set_text(text, "T")
    getattr(P, page_name)()


def _page(page_name, text=""):
    return page_script


@pytest.mark.parametrize("page", ["home", "read", "library_page", "practice", "homework_page", "write",
                                  "progress_page", "settings_page"])
def test_pages_render(page):
    from core.library import PASSAGES
    at = AppTest.from_function(_page(page, PASSAGES[3]["text"] if page == "read" else ""),
                               default_timeout=60, args=(page, PASSAGES[3]["text"] if page == "read" else ""))
    at.run()
    assert not at.exception, at.exception


def test_simplify_button_on_read():
    from core.library import PASSAGES
    at = AppTest.from_function(_page("read", PASSAGES[9]["text"]), args=("read", PASSAGES[9]["text"]), default_timeout=60)
    at.run()
    btn = [b for b in at.button if "Simplify" in b.label][0]
    btn.click()
    at.run()
    assert not at.exception
    assert at.session_state["simplified_from"]
    assert at.session_state["text"] != at.session_state["simplified_from"]
