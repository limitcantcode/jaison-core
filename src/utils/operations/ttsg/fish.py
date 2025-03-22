from fish_audio_sdk import AsyncWebSocketSession, TTSRequest
import os
import logging
from typing import AsyncGenerator
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
        tts_request = TTSRequest(
            text="",
            format="pcm",
            normalize=Config().fish_normalize,
            latency=Config().fish_latency,
            sample_rate=44100, # sw: 2, ch 1
            reference_id=Config().fish_model_id
        )
        async for chunk in self.session.tts(
            tts_request,
            self._stream(in_stream),
            backend=Config().fish_model_backend
        ):
            if len(chunk) > 0:
                yield {"audio_bytes": bytes(chunk), "sr": 44100, "sw": 2, "ch": 1}


    async def _stream(self, in_stream: AsyncGenerator):
        async for in_d in in_stream:
            yield in_d['content']