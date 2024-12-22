'''
This class is responsible for transcribing audio
from wave files.
'''

import whisper
from utils.logging import create_sys_logger

logger = create_sys_logger()

class STTModel():
    def __init__(self, config):
        self.model = whisper.load_model("turbo")
        logger.debug("STTModel initialized!")


    '''
    Transcribed input wave file that contains speech.

    Returns (str) the transcribed text.
    '''
    def __call__(self, filepath):
        logger.debug(f"Got request to transcribe {filepath}")
        result = self.model.transcribe(filepath, language='English')
        logger.debug(f"Got transcription result: {result}")
        return result["text"]