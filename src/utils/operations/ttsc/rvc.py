import logging
import numpy as np
from typing import AsyncGenerator, Any
from rvc.modules.vc.modules import VC
from utils.config import Config
from .meta import TTSCOperation
from ..base import Capability

class RVCProjectTTSC(TTSCOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.TARGET_SR, self.TARGET_SW, self.TARGET_CH = 16000, 2, 1
        self.vc = None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.vc is not None: self.unload()
        self.vc = VC()
        model_name = Config().rvc_voice if Config().rvc_voice.endswith('.pth') else f"{Config().rvc_voice}.pth"
        self.vc.get_vc(model_name)
        
    async def unload(self):
        pass
        
    def _format_audio(self, audio_bytes, sr, sw, ch):
        dtype = np.dtype(f'i{sw}')
        audio_array = np.frombuffer(audio_bytes, dtype=dtype) # parse bytes
        audio_array = (audio_array.reshape([int(audio_array.shape[0]/ch), ch])/ch).sum(1) # average across channels into 1 channel
        audio_array = np.interp(np.arange(0, len(audio_array), float(sr)/self.TARGET_SR), np.arange(0, len(audio_array)), audio_array) # resample
        audio_array = audio_array.flatten().astype(np.float32)
        match sw: # Rescale volume
            case 1:
                audio_array = audio_array / 128.0
            case 2:
                audio_array = audio_array / 32768.0
            case 4:
                audio_array = audio_array / 2147483648.0
            case _:
                raise Exception("Invalid sample width given: {src_sw}")

        return audio_array
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        async for in_d in in_stream:
            audio_bytes: bytes = in_d['audio_bytes']
            sr: int = in_d['sr']
            sw: int = in_d['sw']
            ch: int = in_d['ch']
            
            assert audio_bytes is not None and len(audio_bytes) > 0
            assert sr > 0
            assert sw > 0
            assert ch > 0
            
            audio_array = self._format_audio(audio_bytes, sr, sw, ch)
            tgt_sr, audio_opt, times, _ = self.vc.vc_inference(
                1,
                audio_array,
                f0_up_key=Config().rvc_f0_up_key,
                f0_method=Config().rvc_f0_method,
                f0_file=Config().rvc_f0_file,
                index_file=Config().rvc_index_file,
                index_rate=Config().rvc_index_rate,
                filter_radius=Config().rvc_filter_radius,
                resample_sr=Config().rvc_resample_sr,
                rms_mix_rate=Config().rvc_rms_mix_rate,
                protect=Config().rvc_protect,
            )
            
            yield {
                "audio_bytes": audio_opt,
                "sr": tgt_sr,
                "sw": self.TARGET_SW,
                "ch": self.TARGET_CH
            }