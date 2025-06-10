import os
import asyncio
import azure.cognitiveservices.speech as speechsdk
import logging

from utils.config import Config

from .base import STTOperation

class AzureSTT(STTOperation):
    def __init__(self):
        super().__init__("azure")
        self.client = None
        
        self.language: str = "en-US"
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        
        self.speech_config = speechsdk.SpeechConfig(
            region=os.environ.get('AZURE_REGION'),
            subscription=os.getenv("AZURE_API_KEY")
        )
        
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "language" in config_d: self.model_id = str(config_d["language"])

        assert self.language is not None and len(self.language) > 0
    
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {"language": self.language}

    async def _generate(self, prompt: str = None,  audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        '''Generate a output stream'''
        # Setup transcriber with audio metadata
        wave_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=sr,
            bits_per_sample=sw*8,
            channels=ch,
            wave_stream_format=speechsdk.audio.AudioStreamWaveFormat.PCM
        )
        stream = speechsdk.audio.PushAudioInputStream(stream_format=wave_format)
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        transcriber = speechsdk.transcription.ConversationTranscriber(
            speech_config=self.speech_config,
            audio_config=audio_config,
            language=self.language
        )

        # Setup event callbacks
        transcription = ""
        done = asyncio.Event()
        done.clear()
        def transcribed_cb(evt):
            nonlocal transcription
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                transcription += str(evt.result)
        
        def stop_cb(evt: speechsdk.SessionEventArgs):
            done.set()
                
        transcriber.transcribed.connect(transcribed_cb)
        transcriber.session_stopped.connect(stop_cb)
        transcriber.canceled.connect(stop_cb)

        # Start transcribing
        transcriber.start_transcribing_async()
        stream.write(audio_bytes)
        stream.close()
        await done.wait()
        transcriber.stop_transcribing_async()

        yield {"transcription": transcription}