import requests
from io import BytesIO
import wave

from utils.config import Config
from utils.processes import ProcessManager, ProcessType

from .base import TTSOperation

class KoboldTTS(TTSOperation):
    KOBOLD_LINK_ID = "kobold_tts"
    
    def __init__(self):
        super().__init__("kobold")
        self.uri = None
        
        self.voice = "kobo"
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        await ProcessManager().link(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
        self.uri = "http://127.0.0.1:{}".format(ProcessManager().get_process(ProcessType.KOBOLD).port)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        await ProcessManager().unlink(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
    
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "voice" in config_d: self.voice = str(config_d["voice"])
        
        assert self.voice is not None and len(self.voice) > 0
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "voice": self.voice
        }

    async def _generate(self, content: str = None, **kwargs):
        response = requests.post(
            "{}/api/extra/tts".format(self.uri), 
            json={
                "input": content,
                "voice": self.voice,
                "speaker_json": ""
            },
        )

        if response.status_code == 200:
            result = response.content
            audio = BytesIO(result)
            with wave.open(audio, 'r') as f:
                yield {"audio_bytes": f.readframes(f.getnframes()), "sr": f.getframerate(), "sw": f.getsampwidth(), "ch": f.getnchannels()}
        else:
            raise Exception(f"Failed to get T2T result: {response.status_code} {response.reason}")