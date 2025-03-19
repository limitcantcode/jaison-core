import logging
from typing import Dict, AsyncGenerator, Any
from openai import AsyncOpenAI
from utils.config import Config
from .meta import TTSGOperation
from ..base import Capability

class OpenAITTSG(TTSGOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.client = None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.client is not None: await self.unload()
        self.client = AsyncOpenAI(base_url=Config().openai_ttsg_base_url)
        
    async def unload(self):
        self.client.close()
        self.client = None
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        async for in_d in in_stream:
            yield await self._generate(in_d['content'])
            
    async def _generate(self, content: str):
        assert content is not None and len(content) > 0
        
        # This should be called while sentence chunking, meaning the full output will already be sentence chunked.
        async with self.client.audio.speech.with_streaming_response.create(
            model=Config().openai_ttsg_model,
            voice=Config().openai_ttsg_voice,
            response_format="pcm",  # similar to WAV, but without a header chunk at the start.
            input=content
        ) as response:
            audio_bytes = b''
            async for chunk in response.iter_bytes(chunk_size=4096):
                audio_bytes += chunk
                
            return {
                "audio_bytes": audio_bytes,
                "sr": 24000,
                "sw": 2,
                "ch": 1
            }