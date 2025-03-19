from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

CHUNKER_TYPE = 'chunker'

class ChunkerOperation(BaseOperation):
    async def __call__(
        self,
        in_stream: AsyncGenerator = None, # in_stream {content: str}
        **kwargs
    ): # out_stream {content: str}
        raise NotImplementedError
    
chunker_capabilities: Dict[str, Capability] = {
    "sentence": Capability(
        CHUNKER_TYPE,
        "sentence",
        'SentenceChunker',
        compatibility=True
    )
}