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
    # Every attribute must be typed for validation
    CONFIG_DIR: str = portable_path(os.path.join(os.getcwd(), "configs"))
    WORKING_DIR: str = portable_path(os.path.join(os.getcwd(),"output","temp"))
    current_config: str = None
    
    # General
    compatibility_mode: bool = True
    web_port: int = 7272
    
    # Defaults
    operations: list = list()
    
    # Prompter
    PROMPT_DIR: str = portable_path(os.path.join(os.getcwd(), "prompts"))
    PROMPT_INSTRUCTION_SUBDIR: str = "instructions"
    PROMPT_CHARACTER_SUBDIR: str = "characters"
    PROMPT_SCENE_SUBDIR: str = "scenes"
    
    instruction_prompt_filename: str = 'example.txt'
    character_prompt_filename: str = 'example.txt'
    scene_prompt_filename: str = 'example.txt'
    
    character_name: str = 'JAIson'
    name_translations: dict = dict()
    history_length: int = 50
    
    # Kobold
    kobold_filepath: str = None
    kcpps_filepath: str = None
    
    kobold_stt_suppress_non_speech: bool = True
    kobold_stt_langcode: str = 'en'
    
    kobold_t2t_max_context_length: int = 2048,
    kobold_t2t_max_length: int = 100,
    kobold_t2t_quiet: bool = True,
    kobold_t2t_rep_pen: float = 1.1,
    kobold_t2t_rep_pen_range: int = 256,
    kobold_t2t_rep_pen_slope: int = 1,
    kobold_t2t_temperature: float = 0.5,
    kobold_t2t_tfs: int = 1,
    kobold_t2t_top_a: int = 0,
    kobold_t2t_top_k: int = 100,
    kobold_t2t_top_p: float = 0.9,
    kobold_t2t_typical: int = 1
    
    kobold_tts_voice: str = None
        
    # OpenAI
    openai_t2t_base_url: str = None
    openai_t2t_model: str = None
    
    openai_t2t_temperature: float = 1
    openai_t2t_top_p: float = 0.9
    openai_t2t_presence_penalty: float = 0
    openai_t2t_frequency_penalty: float = 0
    
    openai_stt_model: str = None
    openai_stt_language: str = None
    
    openai_ttsg_base_url: str = None
    openai_ttsg_voice: str = None
    openai_ttsg_model: str = None
        
    # Synthetic TTSG
    synth_ttsg_voice_name: str = None
    synth_ttsg_gender: str = 'female'
    synth_ttsg_working_file: str = portable_path(os.path.join(WORKING_DIR,'ttsg-synth-out.wav'))
    
    # Azure TTSG
    azure_stt_language: str = None
    
    azure_ttsg_voice: str = None
    
    # Fish Audio
    fish_model_id: str = None
    fish_model_backend: str = "speech-1.6"
    fish_normalize: bool = False
    fish_latency: str = "normal"
    
    # Spacy
    spacy_model: str = None
    
    # FFmpeg
    ffmpeg_working_src: str = os.path.join(WORKING_DIR,'ffmpeg_src.wav')
    ffmpeg_working_dest: str = os.path.join(WORKING_DIR,'ffmpeg_dest.wav')
        
    # RVC Project
    rvc_voice: str = None
    rvc_f0_up_key: int = 0
    rvc_f0_method: str = "rmvpe"
    rvc_f0_file: str = None
    rvc_index_file: str = None
    rvc_index_rate: float = 0.75
    rvc_filter_radius: int = 3
    rvc_resample_sr: int = 0
    rvc_rms_mix_rate: float = 0.25
    rvc_protect: float = 0.33
    
    # Pitch corrector
    pitch_amount: int = 0
    
    def __init__(self):
        # Every attribute must be typed for validation
        if args.config is not None: self.load_from_name(args.config)
        
    # Can raise: FileNotFoundError, 
    def load_from_name(self, config_name: str):
        
        with open(os.path.join(self.CONFIG_DIR, self.current_config+".yaml")) as f:
            conf_d = yaml.safe_load(f)
            
        self.load_from_dict(**conf_d)
        self.current_config = config_name
        
    def load_from_dict(self, **conf_d):
        uncommitted = dict(conf_d)
        config_typings = get_type_hints(Config)

        # Pre-check fields before committing changes
        try:
            for field in conf_d:
                if field not in config_typings:
                    raise UnknownField(f"Config tried loading invalid field: {field}")
                uncommitted[field] = config_typings[field](conf_d[field]) if conf_d[field] is not None else None # attempt cast to correct typing
        except Exception as err:
            logging.error(f"Could not update config due to error: {err}")
            raise err
        
        # Commit config change request
        for field in uncommitted:
            setattr(self, field, uncommitted[field])
            
        self.current_config = "Unsaved"
            
    def save(self, config_name: str):
        with open(os.path.join(self.CONFIG_DIR, config_name)) as f:
            yaml.dump(self.get_config_dict(),f)
            
    def get_config_dict(self):
        return vars(self)