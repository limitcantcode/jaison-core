from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import TTSGComponentStreamerStub
from jaison_grpc.common import TTSGComponentRequest, TTSGComponentResponse

class TTSGWorker(BaseComponentWorker):
    def setup(self):
        self.stub = TTSGComponentStreamerStub(self.channel)

    def create_stream(self, run_id, payload):
        return self.stub.invoke(TTSGComponentRequest(run_id=run_id, audio=payload['audio']))
    
    def extract_chunk(self, chunk: TTSGComponentResponse):
        return chunk.audio_chunk