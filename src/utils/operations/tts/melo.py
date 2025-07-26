import wave
from io import BytesIO
from melo.api import TTS
import logging
import numpy as np
import torch
import soundfile

from utils.config import Config

from .base import TTSOperation

class MeloTTS(TTSOperation):
    SAMPLE_RATE = 44100
    SAMPLE_WIDTH = 2
    CHANNELS = 1
    
    def __init__(self):
        super().__init__("melo")
        self.model = None
        self.speaker_ids = dict()
        
        self.config_filepath = None
        self.model_filepath = None
        self.speaker_id = None
        self.device = "cpu"
        self.language = "EN"
        
        self.sdp_ratio = 0.2
        self.noise_scale = 0.6
        self.noise_scale_w = 0.8
        self.speed = 1.0
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        self.model = TTS(
            language=self.language,
            device=self.device,
            config_path=self.config_filepath,
            ckpt_path=self.model_filepath
        )
        self.speaker_ids = self.model.hps.data.spk2id
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        del self.model
        self.model = None
        self.speaker_ids = dict()

    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if config_d.get("config_filepath", None): self.config_filepath = str(config_d['config_filepath'])
        if config_d.get("model_filepath", None): self.model_filepath = str(config_d['model_filepath'])
        if "speaker_id" in config_d: self.speaker_id = str(config_d['speaker_id'])
        if "device" in config_d: self.device = str(config_d['device'])
        if "language" in config_d: self.language = str(config_d['language'])
        
        if "sdp_ratio" in config_d: self.sdp_ratio = float(config_d["sdp_ratio"])
        if "noise_scale" in config_d: self.noise_scale = float(config_d["noise_scale"])
        if "noise_scale_w" in config_d: self.noise_scale_w = float(config_d["noise_scale_w"])
        if "speed" in config_d: self.speed = float(config_d["speed"])
        
        assert self.speaker_id is not None and len(self.speaker_id) > 0
        assert self.device is not None and len(self.device) > 0
        assert self.language is not None and len(self.language) > 0
        assert self.sdp_ratio < 1.25
        assert self.noise_scale < 1.25 and self.noise_scale >= 0
        assert self.noise_scale_w < 1.25 and self.noise_scale_w >= 0
        assert self.speed > 0
 
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "config_filepath": self.config_filepath,
            "model_filepath": self.model_filepath,
            "speaker_id": self.speaker_id,
            "device": self.device,
            "language": self.language
        }

    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        ab_np = self.model.tts_to_file(
            content,
            self.speaker_ids[self.speaker_id],
            # output_path="output/temp/melo_out.wav",
            sdp_ratio=self.sdp_ratio,
            noise_scale=self.noise_scale,
            noise_scale_w=self.noise_scale_w,
            speed=self.speed,
            quiet=True
        )
        ab = torch.from_numpy(ab_np).float()
        audio_buffer = BytesIO()
        soundfile.write(audio_buffer, ab, self.SAMPLE_RATE, format='WAV', subtype='PCM_16')
        audio_buffer.seek(0)
        with wave.open(audio_buffer, 'r') as f:
            yield {
                "audio_bytes": f.readframes(f.getnframes()),
                "sr": self.SAMPLE_RATE,
                "sw": self.SAMPLE_WIDTH,
                "ch": self.CHANNELS
            }