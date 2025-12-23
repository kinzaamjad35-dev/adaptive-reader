"""Display helpers: dyslexia-friendly themes, bionic bolding and the read-aloud HTML component."""
import html
import json
import re

# Defaults follow the British Dyslexia Association Dyslexia Style Guide: cream/soft pastel
# backgrounds instead of white, dark (not pure black) text, sans-serif fonts, 1.5+ line spacing.
THEMES = {
    "Cream (BDA)":        {"bg": "#FAF6E9", "fg": "#2B2B2B", "hl": "#FFE08A", "accent": "#2F5D8A"},
    "Soft yellow":        {"bg": "#FFF8C6", "fg": "#2B2B2B", "hl": "#9FD3FF", "accent": "#3D5A80"},
    "Pale blue":          {"bg": "#E3EEF9", "fg": "#1F2A36", "hl": "#FFE08A", "accent": "#2F5D8A"},
    "Mint green":         {"bg": "#E6F4EA", "fg": "#20302A", "hl": "#FFE08A", "accent": "#2E6B4F"},
    "Peach":              {"bg": "#FDEBDD", "fg": "#2E2622", "hl": "#B9E0FF", "accent": "#8A4B2F"},
    "Lilac":              {"bg": "#EFE7F6", "fg": "#2A2433", "hl": "#FFE08A", "accent": "#5B3F7A"},
    "Dark (low glare)":   {"bg": "#1E1F22", "fg": "#E8E3D3", "hl": "#5A4A00", "accent": "#9CC3FF"},
    "High contrast":      {"bg": "#000000", "fg": "#FFFF00", "hl": "#0050FF", "accent": "#FFFFFF"},
}

FONTS = {
    "Lexend": "'Lexend', 'Verdana', sans-serif",
    "OpenDyslexic": "'OpenDyslexic', 'Comic Sans MS', sans-serif",
    "Atkinson Hyperlegible": "'Atkinson Hyperlegible', 'Verdana', sans-serif",
    "Verdana": "Verdana, sans-serif",
    "Arial": "Arial, sans-serif",
}

FONT_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">'
    '<link href="https://fonts.cdnfonts.com/css/opendyslexic" rel="stylesheet">'
)

TOKEN_RE = re.compile(r"\S+|\s+")


def bionic_word(word: str) -> str:
    """Bold the first ~half of the letters of a word (bionic-style reading aid). Returns HTML."""
    m = re.match(r"^([^A-Za-z0-9]*)([A-Za-z0-9'’-]+)(.*)$", word)
    if not m:
        return html.escape(word)
    pre, core, post = m.groups()
    n = len(core)
    k = 1 if n <= 3 else (n + 1) // 2
    return f"{html.escape(pre)}<b>{html.escape(core[:k])}</b>{html.escape(core[k:])}{html.escape(post)}"


def tokens_with_offsets(text: str):
    """Words with their character offsets (used to sync speech boundary events)."""
    out, pos = [], 0
    for tok in TOKEN_RE.findall(text):
        if not tok.isspace():
            out.append((tok, pos))
        pos += len(tok)
    return out


def tts_mp3(text: str, slow: bool = False) -> bytes:
    """gTTS fallback (free Google Translate voice; needs internet)."""
    import io
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text[:4000], lang="en", slow=slow).write_to_fp(buf)
    return buf.getvalue()
