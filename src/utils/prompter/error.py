class UnknownContext(Exception):
    def __init__(self, context_id):
        super().__init__(f"No custom context with id {context_id}")
        
class InvalidContext(Exception):
    def __init__(self):
        super().__init__("Context must have an ID and name")