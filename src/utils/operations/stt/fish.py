import io
import wave
import logging
import os
from typing import AsyncGenerator
from fish_audio_sdk import Session, ASRRequest
from .meta import STTOperation
from ..base import Capability

class FishSTT(STTOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.session = None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.session is not None: await self.unload()
        self.session = Session(os.getenv("FISH_API_KEY"))
        
    async def unload(self):
        await self.session.close()
        self.session = None
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        audio_bytes: bytes = b''
        sr: int = -1
        sw: int = -1
        ch: int = -1
        async for in_d in in_stream:
            audio_bytes += in_d['audio_bytes']
            sr = in_d['sr']
            sw = in_d['sw']
            ch = in_d['ch']
            
        assert audio_bytes is not None and len(audio_bytes) > 0
        assert sr > 0
        assert sw > 0
        assert ch > 0

        audio_data = io.BytesIO()
        with wave.open(audio_data, 'wb') as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)
        audio_data.seek(0)

        response = self.session.asr(ASRRequest(audio=audio_data.read(), language="en", ignore_timestamps=False))
        result = response.text

        logging.info(f"Operation {self.id} got result: {result:.200}")
        yield {"transcription": result}