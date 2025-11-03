# # preview_stems.py

# import streamlit as st
# from llm_advisor import generate_mix_intent_from_folder

# st.title("Game Audio Stems & Mix Intent Preview")

# st.write(
#     "Pick a theme to preview all available stems (WAVs) and their default mix intent. "
#     "This preview ensures your folder is structured correctly for dynamic/adaptive mixing."
# )

# theme = st.selectbox("Pick a theme", ["explore", "stealth", "combat", "bosscombat"])

# if st.button("Preview Stems/Instruments for this Theme"):
#     try:
#         mix_intent = generate_mix_intent_from_folder(theme)
#         st.subheader(f"Stems for theme: {theme}")
#         st.json(mix_intent.to_dict())

#         st.subheader("Audio Files (Play individually)")
#         for stem in mix_intent.stem_intents:
#             st.write(f"**{stem.stem_name}** ({stem.file_path})")
#             st.audio(stem.file_path)
#     except Exception as e:
#         st.error(f"Error: {e}\nMake sure audioclips/{theme}/ contains one or more .wav files.")

# st.info(
#     "Note: This does not mix stems live—each is played separately for now (Streamlit limitation). "
#     "Next, you will combine stem playback and smooth transition in the frontend."
# )


import streamlit as st
from llm_advisor import generate_mix_intent_from_folder
import streamlit_stem_mixer.stem_mixer as sm  # adjust import to your file/module

st.title("Game Audio Stem/Mix Live Transition (Custom UI)")

theme = st.selectbox("Pick current theme", ["explore", "stealth", "combat", "bosscombat"])
next_theme = st.selectbox("Pick next theme", ["explore", "stealth", "combat", "bosscombat"])

if st.button("Try Real-Time Stem Mixing"):
    curr_intent = generate_mix_intent_from_folder(theme)
    next_intent = generate_mix_intent_from_folder(next_theme)
    sm.mix_and_transition(
        current_stems=curr_intent.to_dict()['stems'],
        next_stems=next_intent.to_dict()['stems']
    )
