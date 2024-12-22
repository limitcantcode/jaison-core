'''
Class implementing TTS generation using old-school speech synthesis.
This may require espeak for Linux. Voices available will differ between OS,
and available voices for your OS can be found using get_available_voices
'''

from .base_worker import BaseTTSGenModel
import pyttsx3
from utils.logging import create_sys_logger
logger = create_sys_logger()

class OldTTSModel(BaseTTSGenModel):
    def __init__(self, config):
        super().__init__(config)
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', self.config.ttsg_voice)
        self.engine.setProperty('gender', 'male')


    def __call__(self, content: str):
        logger.debug("Transforming with traditional synthesis engine...")
        self.engine.save_to_file(content, self.config.RESULT_TTSG)
        self.engine.runAndWait()

    '''
    Get a list of available voices, names of which can be use to r
    eplace the 'voice' property in the __init__ function
    '''
    def get_available_voices(self):
        voices = self.engine.getProperty('voices')
        for ind in range(len(voices)):
            print(ind, voices[ind].id)