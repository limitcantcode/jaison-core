import logging
from typing import Dict, List, AsyncGenerator
from utils.helpers.singleton import Singleton
from utils.config import Config

from .base import BaseOperation, Capability
from .error import (
    InvalidOperationType,
    InvalidOperationID,
    UnloadedOperationError,
    CompatibilityModeEnabled
)

from .chunker import *
from .filter import *
from .emotion import *
from .stt import *
from .t2t import *
from .ttsg import *
from .ttsc import *

class OperationManager(metaclass=Singleton):
    def __init__(self):
        self.op_collection: Dict[str, Dict[str, Capability]] = {
            STT_TYPE: stt_capabilities,
            T2T_TYPE: t2t_capabilities,
            TTSG_TYPE: ttsg_capabilities,
            TTSC_TYPE: ttsc_capabilities,
            CHUNKER_TYPE: chunker_capabilities,
            FILTER_TYPE: filter_capabilities,
            EMOTION_TYPE: emotion_capabilities,
        }
        
        self.stt: STTOperation = None
        self.t2t: T2TOperation = None
        self.ttsg: TTSGOperation = None
        self.ttsc: TTSCOperation = None
        
        self.chunker: ChunkerOperation = None
        self.emotion: EmotionOperation = None
        self.filters: Dict[str, FilterOperation] = dict() # Order doesn't matter for now, but will matter when starting to consider response transformations
    
    ## Main functions ###################
    
    '''Get dictionary containing all loaded operations'''
    def get_loaded_operations(self):
        result = {}
        if self.stt is not None: result = result | {STT_TYPE: self.stt.id}
        if self.t2t is not None: result = result | {T2T_TYPE: self.t2t.id}
        if self.ttsg is not None: result = result | {TTSG_TYPE: self.ttsg.id}
        if self.ttsc is not None: result = result | {TTSC_TYPE: self.ttsc.id}
        if self.chunker is not None: result = result | {CHUNKER_TYPE: self.chunker.id}
        if self.emotion is not None: result = result | {EMOTION_TYPE: self.emotion.id}
        if len(self.filters) > 0:
            result = result | {FILTER_TYPE: [self.filters[key].id for key in self.filters]}
        
        return result
    
    '''
    Start an unloaded operation.
    
    Any conflicting operation should be unloaded prior.
    '''
    async def start_operation(self, op_type: str, op_id: str):
        # Validate operation can be started
        self._validate_op_key(op_type, op_id=op_id)
        if (
            self.op_collection[op_type][op_id].compatibility is False
            and Config().compatibility_mode is True
        ): 
            raise CompatibilityModeEnabled(op_type, op_id)
        
        # Lazy load and start new operation
        op = self.op_collection[op_type][op_id]()
        await op.start()
        
        # Track in manager
        if op_type == FILTER_TYPE: self.filters[op_id] = op
        else: self.__setattr__(op_type, op)
        
    '''Reload a loaded operation'''
    async def reload_operation(self, op_type: str, op_id: str):
        # Validate operation can be started
        self._validate_op_key(op_type, op_id=op_id)
        
        # Confirm loaded, get, and reload
        await self._get_loaded_op(op_type, op_id=op_id)[0].reload()
    
    '''Unload a loaded operation'''
    async def unload_operation(self, op_type: str, op_id: str):
        # Validate operation can be started
        self._validate_op_key(op_type, op_id=op_id)
        
        # Confirm loaded, get, and unload
        await self._get_loaded_op(op_type, op_id=op_id)[0].unload()
        
        # Update manager trakcing
        if op_type == FILTER_TYPE: del self.filters[op_id]
        else: self.__setattr__(op_type, None)
       
    async def reload_all(self):
        loaded_op = self.get_loaded_operations()
        for op_type in loaded_op:
            if isinstance(loaded_op[op_type], str):
                await self.reload_operation(op_type, loaded_op[op_type])
            elif isinstance(loaded_op[op_type], dict):
                for op_key in loaded_op[op_type]:
                    await self.reload_operation(op_type, op_key)     
     
    async def unload_all(self):
        loaded_op = self.get_loaded_operations()
        for op_type in loaded_op:
            if isinstance(loaded_op[op_type], str):
                await self.unload_operation(op_type, loaded_op[op_type])
            elif isinstance(loaded_op[op_type], dict):
                for op_key in loaded_op[op_type]:
                    await self.unload_operation(op_type, op_key)
        
    def use(self, op_type: str, op_id: str = None, in_stream: AsyncGenerator = None, **kwargs):
        self._validate_op_key(op_type, op_id=op_id)
        
        op_list = self._get_loaded_op(op_type, op_id=op_id)
        assert len(op_list) > 0
        
        out_stream: AsyncGenerator = in_stream
        for op in op_list:
            out_stream = op(in_stream=out_stream)
            
        return out_stream
        

    ## Helper functions ###################
    
    '''
    Raises specific exception if operation key is invalid.
    
    Exceptions:
    - InvalidOperationType: When operation type doesn't exist
    - InvalidOperationID: When operation ID doesn't exist under that operation type
    '''
    def _validate_op_key(self, op_type: str, op_id: str = None) -> None:
        if op_type not in self.op_collection: raise InvalidOperationType(op_type)
        if op_id is not None and op_id not in self.op_collection[op_type]: raise InvalidOperationID(op_type, op_id)
        
    '''
    Confirms specified operation is loaded and tracked and returns that operation.
    
    Exceptions:
    - UnloadedOperationError: When specified operation isn't loaded
    '''
    def _get_loaded_op(self, op_type: str, op_id: str = None) -> List[BaseOperation]:
        if op_type == FILTER_TYPE:
            if op_id is not None:
                if op_id not in self.filters: raise UnloadedOperationError(op_type, op_id)
                return [self.filters[op_id]]
            else:
                if len(self.filters) == 0: raise UnloadedOperationError(op_type, op_id)
                return self.filters.values()
        else: 
            op: BaseOperation = self.__getattribute__(op_type)
            if op is None or (op_id is not None and op_id != op.id): raise UnloadedOperationError(op_type, op_id)
            return [op]
