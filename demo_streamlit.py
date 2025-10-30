import streamlit as st
import ast
import re
import json
import os
from llm_advisor import LLMAdvisor
from dotenv import load_dotenv
load_dotenv()

st.title("Game Sound LLMAdvisor Demo UI")

# --- PRESETS ---
DEFAULT_STATES = ["explore", "stealth", "combat", "boss_combat"]
DEFAULT_FLAGS = ["lowhealth", "boss", "safe", "alert"]
STATE_TO_FLAGS = {
    "explore": ["safe"],
    "stealth": ["alert"],
    "combat": ["alert", "boss"],
    "boss_combat": ["boss", "alert"]
}

AUDIO_DIR = "audio_clips"

AUDIO_MAP = {
    "explore": "explore.mp3",
    "stealth": "stealth.mp3",
    "combat": "combat.mp3",
    "boss": "boss.mp3"
}

DEFAULT_USER_QUERY = "I'm in a safe area just exploring, but I can see a large enemy in the distance. Make the music feel a bit more tense."

# --- NEW FLEXIBLE MAPPING LOGIC ---
# We check in this specific order. "boss" must be checked before "combat".
# These are the *keywords* we'll search for.
THEME_KEYWORD_MAP = [
    ("boss", ["boss"]),
    ("combat", ["combat", "battle"]),
    ("stealth", ["stealth", "hidden"]),
    ("explore", ["explor", "jungle", "wondrous", "mysterious"]), # Will match "explore", "exploration"
]

def get_theme_key(theme_str):
    """
    Normalizes the LLM's theme string and maps it to a theme key.
    """
    if not theme_str:
        return None
    
    # Normalize: "Vulnerable_Exploration" -> "vulnerable exploration"
    # Normalize: "VulnerableExploration" -> "vulnerable exploration"
    s = str(theme_str).lower()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s) # Split camelCase

    # Check keywords in order
    for key, keywords in THEME_KEYWORD_MAP:
        for keyword in keywords:
            if keyword in s:
                return key # Found a match

    return None # No match found

def format_dict_as_bullets(data_dict):
    """Converts a dict to a markdown bulleted list."""
    if not data_dict or not isinstance(data_dict, dict):
        return "_None_"
    
    # Use markdown bullets, formatting the key as code
    bullets = [f"- `{key}`: {value}" for key, value in data_dict.items()]
    return "\n".join(bullets)


if "history" not in st.session_state:
    st.session_state.history = []
if "replay_index" not in st.session_state:
    st.session_state.replay_index = None
if "intent_report" not in st.session_state:
    st.session_state.intent_report = None
if "reasoning_report" not in st.session_state:
    st.session_state.reasoning_report = None

# --- Autofill after replay ---
if st.session_state.replay_index is not None:
    entry = st.session_state.history[st.session_state.replay_index]
    st.session_state.current_state = entry["currentstate_struct"]
    st.session_state.flags = entry["flags_struct"]
    st.session_state.intensity = entry["intensity_struct"]
    st.session_state.userquery = entry["userquery"]
    st.session_state.sessionlog_autogen = entry["sessionlog_struct"]
    st.session_state.intent_report = entry["intent"]
    st.session_state.reasoning_report = entry["reasoning"]
    st.session_state.replay_index = None

# --- Structured UI ---
st.header("Game State Selection")
col1, col2, col3 = st.columns([3,2,3])
with col1:
    current_state = st.selectbox("Current Game State", DEFAULT_STATES, key="current_state")
with col2:
    intensity = st.slider("Intensity (0-100)", 0, 100, 50, key="intensity")
with col3:
    possible_flags = STATE_TO_FLAGS.get(current_state, []) + [f for f in DEFAULT_FLAGS if f not in STATE_TO_FLAGS.get(current_state, [])]
    flags = st.multiselect("Flags", possible_flags, default=STATE_TO_FLAGS.get(current_state,[]), key="flags")

st.header("User Query")
userquery = st.text_input(
    "Describe your request or scenario:",
    value=st.session_state.get("userquery", DEFAULT_USER_QUERY),
    key="userquery"
)

st.caption("""
**Examples:**
* Explore: Just entered a new jungle area, make it feel wondrous and mysterious.
* Stealth: I'm sneaking past some guards, it needs to be quiet but tense.
* Combat: A group of enemies just spotted me, start the battle music!
* Boss combat: The main boss just appeared, make it epic and threatening!
""")

# --- Auto-generate session log & state for LLM ---
session_event = {"event": {"state": current_state, "intensity": intensity, "flags": flags}}
sessionlog_struct = [session_event]
currentstate_struct = {"state": current_state, "intensity": intensity, "flags": flags}

# st.markdown("**Session Log Preview:**")
# st.json(sessionlog_struct)
# st.markdown("**Current State Preview:**")
# st.json(currentstate_struct)

# --- Primary interaction ---
sent = st.button("Ask Advisor")

if sent:
    advisor = LLMAdvisor()
    try:
        # --- First Attempt ---
        resp = advisor.recommend(sessionlog_struct, currentstate_struct, userquery)
        intent = resp.get("next_intent", None)
        explanation = resp.get("explanation", "") # Get explanation from first resp

        # --- Fallback Parsing (if intent is None or empty dict {}) ---
        if (intent is None or not intent) and "explanation" in resp:
            json_block_regex = r'```(?:json)?\s*({[\sS]+?})\s*```|({[\s\S]+?})'
            match = re.search(json_block_regex, resp["explanation"])
            if match:
                try:
                    json_str = match.group(1) if match.group(1) else match.group(2)
                    if json_str:
                        intent = json.loads(json_str) 
                except Exception:
                    intent = None

        # --- RETRY LOGIC ---
        # If intent is STILL empty after first call + fallback, it's a cold start.
        if (intent is None or not intent):
            # --- Second Attempt ---
            resp_retry = advisor.recommend(sessionlog_struct, currentstate_struct, userquery)
            intent = resp_retry.get("next_intent", None)
            explanation = resp_retry.get("explanation", "") # Use the new explanation

            # Re-run fallback parsing on the *new* response
            if (intent is None or not intent) and "explanation" in resp_retry:
                json_block_regex = r'```(?:json)?\s*({[\s\S]+?})\s*```|({[\s\S]+?})'
                match = re.search(json_block_regex, resp_retry["explanation"])
                if match:
                    try:
                        json_str = match.group(1) if match.group(1) else match.group(2)
                        if json_str:
                            intent = json.loads(json_str) 
                    except Exception:
                        intent = None # Final failure

        # --- Save to session_state ---
        st.session_state.history.append({
            "sessionlog_struct": sessionlog_struct,
            "currentstate_struct": currentstate_struct,
            "flags_struct": flags,
            "intensity_struct": intensity,
            "userquery": userquery,
            "intent": intent,
            "reasoning": explanation 
        })
        st.session_state.intent_report = intent
        st.session_state.reasoning_report = explanation
        
    except Exception as e:
        st.error(f"Error: {e}")

# --- Display intent, music, reasoning as before ---
if st.session_state.intent_report is not None:
    st.subheader("Musical Intent")
    intent = st.session_state.intent_report
    
    # Check if intent is still empty (final fallback)
    if not intent:
        st.warning("Failed to retrieve musical intent after retry.")
    else:
        # --- NEW FORMATTING BLOCK ---
        st.markdown(f"**Theme:** {intent.get('theme','N/A')}")
        
        st.markdown("**Active Stems:**")
        stems = intent.get('activestems', [])
        # Display stems as a simple comma-separated string
        st.markdown(f"_{', '.join(stems) if stems else 'None'}_")

        st.markdown("**Target Gains:**")
        gains_dict = intent.get('targetgains', {})
        st.markdown(format_dict_as_bullets(gains_dict))
        
        st.markdown("**Fade Durations:**")
        fades_dict = intent.get('fadedurations', {})
        st.markdown(format_dict_as_bullets(fades_dict))
        
        st.markdown(f"**Timestamp:** {intent.get('timestamp','N/A')}")
        st.markdown("---") # Add a horizontal line
        # --- END NEW FORMATTING BLOCK ---

        # --- Audio player logic (unchanged) ---
        theme_raw = intent.get('theme', "")
        theme_key = get_theme_key(theme_raw) # Use new flexible mapping function

        if theme_key:
            audio_path = os.path.join(AUDIO_DIR, AUDIO_MAP.get(theme_key, ""))
        else:
            audio_path = None # No key was found

        if audio_path and os.path.isfile(audio_path):
            st.markdown(f"#### Music Preview: {theme_key.capitalize()}")
            st.audio(audio_path)
        else:
            # Updated warning to be more helpful for debugging
            st.warning(f"No audio file found for theme '{theme_raw}' (Could not map to a file)")

# --- Reasoning display block (this code is correct) ---
if st.session_state.reasoning_report is not None:
    st.subheader("Reasoning")
    explanation = st.session_state.reasoning_report
    
    # 1. Removes the JSON code block
    json_block_regex = r'^\s*(?:```(?:json)?\s*\{[\s\S]+?\}\s*```|(\{[\s\S]+\}))'
    explanation = re.sub(json_block_regex, "", explanation).strip()
    
    # 2. Removes an "undefined" code block
    undefined_code_block_regex = r'^\s*```(?:[a-z]+)?\s*undefined\s*```'
    explanation = re.sub(undefined_code_block_regex, "", explanation, flags=re.IGNORECASE).strip()
    
    # 3. Removes any leftover "undefined" plain text
    explanation = re.sub(r"^\s*undefined\s*", "", explanation, flags=re.IGNORECASE).strip()
    
    st.markdown(explanation)
else:
    st.info("Set the state, flags, intensity, and enter a query, then click 'Ask Advisor'.")

# --- Session History w/ Replay ---
if st.session_state.history:
    st.markdown("---")
    st.subheader("Session History")
    for i, entry in enumerate(reversed(st.session_state.history)):
        idx = len(st.session_state.history) - 1 - i
        st.markdown(f"**User Query:** {entry['userquery']}")
        theme = entry['intent'].get('theme', '') if entry['intent'] else ''
        st.markdown(f"**Theme:** {theme}")
        st.markdown(f"**State:** {entry['currentstate_struct']}")
        if st.button(f"Replay {idx}", key=f"replay_{idx}"):
            st.session_state.replay_index = idx
            st.rerun()
        st.markdown("---")