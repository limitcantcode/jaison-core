import logging
from typing import Dict, AsyncGenerator, Any
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from utils.config import Config
from .meta import FilterOperation
from ..base import Capability

class KoalaAIFilter(FilterOperation):
    FILTERED_MESSAGE = "Filtered."
    GOOD_LABEL = "OK"
    
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.model, self.tokenizer = None, None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.model is not None: await self.unload()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation").to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation")
        
    async def unload(self):
        del self.model, self.tokenizer
        if torch.cuda.is_available(): torch.cuda.empty_cache() # clean cache on cuda
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        if Config().default_skip_filters:
            logging.info("Filter is disabled. Skipping")
            async for in_d in in_stream:
                yield in_d
        else:
            full_content = ""
            sentence = ""
            async for in_d in in_stream:
                sentence += in_d['content']
                full_content += sentence
                is_good = self._filter(full_content)
                yield {"content": sentence} if is_good else {"content": self.FILTERED_MESSAGE}
                sentence = ""
                if not is_good: break
                
            if len(sentence) > 0:
                is_good =  await self._filter(sentence)
                yield {"content": sentence} if is_good else {"content": self.FILTERED_MESSAGE}
                
            logging.info(f"Operation {self.id} has finished")
        
    def _filter(self, content: str):
        assert content is not None and len(content) > 0
        
        # Run the model on your input
        inputs = self.tokenizer(content, return_tensors="pt").to(self.device)
        outputs = self.model(**inputs)

        # Get the predicted logits
        logits = outputs.logits

        # Apply softmax to get probabilities (scores)
        probabilities = logits.softmax(dim=-1).squeeze()

        # Retrieve the labels
        id2label = self.model.config.id2label
        labels = [id2label[idx] for idx in range(len(probabilities))]

        # Combine labels and probabilities, then sort
        label_prob_pairs = list(zip(labels, probabilities))
        label_prob_pairs.sort(key=lambda item: item[1], reverse=True)  

        # Retrieve most likely classification
        top_label, _ = label_prob_pairs[0]
        
        # Handle result
        logging.info(f"Operation {self.id} got result: {top_label}")
        filtered = top_label != self.GOOD_LABEL
        if filtered:
            logging.info("Filtering response")
            return False
        else:
            return True