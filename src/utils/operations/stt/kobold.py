from io import BytesIO
import wave
import requests
import base64

from utils.config import Config
from utils.processes import ProcessManager, ProcessType

from .base import STTOperation

class KoboldSTT(STTOperation):
    KOBOLD_LINK_ID = "kobold_stt"
    
    def __init__(self):
        super().__init__("kobold")
        self.uri = None
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        await ProcessManager().link(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
        self.uri = "http://127.0.0.1:{}".format(ProcessManager().get_process(ProcessType.KOBOLD).port)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        await ProcessManager().unlink(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
    
    async def _generate(self, prompt: str = None,  audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        '''Generate a output stream'''
        audio_data = BytesIO()
        with wave.open(audio_data, 'wb') as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)
        audio_data.seek(0)

        response = requests.post(
            "{}/api/extra/transcribe".format(self.uri), 
            json={
                "prompt": prompt,
                "suppress_non_speech": Config().kobold_stt_suppress_non_speech,
                "langcode": Config().kobold_stt_langcode,
                "audio_data": base64.b64encode(audio_data.read()).decode('utf-8')
            },
        )

        if response.status_code == 200:
            result = response.json()['text']
            yield {"transcription": result}
        else:
            raise Exception(f"Failed to get STT result: {response.status_code} {response.reason}")