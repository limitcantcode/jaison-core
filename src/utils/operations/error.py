class UnknownOpType(Exception):
    def __init__(self, op_type: str):
        super().__init__(f"No operation of type {op_type}")


class UnknownOpRole(Exception):
    def __init__(self, op_role: str):
        super().__init__(f"No operation of role {op_role}")


class UnknownOpID(Exception):
    def __init__(self, op_type: str, op_id):
        super().__init__(f"No operation of type {op_type} with id {op_id}")


class DuplicateFilter(Exception):
    def __init__(self, op_type: str, op_id):
        super().__init__(f"Can not add already active {op_type} {op_id}")


class OperationUnloaded(Exception):
    def __init__(self, op_type: str, op_id: str = None):
        if op_id:
            super().__init__(f"No operation {op_type} with id {op_id} loaded")
        else:
            super().__init__(f"No operation of type {op_type} loaded")
