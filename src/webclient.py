import asyncio
import websockets
import json

async def foo():
    ws = await websockets.connect('ws://localhost:5005')
    await ws.send(json.dumps({"test":"message"}))
    print(await ws.recv())
    await ws.close()

asyncio.run(foo())