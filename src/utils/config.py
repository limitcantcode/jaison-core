# import json
# from .helpers.time import get_current_time

import logging
import os
import yaml
from typing import get_type_hints, List, Dict
from .helpers.singleton import Singleton
from .helpers.path import portable_path
from .args import args

class UnknownField(Exception):
    pass

class Config(metaclass=Singleton):
    def __init__(self):
        # Every attribute must be typed for validation
        self.CONFIG_DIR: str = portable_path(os.path.join(os.getcwd(), "configs"))
        self.WORKING_DIR: str = portable_path(os.path.join(os.getcwd(),"output","temp"))
        self.current_config: str
        
        # General
        self.compatibility_mode: bool = True
        self.web_port: int = 7272
        
        # Defaults
        self.default_skip_filters: bool = True
        self.default_skip_emotions: bool = True
        self.default_skip_ttsc: bool = True
        self.default_operations: List[Dict[str, str]] = list()
        
        # Kobold
        self.kobold_stt_enabled: bool
        self.kobold_t2t_enabled: bool
        self.kobold_filepath: str
        self.kcpps_filepath: str
        
        self.kobold_stt_suppress_non_speech: bool = True
        self.kobold_stt_langcode: str = 'en'
        
        # OpenAI
        self.openai_t2t_base_url: str
        self.openai_t2t_model: str
        
        self.openai_t2t_temperature: float = 1
        self.openai_t2t_top_p: float = 0.9
        self.openai_t2t_presence_penalty: float = 0
        self.openai_t2t_frequency_penalty: float = 0
        
        self.openai_ttsg_base_url: str
        self.openai_ttsg_voice: str
        self.openai_ttsg_model: str
        
        # Synthetic TTSG
        self.synth_ttsg_voice_name: str
        self.synth_ttsg_gender: str = 'female'
        self.synth_ttsg_working_file: str = portable_path(os.path.join(self.CONFIG_DIR,'ttsg-synth-out.wav'))
        
        # RVC Project
        self.rvc_voice: str
        self.rvc_f0_up_key: int = 0
        self.rvc_f0_method: str = "rmvpe"
        self.rvc_f0_file: str | None = None
        self.rvc_index_file: str | None = None
        self.rvc_index_rate: float = 0.75
        self.rvc_filter_radius: int = 3
        self.rvc_resample_sr: int = 0
        self.rvc_rms_mix_rate: float = 0.25
        self.rvc_protect: float = 0.33
    
    def __init__(self):
        if args.config is not None: self.load_from_name(args.config)
        
    # Can raise: FileNotFoundError, 
    def load_from_name(self, config_name: str):
        self.current_config = config_name
        
        with open(os.path.join(self.CONFIG_DIR, self.current_config)) as f:
            conf_d = yaml.safe_load(f)
            
        self.load_from_dict(**conf_d)
        
    def load_from_dict(self, conf_d):
        uncommitted = dict(conf_d)
        config_typings = get_type_hints(self)

        # Pre-check fields before committing changes
        try:
            for field in conf_d:
                if field not in config_typings:
                    raise UnknownField(f"Config tried loading invalid field: {field}")
                uncommitted[field] = config_typings[field](conf_d[field]) # attempt cast to correct typing
        except Exception as err:
            logging.error(f"Could not update config due to error: {err}")
            raise err
        
        # Commit config change request
        for field in uncommitted:
            setattr(self, field, uncommitted[field])
            
    def save(self, config_name: str):
        with open(os.path.join(self.CONFIG_DIR, config_name)) as f:
            yaml.dump(self.get_config_dict(),f)
            
    def get_config_dict(self):
        return vars(self)