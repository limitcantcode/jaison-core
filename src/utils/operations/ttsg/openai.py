import logging
import wave
from io import BytesIO
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
            async with self.client.audio.speech.with_streaming_response.create(
                model=Config().openai_ttsg_model,
                voice=Config().openai_ttsg_voice,
                input=in_d['content'],
                response_format="wav",
            ) as response:
                output_b = BytesIO(await response.read())
        
                with wave.open(output_b, "r") as f:
                    sr = f.getframerate()
                    sw = f.getsampwidth()
                    ch = f.getnchannels()
                    ab = f.readframes(f.getnframes())
                
                yield {
                    "audio_bytes": ab,
                    "sr": sr,
                    "sw": sw,
                    "ch": ch
                }