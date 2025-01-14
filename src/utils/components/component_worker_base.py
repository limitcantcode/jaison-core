import grpc
from .component_details import ComponentDetails
from .error import InvalidComponentConfig
from utils.logging import create_sys_logger

class BaseComponentWorker():
    def __init__(self, details: ComponentDetails):
        if not details.endpoint:
            raise InvalidComponentConfig(f"Endpoint not (auto) set before creating component worker.")
        self.logger = create_sys_logger()
        self.details = details
        self.channel = grpc.aio.insecure_channel(details.endpoint)
        self.setup()

    async def __call__(self, run_id: str, payload: dict):
        stream = self.create_stream(run_id, payload)
        async for response in stream:
            run_id, response_chunk = response.run_id, self.extract_chunk(response)
            self.logger(f"Component worker {self.details.id} returned for {run_id} with result: {response_chunk}")
            yield run_id, response_chunk
        self.logger.debug(f"Component worker {self.details.id} finished streaming.")
    
    def close(self):
        self.channel.close()

    ## TO BE IMPLEMENTED ################
    
    def setup(self):
        raise NotImplementedError
    
    def create_stream(self, run_id: str, payload: dict):
        raise NotImplementedError
    
    def extract_chunk(self, chunk):
        raise NotImplementedError