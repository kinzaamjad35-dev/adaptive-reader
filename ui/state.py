"""Session helpers shared by pages."""
import streamlit as st

from core import store
from core.config import brand


def init():
    ss = st.session_state
    ss.setdefault("profile", None)
    ss.setdefault("settings", dict(store.DEFAULT_SETTINGS))
    ss.setdefault("text", "")
    ss.setdefault("title", "My text")
    ss.setdefault("chunks", [])
    ss.setdefault("ci", 0)
    ss.setdefault("history", [])
    ss.setdefault("quiz", None)
    ss.setdefault("handled", set())
    b = brand()
    ss["settings"].setdefault("theme", b.get("default_theme", "Cream (BDA)"))


def settings():
    return st.session_state["settings"]


def save_settings():
    if st.session_state.get("profile"):
        store.save_settings(st.session_state["profile"], st.session_state["settings"])


def load_profile(name):
    p = store.get_profile(name)
    if not p:
        return
    st.session_state["profile"] = name
    st.session_state["settings"] = dict(p["settings"])
    st.session_state["history"] = [e for e in p["sessions"] if e.get("kind") == "chunk"][-10:]


def llm():
    """(provider, key) if an AI key is configured in secrets or entered this session, else (None, None)."""
    ss = st.session_state
    if ss.get("llm_key"):
        return ss.get("llm_provider", "Groq"), ss["llm_key"]
    try:
        for prov, k in (("Groq", "GROQ_API_KEY"), ("OpenAI", "OPENAI_API_KEY"), ("Gemini", "GEMINI_API_KEY")):
            if st.secrets.get(k):
                return prov, st.secrets[k]
    except Exception:
        pass
    return None, None


def once(payload, tag):
    """True the first time we see a component payload (triggers can repeat on reruns)."""
    if not payload:
        return False
    k = f"{tag}:{payload.get('nonce')}"
    if k in st.session_state["handled"]:
        return False
    st.session_state["handled"].add(k)
    return True
