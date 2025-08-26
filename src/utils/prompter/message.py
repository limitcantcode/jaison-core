import datetime
from .context import ContextMetadata

class Message:
    def to_line():
        raise NotImplementedError
    
    def to_dict():
        raise NotImplementedError
    
class RawMessage(Message):
    def __init__(self, message: str,):
        assert message is not None and len(message) > 0
        
        self.message = message.replace("\n", "")
        
    def to_line(self):
        return self.message
    
    def to_dict(self):
        return {
            "type": "raw",
            "message": self.message
        }
    
class RequestMessage(Message):
    def __init__(self, message: str, time: datetime.datetime):
        assert message is not None and len(message) > 0
        
        self.message = message.replace("\n", "")
        self.time = time
        
    def to_line(self):
        return f"[REQUEST]: {self.message}"
    
    def to_dict(self):
        return {
            "type": "request",
            "time": self.time.timestamp(),
            "message": self.message
        }
    
class ChatMessage(Message):
    def __init__(self, user: str, message: str, time: datetime.datetime):
        assert user is not None
        assert message is not None and len(message) > 0
        
        self.user = user
        self.message = message.replace("\n", "")
        self.time = time
        
    def to_line(self):
        return f"[{self.user}]: {self.message}"
    
    def to_dict(self):
        return {
            "type": "chat",
            "user": self.user,
            "time": self.time.timestamp(),
            "message": self.message
        }

class MCPMessage(Message):
    def __init__(self, tool_name: str, result: str, time: datetime.datetime):
        assert tool_name is not None
        assert result is not None and len(result) > 0
        
        self.tool_name = tool_name
        self.result = result.replace("\n", "")
        self.time = time
        
    def to_line(self):
        return f"[MCP#{self.tool_name}]: {self.result}"
    
    def to_dict(self):
        return {
            "type": "tool",
            "tool": self.tool_name,
            "time": self.time.timestamp(),
            "message": self.message
        }
    
class CustomMessage(Message):
    def __init__(self, context_metadata: ContextMetadata, message: str, time: datetime.datetime):
        assert context_metadata is not None
        assert message is not None and len(message) > 0
        
        self.context_metadata = context_metadata
        self.message = message.replace("\n", "")
        self.time = time
        
    def to_line(self):
        return f"[CONTEXT#{self.context_metadata.name}]: {self.message}"
    
    def to_dict(self):
        return {
            "type": "custom",
            "id": self.context_metadata.id,
            "time": self.time.timestamp(),
            "message": self.message
        }