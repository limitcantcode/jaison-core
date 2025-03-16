import asyncio
from typing import List, AsyncGenerator

'''ObserverClient asynchronously handles events in queue populated by an ObserverServer'''
class BaseObserverClient():
    def __init__(self, server = None):
        self.server = None
        if server:
            self.listen(server)
            
        self.queue = asyncio.Queue()
        self.event_listener = None

    def listen(self, server):
        if self.server:
            self.close()

        self.server = server
        self.server.join(self)
        
        self.event_listener = asyncio.create_task(self._event_listener())

    def close(self):
        self.server.detach(self)
        self.server = None
        
    async def _event_listener(self):
        while True:
            next_event = await self.queue.get()
            await self.handle_event(next_event['event'], next_event['payload'])
            
    # To Be Implement
    async def handle_event(self, event_id: str, payload) -> None:
        raise NotImplementedError

'''ObserverServer adds events and payloads to all listening client queues.'''
class ObserverServer():
    def __init__(self):
        self.clients: List[ObserverClient] = []

    def join(self, client):
        if client not in self.clients:
            self.clients.append(client)

    def detach(self, client):
        if client in self.clients:
            self.clients.remove(client)

    async def broadcast_event(self, event_id: str, payload: dict = {}):
        for client in self.clients:
            await client.queue.put({
                "event": event_id,
                "payload": payload
            })
            
    async def broadcast_stream(self, event_id: str, payload_stream: AsyncGenerator):
        async for payload in payload_stream:
            for client in self.clients:
                await client.queue.put({
                    "event": event_id,
                    "payload": payload
                })