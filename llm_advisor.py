# ---------------------------------------------------------------------------
# llm_advisor.py (v2 - Robust Parsing)
# ---------------------------------------------------------------------------

from google import genai
import os
import re
import json
from schemas import MixIntent, StemIntent

def generate_mix_intent_from_folder(theme: str,
                                   base_dir: str = "static/audio_clips",
                                   default_gain: float = 0.8,
                                   default_fade: float = 2.0
                                   ) -> MixIntent:
    # Handle both local dev paths and potential deployment paths
    theme_dir = os.path.join(base_dir, theme)
    if not os.path.exists(theme_dir):
        if base_dir == "static/audio_clips":
             theme_dir = os.path.join("audio_clips", theme)
        
    if not os.path.exists(theme_dir):
        print(f"Warning: Theme folder not found: {theme_dir}")
        return MixIntent(theme=theme, stem_intents=[])

    stem_intents = []
    for fname in os.listdir(theme_dir):
        if fname.lower().endswith(".wav"):
            stem_name = os.path.splitext(fname)[0]
            file_path = os.path.join(theme_dir, fname)
            stem_intents.append(
                StemIntent(
                    stem_name=stem_name,
                    file_path=file_path,
                    target_gain=default_gain,
                    fade_duration=default_fade
                )
            )
    return MixIntent(theme=theme, stem_intents=stem_intents)

class LLMAdvisor:
    def __init__(self, model_name="gemini-2.0-flash"):
        self.model_name = model_name
        apikey = os.getenv("GOOGLE_API_KEY")
        if not apikey:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = genai.Client(api_key=apikey)

    def recommend(self, session_log, current_state, next_theme, user_query=None):
        # 1. Get valid stems for the NEXT theme
        next_intent_check = generate_mix_intent_from_folder(next_theme)
        valid_stems = [s.stem_name for s in next_intent_check.stem_intents]
        
        # 2. Build prompt
        prompt = self._build_prompt(session_log, current_state, next_theme, valid_stems, user_query)
        
        # 3. Call LLM
        response = self._call_llm_api(prompt)
        return self._parse_response(response)

    def _build_prompt(self, session_log, current_state, next_theme, valid_stems, user_query):
        valid_stems_str = ", ".join([f"'{s}'" for s in valid_stems])

        schema_description = '''Respond in two parts:
1. A valid JSON object describing the next musical intent. schema:
{
    "theme": "string",
    "activestems": ["string"], 
    "targetgains": {"stem_name": float},
    "fadedurations": {"stem_name": float},
    "timestamp": "string"
}

2. A short explanation of your reasoning.
'''
        prompt = (
            f"Current theme: {current_state[0]['filename'].split('/')[0] if current_state else '[unknown]'}\n"
            f"Next theme: {next_theme}\n"
            f"**CRITICAL CONSTRAINT**: The ONLY audio files available for '{next_theme}' are: [{valid_stems_str}].\n"
            f"You MUST NOT invent new filenames. You MUST use a subset of the provided valid stems.\n"
            f"{schema_description}\n"
            f"Transition the music mix from the current theme to '{next_theme}'.\n"
            "What is the next musical intent?"
        )
        if user_query:
            prompt += f"\nUser question: {user_query}"
        return prompt

    def _call_llm_api(self, prompt):
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            if hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                return parts[0].text if parts else ""
            return getattr(response, "text", str(response))
        except Exception as e:
            return f"LLM Error: {str(e)}"

    def _parse_response(self, response):
        result = {"next_intent": {}, "explanation": ""}
        
        # Helper to strip markdown code blocks
        clean_text = response.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
             clean_text = clean_text.split("```")[1].split("```")[0]
        
        # Attempt to find the first JSON object
        try:
            # Look for outer braces if loose text is still present
            match = re.search(r"(\{[\s\S]*\})", clean_text)
            if match:
                json_candidate = match.group(1)
                result["next_intent"] = json.loads(json_candidate)
                # Logic: Explanation is whatever is NOT the JSON
                result["explanation"] = response.replace(json_candidate, "").replace("```json", "").replace("```", "").strip()
            else:
                # Last ditch: try loading the whole cleaned text
                result["next_intent"] = json.loads(clean_text)
                result["explanation"] = "Parsed from pure JSON."
        except json.JSONDecodeError:
            result["explanation"] = f"JSON Parsing Failed. Raw output:\n{response}"
        except Exception as e:
            result["explanation"] = f"General Parse Error: {str(e)}"
            
        return result


# # ---------------------------------------------------------------------------
# # llm_advisor.py
# # ---------------------------------------------------------------------------
# # Updates:
# # 1. In recommend(), we now scan the next_theme folder first.
# # 2. We pass the 'valid_stems' list to the prompt.
# # 3. The prompt explicitly forbids hallucinating filenames not in the list.
# # ---------------------------------------------------------------------------

# from google import genai
# import os
# import re
# import json
# from schemas import MixIntent, StemIntent

# def generate_mix_intent_from_folder(theme: str,
#                                    base_dir: str = "static/audio_clips", # Updated default to match your server structure
#                                    default_gain: float = 0.8,
#                                    default_fade: float = 2.0
#                                    ) -> MixIntent:
#     """
#     Scans the folder for .wav files, returns MixIntent.
#     """
#     # Handle both local dev paths and potential deployment paths
#     # Tries 'static/audio_clips' first (for Streamlit serving), falls back to 'audio_clips'
#     theme_dir = os.path.join(base_dir, theme)
#     if not os.path.exists(theme_dir):
#         # Fallback check
#         if base_dir == "static/audio_clips":
#              theme_dir = os.path.join("audio_clips", theme)
        
#     if not os.path.exists(theme_dir):
#         # Return empty intent rather than crashing, allowing graceful failure later
#         print(f"Warning: Theme folder not found: {theme_dir}")
#         return MixIntent(theme=theme, stem_intents=[])

#     stem_intents = []
#     for fname in os.listdir(theme_dir):
#         if fname.lower().endswith(".wav"):
#             stem_name = os.path.splitext(fname)[0]
#             file_path = os.path.join(theme_dir, fname)
#             stem_intents.append(
#                 StemIntent(
#                     stem_name=stem_name,
#                     file_path=file_path,
#                     target_gain=default_gain,
#                     fade_duration=default_fade
#                 )
#             )
#     return MixIntent(theme=theme, stem_intents=stem_intents)

# class LLMAdvisor:
#     """
#     Advisor class to interact with Gemini/Google LLM API for
#     generating music transition intents and explanations.
#     """
#     def __init__(self, model_name="gemini-2.5-flash"):
#         # Using 2.0 Flash as it is faster/better for structured data, 
#         # fallback to 1.5 if 2.0 not available in your tier.
#         self.model_name = model_name
#         apikey = os.getenv("GOOGLE_API_KEY")
#         if not apikey:
#             raise ValueError("GOOGLE_API_KEY environment variable not set")
#         self.client = genai.Client(api_key=apikey)

#     def recommend(self, session_log, current_state, next_theme, user_query=None):
#         """
#         Recommend the next mix intent. 
#         CRITICAL CHANGE: Scans the destination folder first to get valid files.
#         """
#         # 1. Get valid stems for the NEXT theme
#         next_intent_check = generate_mix_intent_from_folder(next_theme)
#         valid_stems = [s.stem_name for s in next_intent_check.stem_intents]
        
#         # 2. Build prompt with these constraints
#         prompt = self._build_prompt(session_log, current_state, next_theme, valid_stems, user_query)
        
#         # 3. Call LLM
#         response = self._call_llm_api(prompt)
#         return self._parse_response(response)

#     def _build_prompt(self, session_log, current_state, next_theme, valid_stems, user_query):
#         """
#         Construct LLM prompt with STRICT file constraints.
#         """
#         # Format valid stems as a string list for the prompt
#         valid_stems_str = ", ".join([f"'{s}'" for s in valid_stems])

#         schema_description = '''Respond in two parts:
# 1. A valid JSON object describing the next musical intent. schema:
#     "theme": str,
#     "activestems": [str],  <-- MUST be a subset of the Available Stems list below
#     "targetgains": {str: float},
#     "fadedurations": {str: float},
#     "timestamp": str

# 2. A short explanation of your reasoning.
# '''
#         prompt = (
#             f"Current theme: {current_state[0]['filename'].split('/')[0] if current_state else '[unknown]'}\n"
#             f"Next theme: {next_theme}\n"
#             f"**CRITICAL CONSTRAINT**: The ONLY audio files available for '{next_theme}' are: [{valid_stems_str}].\n"
#             f"You MUST NOT invent new filenames. You MUST NOT use files from the current theme. Use only the filenames listed above.\n"
#             f"{schema_description}\n"
#             f"Transition the music mix from the current theme to '{next_theme}'.\n"
#             "What is the next musical intent?"
#         )
#         if user_query:
#             prompt += f"\nUser question: {user_query}"
#         return prompt

#     def _call_llm_api(self, prompt):
#         try:
#             response = self.client.models.generate_content(
#                 model=self.model_name,
#                 contents=prompt
#             )
#             # Handle different response structures (candidates vs text)
#             if hasattr(response, "candidates") and response.candidates:
#                 parts = response.candidates[0].content.parts
#                 return parts[0].text if parts else ""
#             return getattr(response, "text", str(response))
#         except Exception as e:
#             return f"LLM Error: {str(e)}"

#     def _parse_response(self, response):
#         result = {"next_intent": {}, "explanation": ""}
#         try:
#             # Attempt to find JSON block using regex
#             match = re.search(r"({[\s\S]+?})", response)
#             if match:
#                 json_str = match.group(1)
#                 try:
#                     result["next_intent"] = json.loads(json_str)
#                     # Everything after the JSON is the explanation
#                     result["explanation"] = response.replace(json_str, "").strip()
#                 except json.JSONDecodeError:
#                     result["explanation"] = f"JSON Decode Error. Raw: {response}"
#             else:
#                 result["explanation"] = f"No JSON found. Raw: {response}"
#         except Exception as e:
#             result["explanation"] = f"Parse Error: {e}"
#         return result




# # # ---------------------------------------------------------------------------
# # # llm_advisor.py
# # #
# # # Step-by-step overview:
# # # 1. Imports all required dependencies (LLM API, os, regex, schema classes)
# # # 2. Defines generate_mix_intent_from_folder: loads stem info from directory, builds MixIntent
# # # 3. Defines LLMAdvisor class for accessing and using the Gemini (Google) LLM
# # #     - Initializes LLM client (API key required)
# # #     - Builds prompt for new music intent based on previous session and current state
# # #     - Calls the generative LLM model
# # #     - Parses out next mix intent (with robust JSON fallback/explanation)
# # # 4. Returns output for use by main Streamlit app and transition UI
# # # ---------------------------------------------------------------------------

# # from google import genai
# # import os
# # import re
# # import json
# # from schemas import MixIntent, StemIntent

# # def generate_mix_intent_from_folder(theme: str,
# #                                    base_dir: str = "audio_clips",
# #                                    default_gain: float = 0.8,
# #                                    default_fade: float = 2.0
# #                                    ) -> MixIntent:
# #     """
# #     Scans the audio_clips/{theme}/ directory for .wav files,
# #     generates default gain/fade, and returns a MixIntent object.
# #     """
# #     theme_dir = os.path.join(base_dir, theme)
# #     if not os.path.exists(theme_dir):
# #         raise FileNotFoundError(f"Theme folder not found: {theme_dir}")

# #     stem_intents = []
# #     for fname in os.listdir(theme_dir):
# #         if fname.endswith(".wav"):
# #             stem_name = os.path.splitext(fname)[0]
# #             file_path = os.path.join(theme_dir, fname)
# #             stem_intents.append(
# #                 StemIntent(
# #                     stem_name=stem_name,
# #                     file_path=file_path,
# #                     target_gain=default_gain,
# #                     fade_duration=default_fade
# #                 )
# #             )
# #     return MixIntent(theme=theme, stem_intents=stem_intents)

# # class LLMAdvisor:
# #     """
# #     Advisor class to interact with Gemini/Google LLM API for
# #     generating music transition intents and explanations.
# #     """
# #     def __init__(self, model_name="gemini-2.5-flash"):
# #         # Load LLM API key from environment and initialize client
# #         self.model_name = model_name
# #         apikey = os.getenv("GOOGLE_API_KEY")
# #         if not apikey:
# #             raise ValueError("GOOGLE_API_KEY environment variable not set")
# #         self.client = genai.Client(api_key=apikey)

# #     def recommend(self, session_log, current_state, next_theme, user_query=None):
# #         """
# #         Recommend the next mix intent (stems, gains, fades) via LLM API, given session log and theme.
# #         """
# #         prompt = self._build_prompt(session_log, current_state, next_theme, user_query)
# #         response = self._call_llm_api(prompt)
# #         return self._parse_response(response)

# #     def _build_prompt(self, session_log, current_state, next_theme, user_query):
# #         """
# #         Construct LLM prompt with schema and complete context.
# #         Always asks for valid JSON first, then reasoning/explanation.
# #         """
# #         schema_description = '''Respond in two parts:
# # 1. A valid JSON object describing the next musical intent for this session, using this schema:
# #     "theme": str,
# #     "activestems": [str],
# #     "targetgains": {str: float},
# #     "fadedurations": {str: float},
# #     "timestamp": str

# # 2. A detailed explanation of your reasoning for the choice, in plain text (not markdown).
# # Always put the JSON block first, then the explanation.
# # '''
# #         prompt = (
# #             f"Session log: {session_log}\n"
# #             f"Current state: {current_state}\n"
# #             f"Current theme: {current_state[0]['filename'].split('/')[0] if current_state else '[unknown]'}\n"
# #             f"Next theme: {next_theme}\n"
# #             f"{schema_description}\n"
# #             f"Transition the music mix from the current theme to the provided NEXT_THEME ('{next_theme}').\n"
# #             f"Given that the user requests to transition, generate all stem info for the NEXT_THEME ONLY.\n"
# #             "What is the next musical intent?"
# #         )
# #         if user_query:
# #             prompt += f"\nUser question: {user_query}"
# #         return prompt

# #     def _call_llm_api(self, prompt):
# #         """
# #         Calls the Gemini/Google LLM model using the prompt (API key must be set).
# #         """
# #         response = self.client.models.generate_content(
# #             model=self.model_name,
# #             contents=prompt
# #         )
# #         try:
# #             # Gemini returns .candidates, OpenAI returns .text or similar
# #             candidates = getattr(response, "candidates", None)
# #             if candidates:
# #                 parts = candidates[0]['content']['parts']
# #                 result = parts[0]['text'] if parts else str(response)
# #             else:
# #                 result = getattr(response, "text", str(response))
# #         except Exception:
# #             result = str(response)
# #         return result

# #     def _parse_response(self, response):
# #         """
# #         Attempts to parse the LLM's response into two fields:
# #           - next_intent (JSON for new musical stem plan)
# #           - explanation (freeform text)
# #         Handles fallback for malformed output/JSON blocks.
# #         """
# #         result = {"next_intent": {}, "explanation": ""}
# #         try:
# #             # Match JSON object at top of response, then treat rest as explanation
# #             match = re.match(r"\s*({[\s\S]+?})\s*([\s\S]+)", response)
# #             if match:
# #                 intent_json = match.group(1)
# #                 explanation = match.group(2)
# #                 intent = json.loads(intent_json)
# #                 result["next_intent"] = intent
# #                 result["explanation"] = explanation
# #             else:
# #                 # --- Robust fallback: Find any JSON block in full LLM text ---
# #                 explanation = response
# #                 json_regex = re.findall(r'``````', response)
# #                 if not json_regex:
# #                     json_regex = re.findall(r'({[\s\S]+?})', response)
# #                 if json_regex:
# #                     try:
# #                         intent = json.loads(json_regex[0])
# #                         result["next_intent"] = intent
# #                         result["explanation"] = explanation
# #                     except Exception as e:
# #                         result["explanation"] = f"Failed to parse JSON: {e}\nRaw response: {response}"
# #                 else:
# #                     result["explanation"] = response
# #         except Exception as e:
# #             result["explanation"] = f"Failed to parse: {e}\nRaw response: {response}"
# #         return result
