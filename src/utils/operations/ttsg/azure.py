import os
import wave
from io import BytesIO
import azure.cognitiveservices.speech as speechsdk

from typing import AsyncGenerator
from utils.config import Config
from .meta import TTSGOperation
from ..base import Capability

class AzureTTSG(TTSGOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        self.speech_config = speechsdk.SpeechConfig(
            region=os.environ.get('AZURE_REGION'),
            subscription=os.getenv("AZURE_API_KEY")
        )
        self.speech_config.speech_synthesis_voice_name = Config().azure_ttsg_voice
        self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm)
        # set timeout value to bigger ones to avoid sdk cancel the request when GPT latency too high
        self.speech_config.set_property(speechsdk.PropertyId.SpeechSynthesis_FrameTimeoutInterval, "100000000")
        self.speech_config.set_property(speechsdk.PropertyId.SpeechSynthesis_RtfTimeoutThreshold, "10")
        
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
        
    async def unload(self):
        pass
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        async for in_d in in_stream:
            yield await self._generate(in_d['content'])
        
    async def _generate(self, content: str):
        assert content is not None and len(content) > 0
            
        # create request with TextStream input type
        result = self.speech_synthesizer.speak_text_async(content).get()
        
        output_b = BytesIO(result.audio_data)
        
        with wave.open(output_b, "r") as f:
            sr = f.getframerate()
            sw = f.getsampwidth()
            ch = f.getnchannels()
            ab = f.readframes(f.getnframes())
        
        return {
            "audio_bytes": ab,
            "sr": sr,
            "sw": sw,
            "ch": ch
        }
