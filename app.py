"""Adaptive Reader: Streamlit entry point (navigation only; screens in ui/, logic in core/)."""
import streamlit as st

from core.config import brand
from ui import pages as P
from ui.state import init, settings
from ui.style import apply

B = brand()
st.set_page_config(page_title=B["app_name"], page_icon=B["icon"], layout="centered", initial_sidebar_state="auto")
init()
apply(settings())

F = B.get("features", {})
NAV = {
    "home": st.Page(P.home, title="Home", icon="🏠", default=True),
    "read": st.Page(P.read, title="Read", icon="📖", url_path="read"),
}
if F.get("library", True):
    NAV["library"] = st.Page(P.library_page, title="Library", icon="📚", url_path="library")
NAV["practice"] = st.Page(P.practice, title="Word practice", icon="🔤", url_path="practice")
if F.get("homework", True):
    NAV["homework"] = st.Page(P.homework_page, title="Homework", icon="📝", url_path="homework")
if F.get("writing", True):
    NAV["write"] = st.Page(P.write, title="Speak & write", icon="✍️", url_path="write")
NAV["progress"] = st.Page(P.progress_page, title="Progress", icon="📊", url_path="progress")
NAV["settings"] = st.Page(P.settings_page, title="Settings", icon="⚙️", url_path="settings")
P.NAV.update(NAV)

with st.sidebar:
    st.markdown(f"## {B['icon']} {B['app_name']}")
    if st.session_state.get("profile"):
        st.markdown(f"🙂 **{st.session_state['profile']}**")

page = st.navigation(list(NAV.values()))
if page.title == "Read":
    P.quiz_feedback()
page.run()
