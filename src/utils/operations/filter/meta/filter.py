from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

FILTER_TYPE = 'filter'

class FilterOperation(BaseOperation):
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None, # in_stream {content: str}
        **kwargs
    ): # out_stream {content: str}
        raise NotImplementedError

filter_capabilities: Dict[str, Capability] = {
    "koala": Capability(
        FILTER_TYPE,
        "koala",
        'KoalaAIFilter',
        compatibility=False
    )
}