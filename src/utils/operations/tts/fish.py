from fish_audio_sdk import AsyncWebSocketSession, TTSRequest
import os

from utils.config import Config

from .base import TTSOperation

class FishTTS(TTSOperation):
    def __init__(self):
        super().__init__("fish")
        self.session = None
        
        self.model_id = "c9198512a4164a18b11a3bf96e5c668f"
        self.backend = "speech-1.6"
        self.normalize = False
        self.latency = "normal"
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        self.session = AsyncWebSocketSession(os.getenv("FISH_API_KEY"))
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        await self.session.close()
        self.session = None
    
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "model_id" in config_d: self.model_id = str(config_d["model_id"])
        if "backend" in config_d: self.backend = str(config_d["backend"])
        if "normalize" in config_d: self.normalize = bool(config_d["normalize"])
        if "latency" in config_d: self.latency = str(config_d["latency"])
        
        assert self.model_id is not None and len(self.model_id) > 0
        assert self.backend is not None and len(self.backend) > 0
        assert self.latency in ['normal', 'balanced']
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "model_id": self.model_id,
            "backend": self.backend,
            "normalize": self.normalize,
            "latency": self.latency,
        }

    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        tts_request = TTSRequest(
            text=content,
            format="pcm",
            normalize=self.normalize,
            latency=self.latency,
            reference_id=self.model_id
        )
        b = b''
        async for chunk in self.session.tts(
            tts_request,
            self._stream(),
            backend=self.backend
        ):
            b += chunk
            
        yield {"audio_bytes": b, "sr": 44100, "sw": 2, "ch": 1}
    
    async def _stream(self):
        yield ""