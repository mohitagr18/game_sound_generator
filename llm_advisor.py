from google import genai
import os
import re
import json
from schemas import MixIntent, StemIntent

def generate_mix_intent_from_folder(theme: str,
                                   base_dir: str = "audio_clips",
                                   default_gain: float = 0.8,
                                   default_fade: float = 2.0
                                   ) -> MixIntent:
    """Scans audioclips/{theme}/ for .wav files, returns MixIntent."""
    theme_dir = os.path.join(base_dir, theme)
    if not os.path.exists(theme_dir):
        raise FileNotFoundError(f"Theme folder not found: {theme_dir}")

    stem_intents = []
    for fname in os.listdir(theme_dir):
        if fname.endswith(".wav"):
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
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        apikey = os.getenv("GOOGLE_API_KEY")
        if not apikey:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = genai.Client(api_key=apikey)

    def recommend(self, session_log, current_state, next_theme, user_query=None):
        prompt = self._build_prompt(session_log, current_state, next_theme, user_query)
        response = self._call_llm_api(prompt)
        return self._parse_response(response)

    def _build_prompt(self, session_log, current_state, next_theme, user_query):
        schema_description = '''Respond in two parts:
1. A valid JSON object describing the next musical intent for this session, using this schema:
    "theme": str,
    "activestems": [str],
    "targetgains": {str: float},
    "fadedurations": {str: float},
    "timestamp": str

2. A detailed explanation of your reasoning for the choice, in plain text (not markdown).
Always put the JSON block first, then the explanation.
'''
        prompt = (
            f"Session log: {session_log}\n"
            f"Current state: {current_state}\n"
            f"Current theme: {current_state[0]['filename'].split('/')[0] if current_state else '[unknown]'}\n"
            f"Next theme: {next_theme}\n"
            f"{schema_description}\n"
            f"Transition the music mix from the current theme to the provided NEXT_THEME ('{next_theme}').\n"
            f"Given that the user requests to transition, generate all stem info for the NEXT_THEME ONLY.\n"
            "What is the next musical intent?"
        )
        if user_query:
            prompt += f"\nUser question: {user_query}"
        return prompt

    def _call_llm_api(self, prompt):
        # This method assumes working Gemini/Google-provided API and correct auth.
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        try:
            candidates = getattr(response, "candidates", None)
            if candidates:
                parts = candidates[0]['content']['parts']
                result = parts[0]['text'] if parts else str(response)
            else:
                result = getattr(response, "text", str(response))
        except Exception:
            result = str(response)
        return result

    def _parse_response(self, response):
        result = {"next_intent": {}, "explanation": ""}
        try:
            # First try simple extraction
            match = re.match(r"\s*({[\s\S]+?})\s*([\s\S]+)", response)
            if match:
                intent_json = match.group(1)
                explanation = match.group(2)
                intent = json.loads(intent_json)
                result["next_intent"] = intent
                result["explanation"] = explanation
            else:
                # --- Robust Fallback: extract any JSON block inside triple backticks or anywhere ---
                explanation = response
                json_regex = re.findall(r'``````', response)
                if not json_regex:
                    json_regex = re.findall(r'({[\s\S]+?})', response)
                if json_regex:
                    try:
                        intent = json.loads(json_regex[0])
                        result["next_intent"] = intent
                        result["explanation"] = explanation
                    except Exception as e:
                        result["explanation"] = f"Failed to parse JSON: {e}\nRaw response: {response}"
                else:
                    result["explanation"] = response
        except Exception as e:
            result["explanation"] = f"Failed to parse: {e}\nRaw response: {response}"
        return result
