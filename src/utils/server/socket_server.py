import websockets
import json
from utils.config import Configuration
from utils.jaison import JAIson
from utils.observer import ObserverClient

from .common import create_response

class SocketServerObserver(ObserverClient):
    connections = set()

    def __init__(self):
        self.jaison = JAIson()
        self.config = Configuration()
        super().__init__(server=self.jaison.broadcast_server)
        self.socket_server = websockets.serve(self.handler, self.config.web_host, self.config.web_socket_port)

    async def handle_event(self, event_id: str, payload) -> None:
        '''Broadcast events from JAIson'''
        for ws in self.connections:
            await ws.send(json.dumps(create_response(200, event_id, payload)))

    async def handler(self, ws, path):
        '''Handle events from external connections'''
        data = await ws.recv()
        data = json.loads(data)

        if 'request' not in data:
            await ws.send(json.dumps(create_response(400, "'request' field not included", {})))
            return
        
        match data['request']:
            case 'connect':
                if ws in self.connections:
                    await ws.send(json.dumps(create_response(400, f"Already connected", {})))
                else:
                    self.connections.add(ws)
            case 'disconnect':
                if ws not in self.connections:
                    await ws.send(json.dumps(create_response(400, f"Already disconnected", {})))
                else:
                    self.connections.remove(ws)
            case _:
                await ws.send(json.dumps(create_response(400, f"{data['request']} is not a valid request type", {"request": data['request']})))
