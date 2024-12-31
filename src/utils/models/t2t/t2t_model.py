from .openai_worker import OpenAIModel
from .llama_worker import LlamaAIModel
from utils.logging import create_sys_logger
logger = create_sys_logger()

class T2TModel():
    T2T_MODELS = {
        'openai': OpenAIModel,
        'local': LlamaAIModel
    }

    def __init__(self, jaison):
        if jaison.config.t2t_host is None or jaison.config.t2t_host not in self.T2T_MODELS:
            err_msg = "T2T model host key {} doesn't exist".format(jaison.config.t2t_host)
            logger.error(err_msg)
            raise Exception(err_msg)

        self.model = self.T2T_MODELS[jaison.config.t2t_host](jaison)

        logger.debug(f"T2TModel initialized with host {jaison.config.t2t_host}")

    def __call__(self, time, name, message):
        logger.debug(f"Got request for message: {message}")
        result = self.model(time, name, message)
        logger.debug(f"Got response result: {result}")
        return result

    def inject_one_time_request(self, message):
        return self.model.inject_one_time_request(message)