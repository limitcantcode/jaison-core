from openai import AsyncOpenAI

from utils.config import Config

from .base import T2TOperation

class OpenAIT2T(T2TOperation):
    def __init__(self):
        super().__init__()
        self.client = None
        
    async def start(self):
        await super().start()
        self.client = AsyncOpenAI(base_url=Config().openai_t2t_base_url)
        
    async def close(self):
        await super().close()
        await self.client.close()
        self.client = None
        
    async def _generate(self, system_prompt: str = None, user_prompt: str = None, **kwargs):
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
