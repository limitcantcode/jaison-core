class InvalidOperationType(Exception):
    def __init__(self, op_type: str):
        super().__init__(f"Attempt on non-existant type {op_type}")

class InvalidOperationID(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__(f'No operation with ID {op_id} for {op_type}')

class UnloadedOperationError(Exception):
    def __init__(self, op_type: str, op_id: str = None):
        message = ""
        if op_id is not None: message = f"Operation {op_id} is not loaded for {op_type}"
        else: message = f"No operation for {op_type} is loaded"
        super().__init__(message)

class CompatibilityModeEnabled(Exception):
    def __init__(self, op_type: str, op_id: str):
        super().__init__(f"Operation with ID {op_id} of type {op_type} can not be used when compatibility mode is enabled")