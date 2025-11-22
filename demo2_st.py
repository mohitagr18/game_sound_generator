# ---------------------------------------------------------------------------
# 🚀🎶 Live Soundtrack Crossfader: Instantly Blend Game Audio Themes!
#
# Step-by-step breakdown:
# 1. Set up all necessary imports, helpers, and app environment
# 2. Define theme/stem mappings and any utility functions for normalization/parsing
# 3. Initialize Streamlit session state (persistent across reruns)
# 4. Build UI for selecting current and next themes, and transition/play controls
# 5. Handle transitions: generate current intent, call LLM for next intent, validate outputs, handle errors
# 6. Show mixing details: Current and Next stems, with friendly icons and roles per stem
# 7. Show transition history: full table of all transitions and stem/gain details
# 8. (Throughout) Provide clear error/status/warning messages where needed
# ---------------------------------------------------------------------------

import streamlit as st
import os
import re
import time
import json
from llm_advisor import LLMAdvisor, generate_mix_intent_from_folder
from my_component.stem_mixer import mix_and_transition
from dotenv import load_dotenv
import pandas as pd

# Load any environment variables from .env file (for model/backend config)
load_dotenv()

# ----------------------------------------------------------------------------
# STEM_FRIENDLY: mapping from stem keys to (friendly name, emoji, musical role)
# Used for display in the UI and detailed mixing tables
# ----------------------------------------------------------------------------
STEM_FRIENDLY = {
    "synth": ("Synth", "🎹", "Melody"),
    "pad": ("Pad", "🛋️", "Ambiance"),
    "drums": ("Drums", "🥁", "Rhythm"),
    "strings": ("Strings", "🎻", "Melody"),
    "bass": ("Bass", "🎸", "Bassline"),
    "chimes": ("Chimes", "🔔", "Accent"),
}

# ----------------------------------------------------------------------------
# THEME_KEYWORD_MAP: used to map messy theme names to a canonical internal key
# ----------------------------------------------------------------------------
THEME_KEYWORD_MAP = [
    ("bosscombat", ["boss"]),
    ("combat", ["combat", "battle"]),
    ("stealth", ["stealth", "hidden"]),
    ("explore", ["explor", "jungle", "wondrous", "mysterious"]),
]

def get_theme_key(theme_str):
    """
    Normalizes and maps a theme string (from UI or LLM) to a canonical key
    Example: "Boss-Combat" -> "bosscombat"
    """
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

def extract_llm_json_and_reasoning(text):
    """
    Parses out a JSON structure and extra reasoning text from an LLM explanation.
    Used when the LLM doesn't provide properly structured output up front.
    """
    stack = []
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if not stack:
                start = i
            stack.append(c)
        elif c == '}':
            if stack:
                stack.pop()
                if not stack and start is not None:
                    try:
                        json_str = text[start:i+1]
                        obj = json.loads(json_str)
                        reasoning_raw = text[i+1:].strip(" \n:;")
                        reasoning = reasoning_raw.split('"""')[0].strip()
                        reasoning = re.split(r'[\n\r][\s]*[),]+[\n\r]', reasoning)[0].strip()
                        return obj, reasoning
                    except Exception as e:
                        st.warning(f"Error parsing LLM JSON: {e}\n\n{text[start:i+1]}")
                    break
    return {}, ""

# --- Streamlit session state: persist critical variables across reruns ---
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
if "llm_reasoning" not in st.session_state:
    st.session_state.llm_reasoning = ""

# ------------------------ Streamlit UI structure --------------------------
st.title("🚀🎶 Live Soundtrack Crossfader: Instantly Blend Game Audio Themes!")
st.markdown("")

# Theme choices to present in the UI
themes = ["explore", "stealth", "combat", "bosscombat"]

# Theme selectors for UI (Current and Next)
col1, col2 = st.columns([1, 1], gap="large")
with col1:
    st.markdown("#### 🎧 Current Theme")
    current_theme = st.selectbox(
        "Theme", themes, key="current_theme_select", index=2, help="Theme currently playing"
    )
with col2:
    st.markdown("#### 🚀 Next Theme")
    next_theme = st.selectbox(
        "Theme", themes, key="next_theme_select", index=0, help="Theme to fade in/mix with current"
    )
    normalized_next_theme = get_theme_key(next_theme)

st.write("")  # For spacing

# Display transition/play controls (side-by-side for clarity)
colb1, colb2 = st.columns([2, 1])
with colb1:
    clicked = st.button(
        "🔄 Transition to Next Theme", help="Fade out current theme, crossfade in next theme"
    )
with colb2:
    st.write("")

# ------------------- Transition Button Handler ------------------------
if clicked:
    with st.spinner("🚧 Generating next theme, please wait..."):
        # Step 1: Pull out currently active stems (for outgoing/current theme)
        current_intent = generate_mix_intent_from_folder(current_theme, base_dir="audio_clips/")
        current_stem_dicts = [
            {"filename": f"{current_theme}/{os.path.basename(stem.file_path)}",
            "targetgain": stem.target_gain,
            "fadeduration": stem.fade_duration}
            for stem in current_intent.stem_intents
        ]
        st.session_state.current_stem_dicts = current_stem_dicts

        # Step 2: Use LLMAdvisor to recommend next set of stems (for incoming/next theme)
        advisor = LLMAdvisor()
        llm_output = advisor.recommend(
            session_log=st.session_state.get("history", []),
            current_state=current_stem_dicts,
            next_theme=next_theme,
            user_query=None
        )
        intent_dict = llm_output.get("next_intent", {})
        reasoning = ""
        # Try fallback JSON reasoning extraction if needed
        if not intent_dict or not intent_dict.get("activestems"):
            intent_dict, reasoning = extract_llm_json_and_reasoning(llm_output.get("explanation", ""))
        else:
            reasoning = llm_output.get("explanation", "")
        st.session_state.llm_reasoning = reasoning

        # Step 3: Error handling and output validation
        error_msg = None
        if not intent_dict or not intent_dict.get("activestems"):
            error_msg = "🛑 No valid music stems found from the model. Please try a different theme or re-run the transition."
        elif any(val == '?' or val is None for val in intent_dict.get("targetgains", {}).values()):
            error_msg = "⚠️ Some target gain values were not generated. Please check your input or retry."

        if error_msg:
            st.warning(error_msg)
        else:
            # Step 4: Build stem dicts for the next theme (generated by LLM)
            stems_out = []
            for stem_name in intent_dict.get("activestems", []):
                gain = intent_dict.get("targetgains", {}).get(stem_name, "?")
                fade = intent_dict.get("fadedurations", {}).get(stem_name, "?")
                # Ensure stem_name does not already have .wav and does not have the theme as a prefix
                base_stem = os.path.basename(stem_name)  # Strips theme dir if present
                base_stem = re.sub(r'(\.wav)+$', '', base_stem, flags=re.IGNORECASE)  # Remove any .wav extension
                file_path = f"{next_theme}/{base_stem}.wav"
                print(f"Next stem file path: {file_path}")
                stems_out.append({
                    "filename": file_path,
                    "targetgain": gain,
                    "fadeduration": fade
                })
            st.session_state.next_stem_dicts = stems_out

            fade_sec = stems_out[0]['fadeduration'] if stems_out else "?"
            st.session_state.status = f"✅ Transition: {current_theme} → {next_theme} Now Mixing..."
            st.session_state.show_details = True

            # Log all transition data for history view
            st.session_state.history.append({
                "timestamp": time.time(),
                "from_theme": current_theme,
                "from_stem_dicts": list(st.session_state.current_stem_dicts),
                "to_theme": next_theme,
                "to_stem_dicts": list(st.session_state.next_stem_dicts),
                "Transition": f"{current_theme} → {next_theme} | Crossfade over {fade_sec}s"
            })

            # Actually perform the mix/crossfade if both valid stem sets exist
            if st.session_state.current_stem_dicts and st.session_state.next_stem_dicts:
                mix_and_transition(
                    st.session_state.current_stem_dicts,
                    st.session_state.next_stem_dicts
                )

# ------------------- Helper: Format stem display/details --------------------
def stems_detail(stems, theme=None):
    """
    For stem dicts, generates a line-by-line, user-friendly string with all gain/fade data.
    Used in transition history and table columns.
    """
    if not stems:
        return ""
    rows = []
    for stem in stems:
        fname_raw = os.path.basename(stem.get("filename", ""))
        fname = re.sub(r'(\.wav)+$', '', fname_raw, flags=re.IGNORECASE)
        gain = stem.get("targetgain", "?")
        fade = stem.get("fadeduration", "?")
        rows.append(f"{fname} (gain={gain}, fade={fade}s)")
    joined = "<br>- ".join(rows)
    return (f"{theme}:<br>- " if theme else "") + joined

# ------------------- Status, Mixing Details, and History Displays -----------------

if st.session_state.status:
    st.success(st.session_state.status)
    st.write("")

if st.session_state.show_details:
    st.markdown("### 🎼 Mixing Details")
    colA, colB = st.columns(2)
    # Left: Current Theme Stems
    with colA:
        st.markdown(f"##### Current Theme: {current_theme}")
        st.markdown("")
        for stem in st.session_state.current_stem_dicts:
            friendly, icon, role = STEM_FRIENDLY.get(
                os.path.splitext(os.path.basename(stem["filename"]))[0],
                (os.path.basename(stem["filename"]).title(), "🎵", "Unknown"))
            st.markdown(
                f"""
                <div style="background-color:#eef4fa;color:#183151;border-radius:8px;padding:8px; margin-bottom:4px;">
                <span style="font-size:1.2em">{icon}</span> <b>{friendly}</b> <span style="color:#888;">({role})</span>
                <br><small>Gain: <b>{stem["targetgain"]}</b> &nbsp; Fade: <b>{stem["fadeduration"]}s</b></small>
                </div>
                """, unsafe_allow_html=True)
    # Right: Next Theme Stems
    with colB:
        st.markdown(f"##### Next Theme: {next_theme} (🧠 LLM-generated)")
        for stem in st.session_state.next_stem_dicts:
            fname_raw = os.path.basename(stem.get("filename", ""))
            stem_basename = re.sub(r'(\.wav)+$', '', fname_raw, flags=re.IGNORECASE)
            friendly, icon, role = STEM_FRIENDLY.get(
                stem_basename,
                (stem_basename.title(), "🎵", "Unknown")
            )
            st.markdown(
                f'''<div style="background-color:#f9f5ed;color:#183151;border-radius:8px;padding:8px; margin-bottom:4px;">
                <span style="font-size:1.2em">{icon}</span>
                <b>{friendly}</b>
                <span style="color:#888">({role})</span><br>
                <small>Gain <b>{stem["targetgain"]}</b>&nbsp; Fade <b>{stem["fadeduration"]}s</b></small>
                </div>''', unsafe_allow_html=True
            )
    st.write("")
    llm_expl = st.session_state.get("llm_reasoning", "")
    if llm_expl:
        st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
        st.markdown("#### 💡 LLM Reasoning/Explanation")
        st.write(llm_expl)
    st.markdown("---")

# ------------------- Transition History Table ---------------------
if st.session_state.history:
    st.markdown("### 📜 Transition History")
    # Create a styled HTML table with all transition and stem/gain info
    style = """
    <style>
    table.history-table {border-collapse:collapse;width:100%;table-layout:fixed;}
    table.history-table th, table.history-table td {
        padding:8px;
        border:1px solid #ddd;
        vertical-align:top;
        text-align:left;
        word-break:break-word;
        white-space:pre-line;
        max-width:220px;
        font-size:1em;
        color:#183151;
    }
    table.history-table th {background:#faf7f2;}
    table.history-table td {background:#fff;}
    </style>
    """
    table_html = style + "<table class='history-table'><thead><tr>" + \
                 "<th>⏰ Time</th><th>🛤️ From Theme & Stems</th><th>🛤️ To Theme & Stems</th><th>🔄 Details</th></tr></thead><tbody>"

    for entry in st.session_state.history:
        dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry["timestamp"]))
        from_stems_str = stems_detail(entry.get("from_stem_dicts", []), entry.get("from_theme", ""))
        to_stems_str = stems_detail(entry.get("to_stem_dicts", []), entry.get("to_theme", ""))
        transition = entry.get("Transition", "")
        table_html += f"<tr><td>{dt}</td><td>{from_stems_str}</td><td>{to_stems_str}</td><td>{transition}</td></tr>"
    table_html += "</tbody></table>"

    st.markdown(table_html, unsafe_allow_html=True)
