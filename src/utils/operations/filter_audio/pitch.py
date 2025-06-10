from utils.config import Config
from utils.helpers.audio import pitch_audio

from .base import FilterAudioOperation

class PitchFilter(FilterAudioOperation):   
    def __init__(self):
        super().__init__("pitch")
        
        self.pitch_amount: int = 0
        
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "pitch_amount" in config_d: self.pitch_amount = str(config_d["pitch_amount"])
                
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "pitch_amount": self.pitch_amount
        }

    async def _generate(self, audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        ab, sr, sw, ch = pitch_audio(audio_bytes, sr, sw, ch, self.pitch_amount)
        yield {
            "audio_bytes": ab,
            "sr": sr,
            "sw": sw,
            "ch": ch
        }
    