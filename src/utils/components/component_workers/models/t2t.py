from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import T2TComponentStreamerStub
from jaison_grpc.common import T2TComponentRequest, T2TComponentResponse

class T2TWorker(BaseComponentWorker):
    def setup(self):
        self.stub = T2TComponentStreamerStub(self.channel)

    def create_stream(self, run_id, payload):
        return self.stub.invoke(T2TComponentRequest(run_id=run_id, system_input=payload['system_input'], user_input=payload['user_input']))
    
    def extract_chunk(self, chunk: T2TComponentResponse):
        return chunk.content_chunk