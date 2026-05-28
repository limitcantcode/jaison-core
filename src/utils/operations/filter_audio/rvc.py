import os
import wave
from pathlib import Path

import fairseq
import torch
from rvc.modules.vc.modules import VC

from utils.config import config

from .base import FilterAudioOperation


class RVCFilter(FilterAudioOperation):
    TARGET_SR = 16000
    TARGET_SW = 2
    TARGET_CH = 1
    DEFAULT_SPEAKER_ID = 0

    def __init__(self):
        super().__init__("rvc")
        self.vc: VC | None = None
        self._speaker_id = self.DEFAULT_SPEAKER_ID

        self.voice: str | None = None
        self.f0_up_key: int = 0
        self.f0_method: str = "rmvpe"
        self.f0_filepath: str | None = None
        self.index_filepath: str | None = None
        self.index_rate: float = 0
        self.filter_radius: int = 3
        self.resample_sr: int = 0
        self.rms_mix_rate: float = 0
        self.protect: float = 0.5

        torch.serialization.add_safe_globals([fairseq.data.dictionary.Dictionary])

    def _model_id(self) -> str:
        if not self.voice:
            raise RuntimeError("RVC voice model not configured")
        return self.voice if self.voice.endswith(".pth") else f"{self.voice}.pth"

    async def start(self):
        await super().start()
        self.vc = VC()
        _, _, default_index = self.vc.get_vc(self._model_id())
        if not self.index_filepath and default_index:
            self.index_filepath = default_index

    async def close(self) -> None:
        if self.vc is not None:
            try:
                self.vc.get_vc("")
            except Exception:
                pass
            self.vc = None
        await super().close()

    async def configure(self, config_d):
        """Configure and validate operation-specific configuration"""
        if "voice" in config_d:
            self.voice = str(config_d["voice"])
        if "f0_up_key" in config_d:
            self.f0_up_key = int(config_d["f0_up_key"])
        if "f0_method" in config_d:
            self.f0_method = str(config_d["f0_method"])
        if "f0_filepath" in config_d:
            self.f0_filepath = str(config_d["f0_filepath"])
        if "index_filepath" in config_d:
            self.index_filepath = str(config_d["index_filepath"])
        if "index_rate" in config_d:
            self.index_rate = float(config_d["index_rate"])
        if "filter_radius" in config_d:
            self.filter_radius = int(config_d["filter_radius"])
        if "resample_sr" in config_d:
            self.resample_sr = int(config_d["resample_sr"])
        if "rms_mix_rate" in config_d:
            self.rms_mix_rate = float(config_d["rms_mix_rate"])
        if "protect" in config_d:
            self.protect = float(config_d["protect"])

        # TODO check assertions

    async def get_configuration(self):
        """Returns values of configurable fields"""
        return {
            "voice": self.voice,
            "f0_up_key": self.f0_up_key,
            "f0_method": self.f0_method,
            "f0_filepath": self.f0_filepath,
            "index_filepath": self.index_filepath,
            "index_rate": self.index_rate,
            "filter_radius": self.filter_radius,
            "resample_sr": self.resample_sr,
            "rms_mix_rate": self.rms_mix_rate,
            "protect": self.protect,
        }

    async def _generate(
        self, audio_bytes: bytes = None, sr: int = None, sw: int = None, ch: int = None, **kwargs
    ):
        if self.vc is None:
            raise RuntimeError("RVC filter is not started")

        input_path = Path(config.ffmpeg_working_src)
        with wave.open(str(input_path), "wb") as f:
            f.setframerate(sr)
            f.setsampwidth(sw)
            f.setnchannels(ch)
            f.writeframes(audio_bytes)

        tgt_sr, audio_opt, _, info = self.vc.vc_inference(
            self._speaker_id,
            input_path,
            f0_up_key=self.f0_up_key,
            f0_method=self.f0_method,
            f0_file=self.f0_filepath,
            index_file=self.index_filepath,
            index_rate=self.index_rate,
            filter_radius=self.filter_radius,
            resample_sr=self.resample_sr,
            rms_mix_rate=self.rms_mix_rate,
            protect=self.protect,
        )
        if audio_opt is None:
            raise RuntimeError(info or "RVC inference failed")

        yield {
            "audio_bytes": audio_opt.tobytes(),
            "sr": tgt_sr,
            "sw": self.TARGET_SW,
            "ch": self.TARGET_CH,
        }
