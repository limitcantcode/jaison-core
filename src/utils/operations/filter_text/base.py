'''
Filter text operations (at minimum) require the following fields for input chunks:
- content: (text) text to apply filter on

Overwrites in chunk (OR augments chunk):
- content: (str) text after filter application
'''

from typing import Dict, Any, AsyncGenerator

from ..base import Operation

class FilterTextOperation(Operation):
    def __init__(self, op_id: str):
        super().__init__("FILTER_TEXT", op_id)
        
    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
    
    async def _parse_chunk(self, chunk_in: Dict[str, Any]) -> Dict[str, Any]:
        '''Extract information from input for use in _generate'''
        assert "content" in chunk_in
        assert isinstance(chunk_in["content"], str)
        assert len(chunk_in["content"]) > 0
        
        return {
            "content": chunk_in["content"]
        }
    
    ## TO BE IMPLEMENTED ####
    async def configure(self, config_d: Dict[str, Any]):
        '''Configure and validate operation-specific configuration'''
        raise NotImplementedError
    
    async def get_configuration(self) -> Dict[str, Any]:
        '''Returns values of configurable fields'''
        raise NotImplementedError
    
    async def _generate(self, content: str = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        '''Generate a output stream'''
        raise NotImplementedError
    
        yield {
            "content": "example response text"
        }