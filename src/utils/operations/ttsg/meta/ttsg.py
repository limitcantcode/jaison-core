from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

TTSG_TYPE = 'ttsg'
    
class TTSGOperation(BaseOperation):
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None, # {content: str}
        **kwargs
    ): # {audio_bytes: bytes, sr: int, sw: int, ch: int}
        raise NotImplementedError
       
ttsg_capabilities: Dict[str, Capability] = {
    'openai': Capability(
        TTSG_TYPE,
        'openai',
        'OpenAITTSG',
        compatibility=True
    ),
    'pytts': Capability(
        TTSG_TYPE,
        'pytts',
        'PyttsTTSG',
        compatibility=True
    ),
    'fish': Capability(
        TTSG_TYPE,
        'fish',
        'FishTTSG',
        compatibility=True
    )
}