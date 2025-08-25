
from transformers import pipeline
import torch

from .base import FilterTextOperation

class RobertaEmotionFilter(FilterTextOperation):
    def __init__(self):
        super().__init__("emotion_roberta")
        self.classifier = None
        
    async def start(self):
        await super().start()
        self.classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=1, device=('cuda' if torch.cuda.is_available() else 'cpu'))

    async def close(self):
        await super().close()
        del self.classifier
        if torch.cuda.is_available(): torch.cuda.empty_cache() # clean cache on cuda
    
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        return
    
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {}

    async def _generate(self, content: str = None, **kwargs):
        yield {"content": content, "emotion": self.classifier(content)[0][0]['label']}