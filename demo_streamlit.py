import streamlit as st
import ast
import re
import json
from llm_advisor import LLMAdvisor
from dotenv import load_dotenv
load_dotenv()


st.title("Game Sound LLMAdvisor Demo UI")

# Session Log input
sessionlog_input = st.text_area(
    "Session Log (Python list/dict, e.g. [{'event': ...}]):",
    value=""
)

# Current State input
currentstate_input = st.text_area(
    "Current State (Python dict, e.g. {'state': ...}):",
    value=""
)

# User Query input
userquery = st.text_input("User Query:", value="")

if st.button("Ask Advisor"):
    advisor = LLMAdvisor()
    try:
        sessionlog = ast.literal_eval(sessionlog_input) if sessionlog_input.strip() else None
        currentstate = ast.literal_eval(currentstate_input) if currentstate_input.strip() else None
        resp = advisor.recommend(sessionlog, currentstate, userquery)
        
        # Try getting intent from standard field
        intent = resp.get("next_intent", None)
        
        # If not found, try to parse intent from explanation code block
        # if not intent and "explanation" in resp:
        #     match = re.search(r"``````", resp["explanation"], re.DOTALL)
        #     if match:
        #         try:
        #             intent = json.loads(match.group(1))
        #         except Exception:
        #             intent = None
        
        if intent:
            st.subheader("Musical Intent")
            # st.json(intent)
            st.markdown(f"""
| Key           | Value |
|---------------|-------|
| Theme         | {intent.get('theme','')} |
| Active Stems  | {', '.join(intent.get('activestems', []))} |
| Target Gains  | {intent.get('targetgains', '')} |
| Fade Durations| {intent.get('fadedurations', '')} |
| Timestamp     | {intent.get('timestamp', '')} |
""")
        
        if "explanation" in resp:
            st.subheader("Reasoning")
            # Clean explanation by removing code block and "undefined" if present
            explanation = resp["explanation"]
            # 1. Remove the JSON block (this regex is correct)
            json_block_regex = r'^\s*(?:```(?:json)?\s*\{[\s\S]+?\}\s*```|(\{[\s\S]+\}))'
            explanation = re.sub(json_block_regex, "", explanation).strip()
            
            # 2. THIS IS THE FIX:
            # Use a flexible, case-insensitive regex to remove "undefined"
            # surrounded by any whitespace.
            explanation = re.sub(r"^\s*undefined\s*", "", explanation, flags=re.IGNORECASE).strip()
            
            st.markdown(explanation)

            
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Enter session log, current state, and a user query, then click 'Ask Advisor'.")

