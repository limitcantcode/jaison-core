from quart import Quart, request, websocket
import asyncio
import json
import base64
import logging
from utils.helpers.singleton import Singleton
from utils.jaison import JAIson
from utils.config import Config
from utils.helpers.observer import BaseObserverClient
from .common import create_response

class SocketServerObserver(BaseObserverClient, metaclass=Singleton):
    def __init__(self):
        super().__init__(server=JAIson().event_server)
        self.connections = set()
        self.shutdown_signal = asyncio.Future()

    async def handle_event(self, event_id: str, payload) -> None:
        '''Broadcast events from broadcast server'''
        for key in payload:
            if isinstance(payload[key], bytes):
                  payload[key] = base64.b64encode(payload[key]).decode('utf-8')
        message = json.dumps(create_response(200, event_id, payload))
        logging.debug(f"Broadcasting event: {message:.100} to {len(self.connections)} clients")
        for ws in set(self.connections):
            await ws.send(message)
            
    def shutdown(self, *args):
        self.shutdown_signal.set_result(None)

app = Quart(__name__)
cors_header = {'Access-Control-Allow-Origin': '*'}

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
    sso = SocketServerObserver()
    logging.info("Opened new websocket connection")
    ws = websocket._get_current_object()
    await ws.accept()
    sso.connections.add(ws)
    try:
        while not sso.shutdown_signal.is_set():
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        sso.connections.discard(ws)
        logging.info("Closed websocket connection")
        raise
    
@app.route('/run', methods=['POST'])
async def run_start():
    global jaison
    try:
        new_run_id = await jaison.create_run(**await request.get_json(force=True))
    except Exception as err:
        logging.error("Unknown error", stack_info=True, exc_info=True)
        return create_response(500, str(err), {})
    return create_response(200, f"Run {new_run_id} started", {"run_id": new_run_id}, cors_header)

@app.route('/run', methods=['DELETE'])
async def run_cancel():
    request_data = await request.get_json()
    if 'run_id' not in request_data:
        return create_response(400, f"Invalid request body", {}, cors_header)
    run_id, reason = request_data['run_id'], request_data.get('reason')
    try:
        await JAIson().cancel_run(run_id, reason=reason)
        return create_response(200, f"Run {run_id} cancelled", {"run_id": run_id}, cors_header)
    except NonexistantRunException as err:
        return create_response(400, str(err), {"run_id": run_id}, cors_header)
    except Exception as err:
        logging.error("Unknown error", stack_info=True, exc_info=True)
        return create_response(500, str(err), {}, cors_header)
      
@app.route('/context', methods=['POST'])
async def context_register():
    try:
        request_data = await request.get_json()
        JAIson().register_context(request_data.get('id'), request_data.get('name'), request_data.get('description'))
        return create_response(200, f"Context added", {"id": request_data.get('id')}, cors_header)
    except Exception as err:
        logging.error("Unknown error", stack_info=True, exc_info=True)
        return create_response(500, str(err), {}, cors_header)
      
@app.route('/context', methods=['PUT'])
async def context_update():
    try:
        request_data = await request.get_json()
        JAIson().update_context(request_data.get('id'), request_data.get('content'))
        return create_response(200, f"Context updated", {"id": request_data.get('id')}, cors_header)
    except Exception as err:
        logging.error("Unknown error", stack_info=True, exc_info=True)
        return create_response(500, str(err), {}, cors_header)
      
@app.route('/context', methods=['DELETE'])
async def context_delete():
    try:
        request_data = await request.get_json()
        JAIson().register_context(request_data.get('id'))
        return create_response(200, f"Context deleted", {"id": request_data.get('id')}, cors_header)
    except Exception as err:
        logging.error("Unknown error", stack_info=True, exc_info=True)
        return create_response(500, str(err), {}, cors_header)

async def start_web_server():
    global app
    JAIson().start()
    SocketServerObserver()
    await app.run_task(port=Config().web_port)