import requests
from io import BytesIO
import wave

from utils.config import Config
from utils.processes import ProcessManager, ProcessType

from .base import T2TOperation

class KoboldTTS(T2TOperation):
    KOBOLD_LINK_ID = "kobold_tts"
    
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
    
    async def _generate(self, content: str = None, **kwargs):
        response = requests.post(
            "{}/api/extra/tts".format(self.uri), 
            json={
                "input": content,
                "voice": Config().kobold_tts_voice,
                "speaker_json": ""
            },
        )

        if response.status_code == 200:
            result = response.text
            audio = BytesIO(result)
            with wave.open(audio, 'r') as f:
                yield {"audio_bytes": f.readframes(f.getnframes()), "sr": f.getframerate(), "sw": f.getsampwidth(), "ch": f.getnchannels()}
        else:
            raise Exception(f"Failed to get T2T result: {response.status_code} {response.reason}")