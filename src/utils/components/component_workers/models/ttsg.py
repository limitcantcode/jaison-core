from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import TTSGComponentStreamerStub
from jaison_grpc.common import TTSGComponentRequest, TTSGComponentResponse

class TTSGWorker(BaseComponentWorker):
    def setup(self):
        self.stub = TTSGComponentStreamerStub(self.channel)

    async def create_async_generator_from_stream(self, stream): # stream: {run_id, content_chunk}
        first_chunk = await anext(stream)
        yield TTSGComponentRequest(run_id=first_chunk['run_id'], content="")
        yield TTSGComponentRequest(
            run_id=first_chunk['run_id'], 
            content=first_chunk['content_chunk'], 
        )
        async for next_chunk in stream:
            yield TTSGComponentRequest(
                run_id=next_chunk['run_id'], 
                content=next_chunk['content_chunk']
            )

    def create_generator_from_stream(self, stream): # stream: {run_id, content_chunk}
        first_chunk = next(stream)
        yield TTSGComponentRequest(run_id=first_chunk['run_id'], content="")
        yield TTSGComponentRequest(
            run_id=first_chunk['run_id'], 
            content=first_chunk['content_chunk'], 
        )
        for next_chunk in stream:
            yield TTSGComponentRequest(
                run_id=next_chunk['run_id'], 
                content=next_chunk['content_chunk']
            )

    def extract_chunk(self, chunk: TTSGComponentResponse):
        return {
            'run_id': chunk.run_id,
            'audio_chunk': chunk.audio_chunk,
            "channels": chunk.channels,
            "sample_width": chunk.sample_width,
            "sample_rate": chunk.sample_rate
        }