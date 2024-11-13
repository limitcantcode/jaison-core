'''
This class is responsible for transcribing audio
from wave files.
'''

import whisper

class STTWorker():
    def __init__(self):
        self.model = whisper.load_model("turbo")

    '''
    Transcribed input wave file that contains speech.

    Returns (str) the transcribed text.
    '''
    def __call__(self, filepath):
        result = self.model.transcribe(filepath, language='English')
        return result["text"]