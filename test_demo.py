import streamlit as st
from stem_mixer.stem_mixer import mix_and_transition

if st.button("Test Component"):
    mix_and_transition([], [])
