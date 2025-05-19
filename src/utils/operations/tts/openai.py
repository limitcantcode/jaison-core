import wave
from io import BytesIO
from openai import AsyncOpenAI

from utils.config import Config

from .base import TTSOperation

class OpenAITTS(TTSOperation):
    def __init__(self):
        super().__init__("openai")
        self.client = None
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        self.client = AsyncOpenAI(base_url=Config().openai_ttsg_base_url)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        self.client.close()
        self.client = None
    
    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        async with self.client.audio.speech.with_streaming_response.create(
            model=Config().openai_ttsg_model,
            voice=Config().openai_ttsg_voice,
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