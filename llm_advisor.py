# ---------------------------------------------------------------------------
# llm_advisor.py
# ---------------------------------------------------------------------------
# Updates:
# 1. In recommend(), we now scan the next_theme folder first.
# 2. We pass the 'valid_stems' list to the prompt.
# 3. The prompt explicitly forbids hallucinating filenames not in the list.
# ---------------------------------------------------------------------------

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

