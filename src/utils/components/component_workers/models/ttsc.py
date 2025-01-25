from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import TTSCComponentStreamerStub
from jaison_grpc.common import TTSCComponentRequest, TTSCComponentResponse

class TTSCWorker(BaseComponentWorker):
    def setup(self):
        self.stub = TTSCComponentStreamerStub(self.channel)

    async def create_async_generator_from_stream(self, stream): # stream: {run_id, audio_chunk, sample_rate, sample_width, channels}
        first_chunk = await anext(stream)
        yield TTSCComponentRequest(run_id=first_chunk['run_id'], audio=b"", sample_rate=0, sample_width=0, channels=0)
        yield TTSCComponentRequest(
            run_id=first_chunk['run_id'], 
            audio=first_chunk['audio_chunk'], 
            sample_rate=first_chunk['sample_rate'], 
            sample_width=first_chunk['sample_width'], 
            channels=first_chunk['channels']
        )
        async for next_chunk in stream:
            yield TTSCComponentRequest(
                run_id=next_chunk['run_id'], 
                audio=next_chunk['audio_chunk'], 
                sample_rate=next_chunk['sample_rate'], 
                sample_width=next_chunk['sample_width'], 
                channels=next_chunk['channels']
            )

    def create_generator_from_stream(self, stream): # stream: {run_id, audio_chunk, sample_rate, sample_width, channels}
        first_chunk = next(stream)
        yield TTSCComponentRequest(run_id=first_chunk['run_id'], audio=b"", sample_rate=0, sample_width=0, channels=0)
        yield TTSCComponentRequest(
            run_id=first_chunk['run_id'], 
            audio=first_chunk['audio_chunk'], 
            sample_rate=first_chunk['sample_rate'], 
            sample_width=first_chunk['sample_width'], 
            channels=first_chunk['channels']
        )
        for next_chunk in stream:
            yield TTSCComponentRequest(
                run_id=next_chunk['run_id'], 
                audio=next_chunk['audio_chunk'], 
                sample_rate=next_chunk['sample_rate'], 
                sample_width=next_chunk['sample_width'], 
                channels=next_chunk['channels']
            )

    def extract_chunk(self, chunk: TTSCComponentRequest):
        return {
            'run_id': chunk.run_id,
            'audio_chunk': chunk.audio_chunk,
            "channels": chunk.channels,
            "sample_width": chunk.sample_width,
            "sample_rate": chunk.sample_rate
        }