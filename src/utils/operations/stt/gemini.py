import logging
import google.generativeai as genai
from typing import Dict, AsyncGenerator
from .base import STTOperation
from utils.config import Config
import io
import os

class GeminiSTT(STTOperation):
    def __init__(self):
        super().__init__("gemini")
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model_name = "gemini-2.0-flash"  
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    async def _transcribe(self, audio_data: bytes) -> str:
        try:
            audio_bytes = io.BytesIO(audio_data)
            response = self.model.generate_content(["This is an audio file. Please transcribe it.", audio_bytes], stream=False)
            return response.text()
        except Exception as e:
            logging.error(f"Gemini STT API error: {e}", exc_info=True)
            return f"Error transcribing audio with Gemini: {e}"
