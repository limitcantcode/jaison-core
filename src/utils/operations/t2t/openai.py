from openai import AsyncOpenAI

from .base import T2TOperation
from utils.prompter.message import ChatMessage
from utils.prompter import Prompter

class OpenAIT2T(T2TOperation):
    def __init__(self):
        super().__init__("openai")
        self.client = None
        
        self.base_url = "https://api.openai.com/v1/"
        self.model = "gpt-4o"
        self.temperature = 1
        self.top_p = 0.9
        self.presence_penalty = 0
        self.frequency_penalty = 0
        
    async def start(self):
        await super().start()
        self.client = AsyncOpenAI(base_url=self.base_url)
        
    async def close(self):
        await super().close()
        await self.client.close()
        self.client = None
        
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "base_url" in config_d: self.base_url = str(config_d['base_url'])
        if "model" in config_d: self.model = str(config_d['model'])

        if "temperature" in config_d: self.temperature = float(config_d['temperature'])
        if "top_p" in config_d: self.top_p = float(config_d['top_p'])
        if "presence_penalty" in config_d: self.presence_penalty = float(config_d['presence_penalty'])
        if "frequency_penalty" in config_d: self.frequency_penalty = float(config_d['frequency_penalty'])
        
        assert self.base_url is not None and len(self.base_url) > 0
        assert self.model is not None and len(self.model) > 0
        assert self.temperature >= 0 and self.temperature <= 2
        assert self.top_p >= 0 and self.top_p <= 1
        assert self.presence_penalty >= 0 and self.presence_penalty <= 1
        assert self.frequency_penalty >= 0 and self.frequency_penalty <= 1
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }

    async def _generate(self, instruction_prompt: str = None, messages: list = None, **kwargs):
        history = [{ "role": "system", "content": instruction_prompt }]
        for msg in messages:
            next_hist = None
            if isinstance(msg, ChatMessage) and msg.user == Prompter().character_name:
                next_hist = { "role": "assistant", "content": msg.message }
            else:
                next_hist = { "role": "user", "content": msg.to_line() }
            history.append(next_hist)

        stream = await self.client.chat.completions.create(
            messages=history,
            model=self.model,
            stream=True,
            temperature=self.temperature,
            top_p=self.top_p,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty
        )

        full_response = ""
        async for chunk in stream:
            content_chunk = chunk.choices[0].delta.content or ""
            full_response += content_chunk
            yield {"content": content_chunk}
