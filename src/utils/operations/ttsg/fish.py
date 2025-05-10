from fish_audio_sdk import AsyncWebSocketSession, TTSRequest
import os
import logging
import wave
from typing import AsyncGenerator
from io import BytesIO

from utils.config import Config
from .meta import TTSGOperation
from ..base import Capability

class FishTTSG(TTSGOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.session = None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.session is not None: await self.unload()
        self.session = AsyncWebSocketSession(os.getenv("FISH_API_KEY"))
        
    async def unload(self):
        await self.session.close()
        self.session = None
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        async for in_d in in_stream:
            content= in_d['content']
            logging.critical(content)
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