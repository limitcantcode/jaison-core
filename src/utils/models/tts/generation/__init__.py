from .base_worker import BaseTTSGenWorker
from .openai_worker import OpenAITTSWorker
from .sapi_worker import OldTTSWorker

model_dict = {
    "openai": OpenAITTSWorker,
    "old": OldTTSWorker
}