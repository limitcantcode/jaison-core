import wave
from openai import AsyncOpenAI
from pathlib import Path

from utils.config import Config

from .base import STTOperation

class OpenAISTT(STTOperation):
    def __init__(self):
        super().__init__("openai")
        self.client = None
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        self.client = AsyncOpenAI(base_url=Config().openai_stt_base_url)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        self.client.close()
        self.client = None
    
    async def _generate(self, prompt: str = None,  audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        '''Generate a output stream'''
        with wave.open(Config().stt_working_src, 'w') as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)

        transcription = await self.client.audio.transcriptions.create(
            file=Path(Config().stt_working_src),
            model=Config().openai_stt_model,
            response_format="text",
            language=Config().openai_stt_language,
            prompt=prompt
        )
        
        yield {"transcription": transcription}