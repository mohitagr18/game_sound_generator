import streamlit as st
import streamlit.components.v1 as components
import json
import os

# Declare ONCE at import (top-level)
_parent_dir = os.path.dirname(os.path.abspath(__file__))
component = components.declare_component(
    "stem_mixer",
    path=os.path.join(_parent_dir, "frontend", "build")
    # path="/Users/mohit/Documents/GitHub/game_sound_generator/streamlit_stem_mixer/frontend/build"
)

def mix_and_transition(current_stems, next_stems):
    """Show frontend stem mixer/transition."""
    return component(
        current_stems=json.dumps(current_stems),
        next_stems=json.dumps(next_stems)
    )
