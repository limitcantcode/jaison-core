from typing import Dict, Any, AsyncGenerator

from .error import StartActiveError, CloseInactiveError, UsedInactiveError

class Operation:
    def __init__(self, op_type: str, op_id: str):
        self.op_type = op_type
        self.op_id = op_id
        
        self.active = False
    
    async def __call__(self, chunk_in: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any]]:
        '''Generates a stream of chunks similar to chunk_in but augmented with new data'''
        if not self.active: raise UsedInactiveError(self.op_type, self.op_id)
        
        kwargs = await self.parse_chunk(chunk_in)
        
        async for chunk_out in self.generate(**kwargs):
            yield chunk_in | chunk_out
    
    
    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        '''General setup needed to start generated'''
        if self.active: raise StartActiveError(self.op_type, self.op_id)
        self.active = True
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        if not self.active: raise CloseInactiveError(self.op_type, self.op_id)
        self.active = False
    
    ## TO BE IMPLEMENTED ####
    async def _parse_chunk(self, chunk_in: Dict[str, Any]) -> Dict[str, Any]:
        '''Extract information from input for use in _generate'''
        raise NotImplementedError
    
    async def _generate(self, **kwargs) -> AsyncGenerator[Dict[str, Any]]:
        '''Generate a output stream'''
        raise NotImplementedError