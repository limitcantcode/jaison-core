import subprocess
import psutil
import logging

from .error import DuplicateLink, MissingLink

class BaseProcess(): # Be sure to make it a singleton (metaclass=Singleton)
    id: str = None
    process: subprocess.Popen = None
    port: int = None
    links: set = set()
    
    reload_signal: bool = False
    unload_signal: bool = False
    
    def __init__(self, id):
        self.id = id
    
    async def reload(self):
        # This needs to be implemented
        self.reload_signal = False
    
    async def unload(self):
        self.unload_signal = False
        
        if len(self.links):
            logging.warning(f"Unloading process that still has the {len(self.links)} links")
            logging.warning(f"Links: {self.links}")
        
        if self.process:
            ps_process = psutil.Process(self.process.pid)
            for child in ps_process.children(recursive=True):
                child.kill()
            ps_process.kill()
            self.process = None
            self.port = None
            logging.info(f"Unloaded process {self.id}")
        else:
            logging.warning(f"Attempted to unload process {self.id} when it is already unloaded")
    
    async def link(self, link_id):
        logging.debug("Adding link {} to process {}".format(link_id, self.id))
        if link_id in self.links:
            raise DuplicateLink(link_id, self.id)
        
        if self.process is None:
            await self.reload()
            
        self.links.add(link_id) # Add to links after loading process to ensure link established
        
    async def unlink(self, link_id):
        logging.debug("Removing link {} from process {}".format(link_id, self.id))
        if link_id not in self.links:
            raise MissingLink(link_id, self.id)
        self.links.remove(link_id)
        
        if len(self.links):
            logging.info(f"No more links to process {self.id}. Unloading...")
            await self.unload()
