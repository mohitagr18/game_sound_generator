import streamlit as st
import os
import re
import time
import json
from llm_advisor import LLMAdvisor, generate_mix_intent_from_folder
from my_component.stem_mixer import mix_and_transition
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

STEM_FRIENDLY = {
    "synth": ("Synth", "🎹", "Melody"),
    "pad": ("Pad", "🛋️", "Ambiance"),
    "drums": ("Drums", "🥁", "Rhythm"),
    "strings": ("Strings", "🎻", "Melody"),
    "bass": ("Bass", "🎸", "Bassline"),
    "chimes": ("Chimes", "🔔", "Accent"),
}

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

def extract_llm_json_and_reasoning(text):
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
if "llm_reasoning" not in st.session_state:
    st.session_state.llm_reasoning = ""

st.title("🎵 Game Audio StemMix Live Transition Demo")
themes = ["explore", "stealth", "combat", "boss_combat"]

col1, col2 = st.columns([1, 1], gap="large")
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

st.write("")  # For spacing

colb1, colb2 = st.columns([2, 1])
with colb1:
    clicked = st.button(
        "🔄 Transition to Next Theme", help="Fade out current theme, crossfade in next theme"
    )
with colb2:
    st.write("")

if clicked:
    with st.spinner("🚧 Generating next theme, please wait..."):
        current_intent = generate_mix_intent_from_folder(current_theme, base_dir="audio_clips/")
        current_stem_dicts = [
            {"filename": f"{current_theme}/{os.path.basename(stem.file_path)}",
            "targetgain": stem.target_gain,
            "fadeduration": stem.fade_duration}
            for stem in current_intent.stem_intents
        ]
        st.session_state.current_stem_dicts = current_stem_dicts

        advisor = LLMAdvisor()
        llm_output = advisor.recommend(
            session_log=st.session_state.get("history", []),
            current_state=current_stem_dicts,
            next_theme=next_theme,
            user_query=None
        )
        intent_dict = llm_output.get("next_intent", {})
        reasoning = ""
        if not intent_dict or not intent_dict.get("activestems"):
            intent_dict, reasoning = extract_llm_json_and_reasoning(llm_output.get("explanation", ""))
        else:
            reasoning = llm_output.get("explanation", "")
        st.session_state.llm_reasoning = reasoning

        stems_out = []
        for stem_name in intent_dict.get("activestems", []):
            gain = intent_dict.get("targetgains", {}).get(stem_name, "?")
            fade = intent_dict.get("fadedurations", {}).get(stem_name, "?")
            file_path = f"{next_theme}/{stem_name}.wav"  
            stems_out.append({
                "filename": file_path,    # Ensure this is a path the frontend can fetch
                "targetgain": gain,
                "fadeduration": fade
            })
        st.session_state.next_stem_dicts = stems_out

        fade_sec = stems_out[0]['fadeduration'] if stems_out else "?"
        st.session_state.status = f"✅ Transition: {current_theme} → {next_theme} Now Mixing..."
        st.session_state.show_details = True

        if st.session_state.current_stem_dicts and st.session_state.next_stem_dicts:
            mix_and_transition(
                st.session_state.current_stem_dicts,
                st.session_state.next_stem_dicts
            )


        # --- History: Store FULL data for each theme and stem dicts for table display
        st.session_state.history.append({
            "timestamp": time.time(),
            "from_theme": current_theme,
            "from_stem_dicts": list(st.session_state.current_stem_dicts),  # full stem dicts
            "to_theme": next_theme,
            "to_stem_dicts": list(st.session_state.next_stem_dicts),
            "Transition": f"{current_theme} → {next_theme} | Crossfade over {fade_sec}s"
        })

def stems_detail(stems, theme=None):
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
    # return (f"{theme}: " if theme else "") + ", ".join(rows)

if st.session_state.status:
    st.success(st.session_state.status)
    st.write("")

if st.session_state.show_details:
    st.markdown("### 🎼 Mixing Details")
    colA, colB = st.columns(2)
    # Current Theme Stems
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
    # Next Theme Stems
    with colB:
        st.markdown(f"##### Next Theme: {next_theme} (🧠 LLM-generated)")
        for stem in st.session_state.next_stem_dicts:
            fname_raw = os.path.basename(stem.get("filename", ""))
            stem_basename = re.sub(r'(\.wav)+$', '', fname_raw, flags=re.IGNORECASE)
            # stem_basename = os.path.splitext(os.path.basename(stem["filename"]))[0]
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

if st.session_state.history:
    st.markdown("### 📜 Transition History")
    # Only use this style + HTML snippet, nothing else
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



# if st.session_state.history:
#     st.markdown("### 📜 Transition History")
#     hist_rows = [
#         {
#             "⏰ Time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry["timestamp"])),
#             "🛤️ From Theme & Stems": stems_detail(entry.get("from_stem_dicts", []), entry.get("from_theme", "")),
#             "🛤️ To Theme & Stems": stems_detail(entry.get("to_stem_dicts", []), entry.get("to_theme", "")),
#             "🔄 Details": entry.get("Transition", "")
#         }
#         for entry in st.session_state.history
#     ]
#     df = pd.DataFrame(hist_rows)
#     st.dataframe(df, use_container_width=False)
