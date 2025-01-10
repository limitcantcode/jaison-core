from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import TTSCComponentStreamerStub
from jaison_grpc.common import TTSCComponentRequest, TTSCComponentResponse

class TTSCWorker(BaseComponentWorker):
    def setup(self):
        self.stub = TTSCComponentStreamerStub(self.channel)

    def create_stream(self, run_id, payload):
        return self.stub.invoke(TTSCComponentRequest(run_id=run_id, content=payload['content']))
    
    def extract_chunk(self, chunk: TTSCComponentResponse):
        return chunk.audio_chunk