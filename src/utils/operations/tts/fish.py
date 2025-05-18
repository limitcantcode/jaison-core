from fish_audio_sdk import AsyncWebSocketSession, TTSRequest
import os

from utils.config import Config

from .base import TTSOperation

class FishTTS(TTSOperation):
    def __init__(self):
        super().__init__()
        self.session = None
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        self.session = AsyncWebSocketSession(os.getenv("FISH_API_KEY"))
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        await self.session.close()
        self.session = None
    
    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        tts_request = TTSRequest(
            text=content,
            format="pcm",
            normalize=Config().fish_normalize,
            latency=Config().fish_latency,
            reference_id=Config().fish_model_id
        )
        b = b''
        async for chunk in self.session.tts(
            tts_request,
            self._stream(),
            backend=Config().fish_model_backend
        ):
            b += chunk
            
        yield {"audio_bytes": b, "sr": 44100, "sw": 2, "ch": 1}
    
    async def _stream(self):
        yield ""