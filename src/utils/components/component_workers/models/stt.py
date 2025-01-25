from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import STTComponentStreamerStub
from jaison_grpc.common import STTComponentRequest, STTComponentResponse

class STTWorker(BaseComponentWorker):
    def setup(self):
        self.stub = STTComponentStreamerStub(self.channel)

    async def create_async_generator_from_stream(self, stream): # stream: {run_id, audio_chunk, sample_rate, sample_width, channels}
        first_chunk = anext(stream)
        yield STTComponentRequest(run_id=first_chunk['run_id'], audio=b"", sample_rate=0, sample_width=0, channels=0)
        yield STTComponentRequest(
            run_id=first_chunk['run_id'], 
            audio=first_chunk['audio_chunk'], 
            sample_rate=first_chunk['sample_rate'], 
            sample_width=first_chunk['sample_width'], 
            channels=first_chunk['channels']
        )
        async for next_chunk in stream:
            yield STTComponentRequest(
                run_id=next_chunk['run_id'], 
                audio=next_chunk['audio_chunk'], 
                sample_rate=next_chunk['sample_rate'], 
                sample_width=next_chunk['sample_width'], 
                channels=next_chunk['channels']
            )

    async def create_generator_from_stream(self, stream): # stream: {run_id, audio_chunk, sample_rate, sample_width, channels}
        first_chunk = next(stream)
        yield STTComponentRequest(run_id=first_chunk['run_id'], audio=b"", sample_rate=0, sample_width=0, channels=0)
        yield STTComponentRequest(
            run_id=first_chunk['run_id'], 
            audio=first_chunk['audio_chunk'], 
            sample_rate=first_chunk['sample_rate'], 
            sample_width=first_chunk['sample_width'], 
            channels=first_chunk['channels']
        )
        for next_chunk in stream:
            yield STTComponentRequest(
                run_id=next_chunk['run_id'], 
                audio=next_chunk['audio_chunk'], 
                sample_rate=next_chunk['sample_rate'], 
                sample_width=next_chunk['sample_width'], 
                channels=next_chunk['channels']
            )

    def extract_chunk(self, chunk: STTComponentResponse):
        return {
            'run_id': chunk.run_id,
            'content_chunk': chunk.content_chunk
        }