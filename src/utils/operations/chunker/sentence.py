
import logging
import re
from typing import Dict, AsyncGenerator, Any
from .meta import ChunkerOperation
from ..base import Capability

class SentenceChunker(ChunkerOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.sentence_pattern: re.Pattern = None
        
    async def start(self):
        self.sentence_pattern = re.compile("[{}]+".format(re.escape(".?,;!")))
        
    async def reload(self):
        pass
        
    async def unload(self):
        pass
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        content = ""
        async for in_d in in_stream:
            content = in_d['content']
            while True:
                sentence_match = self.sentence_pattern.search(content, 10) # Give some characters before
                if sentence_match is not None:
                    slice_ind = sentence_match.endpos
                    content_slice = content[:slice_ind]
                    content = content[slice_ind:]
                    yield {"content": content_slice}
                else:
                    break
                
        if len(content) > 0:
            yield {"content": content}
