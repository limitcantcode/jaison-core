from typing import Dict, AsyncGenerator, Any
from ...base import BaseOperation, Capability

T2T_TYPE = 't2t'

class T2TOperation(BaseOperation):
    async def __call__(
        self, 
        in_stream: AsyncGenerator[Dict[str, Any]] = None, # {system_prompt: str, user_prompt: str}
        **kwargs
    ): # {content: str}
        raise NotImplementedError

t2t_capabilities: Dict[str, Capability] = {
    "openai": Capability(
        T2T_TYPE,
        "openai",
        'OpenAIT2T',
        compatibility=True
    )
}