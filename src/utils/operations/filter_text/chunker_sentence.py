import spacy

from utils.config import Config

from .base import FilterTextOperation


class SentenceChunkerFilter(FilterTextOperation):
    def __init__(self):
        super().__init__("chunker_sentence")
        self.nlp = None

    async def start(self):
        await super().start()
        self.nlp = spacy.load(Config().spacy_model)

    async def close(self):
        await super().close()
        self.nlp = None

    async def configure(self, config_d):
        """Configure and validate operation-specific configuration"""
        return

    async def get_configuration(self):
        """Returns values of configurable fields"""
        return {}

    async def _generate(self, content: str = None, **kwargs):
        """Generate a output stream"""
        sentences = [sent.text.strip() for sent in self.nlp(content).sents]

        for s in sentences:
            yield {"content": s}
