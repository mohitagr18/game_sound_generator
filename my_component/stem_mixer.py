# ---------------------------------------------------------------------------
# stem_mixer.py
#
# Step-by-step overview:
# 1. Imports Streamlit and component modules, as well as json and os for serialization and file paths.
# 2. Declares the custom component (frontend React bundle) for visual mixing/crossfade interface.
# 3. Defines mix_and_transition() function that serializes the stems and displays the mixer UI.
# ---------------------------------------------------------------------------

import streamlit as st
import streamlit.components.v1 as components
import json
import os

_parent_dir = os.path.dirname(os.path.abspath(__file__))
component = components.declare_component(
    "stem_mixer",
    path=os.path.join(_parent_dir, "frontend", "build")
)

def mix_and_transition(current_stems, next_stems):
    """
    Show the frontend stem mixer/transition UI.
    Accepts two lists of stems (current, next), serializes to JSON and passes to frontend.
    Returns any output or input events from the component (if present).
    """
    return component(
        current_stems=json.dumps(current_stems),
        next_stems=json.dumps(next_stems)
    )
