# llm_advisor.py (full file with separated helpers)

from google import genai
import os
import re
import json

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
        # Find the first JSON block, either as plain `{...}` or inside ``````
        match = re.search(r'``````|({[\s\S]+?})', text)
        next_intent = {}
        explanation = text
        if match:
            json_str = match.group(1) if match.group(1) else match.group(2)
            try:
                next_intent = json.loads(json_str)
                # Remove both code block and JSON from explanation for clarity
                explanation = text.replace(f"``````", "").replace(json_str, "").strip()
            except Exception as e:
                print("Error parsing LLM JSON:", e)
        return {
            "next_intent": next_intent,
            "explanation": explanation
        }


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


    def _parse_intent(self, llm_output):
        # Regex to find first JSON object in response (inside or outside code block)
        match = re.search(r'``````|({[\s\S]+?})', llm_output)
        if match:
            json_str = match.group(1) if match.group(1) else match.group(2)
            try:
                return json.loads(json_str)
            except Exception as e:
                print("Error parsing LLM JSON:", e)
                return {}
        else:
            print("No JSON found in LLM response.")
            return {}


