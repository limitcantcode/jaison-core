class StartActiveError(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__("Start called on already active {} operation {}".format(op_type, op_id))
        
class CloseInactiveError(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__("Close called on already inactive {} operation {}".format(op_type, op_id))
    
class UsedInactiveError(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__("Usage on inactive {} operation {}".format(op_type, op_id))