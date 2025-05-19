'''
TTS Operations (at minimum) require the following fields for input chunks:
- content: (str) Text to generate speech for

Adds to chunk:
- audio_bytes: (bytes) pcm audio data
- sr: (int) sample rate
- sw: (int) sample width
- ch: (int) audio channels
'''

from typing import Dict, Any, AsyncGenerator

from ..base import Operation

class TTSOperation(Operation):
    def __init__(self, op_id: str):
        super().__init__("TTS", op_id)
        
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
    async def _generate(self, content: str = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        '''Generate a output stream'''
        raise NotImplementedError
    
        yield {
            "audio_bytes": b'',
            "sr": 123,
            "sw": 123,
            "ch": 123
        }