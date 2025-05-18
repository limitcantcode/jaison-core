import wave
from rvc.modules.vc.modules import VC

from utils.config import Config

from .base import FilterAudioOperation

class RVCFilter(FilterAudioOperation):
    TARGET_SR = 16000
    TARGET_SW = 2
    TARGET_CH = 1
    
    def __init__(self):
        super().__init__()
        self.vc = None
        
    async def start(self):
        await super().start()
        self.vc = VC()
        model_name = Config().rvc_voice if Config().rvc_voice.endswith('.pth') else f"{Config().rvc_voice}.pth"
        self.vc.get_vc(model_name)
        
    async def _generate(self, audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs):
        with wave.open(Config().ffmpeg_working_src, 'wb') as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)
            
        tgt_sr, audio_opt, times, _ = self.vc.vc_inference(
            1,
            Config().ffmpeg_working_src,
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
            "audio_bytes": audio_opt.tobytes(),
            "sr": tgt_sr,
            "sw": self.TARGET_SW,
            "ch": self.TARGET_CH
        }
    