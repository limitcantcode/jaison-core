from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from .base import FilterTextOperation

class KoalaModerationFilter(FilterTextOperation):
    GOOD_LABEL = "OK"
    
    def __init__(self):
        super().__init__("mod_koala")
        self.model, self.tokenizer = None, None
        
    async def start(self):
        await super().start()
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation").to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation")
        
    async def close(self):
        await super().close()
        del self.model, self.tokenizer
        if torch.cuda.is_available(): torch.cuda.empty_cache() # clean cache on cuda
    
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        return
      
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {}

    async def _generate(self, content: str = None, **kwargs):
        '''Generate a output stream'''
        # Classify content
        inputs = self.tokenizer(content, return_tensors="pt").to(self.device)
        outputs = self.model(**inputs)

        # Get class scores
        logits = outputs.logits
        probabilities = logits.softmax(dim=-1).squeeze()

        # Retrieve the labels
        id2label = self.model.config.id2label
        labels = [id2label[idx] for idx in range(len(probabilities))]

        # Sort labels by score
        label_prob_pairs = list(zip(labels, probabilities))
        label_prob_pairs.sort(key=lambda item: item[1], reverse=True)  

        # Handle top classification
        top_label, _ = label_prob_pairs[0]
        filtered = top_label != self.GOOD_LABEL
        
        yield {
            "content": content, 
            "filtered": filtered
        }
