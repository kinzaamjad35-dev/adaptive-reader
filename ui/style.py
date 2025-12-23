import streamlit as st

from core.display import FONTS, THEMES

FONT_CSS = ("@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;600;700&family=Atkinson+Hyperlegible:wght@400;700&display=swap');"
            "@import url('https://fonts.cdnfonts.com/css/opendyslexic');")


def apply(settings):
    t = THEMES.get(settings.get("theme"), THEMES["Cream (BDA)"])
    font = FONTS.get(settings.get("font"), FONTS["Lexend"])
    st.markdown(f"""<style>{FONT_CSS}
.stApp, [data-testid="stSidebar"], [data-testid="stHeader"] {{ background:{t['bg']} !important; color:{t['fg']}; }}
.stApp p, .stApp label, .stApp li, .stApp span:not([data-testid='stIconMaterial']), .stApp input, .stApp textarea, .stApp button {{ font-family:{font}; }}
[data-testid='stIconMaterial'] {{ font-family:'Material Symbols Rounded' !important; }}
.stApp p, .stApp li, .stApp label, [data-testid="stMarkdownContainer"] {{ color:{t['fg']}; font-size:19px; line-height:1.6; }}
h1, h2, h3 {{ color:{t['fg']} !important; font-family:{font} !important; }}
.stButton button, .stDownloadButton button, .stFormSubmitButton button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {{
   min-height:54px; font-size:20px !important; border-radius:14px !important; border:2px solid {t['accent']} !important; padding:6px 18px; }}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{ background:{t['accent']} !important; color:{t['bg']} !important; }}
[data-testid='stBaseButton-primary'] p, [data-testid='stBaseButton-primaryFormSubmit'] p {{ color:{t['bg']} !important; }}
.stButton button:focus-visible {{ outline:4px solid {t['accent']} !important; }}
textarea, input {{ font-size:19px !important; }}
[data-testid="stSidebarNav"] a span {{ font-size:20px !important; }}
[data-testid="stSidebarNav"] a {{ min-height:46px; }}
.card {{ border:2px solid {t['accent']}; border-radius:16px; padding:14px 18px; margin:6px 0; }}
.big {{ font-size:28px; font-weight:700; }}
</style>""", unsafe_allow_html=True)
