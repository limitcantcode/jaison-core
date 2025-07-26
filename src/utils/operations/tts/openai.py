import wave
from io import BytesIO
from openai import AsyncOpenAI

from utils.config import Config

from .base import TTSOperation

class OpenAITTS(TTSOperation):
    def __init__(self):
        super().__init__("openai")
        self.client = None
        
        self.base_url = "https://api.openai.com/v1/"
        self.voice = "nova"
        self.model = "tts-1"
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        self.client = AsyncOpenAI(base_url=self.base_url)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        await self.client.close()
        self.client = None

    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "base_url" in config_d: self.base_url = str(config_d["base_url"])
        if "voice" in config_d: self.voice = str(config_d["voice"])
        if "model" in config_d: self.model = str(config_d["model"])
        
        assert self.base_url is not None and len(self.base_url) > 0
        assert self.voice is not None and len(self.voice) > 0
        assert self.model is not None and len(self.model) > 0
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "base_url": self.base_url,
            "voice": self.voice,
            "model": self.model
        }

    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        async with self.client.audio.speech.with_streaming_response.create(
            model=self.model,
            voice=self.voice,
            input=content,
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