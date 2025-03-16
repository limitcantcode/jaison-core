from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

EMOTION_TYPE = 'emotion'

class EmotionOperation(BaseOperation):
    async def __call__(
        self,
        in_stream: AsyncGenerator[Dict[str, Any]] = None, # in_stream {content: str}
        **kwargs
    ): # out_stream {label: str}
        raise NotImplementedError
    
emotion_capabilities: Dict[str, Capability] = {
    "roberta_emotion": Capability(
        EMOTION_TYPE,
        "roberta_emotion",
        'RobertaEmotionClassifier',
        compatibility=False
    )
}