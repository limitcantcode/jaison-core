from .openai_worker import OpenAIWorker
from .llama_worker import LlamaAIWorker
from .base_worker import EmptyRequestException

model_dict = {
    'openai': OpenAIWorker,
    'local': LlamaAIWorker
}

def get_prompt_from_file(filepath: str):
    with open(filepath, 'r') as f:
        return f.read()