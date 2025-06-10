import os
import wave
from io import BytesIO
import azure.cognitiveservices.speech as speechsdk

from utils.config import Config

from .base import TTSOperation

class AzureTTS(TTSOperation):
    def __init__(self):
        super().__init__("azure")
        self.client = None
        
        self.voice: str = "en-US-AshleyNeural"
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        
        self.speech_config = speechsdk.SpeechConfig(
            region=os.environ.get('AZURE_REGION'),
            subscription=os.getenv("AZURE_API_KEY")
        )
        self.speech_config.speech_synthesis_voice_name = self.voice
        self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm)
        # set timeout value to bigger ones to avoid sdk cancel the request when GPT latency too high
        self.speech_config.set_property(speechsdk.PropertyId.SpeechSynthesis_FrameTimeoutInterval, "100000000")
        self.speech_config.set_property(speechsdk.PropertyId.SpeechSynthesis_RtfTimeoutThreshold, "10")
        
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=None)
                
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "voice" in config_d: self.voice = str(config_d['voice'])
        
        assert self.voice is not None and len(self.voice) > 0
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "voice": self.voice
        }

    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        # create request with TextStream input type
        result = self.speech_synthesizer.speak_text_async(content).get()
        
        output_b = BytesIO(result.audio_data)
        
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