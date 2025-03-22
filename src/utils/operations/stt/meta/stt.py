from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

STT_TYPE = 'stt'

class STTOperation(BaseOperation):
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None, # {audio_bytes: bytes, sr: int, sw: int, ch: int, initial_prompt: str}
        **kwargs
    ): # {transcription: str}
        raise NotImplementedError
     
stt_capabilities: Dict[str, Capability] = {
    "kobold": Capability(
        STT_TYPE,
        "kobold",
        "KoboldSTT",
        compatibility=True
    ),
    "fish": Capability(
        STT_TYPE,
        "fish",
        "FishSTT",
        compatibility=True
    )
}