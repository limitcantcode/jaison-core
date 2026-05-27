import re

from .base import FilterTextOperation


class ResponseCleaningFilter(FilterTextOperation):
    def __init__(self):
        super().__init__("filter_clean")
        self.pattern = None

    async def start(self):
        await super().start()
        self.pattern = re.compile(r"\[[^\[\]]+\]:\s*")

    async def close(self):
        await super().close()

    async def configure(self, config_d):
        """Configure and validate operation-specific configuration"""
        return

    async def get_configuration(self):
        """Returns values of configurable fields"""
        return {}

    async def _generate(self, content: str = None, **kwargs):
        """Generate a output stream"""
        while True:
            match = self.pattern.search(content)
            if match:
                tmp = content[: match.span()[0]]
                tmp += content[match.span()[1] :]
                content = tmp
            else:
                break

        yield {"content": content}
