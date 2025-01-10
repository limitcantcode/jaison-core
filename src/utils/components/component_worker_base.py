import grpc
from .component_details import ComponentDetails
from .error import InvalidComponentConfig
from utils.logging import create_sys_logger

class BaseComponentWorker():
    def __init__(self, details: ComponentDetails):
        STREAM_END = grpc.aio.EOF
        
        if not details.endpoint:
            raise InvalidComponentConfig(f"Endpoint no (auto) set before creating component worker.")
        self.logger = create_sys_logger()
        self.details = details
        self.channel = grpc.aio.insecure_channel(details.endpoint)
        self.setup()

    async def __call__(self, run_id: str, payload: dict):
        stream = self.create_stream(run_id, payload)
        while True:
            response = await stream.read()
            if response == self.STREAM_END:
                break
            yield response.run_id, self.extract_chunk(response)
    
    def close(self):
        self.channel.close()

    ## TO BE IMPLEMENTED ################
    
    def setup(self):
        raise NotImplementedError
    
    def create_stream(self, run_id: str, payload: dict):
        raise NotImplementedError
    
    def extract_chunk(self, chunk):
        raise NotImplementedError