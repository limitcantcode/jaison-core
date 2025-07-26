'''
Global processes manager

Enables expensive processes used in one place to be reused elsewhere
For example: Kobold server shared between STT and T2T operation implementation
'''

import logging
from enum import Enum

from utils.helpers.singleton import Singleton

from .error import UnknownProcessError, UnloadedProcessError

class ProcessType(Enum):
    KOBOLD = "kobold"

class ProcessManager(metaclass=Singleton):
    loaded_processes = dict()
    
    '''Perform initial load'''
    async def load(self, process_type: ProcessType):
        logging.info("Loading process by type {}".format(process_type.value))
        match process_type:
            case ProcessType.KOBOLD:
                from .processes.koboldcpp import KoboldCPPProcess
                self.loaded_processes[ProcessType.KOBOLD] = KoboldCPPProcess()
                await self.loaded_processes[ProcessType.KOBOLD].reload()
            case _:
                raise UnknownProcessError(process_type)
        
    '''Reload any process where reload_signal is True'''
    async def reload(self):
        for process_type in self.loaded_processes:
            if self.loaded_processes[process_type] and self.loaded_processes[process_type].reload_signal:
                logging.info("Reloading process {}".format(self.loaded_processes[process_type].id))
                await self.loaded_processes[process_type].reload()
        
    '''Unload any process where unload_signal is True'''
    async def unload(self):
        for process_type in self.loaded_processes:
            if self.loaded_processes[process_type] and self.loaded_processes[process_type].unload_signal:
                logging.info("Unloading process {}".format(self.loaded_processes[process_type].id))
                await self.loaded_processes[process_type].unload()
                
    async def link(self, link_id: str, process_type: ProcessType):
        if not (process_type in self.loaded_processes and self.loaded_processes[process_type]):
            await self.load(process_type)
            
        await self.loaded_processes[process_type].link(link_id)
        
    async def unlink(self, link_id: str, process_type: ProcessType):
        if not (process_type in self.loaded_processes and self.loaded_processes[process_type]):
            raise UnloadedProcessError(process_type.value)
            
        await self.loaded_processes[process_type].unlink(link_id)
    
    def signal_reload(self, process_type: ProcessType):
        if not (process_type in self.loaded_processes and self.loaded_processes[process_type]):
            raise UnloadedProcessError(process_type.value)
            
        self.loaded_processes[process_type].reload_signal = True
        
    def signal_unload(self, process_type: ProcessType):
        if not (process_type in self.loaded_processes and self.loaded_processes[process_type]):
            raise UnloadedProcessError(process_type.value)
            
        self.loaded_processes[process_type].unload_signal = True
        
    def get_process(self, process_type: ProcessType):
        if not (process_type in self.loaded_processes and self.loaded_processes[process_type]):
            raise UnloadedProcessError(process_type.value)
            
        return self.loaded_processes[process_type]