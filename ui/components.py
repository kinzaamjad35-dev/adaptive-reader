"""Browser-side components (Streamlit components v2): reader, speaker, dictation.
These run in the learner's browser: speech uses the Web Speech API, so no audio leaves the device
except to the browser's own speech service."""
import html
import json
import re

import streamlit as st

from core.display import FONTS, THEMES, TOKEN_RE, bionic_word
from core.readability import sentences

# ---------------------------------------------------------------- Reader
READER_CSS = """
.ar { --bg:#FAF6E9; --fg:#2B2B2B; --hl:#FFE08A; --ac:#2F5D8A; background:var(--bg); color:var(--fg);
      border-radius:14px; border:2px solid var(--ac); position:relative; }
.ar .bar { position:sticky; top:0; background:var(--bg); padding:10px; display:flex; flex-wrap:wrap; gap:8px;
           align-items:center; border-bottom:2px solid var(--ac); border-radius:14px 14px 0 0; z-index:3; }
.ar button { font-family:inherit; font-size:19px; padding:10px 16px; border-radius:12px; border:2px solid var(--ac);
             background:var(--bg); color:var(--fg); cursor:pointer; min-height:52px; min-width:52px; }
.ar button.big { background:var(--ac); color:var(--bg); font-weight:700; }
.ar button:focus-visible, .ar .w:focus-visible { outline:4px solid var(--ac); outline-offset:2px; }
.ar label { font-size:17px; display:flex; gap:6px; align-items:center; }
.ar input[type=range] { width:120px; height:28px; }
.ar .txt { padding:18px 20px 30px; max-width:70ch; text-align:left; min-height:120px; }
.ar .w { border-radius:5px; cursor:pointer; padding:0 1px; }
.ar .w.on { background:var(--hl); box-shadow:0 0 0 2px var(--hl); }
.ar .w.ok { border-bottom:3px solid #4CAF50; }
.ar .w.miss { border-bottom:3px dotted #E07A00; }
.ar .sent { display:none; }
.ar.focus .sent.cur { display:inline; }
.ar.focus .txt { min-height:180px; display:flex; align-items:center; }
.ar:not(.focus) .sent { display:inline; }
.ar:not(.focus) .sent.dim { opacity:1; }
.ar .ruler { position:absolute; left:0; right:0; pointer-events:none; background:var(--hl); opacity:.28; display:none; }
.ar .def { margin:0 12px 12px; padding:12px 14px; border:2px solid var(--ac); border-radius:12px; font-size:18px; display:none; }
.ar .msg { font-size:16px; opacity:.85; flex-basis:100%; }
.ar .foot { padding:10px; display:flex; gap:10px; flex-wrap:wrap; border-top:2px solid var(--ac); }
"""

READER_JS = r"""
export default function(component) {
  const { data, parentElement, setTriggerValue } = component;
  const sig = data.sig;
  if (parentElement.__sig === sig) return;
  parentElement.__sig = sig;
  if (parentElement.__cleanup) parentElement.__cleanup();
  let host = parentElement.querySelector('.ar-host');
  if (!host) { host = document.createElement('div'); host.className = 'ar-host'; parentElement.appendChild(host); }
  host.innerHTML = data.html;
  const root = host.querySelector('.ar');
  for (const [k,v] of Object.entries(data.vars)) root.style.setProperty(k, v);
  const txt = root.querySelector('.txt');
  Object.assign(txt.style, data.textStyle);
  const synth = window.speechSynthesis;
  const words = [...root.querySelectorAll('.w')];
  const sents = [...root.querySelectorAll('.sent')];
  const starts = words.map(w => +w.dataset.s);
  const T = data.text;
  const $ = s => root.querySelector(s);
  const rate = $('.rate'), rv = $('.rv'), msg = $('.msg'), vsel = $('.voice'), def = $('.def'), ruler = $('.ruler');
  let cur = -1, playing = false, paused = false, voices = [], timer = null, sIdx = 0;
  const t0 = Date.now();
  const stats = { replays: 0, lookups: [], replayed: [], misread: [], listens: 0 };
  const focus = data.mode === 'focus';
  if (focus) root.classList.add('focus');
  if (data.ruler && !focus) ruler.style.display = 'block';
  rv.textContent = (+rate.value).toFixed(2) + '×';
  function beep(f=660, d=0.12) { try { const c = new (window.AudioContext||window.webkitAudioContext)(); const o = c.createOscillator(), g = c.createGain();
    o.frequency.value = f; g.gain.value = 0.08; o.connect(g); g.connect(c.destination); o.start(); o.stop(c.currentTime + d); } catch(e) {} }
  function loadVoices() {
    if (!synth) return;
    voices = synth.getVoices().filter(v => v.lang.toLowerCase().startsWith('en'));
    vsel.innerHTML = voices.map((v,i) => `<option value="${i}">${v.name.slice(0,28)}</option>`).join('');
  }
  if (!synth) msg.textContent = 'Your browser cannot speak. Use the "Audio file" button under the reader.';
  else { loadVoices(); synth.onvoiceschanged = loadVoices; }
  function moveRuler(w) { const r = w.getBoundingClientRect(), p = root.getBoundingClientRect();
    ruler.style.top = (r.top - p.top - 3) + 'px'; ruler.style.height = (r.height + 6) + 'px'; }
  function mark(i) {
    if (cur >= 0 && words[cur]) words[cur].classList.remove('on');
    cur = i; const w = words[i]; if (!w) return;
    w.classList.add('on');
    if (focus) showSent(+w.dataset.k, false);
    const r = w.getBoundingClientRect();
    if (r.bottom > window.innerHeight - 10 || r.top < 0) w.scrollIntoView({block:'center', behavior:'smooth'});
    if (data.ruler && !focus) moveRuler(w);
  }
  function showSent(k, speak) {
    sIdx = Math.max(0, Math.min(sents.length - 1, k));
    sents.forEach((s,i) => s.classList.toggle('cur', i === sIdx));
    $('.pos') && ($('.pos').textContent = `${sIdx+1} / ${sents.length}`);
    if (speak) { const first = words.findIndex(w => +w.dataset.k === sIdx); speakRange(first, sentEnd(sIdx)); }
  }
  function sentEnd(k) { let e = words.length; for (let i = 0; i < words.length; i++) if (+words[i].dataset.k > k) { e = i; break; } return e; }
  function idxAt(ch) { let lo=0, hi=starts.length-1, a=0; while(lo<=hi){const m=(lo+hi)>>1; if(starts[m]<=ch){a=m;lo=m+1}else hi=m-1} return a; }
  function stopAll() { if (synth) synth.cancel(); playing = false; paused = false; clearInterval(timer); $('.play').textContent = '▶ Listen'; }
  function speakRange(i, end) {
    if (!synth || i < 0) return;
    synth.cancel(); clearInterval(timer);
    const a = starts[i] || 0, b = end < words.length ? starts[end] : T.length;
    const u = new SpeechSynthesisUtterance(T.slice(a, b));
    u.rate = +rate.value; u.lang = 'en-US';
    if (voices[vsel.value]) u.voice = voices[vsel.value];
    let gotB = false, k = i;
    u.onboundary = e => { if (e.name && e.name !== 'word') return; gotB = true; mark(idxAt(a + e.charIndex)); };
    u.onend = () => { playing = false; paused = false; clearInterval(timer); $('.play').textContent = '▶ Listen'; };
    timer = setInterval(() => { if (!gotB && !paused && k < end) mark(k++); }, 60000 / (165 * u.rate));
    stats.listens++;
    synth.speak(u); playing = true; paused = false; $('.play').textContent = '⏸ Pause';
  }
  $('.play').onclick = () => {
    if (!synth) return;
    if (playing && !paused) { synth.pause(); paused = true; $('.play').textContent = '▶ Resume'; }
    else if (paused) { synth.resume(); paused = false; $('.play').textContent = '⏸ Pause'; }
    else if (focus) showSent(sIdx, true);
    else speakRange(cur > 0 && cur < words.length - 1 ? cur : 0, words.length);
  };
  $('.stop').onclick = () => { stopAll(); if (cur >= 0) words[cur].classList.remove('on'); cur = -1; };
  $('.again').onclick = () => {
    stats.replays++;
    let i = Math.max(cur, 0);
    while (i > 0 && +words[i-1].dataset.k === +words[Math.max(cur,0)].dataset.k) i--;
    const k = +words[i].dataset.k;
    words.filter(w => +w.dataset.k === k && w.dataset.w.length > 6).forEach(w => stats.replayed.push(w.dataset.w));
    speakRange(i, sentEnd(k));
  };
  if (focus) {
    $('.prev').onclick = () => { stopAll(); showSent(sIdx - 1, data.autoread); };
    $('.next').onclick = () => { stopAll(); showSent(sIdx + 1, data.autoread); };
    showSent(0, false);
  }
  rate.oninput = () => { rv.textContent = (+rate.value).toFixed(2) + '×'; };
  // Tap a word: hear it + see meaning
  async function lookup(w) {
    const word = w.dataset.w; if (!word) return;
    stats.lookups.push(word);
    if (synth) { stopAll(); const u = new SpeechSynthesisUtterance(word); u.rate = 0.8; synth.speak(u); }
    def.style.display = 'block'; def.innerHTML = `<b>${word}</b> …`;
    const strip = h => { const d = document.createElement('div'); d.innerHTML = h; return d.textContent.trim(); };
    let out = '';
    try {
      const r = await fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + encodeURIComponent(word.toLowerCase()));
      const j = await r.json(); if (!Array.isArray(j)) throw 0;
      out = `<b style="font-size:1.3em">${word}</b> ${j[0].phonetic || ''}<br>` +
            j[0].meanings.slice(0,2).map(m => `<i>${m.partOfSpeech}</i>: ${m.definitions[0].definition}`).join('<br>');
    } catch(e) {
      try {  // fallback: Wiktionary (free, CORS-enabled)
        const r = await fetch('https://en.wiktionary.org/api/rest_v1/page/definition/' + encodeURIComponent(word.toLowerCase()));
        const j = await r.json(); const en = (j.en || []).slice(0,2);
        const lines = en.map(m => { const d = (m.definitions || []).map(x => strip(x.definition)).find(Boolean); return d ? `<i>${m.partOfSpeech.toLowerCase()}</i>: ${d}` : ''; }).filter(Boolean);
        if (lines.length) out = `<b style="font-size:1.3em">${word}</b><br>` + lines.join('<br>');
      } catch(e2) {}
    }
    def.innerHTML = out || `<b>${word}</b>: no meaning found.`;
    const cl = document.createElement('button'); cl.textContent = '✕ Close'; cl.style.marginTop = '8px';
    cl.onclick = () => def.style.display = 'none'; def.appendChild(document.createElement('br')); def.appendChild(cl);
  }
  words.forEach((w,i) => {
    w.addEventListener('click', () => lookup(w));
    w.addEventListener('keydown', e => { if (e.key === 'Enter') lookup(w); if (e.key === ' ') { e.preventDefault(); speakRange(i, words.length); } });
    if (data.ruler && !focus) w.addEventListener('mouseenter', () => moveRuler(w));
  });
  // Read-along: learner reads aloud, we follow and gently flag skipped words
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null, pos = 0;
  const norm = s => s.toLowerCase().replace(/’/g, "'").replace(/[^a-z0-9']/g, '');
  function sim(a, b) { a = norm(a); b = norm(b); if (!a || !b) return false; if (a === b) return true;
    if (a.length < 4) return false; let m = 0; for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] === b[i]) m++;
    return m / Math.max(a.length, b.length) >= 0.75; }
  const mic = $('.mic');
  if (mic) mic.onclick = () => {
    if (!SR) { msg.textContent = 'Read-along needs Chrome or Edge (speech recognition).'; return; }
    if (rec) { rec.stop(); rec = null; mic.textContent = '🎤 Read to me'; return; }
    stopAll();
    rec = new SR(); rec.lang = 'en-US'; rec.continuous = true; rec.interimResults = true;
    let done = 0;
    rec.onresult = e => {
      const said = [...e.results].map(r => r[0].transcript).join(' ').split(/\s+/).filter(Boolean);
      for (let j = done; j < said.length; j++) {
        for (let k = 0; k <= 3; k++) {
          const w = words[pos + k];
          if (w && sim(w.dataset.w || w.textContent, said[j])) {
            for (let m = pos; m < pos + k; m++) { words[m].classList.add('miss'); stats.misread.push(words[m].dataset.w); }
            w.classList.add('ok'); mark(pos + k); pos += k + 1; break;
          }
        }
      }
      done = e.results[e.results.length-1].isFinal ? said.length : Math.max(done, said.length - 2);
      if (pos >= words.length) { rec.stop(); rec = null; mic.textContent = '🎤 Read to me'; beep(880); msg.textContent = '🎉 Great reading!'; }
    };
    rec.onerror = ev => { msg.textContent = 'Microphone: ' + ev.error + '. Check that the browser may use your mic.'; };
    rec.onend = () => { if (rec) try { rec.start(); } catch(e) {} };
    stats.mic = true; rec.start(); mic.textContent = '⏹ Stop mic'; msg.textContent = 'Start reading out loud. Green = heard ✓, orange = check this word.';
  };
  $('.done').onclick = () => {
    stopAll(); if (rec) { rec.stop(); rec = null; }
    beep(880);
    setTriggerValue('done', { seconds: (Date.now() - t0) / 1000, words: words.length, replays: stats.replays,
      lookups: stats.lookups, replayed: stats.replayed, misread: [...new Set(stats.misread)], listens: stats.listens, mic: !!stats.mic,
      rate: +rate.value, nonce: Date.now() });
  };
  parentElement.__cleanup = () => { if (synth) synth.cancel(); clearInterval(timer); if (rec) { const r = rec; rec = null; r.stop(); } };
  if (data.autoplay && synth) setTimeout(() => focus ? showSent(0, true) : speakRange(0, words.length), 300);
}
"""

_reader = st.components.v2.component("adaptive_reader", css=READER_CSS, js=READER_JS)


def _build_body(text: str, bionic: bool):
    parts, idx, pos = [], 0, 0
    sent_list = sentences(text) or [text]
    # map character offsets to sentence index
    bounds, search = [], 0
    for s in sent_list:
        i = text.find(s, search)
        i = search if i < 0 else i
        bounds.append(i)
        search = i + len(s)
    k_of = lambda p: max([k for k, b in enumerate(bounds) if b <= p] or [0])
    cur_k, open_sent = -1, False
    for tok in TOKEN_RE.findall(text):
        if tok.isspace():
            parts.append("<br><br>" if "\n\n" in tok and not open_sent else " ")
        else:
            k = k_of(pos)
            if k != cur_k:
                if open_sent:
                    parts.append("</span> ")
                parts.append(f'<span class="sent" data-k="{k}">')
                cur_k, open_sent = k, True
            inner = bionic_word(tok) if bionic else html.escape(tok)
            clean = re.sub(r"[^A-Za-z0-9'’-]", "", tok)
            parts.append(f'<span class="w" data-s="{pos}" data-k="{k}" data-w="{html.escape(clean)}" tabindex="0">{inner}</span>')
            idx += 1
        pos += len(tok)
    if open_sent:
        parts.append("</span>")
    return "".join(parts)


def reader(text: str, s: dict, key: str, mode: str = "flow", readalong: bool = True, autoplay: bool = False,
           done_label: str = "✅ I finished this part"):
    """Render the reader. Returns the 'done' payload dict on the run after the learner taps finish."""
    theme = THEMES.get(s.get("theme"), THEMES["Cream (BDA)"])
    focus_btns = ('<button class="prev" aria-label="Previous sentence">◀ Back</button>'
                  '<span class="pos" style="font-size:18px"></span>'
                  '<button class="next big" aria-label="Next sentence">Next ▶</button>') if mode == "focus" else ""
    body = f"""<div class="ar" role="region" aria-label="Reader">
<div class="bar" role="toolbar" aria-label="Reading controls">
 <button class="play big" aria-label="Listen">▶ Listen</button>
 <button class="stop" aria-label="Stop">■</button>
 <button class="again" aria-label="Hear this sentence again">↺ Again</button>
 {'<button class="mic" aria-label="Read aloud to the app">🎤 Read to me</button>' if readalong else ''}
 {focus_btns}
 <label>🐢<input class="rate" type="range" min="0.5" max="1.8" step="0.05" value="{s.get('rate', 1.0)}" aria-label="Voice speed">🐇<span class="rv"></span></label>
 <label>🗣<select class="voice" aria-label="Voice" style="font-size:16px;max-width:160px"></select></label>
 <span class="msg" aria-live="polite">Tip: tap any word to hear it and see what it means.</span>
</div>
<div class="ruler"></div>
<div class="txt" lang="en">{_build_body(text, s.get('bionic', False))}</div>
<div class="def" aria-live="polite"></div>
<div class="foot"><button class="done big">{html.escape(done_label)}</button></div>
</div>"""
    data = {
        "html": body, "text": text, "mode": mode, "ruler": bool(s.get("ruler")), "autoplay": autoplay,
        "autoread": bool(s.get("autoread", True)),
        "vars": {"--bg": theme["bg"], "--fg": theme["fg"], "--hl": theme["hl"], "--ac": theme["accent"]},
        "textStyle": {"fontFamily": FONTS.get(s.get("font"), FONTS["Lexend"]), "fontSize": f"{s.get('size', 22)}px",
                      "letterSpacing": f"{s.get('letter', 0.05)}em", "wordSpacing": f"{s.get('word', 0.16)}em",
                      "lineHeight": str(s.get("line", 1.6))},
    }
    data["sig"] = str(hash(json.dumps(data, sort_keys=True)))
    res = _reader(data=data, key=key, on_done_change=lambda: None)
    return getattr(res, "done", None)


# ---------------------------------------------------------------- Speaker (audio cues / say a phrase)
SPEAK_JS = r"""
export default function(component) {
  const { data, parentElement } = component;
  if (parentElement.__n === data.nonce) return; parentElement.__n = data.nonce;
  const synth = window.speechSynthesis;
  if (data.beep) { try { const c = new (window.AudioContext||window.webkitAudioContext)(); const o = c.createOscillator(), g = c.createGain();
      o.frequency.value = data.beep; g.gain.value = 0.08; o.connect(g); g.connect(c.destination); o.start(); o.stop(c.currentTime + 0.15); } catch(e) {} }
  if (synth && data.text) { synth.cancel(); const u = new SpeechSynthesisUtterance(data.text); u.rate = data.rate || 0.95; u.lang = 'en-US'; synth.speak(u); }
  if (data.button) {
    parentElement.querySelectorAll('button').forEach(x => x.remove());
    const b = document.createElement('button'); b.textContent = data.button; b.setAttribute('aria-label', data.button);
    b.style.cssText = 'font-size:20px;padding:10px 18px;border-radius:12px;border:2px solid #2F5D8A;background:#FAF6E9;color:#2B2B2B;min-height:52px;cursor:pointer;font-family:inherit';
    b.onclick = () => { if (!synth) return; synth.cancel(); const u = new SpeechSynthesisUtterance(data.say); u.rate = data.rate || 0.9; u.lang='en-US'; synth.speak(u); };
    parentElement.appendChild(b);
  }
}
"""
_speak = st.components.v2.component("ar_speak", js=SPEAK_JS)


def say(text: str, key: str, beep: int = 0, rate: float = 0.95):
    """Speak a phrase once (e.g. feedback 'Well done!') with optional beep."""
    import time
    _speak(data={"text": text, "beep": beep, "rate": rate, "nonce": time.time()}, key=key)


def listen_button(say_text: str, key: str, label: str = "🔊", rate: float = 0.85):
    """A big button that speaks a word/phrase when tapped."""
    _speak(data={"button": label, "say": say_text, "rate": rate, "nonce": say_text + label}, key=key)


# ---------------------------------------------------------------- Dictation (speech to text)
DICT_JS = r"""
export default function(component) {
  const { data, parentElement, setTriggerValue } = component;
  if (parentElement.__init) return; parentElement.__init = true;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const host = document.createElement('div'); parentElement.appendChild(host);
  host.innerHTML = `<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <button class="m" style="font-size:22px;padding:12px 22px;border-radius:14px;border:2px solid #2F5D8A;background:#2F5D8A;color:#FAF6E9;min-height:56px;cursor:pointer;font-family:inherit">🎤 ${data.label}</button>
    <span class="s" aria-live="polite" style="font-size:18px"></span></div>
    <div class="live" style="font-size:20px;margin-top:8px;min-height:28px;opacity:.8"></div>`;
  const b = host.querySelector('.m'), s = host.querySelector('.s'), live = host.querySelector('.live');
  if (!SR) { s.textContent = 'Voice typing needs Chrome or Edge. You can type instead.'; b.disabled = true; return; }
  let rec = null, finalText = '';
  b.onclick = () => {
    if (rec) { rec.stop(); return; }
    rec = new SR(); rec.lang = 'en-US'; rec.interimResults = true; rec.continuous = true; finalText = '';
    rec.onresult = e => { let interim = ''; finalText = '';
      for (const r of e.results) { if (r.isFinal) finalText += r[0].transcript + ' '; else interim += r[0].transcript; }
      live.textContent = finalText + interim; };
    rec.onerror = ev => { s.textContent = 'Mic problem: ' + ev.error; };
    rec.onend = () => { rec = null; b.textContent = '🎤 ' + data.label; s.textContent = '';
      const t = (finalText || live.textContent).trim(); if (t) setTriggerValue('text', { text: t, nonce: Date.now() }); };
    rec.start(); b.textContent = '⏹ Stop'; s.textContent = 'Listening… speak now';
  };
}
"""
_dict = st.components.v2.component("ar_dictate", js=DICT_JS)


def dictation(key: str, label: str = "Speak"):
    res = _dict(data={"label": label}, key=key, on_text_change=lambda: None)
    return getattr(res, "text", None)
