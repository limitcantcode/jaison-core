'''
Global processes manager

Enables expensive processes used in one place to be reused elsewhere
For example: Kobold server shared between STT and T2T operation implementation
'''

from utils.helpers.singleton import Singleton
from .processes.koboldcpp import KoboldCPPProcess # TODO: will this introduce dependency issues (for not, no since process classes are minimal)

class ProcessManager(metaclass=Singleton): # TODO something for process readying events
    koboldcpp = KoboldCPPProcess()
    
    '''Reload any process where reload_signal is True'''
    async def reload(self):
        # Just list them here sequentially
        if self.koboldcpp.reload_signal: await self.koboldcpp.reload()
        
    '''Unload any process where unload_signal is True'''
    async def unload(self):
        # Just list them here sequentially
        if self.koboldcpp.unload_signal: await self.koboldcpp.unload()