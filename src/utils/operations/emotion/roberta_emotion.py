
import logging
from transformers import pipeline
import torch
from typing import Dict, AsyncGenerator, Any
from .meta import EmotionOperation
from ..base import Capability

class RobertaEmotionClassifier(EmotionOperation):
    FILTERED_MESSAGE = "Filtered."
    GOOD_LABEL = "OK"
    
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.classifier = None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.classifier is not None: await self.unload()
        self.classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=1, device=('cuda' if torch.cuda.is_available() else 'cpu'))
        
    async def unload(self):
        del self.classifier
        if torch.cuda.is_available(): torch.cuda.empty_cache() # clean cache on cuda
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        content = ""
        async for in_d in in_stream:
            content += in_d['content']
            
        assert content is not None and len(content) > 0
        
        emotion = self.classifier(content)[0][0]['label']
        
        logging.debug(f"Operation {self.id} got result: {emotion}")
        yield {"label": emotion}