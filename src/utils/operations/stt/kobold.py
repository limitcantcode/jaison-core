import io
import wave
import requests
import base64
import logging
from typing import Dict, AsyncGenerator, Any
from utils.config import Config
from utils.processes import ProcessManager, DuplicateLink, MissingLink
from .meta import STTOperation
from ..base import Capability

class KoboldSTT(STTOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        pm = ProcessManager()
        try:
            await pm.koboldcpp.link(self.id)
        except DuplicateLink:
            pass
        
        pm.koboldcpp.reload_signal = True
        
    async def unload(self):
        pm = ProcessManager()
        try:
            await pm.koboldcpp.unlink(self.id)
        except MissingLink:
            pass
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        audio_bytes: bytes = b''
        sr: int = -1
        sw: int = -1
        ch: int = -1
        initial_prompt: str = ""
        async for in_d in in_stream:
            audio_bytes += in_d['audio_bytes']
            sr = in_d['sr']
            sw = in_d['sw']
            ch = in_d['ch']
            initial_prompt = in_d['initial_prompt']
            
        assert audio_bytes is not None and len(audio_bytes) > 0
        assert sr > 0
        assert sw > 0
        assert ch > 0
        
        uri = "http://127.0.0.1:{}".format(ProcessManager().koboldcpp.port)

        audio_data = io.BytesIO()
        with wave.open(audio_data, 'wb') as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)
        audio_data.seek(0)

        response = requests.post(
            "{}/api/extra/transcribe".format(uri), 
            json={
                "prompt": initial_prompt or '',
                "suppress_non_speech": Config().kobold_stt_suppress_non_speech,
                "langcode": Config().kobold_stt_langcode,
                "audio_data": base64.b64encode(audio_data.read()).decode('utf-8')
            },
        )

        if response.status_code == 200:
            result = response.json()['text']
            logging.debug(f"Operation {self.id} got result: {result:.200}")
            yield {"transcription": result}
        else:
            raise Exception(f"Failed to get STT result: {response.status_code} {response.reason}")