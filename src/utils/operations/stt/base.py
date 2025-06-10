'''
STT Operations (at minimum) require the following fields for input chunks:
- prompt: (str) initial words to help with transcription (Optional)
- audio_bytes: (bytes) pcm audio data
- sr: (int) sample rate
- sw: (int) sample width
- ch: (int) audio channels

Adds to chunk:
- transcription: (str) transcribed audio
'''

from typing import Dict, Any, AsyncGenerator

from ..base import Operation

class STTOperation(Operation):
    def __init__(self, op_id: str):
        super().__init__("STT", op_id)
        
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
            "prompt": chunk_in.get("prompt", ""),
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
    
    async def _generate(self, prompt: str = None, audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        '''Generate a output stream'''
        raise NotImplementedError
    
        yield {
            "transcription": "example transcribed text"
        }