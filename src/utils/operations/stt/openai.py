import wave
from openai import AsyncOpenAI
from pathlib import Path

from utils.config import Config

from .base import STTOperation

class OpenAISTT(STTOperation):
    def __init__(self):
        super().__init__("openai")
        self.client = None
        
        self.base_url: str = "https://api.openai.com/v1/"
        self.model: str = "gpt-4o"
        self.language: str = "en"
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        self.client = AsyncOpenAI(base_url=self.base_url)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        self.client.close()
        self.client = None
            
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "base_url" in config_d: self.base_url = str(config_d['base_url'])
        if "model" in config_d: self.model = str(config_d['model'])
        if "language" in config_d: self.language = str(config_d['language'])
        
        assert self.base_url is not None and len(self.base_url) > 0
        assert self.model is not None and len(self.model) > 0
        assert self.language is not None and len(self.language) > 0
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "base_url": self.base_url,
            "model": self.model,
            "language": self.language
        }

    async def _generate(self, prompt: str = None,  audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        '''Generate a output stream'''
        with wave.open(Config().stt_working_src, 'w') as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)

        transcription = await self.client.audio.transcriptions.create(
            file=Path(Config().stt_working_src),
            model=self.model,
            response_format="text",
            language=self.language,
            prompt=prompt
        )
        
        yield {"transcription": transcription}