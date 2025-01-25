'''
Class implementing TTS generation using OpenAI TTS service.
'''

from openai import OpenAI
from .base_worker import BaseTTSGenModel
from utils.logging import create_sys_logger
logger = create_sys_logger()

class OpenAITTSModel(BaseTTSGenModel):
    def __call__(self, content: str):
        logger.debug("Transforming with OpenAI Voice models...")
        client = OpenAI()
        response = client.audio.speech.create(
            model="tts-1",
            voice=self.config.ttsg_voice,
            input=content
        )
        logger.debug("Finished transformation. Copying results...")
        response.stream_to_file(self.config.RESULT_TTSG)