'''
Class implementing TTS generation using old-school speech synthesis.
This version runs entirely offline.This may require espeak for Linux. 
Voices available will differ between OS, and available voices for your 
OS can be found using get_available_voices
'''

import logging
import pyttsx3
import wave
from typing import Dict, AsyncGenerator, Any
from utils.config import Config
from .meta import TTSGOperation
from ..base import Capability

class PyttsTTSG(TTSGOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.engine = None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.engine is not None: self.unload()
        
        self.engine = pyttsx3.init()
        
        voices = self.engine.getProperty('voices')
        logging.debug("Operation {}: Available voices are: {}".format(self.id, list(map(lambda x: x.id, voices))))

        self.engine.setProperty('voice', Config().synth_ttsg_voice_name)
        self.engine.setProperty('gender', Config().synth_ttsg_gender)
        
    async def unload(self):
        self.engine.stop()
        self.engine = None
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator[Dict[str, Any]] = None,
        **kwargs
    ):
        async for in_d in in_stream:
            yield await self._generate(in_stream['content'])

    async def _generate(self, content: str):
        assert content is not None and len(content) > 0
        
        self.engine.save_to_file(content, Config().sythn_ttsg_working_file)
        self.engine.runAndWait()
        
        with wave.open(Config().synth_ttsg_working_file, 'r') as f:
            return {
                "audio_bytes": f.readframes(f.getnframes()),
                "sr": f.getframerate(),
                "sw": f.getsampwidth(),
                "ch": f.getnchannels()
            }