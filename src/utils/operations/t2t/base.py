'''
T2T Operations (at minimum) require the following fields for input chunks:
- system_prompt: (str) System prompt text
- user_prompt: (str) User prompt text

Adds to chunk:
- content: (str) Generated text
'''

from typing import Dict, Any, AsyncGenerator

from ..base import Operation

class T2TOperation(Operation):
    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        '''General setup needed to start generated'''
        super().start()
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        super().close()
    
    async def _parse_chunk(self, chunk_in: Dict[str, Any]) -> Dict[str, Any]:
        '''Extract information from input for use in _generate'''
        assert "system_prompt" in chunk_in
        assert isinstance(chunk_in["system_prompt"], str)
        assert len(chunk_in["system_prompt"]) > 0
        assert "user_prompt" in chunk_in
        assert isinstance(chunk_in["user_prompt"], str)
        assert len(chunk_in["user_prompt"]) > 0
        
        return {
            "system_prompt": chunk_in["system_prompt"],
            "user_prompt": chunk_in["user_prompt"],
        }
    
    ## TO BE IMPLEMENTED ####
    async def _generate(self, system_prompt: str = None, user_prompt: str = None, **kwargs) -> AsyncGenerator[Dict[str, Any]]:
        '''Generate a output stream'''
        raise NotImplementedError
    
        yield {
            "content": "example generated text"
        }