'''
Filter text operations (at minimum) require the following fields for input chunks:
- content: (text) text to apply filter on

Overwrites in chunk (OR augments chunk):
- content: (str) text after filter application
'''

from typing import Dict, Any, AsyncGenerator

from ..base import Operation

class FilterTextOperation(Operation):
    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        '''General setup needed to start generated'''
        super().start()
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        super().close()
    
    async def _parse_chunk(self, chunk_in: Dict[str, Any]) -> Dict[str, Any]:
        '''Extract information from input for use in _generate'''
        assert "content" in chunk_in
        assert isinstance(chunk_in["content"], str)
        assert len(chunk_in["content"]) > 0
        
        return {
            "content": chunk_in["content"]
        }
    
    ## TO BE IMPLEMENTED ####
    async def _generate(self, content: str = None, **kwargs) -> AsyncGenerator[Dict[str, Any]]:
        '''Generate a output stream'''
        raise NotImplementedError
    
        yield {
            "content": "example response text"
        }