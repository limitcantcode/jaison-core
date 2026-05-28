class StartActiveError(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__(f"Start called on already active {op_type} operation {op_id}")


class CloseInactiveError(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__(f"Close called on already inactive {op_type} operation {op_id}")


class UsedInactiveError(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__(f"Usage on inactive {op_type} operation {op_id}")
