class ObserverClient():
    def __init__(self, server = None):
        self.server = None
        if server:
            self.listen(server)

    def listen(self, server):
        if self.server:
            self.close()

        self.server = server
        self.server.join(self)

    def close(self):
        self.server.detach(self)
        self.server = None

    # To Be Implement
    async def handle_event(self, event_id: str, payload) -> None:
        raise NotImplementedError