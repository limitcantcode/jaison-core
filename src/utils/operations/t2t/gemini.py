import logging
import google.generativeai as genai
from typing import Dict, AsyncGenerator
from .base import T2TOperation
from utils.config import Config
import json
import os

class GeminiT2T(T2TOperation):

    def __init__(self):
        super().__init__("gemini")
        self.api_key = os.environ.get("GEMINI_API_KEY") 
        self.model_name = "gemini-2.0-flash"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    async def _generate(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[Dict, None]:
        try:
            prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.model.generate_content(prompt)
            for chunk in response.parts:
                content = chunk.text
                yield {"content": content}
        except Exception as e:
            logging.error(f"Gemini API error: {e}", exc_info=True)
            yield {"content": f"Error generating text with Gemini: {e}"}
