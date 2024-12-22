from .base_worker import BaseTTSGenModel
from .openai_worker import OpenAITTSModel
from .sapi_worker import OldTTSModel
from utils.logging import create_sys_logger
logger = create_sys_logger()

class TTSGModel():
    TTSG_MODELS = {
        "openai": OpenAITTSModel,
        "old": OldTTSModel
    }

    def __init__(self, config):
        self.model = self.TTSG_MODELS[config.ttsg_host](config)
        logger.debug(f"TTSGModel initialized with host {config.ttsg_host}")


    def __call__(self, content: str):
        logger.debug(f"Got request to transform message into audio: {content}")
        self.model(content)
        logger.debug(f"Finished transforming message into audio")
        return True