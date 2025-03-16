'''
Capability class

Metadata and lazy loader for each operation
'''

from importlib import import_module
from .operation import BaseOperation
from .constants import OPERATION_MODULE

class Capability:
    def __init__(
        self,
        op_type: str,
        op_implem_filename: str,
        op_cls_name: str,
        compatibility: bool=False
    ):
        # Operation type, same as its root directory name e.g. 'filter' for koala_ai_filter
        self.op_type: str = op_type
        
        # Filename without extension, e.g. 'koala_ai_filter' for 'koala_ai_filter.py'
        # Will be used as ID
        self.op_implem_filename: str = op_implem_filename
        
        # Operation class in that file, e.g. 'KoalaAIFilter'
        self.op_cls_name: str = op_cls_name 
        
        # Actual capabilities
        self.compatibility: bool = compatibility # If true, can be loaded while compatibility mode is on
        
    def __call__(self) -> BaseOperation:
        return getattr(
            import_module(f"{OPERATION_MODULE}.{self.op_type}.{self.op_implem_filename}"),
            self.op_cls_name
        )(self)