import streamlit as st
import ast
import re
import json
from llm_advisor import LLMAdvisor
from dotenv import load_dotenv
import os
load_dotenv()

st.title("Game Sound LLMAdvisor Demo UI")

# Session state for memory, replay, and last result
if "history" not in st.session_state:
    st.session_state.history = []
if "replay_index" not in st.session_state:
    st.session_state.replay_index = None
if "intent_report" not in st.session_state:
    st.session_state.intent_report = None
if "reasoning_report" not in st.session_state:
    st.session_state.reasoning_report = None

# Autofill on rerun after replay (before widgets)
if st.session_state.replay_index is not None:
    entry = st.session_state.history[st.session_state.replay_index]
    st.session_state.sessionlog_input = entry["sessionlog"]
    st.session_state.currentstate_input = entry["currentstate"]
    st.session_state.userquery = entry["userquery"]
    st.session_state.intent_report = entry["intent"]
    st.session_state.reasoning_report = entry["reasoning"]
    st.session_state.replay_index = None

sessionlog_input = st.text_area(
    "Session Log (Python list/dict, e.g. [{'event': ...}]):",
    value=st.session_state.get("sessionlog_input", ""),
    key="sessionlog_input"
)
currentstate_input = st.text_area(
    "Current State (Python dict, e.g. {'state': ...}):",
    value=st.session_state.get("currentstate_input", ""),
    key="currentstate_input"
)
userquery = st.text_input(
    "User Query:",
    value=st.session_state.get("userquery", ""),
    key="userquery"
)

sent = st.button("Ask Advisor")
if sent:
    advisor = LLMAdvisor()
    try:
        sessionlog = ast.literal_eval(sessionlog_input) if sessionlog_input.strip() else None
        currentstate = ast.literal_eval(currentstate_input) if currentstate_input.strip() else None
        resp = advisor.recommend(sessionlog, currentstate, userquery)
        
        intent = resp.get("next_intent", None)
        
        # Store history for replay
        st.session_state.history.append({
            "sessionlog": sessionlog_input,
            "currentstate": currentstate_input,
            "userquery": userquery,
            "intent": intent,
            "reasoning": resp.get("explanation", "")
        })
        st.session_state.intent_report = intent
        st.session_state.reasoning_report = resp.get("explanation", "")
        
    except Exception as e:
        st.error(f"Error: {e}")

# Always display last Musical Intent and Reasoning after any run
if st.session_state.intent_report:
    st.subheader("Musical Intent")
    intent = st.session_state.intent_report
    st.markdown(f"""
| Key           | Value |
|---------------|-------|
| Theme         | {intent.get('theme','')} |
| Active Stems  | {', '.join(intent.get('activestems', []))} |
| Target Gains  | {intent.get('targetgains', '')} |
| Fade Durations| {intent.get('fadedurations', '')} |
| Timestamp     | {intent.get('timestamp', '')} |
""")
    
    # Basic theme-mp3 playback mapping
    AUDIO_DIR = "audio_clips"
    THEME_TO_CLIP = {
        "explore": "explore.mp3",
        "combat": "combat.mp3",
        "stealth": "stealth.mp3",
        "boss_combat": "boss.mp3"
    }
    theme = intent.get('theme', None)
    audio_file = None
    if theme in THEME_TO_CLIP:
        audio_path = os.path.join(AUDIO_DIR, THEME_TO_CLIP[theme])
        
        st.write("Looking for audio at:", audio_path)
        st.write("Theme:", theme)

        if os.path.isfile(audio_path):
            st.markdown(f"#### Music Preview: {THEME_TO_CLIP[theme]}")
            st.audio(audio_path)
        else:
            st.warning(f"No audio file found for theme '{theme}' (expected: {audio_path})")


if st.session_state.reasoning_report:
    st.subheader("Reasoning")
    explanation = st.session_state.reasoning_report
    # 1. Remove the JSON block (this regex is correct)
    json_block_regex = r'^\s*(?:```(?:json)?\s*\{[\s\S]+?\}\s*```|(\{[\s\S]+\}))'
    explanation = re.sub(json_block_regex, "", explanation).strip()
    # 2. NEW FIX: Remove any "undefined" code block
    undefined_code_block_regex = r'^\s*```(?:[a-z]+)?\s*undefined\s*```'
    explanation = re.sub(undefined_code_block_regex, "", explanation, flags=re.IGNORECASE).strip()
    # 3. Clean up any remaining plain "undefined" text at the start.
    explanation = re.sub(r"^\s*undefined\s*", "", explanation, flags=re.IGNORECASE).strip()

    st.markdown(explanation)
else:
    st.info("Enter session log, current state, and a user query, then click 'Ask Advisor'.")

# Display history & replay (simple readable layout)
if st.session_state.history:
    st.markdown("---")
    st.subheader("Session History")
    for i, entry in enumerate(reversed(st.session_state.history)):
        idx = len(st.session_state.history) - 1 - i
        st.markdown(f"**User Query:** {entry['userquery']}")
        theme = entry['intent'].get('theme', '') if entry['intent'] else ''
        st.markdown(f"**Theme:** {theme}")
        st.markdown(f"**State:** {entry['currentstate']}")
        if st.button(f"Replay {idx}", key=f"replay_{idx}"):
            st.session_state.replay_index = idx
            st.rerun()
        st.markdown("---")
