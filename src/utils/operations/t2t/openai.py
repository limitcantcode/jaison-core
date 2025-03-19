import logging
from typing import Dict, AsyncGenerator, Any
from openai import AsyncOpenAI
from utils.config import Config
from .meta import T2TOperation
from ..base import Capability

class OpenAIT2T(T2TOperation):
    def __init__(self, capability: Capability):
        super().__init__(capability)
        self.client = None
        
    async def start(self):
        await self.reload()
        
    async def reload(self):
        if self.client is not None: await self.unload()
        self.client = AsyncOpenAI(base_url=Config().openai_t2t_base_url)
        
    async def unload(self):
        self.client.close()
        self.client = None
        
    async def __call__(
        self, 
        in_stream: AsyncGenerator = None,
        **kwargs
    ):
        system_prompt: str = ""
        user_prompt: str = ""
        async for in_d in in_stream:
            system_prompt += in_d['system_prompt']
            user_prompt += in_d['user_prompt']
            
        assert system_prompt is not None and len(system_prompt) > 0
        assert user_prompt is not None and  len(user_prompt) > 0
        
        messages=[
            { "role": "system", "content": system_prompt },
            { "role": "user", "content": user_prompt }
        ]

        stream = await self.client.chat.completions.create(
            messages=messages,
            model=Config().openai_t2t_model,
            stream=True,
            temperature=Config().openai_t2t_temperature,
            top_p=Config().openai_t2t_top_p,
            presence_penalty=Config().openai_t2t_presence_penalty,
            frequency_penalty=Config().openai_t2t_frequency_penalty
        )

        full_response = ""
        async for chunk in stream:
            content_chunk = chunk.choices[0].delta.content or ""
            full_response += content_chunk
            yield {"content": content_chunk}
        logging.debug(f"Operation {self.id} finished with result: {full_response}")
