from typing import Dict, Any, AsyncGenerator
import time
import logging

from .error import StartActiveError, CloseInactiveError, UsedInactiveError

class Operation:
    def __init__(self, op_type: str, op_id: str):
        self.op_type = op_type
        self.op_id = op_id
        
        self.active = False
    
    async def __call__(self, chunk_in: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        '''Generates a stream of chunks similar to chunk_in but augmented with new data'''
        if not self.active: raise UsedInactiveError(self.op_type, self.op_id)
        start_time = time.perf_counter()
        
        kwargs = await self._parse_chunk(chunk_in)
        
        async for chunk_out in self._generate(**kwargs):
            # yield chunk_in | chunk_out
            yield chunk_out
        end_time = time.perf_counter()
        logging.info("{} operation {} completed in {} ms".format(self.op_type, self.op_id, (end_time-start_time)*1000))
    
    
    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        '''General setup needed to start generated'''
        if self.active: raise StartActiveError(self.op_type, self.op_id)
        logging.info("Starting {} operation {}".format(self.op_type, self.op_id))
        self.active = True
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        if not self.active: raise CloseInactiveError(self.op_type, self.op_id)
        logging.info("Closing {} operation {}".format(self.op_type, self.op_id))
        self.active = False
    
    ## TO BE IMPLEMENTED ####
    async def configure(self, config_d: Dict[str, Any]):
        '''Configure and validate operation-specific configuration'''
        raise NotImplementedError
    
    async def get_configuration(self) -> Dict[str, Any]:
        '''Returns values of configurable fields'''
        raise NotImplementedError
    
    async def _parse_chunk(self, chunk_in: Dict[str, Any]) -> Dict[str, Any]:
        '''Extract information from input for use in _generate'''
        raise NotImplementedError
    
    async def _generate(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        '''Generate a output stream'''
        raise NotImplementedError