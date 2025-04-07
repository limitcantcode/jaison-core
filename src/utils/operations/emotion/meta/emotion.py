from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

EMOTION_TYPE = 'emotion'

class EmotionOperation(BaseOperation):
    async def __call__(
        self,
        in_stream: AsyncGenerator = None, # in_stream {content: str}
        **kwargs
    ): # out_stream {label: str}
        raise NotImplementedError
    
emotion_capabilities: Dict[str, Capability] = {
    "roberta": Capability(
        EMOTION_TYPE,
        "roberta",
        'RobertaEmotionClassifier',
        compatibility=False
    )
}