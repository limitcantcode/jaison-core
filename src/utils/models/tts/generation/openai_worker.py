'''
Class implementing TTS generation using OpenAI TTS service.
'''

from openai import OpenAI
from .base_worker import BaseTTSGenWorker
from utils.logging import system_logger

class OpenAITTSWorker(BaseTTSGenWorker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = OpenAI()
        system_logger.debug("OpenAITTSWorker loaded.")

    def tts(self, msg: str):
        system_logger.debug("OpenAITTSWorker called.")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=msg
        )

        response.stream_to_file(self.output_filepath)
        system_logger.debug("OpenAITTSWorker finished.")