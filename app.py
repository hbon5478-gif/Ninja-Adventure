import re
import io
import time
import base64
import urllib.parse
from pathlib import Path
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS

# ---------- Setup ----------
ASSETS = Path(__file__).parent / "assets"
AVATAR = str(ASSETS / "ninja.png")

st.set_page_config(page_title="Ninja Adventure", page_icon=Image.open(AVATAR), layout="wide")
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# একটার quota শেষ হলে পরেরটা চেষ্টা হবে
MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
]

SYSTEM = (
    "You are Ninja Adventure, a brave, friendly and clever ninja AI assistant. "
    "Always reply in the same language the user uses (Bangla or English). "
    "Be helpful, clear and a little adventurous."
)


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


bg = b64(ASSETS / "red_sky.jpg")
logo = b64(ASSETS / "ninja.png")

# শুরিকেন (ঘুরন্ত spinner-এর ছবি)
SHURIKEN_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<path d="M50 2 L61 39 L98 50 L61 61 L50 98 L39 61 L2 50 L39 39 Z" fill="#e63946"/>'
    '<circle cx="50" cy="50" r="9" fill="#0b0d17"/></svg>'
)
SHURIKEN = base64.b64encode(SHURIKEN_SVG.encode()).decode()

/* ---------- Premium animated theme (Updated with High Readability) ---------- */
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Cinzel:wght@600;800&display=swap');

/* Streamlit-er বাড়তি অংশ লুকানো */
#MainMenu, footer, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }

/* Sundor o spshto font color fix */
.stApp, .stApp p, .stApp li, .stApp label, .stApp small, .stApp textarea, .stApp input, .stApp button,
.stApp [data-testid="stCaptionContainer"] {
    font-family: 'Hind Siliguri', 'Noto Sans Bengali', 'Segoe UI', sans-serif;
    color: #ffffff !important;
}

.stApp {
    background-image: linear-gradient(rgba(5,6,15,0.85), rgba(5,6,15,0.95)), url("data:image/jpg;base64,__BG__");
    background-size: cover; background-attachment: fixed; background-position: center;
    animation: bgfade 1.2s ease;
}
@keyframes bgfade { from {opacity:0;} to {opacity:1;} }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(11,13,23,0.98), rgba(22,10,18,0.98));
    border-right: 1px solid rgba(230,57,70,0.6);
    box-shadow: 4px 0 30px rgba(230,57,70,0.15);
}
[data-testid="stSidebar"] img { border-radius: 14px; box-shadow: 0 0 22px rgba(230,57,70,0.35); }

.hero { display:flex; align-items:center; gap:18px; margin: 4px 0 10px 0; }
.hero img.logo {
    width: 84px; height: 84px; border-radius: 50%; object-fit: cover;
    border: 2px solid #e63946;
    animation: floaty 3.5s ease-in-out infinite, glow 2.5s ease-in-out infinite;
}
.side-brand { display:flex; align-items:center; gap:12px; margin: 10px 0 4px 0; }
.side-brand img.logo {
    width: 52px; height: 52px; border-radius: 50%; object-fit: cover;
    border: 2px solid #e63946;
    animation: floaty 3.5s ease-in-out infinite, glow 2.5s ease-in-out infinite;
}
.brand {
    font-family: 'Cinzel', serif; font-weight: 800; letter-spacing: 4px; font-size: 2.6rem; line-height: 1.1;
    background: linear-gradient(90deg, #ff4d5a, #ffb347, #ff4d5a);
    background-size: 200% auto; -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; animation: shimmer 4s linear infinite;
}
.brand.small { font-size: 1.25rem; letter-spacing: 2px; }
.tagline { color: #d0d0e0; letter-spacing: 3px; font-size: 0.82rem; opacity: 0.9; text-transform: uppercase; font-weight: 500; }
@keyframes shimmer { to { background-position: 200% center; } }
@keyframes floaty { 0%,100% { transform: translateY(0px); } 50% { transform: translateY(-7px); } }
@keyframes glow {
    0%,100% { box-shadow: 0 0 10px rgba(230,57,70,0.4), 0 0 24px rgba(230,57,70,0.2); }
    50% { box-shadow: 0 0 22px rgba(230,57,70,0.9), 0 0 48px rgba(230,57,70,0.45); }
}

.u-mark, .a-mark { display: none; }
[data-testid="stElementContainer"]:has(.u-mark), [data-testid="stElementContainer"]:has(.a-mark),
.element-container:has(.u-mark), .element-container:has(.a-mark) { display: none; }

[data-testid="stChatMessage"] {
    backdrop-filter: blur(12px); border-radius: 16px;
    animation: slidein 0.5s ease both;
    padding: 14px 18px;
}

/* Chat-er sob text-e sadha r high-contrast fix */
[data-testid="stChatMessage"] *,
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    font-size: 1.1rem !important;
    line-height: 1.75 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    opacity: 1 !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.95);
}

/* User Chat Bubble - Darker Red for Readability */
[data-testid="stChatMessage"]:has(.u-mark) {
    flex-direction: row-reverse;
    margin-left: 18%;
    background: linear-gradient(135deg, rgba(150,20,30,0.95), rgba(60,8,15,0.95)) !important;
    border: 1px solid rgba(255,90,105,0.7);
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
}

/* Ninja AI Chat Bubble - Deep Dark Blue/Black */
[data-testid="stChatMessage"]:has(.a-mark) {
    margin-right: 10%;
    background: rgba(12, 15, 28, 0.96) !important;
    border: 1px solid rgba(255, 179, 71, 0.4);
    border-left: 5px solid #ffb347;
    box-shadow: 0 4px 22px rgba(0,0,0,0.7);
}

@keyframes slidein { from { opacity:0; transform: translateY(18px); } to { opacity:1; transform: translateY(0); } }

.thinking { display:flex; align-items:center; gap:12px; color:#ffb347; font-weight:600; letter-spacing:1px; padding:6px 0; }
.thinking img { width: 30px; height: 30px; animation: spin 0.9s linear infinite; filter: drop-shadow(0 0 6px rgba(230,57,70,0.9)); }
@keyframes spin { to { transform: rotate(360deg); } }

[data-testid="stChatInput"] { animation: pulse 3s ease-in-out infinite; border-radius: 14px; }
@keyframes pulse {
    0%,100% { box-shadow: 0 0 6px rgba(230,57,70,0.35); }
    50% { box-shadow: 0 0 20px rgba(230,57,70,0.8); }
}
.stButton button { border: 1px solid #e63946; background: transparent; color: #f1f1f1; transition: all 0.3s ease; }
.stButton button:hover { background: #e63946; color: white; transform: translateY(-2px); box-shadow: 0 6px 18px rgba(230,57,70,0.5); }
.embers { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.ember { position: absolute; bottom: -12px; border-radius: 50%; background: #ff5a36; box-shadow: 0 0 10px #ff5a36; opacity: 0; animation: rise linear infinite; }
@keyframes rise {
    0% { transform: translateY(0) translateX(0); opacity: 0; }
    10% { opacity: 0.85; }
    100% { transform: translateY(-105vh) translateX(45px); opacity: 0; }
}
</style>
"""
st.markdown(CSS.replace("__BG__", bg), unsafe_allow_html=True)

embers = ""
for i in range(18):
    left = (i * 6 + 3) % 100
    size = 3 + (i % 3) * 2
    dur = 8 + (i % 5) * 2
    delay = round((i * 0.9) % 9, 1)
    embers += f'<div class="ember" style="left:{left}%;width:{size}px;height:{size}px;animation-duration:{dur}s;animation-delay:{delay}s;"></div>'
st.markdown(f'<div class="embers">{embers}</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# ---------- Sidebar ----------
with st.sidebar:
    st.image(str(ASSETS / "r (2).png"), use_container_width=True)
    st.markdown(
        f'<div class="side-brand"><img class="logo" src="data:image/png;base64,{logo}">'
        f'<div><div class="brand small">NINJA ADVENTURE</div></div></div>',
        unsafe_allow_html=True,
    )
    st.caption("তোমার ছায়া-যোদ্ধা AI সঙ্গী")
    uploaded = st.file_uploader("ছবি / PDF / TXT আপলোড করো", type=["png", "jpg", "jpeg", "webp", "pdf", "txt"])
    voice_reply = st.toggle("🔊 Voice response", value=False)
    st.caption("ছবি আঁকতে লেখো: /image একটা নিনজা পাহাড়ে দাঁড়িয়ে আছে")
    if st.button("🗑️ Chat মুছো"):
        st.session_state.messages = []
        st.rerun()

# ---------- Hero title ----------
st.markdown(
    f'<div class="hero"><img class="logo" src="data:image/png;base64,{logo}">'
    f'<div><div class="brand">NINJA ADVENTURE</div>'
    f'<div class="tagline">Shadow Warrior AI</div></div></div>',
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def generate_with_retry(contents, config=None):
    last_err = None
    for model in MODELS:
        for attempt in range(2):
            try:
                return client.models.generate_content(model=model, contents=contents, config=config)
            except Exception as e:
                last_err = e
                msg = str(e)
                if "503" in msg or "UNAVAILABLE" in msg:
                    time.sleep(2 * (attempt + 1))
                    continue
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "404" in msg or "NOT_FOUND" in msg:
                    break
                raise
    raise last_err


def friendly_error(e):
    msg = str(e)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        return "⚠️ আজকের ফ্রি শক্তি শেষ হয়ে গেছে 🥷 কিছুক্ষণ পরে আবার এসো, অথবা নতুন API key ব্যবহার করো।"
    if "503" in msg or "UNAVAILABLE" in msg:
        return "⚠️ সার্ভার এখন ব্যস্ত। একটু পরে আবার চেষ্টা করো।"
    return f"⚠️ সমস্যা হয়েছে: {e}"


def thinking_html(text):
    return f'<div class="thinking"><img src="data:image/svg+xml;base64,{SHURIKEN}"><span>{text}</span></div>'


def mark(role):
    cls = "u-mark" if role == "user" else "a-mark"
    st.markdown(f'<span class="{cls}"></span>', unsafe_allow_html=True)


def transcribe(audio_bytes):
    res = generate_with_retry(
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            "Transcribe this audio exactly. Output only the transcript text.",
        ],
    )
    return res.text.strip()


def speak(text):
    clean = re.sub(r"[*#`_>\-]", "", text)[:600]
    lang = "bn" if re.search(r"[\u0980-\u09FF]", clean) else "en"
    buf = io.BytesIO()
    gTTS(clean, lang=lang).write_to_fp(buf)
    return buf.getvalue()


def make_image_url(prompt):
    styled = prompt + ", ninja theme, dark cinematic, japanese art style"
    return "https://image.pollinations.ai/prompt/" + urllib.parse.quote(styled) + "?width=768&height=768&nologo=true"


def build_history():
    contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["text"])]))
    return contents


def avatar_for(role):
    return AVATAR if role == "assistant" else "🧑"


def typewriter(text):
    for token in re.split(r"(\s+)", text):
        yield token
        time.sleep(0.015)


# ---------- Show old messages ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=avatar_for(m["role"])):
        mark(m["role"])
        st.markdown(m["text"])
        if m.get("image"):
            st.image(m["image"])

# ---------- Input ----------
typed = st.chat_input("Ninja-কে কিছু জিজ্ঞেস করো...")
st.caption("🎤 Voice দিয়ে বলো")
audio = st.audio_input("Voice", label_visibility="collapsed")

prompt = typed
if audio is not None and audio.file_id != st.session_state.last_audio:
    st.session_state.last_audio = audio.file_id
    holder = st.empty()
    holder.markdown(thinking_html("তোমার কথা শুনছি..."), unsafe_allow_html=True)
    try:
        prompt = transcribe(audio.getvalue())
    except Exception as e:
        st.error(friendly_error(e))
    finally:
        holder.empty()

# ---------- Handle new message ----------
if prompt:
    with st.chat_message("user", avatar=avatar_for("user")):
        mark("user")
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATAR):
        mark("assistant")
        reply_text, reply_image = "", None

        if prompt.lower().startswith("/image"):
            img_prompt = prompt[6:].strip() or "a ninja adventure"
            reply_image = make_image_url(img_prompt)
            reply_text = f"এই নাও তোমার ছবি: **{img_prompt}** 🥷"
            st.markdown(reply_text)
            st.image(reply_image)
        else:
            parts = []
            if uploaded is not None:
                if uploaded.type == "text/plain":
                    parts.append(types.Part(text="Attached file content:\n" + uploaded.getvalue().decode("utf-8", errors="ignore")))
                else:
                    parts.append(types.Part.from_bytes(data=uploaded.getvalue(), mime_type=uploaded.type))
            parts.append(types.Part(text=prompt))

            contents = build_history() + [types.Content(role="user", parts=parts)]
            holder = st.empty()
            holder.markdown(thinking_html("ছায়ার মধ্যে ভাবছি..."), unsafe_allow_html=True)
            try:
                res = generate_with_retry(
                    contents=contents,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM),
                )
                reply_text = res.text or ""
            except Exception as e:
                reply_text = friendly_error(e)
            finally:
                holder.empty()
            st.write_stream(typewriter(reply_text))

        if voice_reply and reply_text and not reply_image and not reply_text.startswith("⚠️"):
            try:
                st.audio(speak(reply_text), format="audio/mp3", autoplay=True)
            except Exception:
                st.caption("Voice তৈরি করা গেল না।")

    st.session_state.messages.append({"role": "user", "text": prompt})
    st.session_state.messages.append({"role": "assistant", "text": reply_text, "image": reply_image})