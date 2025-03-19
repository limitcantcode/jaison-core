from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

TTSC_TYPE = 'ttsc'

class TTSCOperation(BaseOperation):
    async def __call__(
        self,
        in_stream: AsyncGenerator = None, # {audio_bytes: bytes, sr: int, sw: int, ch: int}
        **kwargs
    ): # {audio_bytes: bytes, sr: int, sw: int, ch: int}
        raise NotImplementedError
    
ttsc_capabilities: Dict[str, Capability] = {
    "rvc": Capability(
        TTSC_TYPE,
        "rvc",
        'RVCProjectTTSC',
        compatibility=False
    )
}
