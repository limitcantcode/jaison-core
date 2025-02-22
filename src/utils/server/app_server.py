from quart import Quart, request, websocket, make_response
import asyncio
import json
from utils.jaison import JAIson, NonexistantRunException
from utils.config import Configuration
from utils.observer import ObserverClient
from utils.signal import GracefulKiller
from utils.logging import create_sys_logger
from .common import create_response
logger = create_sys_logger(use_stdout=True)
kill_handler = GracefulKiller()

class SocketServerObserver(ObserverClient):
    connections = set()

    def __init__(self, jaison):
        super().__init__(server=jaison.broadcast_server)

    async def handle_event(self, event_id: str, payload) -> None:
        '''Broadcast events from JAIson'''
        message = json.dumps(create_response(200, event_id, payload))
        logger.debug(f"Broadcasting event: {message:.50} to {len(self.connections)} clients")
        for ws in set(self.connections):
            await ws.send(message)

app = Quart(__name__)

jaison = None
config = None
sso = None

cors_header = {'Access-Control-Allow-Origin': '*'}

@app.route('/run', methods=['POST'])
async def run_start():
      global jaison
      try:
            new_run_id = await jaison.create_run(**await request.get_json(force=True))
      except Exception as err:
            logger.error("Unknown error", stack_info=True, exc_info=True)
            return create_response(500, str(err), {})
      return create_response(200, f"Run {new_run_id} started", {"run_id": new_run_id}, cors_header)

@app.route('/run', methods=['DELETE'])
async def run_cancel():
      global jaison
      request_data = await request.get_json()
      if 'run_id' not in request_data:
            return create_response(400, f"Invalid request body", {}, cors_header)
      run_id, reason = request_data['run_id'], request_data.get('reason')
      try:
            await jaison.cancel_run(run_id, reason=reason)
            return create_response(200, f"Run {run_id} cancelled", {"run_id": run_id}, cors_header)
      except NonexistantRunException as err:
            return create_response(400, str(err), {"run_id": run_id}, cors_header)
      except Exception as err:
            logger.error("Unknown error", stack_info=True, exc_info=True)
            return create_response(500, str(err), {}, cors_header)
      
@app.route('/context', methods=['POST'])
async def context_register():
      global jaison
      try:
            request_data = await request.get_json()
            jaison.register_context(request_data.get('id'), request_data.get('name'), request_data.get('description'))
            return create_response(200, f"Context added", {"id": request_data.get('id')}, cors_header)
      except Exception as err:
            logger.error("Unknown error", stack_info=True, exc_info=True)
            return create_response(500, str(err), {}, cors_header)
      
@app.route('/context', methods=['PUT'])
async def context_update():
      global jaison
      try:
            request_data = await request.get_json()
            jaison.update_context(request_data.get('id'), request_data.get('content'))
            return create_response(200, f"Context updated", {"id": request_data.get('id')}, cors_header)
      except Exception as err:
            logger.error("Unknown error", stack_info=True, exc_info=True)
            return create_response(500, str(err), {}, cors_header)
      
@app.route('/context', methods=['DELETE'])
async def context_delete():
      global jaison
      try:
            request_data = await request.get_json()
            jaison.register_context(request_data.get('id'))
            return create_response(200, f"Context deleted", {"id": request_data.get('id')}, cors_header)
      except Exception as err:
            logger.error("Unknown error", stack_info=True, exc_info=True)
            return create_response(500, str(err), {}, cors_header)

# Allow CORS
@app.route('/run', methods=['OPTIONS'])
async def run_preflight():
      return ("Success", 200, {
           'Access-Control-Allow-Origin': '*',
           'Access-Control-Allow-Methods': 'POST, DELETE, OPTIONS',
           'Access-Control-Allow-Headers': 'Content-Type'})

@app.route('/context', methods=['OPTIONS'])
async def context_preflight():
      return ("Success", 200, {
           'Access-Control-Allow-Origin': '*',
           'Access-Control-Allow-Methods': 'POST, DELETE, OPTIONS, PUT',
           'Access-Control-Allow-Headers': 'Content-Type'})

@app.websocket("/")
async def ws():
    logger.info("Opened new websocket connection")
    ws = websocket._get_current_object()
    await ws.accept()
    sso.connections.add(ws)
    try:
        while True:
            await asyncio.sleep(10)
            # await ws.ping()
    except asyncio.CancelledError:
        logger.info("Closed websocket connection")
        sso.connections.remove(ws)
        raise

async def start_web_server():
    global jaison, config, sso, kill_handler
    jaison = JAIson()
    await jaison.setup()
    config = Configuration()
    sso = SocketServerObserver(jaison)
    kill_handler.add_cleanup(jaison) # TODO handle cleanup properly again
    await app.run_task(port=config.web_port, debug=True)