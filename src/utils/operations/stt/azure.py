import io
import wave
import os
import asyncio
import azure.cognitiveservices.speech as speechsdk

from utils.config import Config

from .base import STTOperation

class AzureSTT(STTOperation):
    def __init__(self):
        super().__init__("azure")
        self.client = None
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        
        self.speech_config = speechsdk.SpeechConfig(
            region=os.environ.get('AZURE_REGION'),
            subscription=os.getenv("AZURE_API_KEY")
        )
        
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
            language=Config().azure_stt_language
        )

        # Setup event callbacks
        transcription = ""
        done = asyncio.Event()
        done.clear()
        def transcribed_cb(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                transcription += evt.result.text
        
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