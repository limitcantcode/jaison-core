'''
Abstract Operation class

An operation is a transforming unit within the response pipeline.
It accepts data at a stage within the pipeline and may process it
for the next stage.

For example: T2T operations transform prompts into the actual response
'''

from typing import Dict, AsyncGenerator, Any

class BaseOperation:
    def __init__(self, capability):
        self.id: str = capability.op_implem_filename
        self.compatibility: bool = capability.compatibility
    
    async def __call__(self, in_stream: AsyncGenerator = None, **kwargs) -> AsyncGenerator:
        raise NotImplementedError
    
    async def start(self):
        raise NotImplementedError
        
    '''Re-initialize operation like program startup'''
    async def reload(self):
        raise NotImplementedError
    
    '''Cleanly shutdown component'''
    async def unload(self):
        raise NotImplementedError
