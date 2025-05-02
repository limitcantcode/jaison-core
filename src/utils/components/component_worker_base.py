import grpc
from typing import Generator, AsyncGenerator, Iterator, AsyncIterator
from .component_details import ComponentDetails
from .error import InvalidComponentConfig
from src.utils.logging import create_sys_logger

class BaseComponentWorker():
    def __init__(self, details: ComponentDetails):
        if not details.endpoint:
            raise InvalidComponentConfig(f"Endpoint not (auto) set before creating component worker.")
        self.logger = create_sys_logger()
        self.details = details
        self.channel = grpc.aio.insecure_channel(details.endpoint)
        self.setup()

    async def __call__(self, input_stream):
        stream = self.create_stream(input_stream)
        async for response in stream:
            response_chunk = self.extract_chunk(response)
            self.logger.debug(f"Component worker {self.details.id} returned for {response_chunk.get('run_id')} with result: {str(response_chunk):.200}")
            yield response_chunk
        self.logger.debug(f"Component worker {self.details.id} finished streaming.")
    
    def close(self):
        self.channel.close()

    def create_stream(self, stream):
        if isinstance(stream, (Generator,Iterator)):
            generator = self.create_generator_from_stream(stream)
        elif isinstance(stream, (AsyncGenerator,AsyncIterator)):
            generator = self.create_async_generator_from_stream(stream)
        else:
            raise TypeError(f"Got unexpected type: {type(stream)}")
        return self.stub.invoke(generator)

    ## TO BE IMPLEMENTED ################
    
    def setup(self):
        raise NotImplementedError
    
    def create_async_generator_from_stream(self, stream: AsyncGenerator):
        raise NotImplementedError
    
    def create_generator_from_stream(self, stream: Generator):
        raise NotImplementedError
    
    def extract_chunk(self, chunk):
        raise NotImplementedError