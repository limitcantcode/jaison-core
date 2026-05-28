import logging
import socket
import subprocess
from subprocess import DEVNULL

from utils.config import config

from ..base import BaseProcess


class KoboldCPPProcess(BaseProcess):
    def __init__(self):
        super().__init__("koboldcpp")
        self.reload_signal = True

    async def reload(self):
        # Close any existing servers
        if self.process is not None:
            await self.unload()

        await super().reload()

        # Find open port
        sock = socket.socket()
        sock.bind(("", 0))
        self.port = sock.getsockname()[1]
        sock.close()

        # Start Kobold server on that port
        cmd = f'{config.kobold_filepath} --quiet --config "{config.kcpps_filepath}" --port {self.port}'
        logging.debug(f'Running Koboldcpp server using command: "{cmd}"')
        self.process = subprocess.Popen(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)
        logging.info(f"Opened Koboldcpp server (PID: {self.process.pid}) on port {self.port}")
