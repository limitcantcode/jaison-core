'''
Class implementing TTS generation using old-school speech synthesis.
This version runs entirely offline.This may require espeak for Linux. 
Voices available will differ between OS, and available voices for your 
OS can be found using get_available_voices
'''

import logging
import pyttsx3
import wave

from utils.config import Config

from .base import TTSOperation

class PyttsTTS(TTSOperation):
    def __init__(self):
        super().__init__("pytts")
        self.engine = None
        
    async def start(self):
        await super().start()
        
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        logging.info("Operation {}: Available voices are: {}".format(self.id, list(map(lambda x: x.id, voices))))
        
        self.engine.setProperty('voice', Config().synth_ttsg_voice_name)
        self.engine.setProperty('gender', Config().synth_ttsg_gender)
        
    async def close(self):
        await super().close()
        self.engine.stop()
        self.engine = None
     
    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        self.engine.save_to_file(content, Config().synth_ttsg_working_file)
        self.engine.runAndWait()
        
        with wave.open(Config().synth_ttsg_working_file, 'r') as f:
            yield {
                "audio_bytes": f.readframes(f.getnframes()),
                "sr": f.getframerate(),
                "sw": f.getsampwidth(),
                "ch": f.getnchannels()
            }