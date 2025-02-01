import os
import json
from typing import get_type_hints
from utils.args import args
from utils.helpers.singleton import Singleton
from utils.logging import create_sys_logger
logger = create_sys_logger()

class Configuration(metaclass=Singleton):
    # DONT SAVE
    RESULT_TTSG = os.path.join(os.getcwd(),"output","audio","tts_raw.wav")
    RESULT_TTSC = os.path.join(os.getcwd(),"output","audio","tts.wav")
    RESULT_INPUT_SPEECH = os.path.join(os.getcwd(),"output","audio","recorded_speech.wav")
    CONFIG_DIR = os.path.join(os.getcwd(),"configs","jaison")
    CURRENT_CONFIG_FILENAME = None

    # T2T
    t2t_default_prompt_file: str = "example.txt"
    t2t_current_prompt_file: str = None # DONT SAVE: session specific
    t2t_prompt_dir: str = os.path.join(os.getcwd(),"prompts","production") # DONT SAVE: constant
    t2t_prompt_params: dict = dict()
    t2t_name_translation_dir: str = os.path.join(os.getcwd(),"configs","translations") # DONT SAVE: constant
    t2t_name_translation_file: str = None
    t2t_convo_retention_length: int = 40

    # Plugins
    plugins_config_dir: str = os.path.join(os.getcwd(),"configs","plugins")
    plugins_config_file: str = "example.yaml"
    active_plugins: list = list()

    # Web
    web_host: str = "localhost"
    web_api_port: int = 1337
    web_socket_port: int = 7270

    def __init__(self):
        if not self.load(args.config):
            raise Exception(f"Could not initialize using config {args.config}")

    def update(self, config_d: dict) -> tuple[bool, str]:
        '''
        Returns:
        - If successful: True, None
        - If unsuccessful: False, "failing field"
        '''

        uncommitted = dict()
        config_typings = get_type_hints(self)

        # Pre-check fields before committing changes
        for field in config_d:
            if field not in config_typings:
                raise Exception(f"Config has no field named: {field}")
            uncommitted[field] = config_typings[field](config_d[field])
        
        # Commit config change request
        for field in uncommitted:
            setattr(self, field, uncommitted[field])

        logger.debug("Config update applied without issue.")
        return True

    def save(self, config_d: dict = None, filename: str = None) -> bool:
        config_to_save = config_d
        file_to_save = filename or self.CURRENT_CONFIG_FILENAME
        if config_to_save is None:
            config_to_save = {
                "t2t_default_prompt_file": self.t2t_default_prompt_file,
                "t2t_prompt_params": self.t2t_prompt_params,
                "t2t_name_translation_file": self.t2t_name_translation_file,
                "t2t_convo_retention_length": self.t2t_convo_retention_length,
                "plugins_config_file": self.plugins_config_file,
                "active_plugins": self.active_plugins,
                "web_host": self.web_host,
                "web_api_port": self.web_api_port,
                "web_socket_port": self.web_socket_port
            }

        with open(os.path.join(self.CONFIG_DIR, file_to_save), 'w') as f:
            json.dump(config_to_save, f, indent=4)
            logger.info(f"Saved config to {file_to_save}!")
        self.CURRENT_CONFIG_FILENAME = file_to_save

        return True

    def load(self, filename: str):
        with open(os.path.join(self.CONFIG_DIR, filename), 'r') as f:
            config_d = json.load(f)
        is_ok = self.update(config_d)
        if is_ok:
            self.CURRENT_CONFIG_FILENAME = filename
        return is_ok