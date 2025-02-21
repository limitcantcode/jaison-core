import socket
import psutil
import os
import subprocess
from copy import deepcopy
from .component_details import ComponentDetails
from .component_worker_base import BaseComponentWorker
from .component_workers import COMPONENT_COLLECTION
from utils.logging import create_sys_logger

logger = create_sys_logger()

class Component():
    def __init__(self, details: ComponentDetails):
        logger.debug(f"Creating new component for {details.id}")
        self.details: ComponentDetails = deepcopy(details)
        self.process: subprocess.Popen = None
        if not self.details.endpoint:
            self._run_process()
        logger.debug(f"Using component type: {self.details.comp_type}")
        logger.debug(f"Connected component worker to process at endpoint {self.details.endpoint}.")

    def __call__(self, input_stream):
        worker: BaseComponentWorker = COMPONENT_COLLECTION[self.details.comp_type](self.details)

        logger.debug(f"Streaming from component {self.details.id}")
        return worker(input_stream)
            
    def close(self):
        if self.process:
            logger.debug(f"Stopping process for component {self.details.id}")
            process = psutil.Process(self.process.pid)
            for child in process.children(recursive=True):
                child.kill()
            process.kill()

    def _get_open_port(self):
        logger.debug(f"Finding open port...")
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        logger.debug(f"Found open port: {port}")
        return port

    def _run_process(self):
        logger.debug("Starting component in new process.")
        port = self._get_open_port()
        cmd = f"cd {self.details.directory} && {os.path.join("./", self.details.run_script)} {str(port)}"
        logger.debug(f"Running command: {cmd}")
        self.process = subprocess.Popen(cmd, shell=True)
        address = f'127.0.0.1:{port}'
        self.details.update_endpoint(address)
        logger.debug(f"Started new process on {address}.")

