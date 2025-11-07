import streamlit as st
import os
import re
import time
from llm_advisor import generate_mix_intent_from_folder
from my_component.stem_mixer import mix_and_transition

# --- Filename Label, Icon, Role Lookup ---
STEM_FRIENDLY = {
    "synth": ("Synth", "🎹", "Melody"),
    "pad": ("Pad", "🛋️", "Ambiance"),
    "drums": ("Drums", "🥁", "Rhythm"),
    "strings": ("Strings", "🎻", "Melody"),
    "bass": ("Bass", "🎸", "Bassline"),
    "chimes": ("Chimes", "🔔", "Accent"),
}

# --- Theme Normalization ---
THEME_KEYWORD_MAP = [
    ("boss_combat", ["boss"]),
    ("combat", ["combat", "battle"]),
    ("stealth", ["stealth", "hidden"]),
    ("explore", ["explor", "jungle", "wondrous", "mysterious"]),
]
def get_theme_key(theme_str):
    if not theme_str:
        return None
    s = str(theme_str).lower()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    for key, keywords in THEME_KEYWORD_MAP:
        for keyword in keywords:
            if keyword in s:
                return key
    return None

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = []
if "status" not in st.session_state:
    st.session_state.status = ""
if "current_stem_dicts" not in st.session_state:
    st.session_state.current_stem_dicts = []
if "next_stem_dicts" not in st.session_state:
    st.session_state.next_stem_dicts = []
if "show_details" not in st.session_state:
    st.session_state.show_details = False

st.title("🎵 Game Audio StemMix Live Transition Demo")
themes = ["explore", "stealth", "combat", "boss_combat"]

col1, col2 = st.columns([1, 1], gap="large")

# --- Theme Selectors ---
with col1:
    st.markdown("#### 🎧 Current Theme")
    current_theme = st.selectbox(
        "Theme", themes, key="current_theme_select", index=0, help="Theme currently playing"
    )

with col2:
    st.markdown("#### 🚀 Next Theme")
    next_theme = st.selectbox(
        "Theme", themes, key="next_theme_select", index=1, help="Theme to fade in/mix with current"
    )
    normalized_next_theme = get_theme_key(next_theme)

st.write("")  # For spacing before button

colb1, colb2 = st.columns([2, 1])
with colb1:
    clicked = st.button(
        "🔄 Transition to Next Theme", help="Fade out current theme, crossfade in next theme"
    )
with colb2:
    st.write("")  # For alignment

if clicked:
    current_intent = generate_mix_intent_from_folder(
        current_theme, base_dir="audio_clips/")
    current_stem_dicts = [
        {"filename": f"{current_theme}/{os.path.basename(stem.file_path)}",
         "targetgain": stem.target_gain,
         "fadeduration": stem.fade_duration}
        for stem in current_intent.stem_intents
    ]
    st.session_state.current_stem_dicts = current_stem_dicts

    next_intent = generate_mix_intent_from_folder(
        normalized_next_theme, base_dir="audio_clips/")
    next_stem_dicts = [
        {"filename": f"{normalized_next_theme}/{os.path.basename(stem.file_path)}",
         "targetgain": stem.target_gain,
         "fadeduration": stem.fade_duration}
        for stem in next_intent.stem_intents
    ]
    st.session_state.next_stem_dicts = next_stem_dicts

    st.session_state.status = f"✅ Transition: {current_theme} → {next_theme} Now Mixing..."
    st.session_state.show_details = True  # Toggle stem detail display on

    def get_friendly(stem):
        fname = os.path.splitext(os.path.basename(stem["filename"]))[0]
        return STEM_FRIENDLY.get(fname, (fname.title(), "🎵", "Unknown"))

    fade_sec = next_stem_dicts[0]['fadeduration'] if next_stem_dicts else "?"
    st.session_state.history.append({
        "timestamp": time.time(),
        "From": f"{current_theme}: {', '.join(get_friendly(s)[1] + ' ' + get_friendly(s)[0] for s in current_stem_dicts)}",
        "To": f"{next_theme}: {', '.join(get_friendly(s)[1] + ' ' + get_friendly(s)[0] for s in next_stem_dicts)}",
        "Transition": f"{current_theme} → {next_theme} | Crossfade over {fade_sec}s"
    })

# --- Status and Mixing Details FIRST ---
if st.session_state.status:
    st.success(st.session_state.status)
    st.write("")

if st.session_state.show_details:
    st.markdown("### 🎼 Mixing Details")
    colA, colB = st.columns(2)
    # Panel: Current Theme Stems
    with colA:
        st.markdown(f"##### Current Theme: {current_theme}")
        for stem in st.session_state.current_stem_dicts:
            friendly, icon, role = STEM_FRIENDLY.get(
                os.path.splitext(os.path.basename(stem["filename"]))[0],
                (os.path.basename(stem["filename"]).title(), "🎵", "Unknown"))
            st.markdown(
                f"""
                <div style="background-color:#eef4fa;border-radius:8px;padding:8px; margin-bottom:4px;">
                <span style="font-size:1.2em">{icon}</span> <b>{friendly}</b> <span style="color:#888;">({role})</span>
                <br><small>Gain: <b>{stem["targetgain"]}</b> &nbsp; Fade: <b>{stem["fadeduration"]}s</b></small>
                </div>
                """, unsafe_allow_html=True)
    # Panel: Next Theme Stems
    with colB:
        st.markdown(f"##### Next Theme: {next_theme}")
        for stem in st.session_state.next_stem_dicts:
            friendly, icon, role = STEM_FRIENDLY.get(
                os.path.splitext(os.path.basename(stem["filename"]))[0],
                (os.path.basename(stem["filename"]).title(), "🎵", "Unknown"))
            st.markdown(
                f"""
                <div style="background-color:#f9f5ed;border-radius:8px;padding:8px; margin-bottom:4px;">
                <span style="font-size:1.2em">{icon}</span> <b>{friendly}</b> <span style="color:#888;">({role})</span>
                <br><small>Gain: <b>{stem["targetgain"]}</b> &nbsp; Fade: <b>{stem["fadeduration"]}s</b></small>
                </div>
                """, unsafe_allow_html=True)
    st.write("") 
    # --- Play Mix React Component directly after details/collapse panels ---
    mix_and_transition(
        current_stems=st.session_state.current_stem_dicts,
        next_stems=st.session_state.next_stem_dicts
    )
    st.markdown("---")  # Separator after Play Mix

# --- History Table, User Readable ---
st.write("")
if st.session_state.history:
    st.markdown("### 📜 Transition History")
    st.write("")
    hist_rows = [
        {
            "⏰ Time": time.strftime('%H:%M:%S', time.localtime(entry["timestamp"])),
            "🛤️ From Theme & Stems": entry["From"],
            "🛤️ To Theme & Stems": entry["To"],
            "🔄 Details": entry["Transition"]
        }
        for entry in st.session_state.history
    ]
    st.table(hist_rows)
