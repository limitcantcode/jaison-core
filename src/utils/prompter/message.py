import datetime
from .context import ContextMetadata

class Message:
    def to_line():
        raise NotImplementedError
    
class RequestMessage(Message):
    def __init__(self, message: str, time: datetime.datetime):
        assert message is not None and len(message) > 0
        
        self.message = message.replace("\n", "")
        self.time = time
        
    def to_line(self):
        return f"[REQUEST]: {self.message}"
    
class ChatMessage(Message):
    def __init__(self, user: str, message: str, time: datetime.datetime):
        assert user is not None
        assert message is not None and len(message) > 0
        
        self.user = user
        self.message = message.replace("\n", "")
        self.time = time
        
    def to_line(self):
        return f"[{self.user}]: {self.message}"
    
class CustomMessage(Message):
    def __init__(self, context_metadata: ContextMetadata, message: str, time: datetime.datetime):
        assert context_metadata is not None
        assert message is not None and len(message) > 0
        
        self.context_metadata = context_metadata
        self.message = message.replace("\n", "")
        self.time = time
        
    def to_line(self):
        return f"[CONTEXT#{self.context_metadata.name}]: {self.message}"