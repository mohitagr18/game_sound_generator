import streamlit as st
from llm_advisor import generate_mix_intent_from_folder
from my_component.stem_mixer import mix_and_transition
import os

# Import your custom component declaration function from my_component (adjust path if needed)
# from my_component import st_my_component  # Use the actual Python register function name

st.title("Game Audio StemMix Live Transition Demo")

theme = st.selectbox("Pick current theme", ["explore", "stealth", "combat", "bosscombat"])

if theme:
    intent = generate_mix_intent_from_folder(theme, base_dir="audio_clips/")

    # Debug: Show available fields just once for one stem
    st.write(intent.stem_intents[0].__dict__)

    stem_dicts = [
        {
            "filename": f"{theme}/{os.path.basename(stem.file_path)}",      # use actual attribute—likely 'filepath'
            "targetgain": stem.target_gain,
            "fadeduration": stem.fade_duration
        }
        for stem in intent.stem_intents
    ]

    st.write("Stem payload to frontend:", stem_dicts)

    # Pass payload to your Streamlit custom component
    mix_and_transition(current_stems=stem_dicts, next_stems=[])

# (Optional) Add additional UI and triggers for transitions, mixing, etc.
