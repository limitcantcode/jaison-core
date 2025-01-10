from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import STTComponentStreamerStub
from jaison_grpc.common import STTComponentRequest, STTComponentResponse

class STTWorker(BaseComponentWorker):
    def setup(self):
        self.stub = STTComponentStreamerStub(self.channel)

    def create_stream(self, run_id, payload):
        return self.stub.invoke(STTComponentRequest(run_id=run_id, audio=payload['audio']))
        
    def extract_chunk(self, chunk: STTComponentResponse):
        return chunk.content_chunk