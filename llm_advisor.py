# llm_advisor.py (full file with separated helpers)

from google import genai
import os
import re
import json

# ---- Utility to generate MixIntent from stems folder ----
from schemas import MixIntent, StemIntent

def generate_mix_intent_from_folder(theme: str,
                                    base_dir: str = "audioclips",
                                    default_gain: float = 0.8,
                                    default_fade: float = 2.0
                                   ) -> MixIntent:
    """
    Scans audioclips/{theme}/ for .wav files, returns MixIntent.
    """
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
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)

    def recommend(self, session_log, current_state, user_query=None):
        prompt = self._build_prompt(session_log, current_state, user_query)
        response = self._call_llm_api(prompt)
        return self._parse_response(response)

    def _call_llm_api(self, prompt):
        return self.client.models.generate_content(model=self.model_name, contents=prompt)

    def _parse_response(self, response):
        text = response.text
        match = re.search(r'```(?:json)?\s*({[\s\S]+?})\s*```|({[\s\S]+?})', text)
        
        next_intent = {}
        explanation = text
        
        if match:
            json_str = match.group(1) if match.group(1) else match.group(2)
            try:
                next_intent = json.loads(json_str)
                # Remove JSON/codeblock from explanation, preserve reasoning text
                explanation = text.replace(f"```{json_str}```", "").replace(json_str, "").strip()
            except Exception as e:
                print(f"Error parsing LLM JSON: {e}")
                print(f"Offending JSON string: {json_str}")
        return {
            "next_intent": next_intent,
            "explanation": explanation
        }

    def _parse_intent(self, llm_output):
        # Use the same robust regex here
        match = re.search(r'```(?:json)?\s*({[\s\S]+?})\s*```|({[\s\S]+?})', llm_output)
        
        if match:
            # This logic is also correct now
            json_str = match.group(1) if match.group(1) else match.group(2)
            try:
                return json.loads(json_str)
            except Exception as e:
                print(f"Error parsing LLM JSON: {e}")
                print(f"Offending JSON string: {json_str}")
                return {}
        else:
            print("No JSON found in LLM response.")
            return {}


    def _build_prompt(self, session_log, current_state, user_query):
        schema_description = '''
        Respond in two parts:
        1. A valid JSON object describing the next musical intent for this session, using this schema:
        {
        "theme": str,
        "activestems": [str],
        "targetgains": {str: float},
        "fadedurations": {str: float},
        "timestamp": str
        }
        2. A detailed explanation of your reasoning for the choice, in plain text (not markdown).
        Always put the JSON block first, then the explanation.
        '''
        prompt = (f"Session log: {session_log}\nCurrent state: {current_state}\n"
                f"{schema_description}\n"
                "What is the next musical intent?")
        if user_query:
            prompt += f"\nUser question: {user_query}"
        return prompt
