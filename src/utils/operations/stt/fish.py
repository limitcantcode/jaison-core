import io
import wave
import os

from fish_audio_sdk import Session, ASRRequest

from .base import STTOperation

class FishSTT(STTOperation):
    def __init__(self):
        super().__init__("fish")
        self.session = None
        
    async def start(self):
        await super().start()
        self.session = Session(os.getenv("FISH_API_KEY"))
        
    async def unload(self):
        await super().close()
        await self.session.close()
        self.session = None
        
                    
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        return
    
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {}

    async def _generate(self, prompt: str = None,  audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        '''Generate a output stream'''
        audio_data = io.BytesIO()
        with wave.open(audio_data, 'wb') as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)
        audio_data.seek(0)

        response = self.session.asr(ASRRequest(audio=audio_data.read(), language="en", ignore_timestamps=False))
        result = response.text

        yield {"transcription": result}