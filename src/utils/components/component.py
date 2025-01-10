import socket
import psutil
import subprocess
from copy import deepcopy
from .component_details import ComponentDetails
from .component_worker_base import BaseComponentWorker
from .component_workers import COMPONENT_COLLECTION

class Component():
    def __init__(self, details: ComponentDetails):
        self.details: ComponentDetails = deepcopy(details)
        self.process: subprocess.Popen = None
        if not self.details.endpoint:
            self._connect_new()
        self.worker: BaseComponentWorker = COMPONENT_COLLECTION[details.comp_type]

    def __call__(self, run_id, payload):
        for run_id, chunk in self.worker(run_id, payload):
            yield run_id, chunk
            
    def close(self):
        if self.process:
            process = psutil.Process(self.process.pid)
            for child in process.children(recursive=True):
                child.kill()
            process.kill()

        if self.worker:
            self.worker.close()

    def _get_open_port(self):
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def _connect_new(self):
        port = self._get_open_port()
        self.process = subprocess.Popen(["cd",self.details.directory,";",self.details.run_script,str(port)], shell=True)
        self.details.update_endpoint(f'127.0.0.1:{port}')

