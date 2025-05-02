import os
import json
from typing import get_type_hints
from src.utils.args import args
from src.utils.helpers.singleton import Singleton
from src.utils.logging import create_sys_logger
logger = create_sys_logger()

class Configuration(metaclass=Singleton):
    # DONT SAVE
    CONFIG_DIR = os.path.join(os.getcwd(),"configs","jaison") # DONT SAVE: constant
    CURRENT_CONFIG_FILENAME = None # DONT SAVE

    # T2T
    prompt_dir: str = os.path.join(os.getcwd(),"prompts","production") # DONT SAVE: constant
    name_translation_dir: str = os.path.join(os.getcwd(),"configs","translations") # DONT SAVE: constant
    prompt_current_file: str = None # DONT SAVE: session specific
    prompt_default_file: str = "example.txt"
    prompt_params: dict = dict()
    name_translation_file: str = None
    convo_retention_length: int = 5

    # Plugins
    plugins_config_dir: str = os.path.join(os.getcwd(),"configs","plugins") # DONT SAVE: constant
    plugins_config_file: str = "example.yaml"
    active_plugins: list = list()

    # Web
    web_port: int = 5001

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
                "prompt_default_file": self.prompt_default_file,
                "prompt_params": self.prompt_params,
                "name_translation_file": self.name_translation_file,
                "convo_retention_length": self.convo_retention_length,
                "plugins_config_file": self.plugins_config_file,
                "active_plugins": self.active_plugins,
                "web_port": self.web_port
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