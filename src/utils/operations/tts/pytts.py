'''
Class implementing TTS generation using old-school speech synthesis.
This version runs entirely offline.This may require espeak for Linux. 
Voices available will differ between OS, and available voices for your 
OS can be found using get_available_voices
'''

import logging
import pyttsx3
import wave
import os

from utils.helpers.path import portable_path
from utils.config import Config

from .base import TTSOperation

class PyttsTTS(TTSOperation):
    def __init__(self):
        super().__init__("pytts")
        self.engine = None
        
        self.voice: str = None
        self.gender: str = 'female'
        self.working_file: str = portable_path(os.path.join(Config().WORKING_DIR,'ttsg-synth-out.wav'))  

    async def start(self):
        await super().start()
        
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        logging.info("Operation {}: Available voices are: {}".format(self.op_id, list(map(lambda x: x.id, voices))))
        
        self.engine.setProperty('voice', self.voice)
        self.engine.setProperty('gender', self.gender)

    async def close(self):
        await super().close()
        self.engine.stop()
        self.engine = None

    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "voice" in config_d: self.voice = str(config_d['voice'])
        if "gender" in config_d: self.gender = str(config_d['gender'])
        if "working_file" in config_d: self.working_file = str(config_d['working_file'])
        
        assert self.voice is not None and len(self.voice) > 0
        assert self.working_file is not None and len(self.working_file) > 0
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "voice": self.voice,
            "gender": self.gender,
            "working_file": self.working_file
        }

    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        self.engine.save_to_file(content, self.working_file)
        self.engine.runAndWait()
        
        with wave.open(self.working_file, 'r') as f:
            yield {
                "audio_bytes": f.readframes(f.getnframes()),
                "sr": f.getframerate(),
                "sw": f.getsampwidth(),
                "ch": f.getnchannels()
            }