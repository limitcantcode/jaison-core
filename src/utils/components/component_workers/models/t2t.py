from ...component_worker_base import BaseComponentWorker
from jaison_grpc.client import T2TComponentStreamerStub
from jaison_grpc.common import T2TComponentRequest, T2TComponentResponse

class T2TWorker(BaseComponentWorker):
    def setup(self):
        self.stub = T2TComponentStreamerStub(self.channel)

    async def create_async_generator_from_stream(self, stream): # stream: {run_id, system_input, user_input}
        first_chunk = await anext(stream)
        yield T2TComponentRequest(run_id=first_chunk['run_id'], system_input="", user_input="")
        yield T2TComponentRequest(run_id=first_chunk['run_id'], system_input=first_chunk['system_input_chunk'], user_input=first_chunk['user_input_chunk'])
        async for next_chunk in stream:
            yield T2TComponentRequest(run_id=next_chunk['run_id'], system_input=next_chunk['system_input_chunk'], user_input=next_chunk['user_input_chunk'])

    def create_generator_from_stream(self, stream): # stream: {run_id, system_input, user_input}
        first_chunk = next(stream)
        yield T2TComponentRequest(run_id=first_chunk['run_id'], system_input="", user_input="")
        yield T2TComponentRequest(run_id=first_chunk['run_id'], system_input=first_chunk['system_input_chunk'], user_input=first_chunk['user_input_chunk'])
        for next_chunk in stream:
            yield T2TComponentRequest(run_id=next_chunk['run_id'], system_input=next_chunk['system_input_chunk'], user_input=next_chunk['user_input_chunk'])

    def extract_chunk(self, chunk: T2TComponentResponse):
        return {
            'run_id': chunk.run_id,
            'content_chunk': chunk.content_chunk
        }