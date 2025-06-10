'''
Filter audio operations (at minimum) require the following fields for input chunks:
- audio_bytes: (bytes) pcm audio data
- sr: (int) sample rate
- sw: (int) sample width
- ch: (int) audio channels

Overwrites in chunk (OR augments chunk):
- audio_bytes: (bytes) new pcm audio data
- sr: (int) new sample rate
- sw: (int) new sample width
- ch: (int) new audio channels
'''

from typing import Dict, Any, AsyncGenerator

from ..base import Operation

class FilterAudioOperation(Operation):
    def __init__(self, op_id: str):
        super().__init__("FILTER_AUDIO", op_id)
        
    ## TO BE OVERRIDEN ####
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
    
    async def _parse_chunk(self, chunk_in: Dict[str, Any]) -> Dict[str, Any]:
        '''Extract information from input for use in _generate'''
        assert "audio_bytes" in chunk_in
        assert isinstance(chunk_in["audio_bytes"], bytes)
        assert len(chunk_in["audio_bytes"]) > 0
        assert "sr" in chunk_in
        assert isinstance(chunk_in["sr"], int)
        assert chunk_in["sr"] > 0
        assert "sw" in chunk_in
        assert isinstance(chunk_in["sw"], int)
        assert chunk_in["sw"] > 0
        assert "ch" in chunk_in
        assert isinstance(chunk_in["ch"], int)
        assert chunk_in["ch"] > 0
        
        return {
            "audio_bytes": chunk_in["audio_bytes"],
            "sr": chunk_in["sr"],
            "sw": chunk_in["sw"],
            "ch": chunk_in["ch"]
        }
    
    ## TO BE IMPLEMENTED ####
    async def configure(self, config_d: Dict[str, Any]):
        '''Configure and validate operation-specific configuration'''
        raise NotImplementedError
    
    async def get_configuration(self) -> Dict[str, Any]:
        '''Returns values of configurable fields'''
        raise NotImplementedError
    
    async def _generate(self, audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        '''Generate a output stream'''
        raise NotImplementedError
    
        yield {
            "audio_bytes": b'',
            "sr": 123,
            "sw": 123,
            "ch": 123
        }