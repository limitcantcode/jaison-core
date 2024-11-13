'''
Class implementing TTS generation using OpenAI TTS service.
'''

from openai import OpenAI
from .base_worker import BaseTTSGenWorker

class OpenAITTSWorker(BaseTTSGenWorker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = OpenAI()

    def tts(self, msg: str):
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=msg
        )

        response.stream_to_file(self.output_filepath)