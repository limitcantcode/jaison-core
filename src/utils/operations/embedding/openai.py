from openai import AsyncOpenAI
import struct
import base64

from .base import EmbeddingOperation

class OpenAIEmbedding(EmbeddingOperation):
    def __init__(self):
        super().__init__("openai")
        self.client = None
        
        self.base_url = "https://api.openai.com/v1/"
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
        
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
        if "dimensions" in config_d: self.dimensions = int(config_d['dimensions'])

        assert self.base_url is not None and len(self.base_url) > 0
        assert self.model is not None and len(self.model) > 0
        assert self.dimensions in [1536]
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "base_url": self.base_url,
            "model": self.model,
            "dimensions": self.dimensions
        }

    async def _generate(self, content: str = None, **kwargs):
        response = await self.client.embeddings.create( # dimension 1536 default for small
            model=self.model,
            input=content,
            dimensions=self.dimensions,
            encoding_format="float"
        )

        float_list = response.data[0].embedding
        format_string = '<' + 'f' * len(float_list)
        packed_bytes = struct.pack(format_string, *float_list)
        result = base64.b64encode(packed_bytes).decode('utf-8')

        yield {
            "embedding": result
        }