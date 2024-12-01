'''
This class is responsible for transcribing audio
from wave files.
'''

import whisper
from utils.logging import system_logger

class STTWorker():
    def __init__(self):
        self.model = whisper.load_model("turbo")
        system_logger.debug("STTWorker loaded.")

    '''
    Transcribed input wave file that contains speech.

    Returns (str) the transcribed text.
    '''
    def __call__(self, filepath):
        system_logger.debug("STTWorker called.")
        result = self.model.transcribe(filepath, language='English')
        system_logger.debug(f"STTWorker finished with result: {result}")
        return result["text"]