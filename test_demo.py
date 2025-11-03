import streamlit as st
from streamlit_stem_mixer.stem_mixer import mix_and_transition

if st.button("Test Component"):
    mix_and_transition([], [])
