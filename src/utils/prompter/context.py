class ContextMetadata:
    def __init__(self, id: str, name: str, description: str):
        assert id and len(id) > 0
        assert name and len(name) > 0

        self.id: str = id
        self.name: str = name
        self.description: str = description or ""
