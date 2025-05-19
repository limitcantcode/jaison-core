import logging
import subprocess
from subprocess import DEVNULL
import socket
from utils.config import Config
from utils.helpers.singleton import Singleton
from ..base import BaseProcess

class KoboldCPPProcess(BaseProcess, metaclass=Singleton):
    def __init__(self):
        super().__init__("koboldcpp")
        self.reload_signal = True
        
    async def reload(self):
        # Close any existing servers
        if self.process is not None:
            await self.unload()
        
        await super().reload()
        
        # Find open port
        config = Config()
        sock = socket.socket()
        sock.bind(('', 0))
        self.port = sock.getsockname()[1]
        sock.close()
        
        # Start Kobold server on that port
        cmd = '{} --quiet --config "{}" --port {}'.format(config.kobold_filepath, config.kcpps_filepath, self.port)
        logging.debug(f"Running Koboldcpp server using command: \"{cmd}\"")
        self.process = subprocess.Popen(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)
        logging.info(f"Opened Koboldcpp server (PID: {self.process.pid}) on port {self.port}")