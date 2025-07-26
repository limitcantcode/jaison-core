class UnknownOpType(Exception):
    def __init__(self, op_type: str):
        super().__init__("No operation of type {}".format(op_type))
        
class UnknownOpRole(Exception):
    def __init__(self, op_role: str):
        super().__init__("No operation of role {}".format(op_role))
        
class UnknownOpID(Exception):
    def __init__(self, op_type: str, op_id):
        super().__init__("No operation of type {} with id {}".format(op_type, op_id))
        
class DuplicateFilter(Exception):
    def __init__(self, op_type: str, op_id):
        super().__init__("Can not add already active {} {}".format(op_type, op_id))
        
class OperationUnloaded(Exception):
    def __init__(self, op_type: str, op_id: str = None):
        if op_id: super().__init__("No operation {} with id {} loaded".format(op_type, op_id))
        else: super().__init__("No operation of type {} loaded".format(op_type))