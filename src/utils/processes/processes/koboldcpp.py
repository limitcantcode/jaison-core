import logging
import subprocess
import socket
from utils.config import Config
from utils.helpers.singleton import Singleton
from ..base import BaseProcess

class KoboldCPPProcess(BaseProcess, metaclass=Singleton):
    async def __init__(self):
        super().__init__("koboldcpp")
        self.reload()
        
    async def reload(self): # TODO asynchronously start process and signal ready
        # Close any existing servers
        if self.process is not None:
            self.unload()
        
        # Find open port
        config = Config()
        sock = socket.socket()
        sock.bind(('', 0))
        self.port = sock.getsockname()[1]
        sock.close()
        
        # Start Kobold server on that port
        cmd = '{} --quiet --config "{}"'.format(config.kobold_filepath, config.kcpps_filepath)
        cmd += " --port {}".format(self.port)
        if config['use-vulkan']: cmd += " --usevulkan {}".format(config['vulkan-device'] or "")
        logging.debug(f"Running Koboldcpp server using command: \"{cmd}\"")
        self.process = subprocess.Popen(cmd, shell=True)
        logging.info(f"Opened Koboldcpp server on port {self.port}")