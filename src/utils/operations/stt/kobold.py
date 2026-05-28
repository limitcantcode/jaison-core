import base64
import wave
from io import BytesIO

import requests

from utils.processes import ProcessType

from .base import STTOperation


class KoboldSTT(STTOperation):
    KOBOLD_LINK_ID = "kobold_stt"

    def __init__(self):
        super().__init__("kobold")
        self.uri = None

        self.suppress_non_speech: bool = True
        self.langcode: str = "en"

    async def start(self) -> None:
        """General setup needed to start generated"""
        await super().start()
        if self.process_manager is None:
            raise RuntimeError("KoboldSTT missing runtime dependency: process_manager")
        await self.process_manager.link(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
        self.uri = f"http://127.0.0.1:{self.process_manager.get_process(ProcessType.KOBOLD).port}"

    async def close(self) -> None:
        """Clean up resources before unloading"""
        await super().close()
        if self.process_manager is None:
            return
        await self.process_manager.unlink(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)

    async def configure(self, config_d):
        """Configure and validate operation-specific configuration"""
        if "suppress_non_speech" in config_d:
            self.suppress_non_speech = bool(config_d["suppress_non_speech"])
        if "langcode" in config_d:
            self.langcode = str(config_d["langcode"])

        assert self.langcode is not None and len(self.langcode) > 0

    async def get_configuration(self):
        """Returns values of configurable fields"""
        return {"suppress_non_speech": self.suppress_non_speech, "langcode": self.langcode}

    async def _generate(
        self,
        prompt: str = None,
        audio_bytes: bytes = None,
        sr: int = None,
        sw: int = None,
        ch: int = None,
        **kwargs,
    ):
        """Generate a output stream"""
        audio_data = BytesIO()
        with wave.open(audio_data, "wb") as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)
        audio_data.seek(0)

        response = requests.post(
            f"{self.uri}/api/extra/transcribe",
            json={
                "prompt": prompt,
                "suppress_non_speech": self.suppress_non_speech,
                "langcode": self.langcode,
                "audio_data": base64.b64encode(audio_data.read()).decode("utf-8"),
            },
        )

        if response.status_code == 200:
            result = response.json()["text"]
            yield {"transcription": result}
        else:
            raise Exception(f"Failed to get STT result: {response.status_code} {response.reason}")
