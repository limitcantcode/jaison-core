import asyncio

class ObserverServer():
    def __init__(self):
        self.clients = []
        self.ongoing = set()
        # self.loop = event_loop

    def join(self, client):
        if client not in self.clients:
            self.clients.append(client)

    def detach(self, client):
        if client in self.clients:
            self.clients.remove(client)

    async def broadcast_event(self, event_id: str, payload = None):
        # for task in set(self.ongoing):
        #     if not task.done():
        #         self.ongoing.discard(task)

        for client in self.clients:
            # task = asyncio.run_coroutine_threadsafe(
            #     client.handle_event(event_id, payload), self.loop
            # )
            # self.ongoing.add(task)

            await client.handle_event(event_id, payload)