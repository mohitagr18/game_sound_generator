import streamlit as st
from my_component.stem_mixer import mix_and_transition

if st.button("Test Component"):
    mix_and_transition([], [])
