class ContextMetadata:
    def __init__(self, id: str, name: str, description: str):
        assert id and len(id) > 0 # TODO throw custom error
        assert name and len(name) > 0 # TODO throw custom error
        
        self.id: str = id
        self.name: str = name
        self.description: str = description or ""