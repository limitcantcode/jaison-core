from utils.config import Config
from utils.helpers.audio import pitch_audio

from .base import FilterAudioOperation

class PitchFilter(FilterAudioOperation):   
    def __init__(self):
        super().__init__("pitch")
        
    async def _generate(self, audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        ab, sr, sw, ch = pitch_audio(audio_bytes, sr, sw, ch, Config().pitch_amount)
        yield {
            "audio_bytes": ab,
            "sr": sr,
            "sw": sw,
            "ch": ch
        }
    