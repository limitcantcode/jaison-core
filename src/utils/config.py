import os
import yaml
from typing import get_type_hints, List, Dict
from .helpers.singleton import Singleton
from .helpers.path import portable_path
from .args import args

class UnknownField(Exception):
    def __init__(self, field: str):
        super().__init__("Config field {} does not exist".format(field))

class UnknownFile(Exception):
    def __init__(self, filepath: str):
        super().__init__("Config file {} does not exist".format(filepath))

class Config(metaclass=Singleton):
    # Every attribute must be typed for validation
    CONFIG_DIR: str = portable_path(os.path.join(os.getcwd(), "configs"))
    WORKING_DIR: str = portable_path(os.path.join(os.getcwd(),"output","temp"))
    current_config: str = "Unsaved"
    
    # Defaults
    operations: list = list()
    
    # Prompter
    PROMPT_DIR: str = portable_path(os.path.join(os.getcwd(), "prompts"))
    PROMPT_INSTRUCTION_SUBDIR: str = "instructions"
    PROMPT_CHARACTER_SUBDIR: str = "characters"
    PROMPT_SCENE_SUBDIR: str = "scenes"
    
    prompter: dict = dict()
    history_filepath: str = portable_path(os.path.join(os.getcwd(), "output", "history.txt")) # debug

    # MCP
    MCP_DIR: str = portable_path(os.path.join(os.getcwd(), "models", "mcp"))
    mcp: list = list()

    # Kobold
    kobold_filepath: str = None
    kcpps_filepath: str = None
    
    # Melo
    MELO_DIR: str = portable_path(os.path.join(os.getcwd(), "models", "melotts"))

    # Shared
    stt_working_src: str = portable_path(os.path.join(WORKING_DIR,'stt_src.wav'))
    ffmpeg_working_src: str = portable_path(os.path.join(WORKING_DIR,'ffmpeg_src.wav'))
    ffmpeg_working_dest: str = portable_path(os.path.join(WORKING_DIR,'ffmpeg_dest.wav'))
    spacy_model: str = None
    
    def __init__(self):
        # Every attribute must be typed for validation
        if args.config is not None: self.load_from_name(args.config)
        
    # Can raise: FileNotFoundError, 
    def load_from_name(self, config_name: str):
        filepath = os.path.join(self.CONFIG_DIR, config_name+".yaml")
        if not os.path.isfile(filepath): 
            filepath = os.path.join(self.CONFIG_DIR, config_name)
        if not os.path.isfile(filepath): raise UnknownFile(filepath)
        
        with open(filepath) as f:
            conf_d = yaml.safe_load(f)
            
        self.load_from_dict(**conf_d)
        self.current_config = config_name
        
    def load_from_dict(self, **conf_d):
        uncommitted = dict(conf_d)
        config_typings = get_type_hints(Config)

        # Pre-check fields before committing changes
        for field in conf_d:
            if field not in config_typings:
                raise UnknownField(field)
            uncommitted[field] = config_typings[field](conf_d[field]) if conf_d[field] is not None else None # attempt cast to correct typing
        
        # Commit config change request
        for field in uncommitted:
            setattr(self, field, uncommitted[field])
            
        self.current_config = "Unsaved"
            
    def save(self, config_name: str):
        with open(portable_path(os.path.join(self.CONFIG_DIR, config_name))) as f:
            yaml.dump(self.get_config_dict(),f)
            
    def get_config_dict(self):
        return vars(self)