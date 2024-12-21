from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import os
import json
import shutil
import time
from utils.observer import ObserverClient

PORT = 5000
HOST_SERVER_URL = f"http://127.0.0.1:{PORT}"
app = Flask(__name__)
cors = CORS(app, resources={r"/static/*": {"origins": f"http://127.0.0.1:{PORT}"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'jaisonSecret!'
socketio = SocketIO(app)

jaison = None
event_client = None

@app.route('/')
def page_home():
        return render_template('page_home.html')

@app.route('/assets')
def page_assets():
    return render_template('page_assets.html', host_server_url=HOST_SERVER_URL)

@app.route('/configs')
def page_configs():
    return render_template('page_configs.html')

@app.route('/controls')
def page_controls():
    return render_template('page_controls.html', host_server_url=HOST_SERVER_URL)

@app.route('/datasets')
def page_datasets():
    return render_template('page_datasets.html')

## WEBSOCKET SERVICE #########

class WSBroadcaster(ObserverClient):
    def __init__(self, server = None):
        global socketio
        super().__init__(server=server)
        self.socketio = socketio
        self.event_queue = []

    def handle_event(self, event_id, payload) -> None:
        if event_id == 'response_generated':
            global jaison
            if jaison.response_cancelled:
                return
            shutil.copy(jaison.config.RESULT_TTSC, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/generated/response.wav'))

        global socketio
        socketio.emit(
            event_id, 
            payload
        )


## API #########################

def base_api_with_response(fun, params=[], kwargs={}, info_msg="", success_msg="", error_msg="", no_toast=False):
    global event_client
    if not no_toast:
        event_client.handle_event('toast_info', info_msg)
    try:
        result = fun(*params, **kwargs)
        if not no_toast:
            event_client.handle_event('toast_success', success_msg)
        return result
    except Exception as err:
        print(err)
        if not no_toast:
            event_client.handle_event('toast_error', error_msg)
        raise err

def base_api_no_response(fun, params=[], kwargs={}, info_msg="", success_msg="", error_msg="", no_toast=False):
    global event_client
    if not no_toast:
        event_client.handle_event('toast_info', info_msg)
    try:
        is_ok = fun(*params, **kwargs)
        if is_ok:
            if not no_toast:
                event_client.handle_event('toast_success', success_msg)
            return { "status": True }
        else:
            raise Exception("Internal server error")
    except Exception as err:
        print(err)
        if not no_toast:
            event_client.handle_event('toast_error', error_msg)
        return { "status": False }

@app.route('/api/one-time-request', methods=['POST'])
def api_one_time_request():
    return base_api_no_response(
        jaison.inject_one_time_request,
        params=[json.loads(request.data)],
        info_msg="Queuing one-time request...",
        success_msg="One-time request queued!",
        error_msg="Failed to queue one-time request!"
    )

@app.route('/api/get_name_translations', methods=['GET'])
def api_get_name_translations():
    return base_api_with_response(
        jaison.get_name_translations,
        no_toast=True
    )

@app.route('/api/save_name_translations', methods=['POST'])
def api_save_name_translations():
    return base_api_no_response(
        jaison.save_name_translations,
        params=[json.loads(request.data)['message']],
        info_msg="Saving name translations...",
        success_msg="Saved name translation!",
        error_msg="Failed to save name translations!"
    )

@app.route('/api/get_prompt_filenames', methods=['GET'])
def api_get_prompt_filenames():
    return base_api_with_response(
        jaison.get_prompt_filenames,
        no_toast=True
    )

@app.route('/api/load_prompt_file', methods=['POST'])
def api_load_prompt_file():
    return base_api_no_response(
        jaison.load_prompt_file,
        params=[json.loads(request.data)['filename']],
        info_msg="Loading prompt file...",
        success_msg="Prompt file loaded!",
        error_msg="Failed to load prompt file!"
    )

@app.route('/api/get_current_prompt', methods=['GET'])
def api_get_current_prompt():
    return base_api_with_response(
        jaison.get_current_prompt,
        no_toast=True
    )

@app.route('/api/save_prompt_file', methods=['POST'])
def api_save_prompt_file():
    request_data = json.loads(request.data)
    return base_api_no_response(
        jaison.save_prompt_file,
        params=[request_data['filename'],
        request_data['contents']],
        info_msg="Saving prompt file...",
        success_msg="Saved prompt file!",
        error_msg="Failed to save prompt file!"
    )

@app.route('/api/set_context_toggles', methods=['POST'])
def api_set_context_toggles():
    return base_api_no_response(
        jaison.set_context_toggles, 
        params=[json.loads(request.data)],
        info_msg="Updating context toggles...",
        success_msg="Updated context toggles!",
        error_msg="Failed to update context toggles!"
    )

@app.route('/api/get_context_toggles', methods=['GET'])
def api_get_context_toggles():
    return base_api_with_response(
        jaison.get_context_toggles,
        no_toast=True
    )

@app.route('/api/get_config_from_file', methods=['POST'])
def api_get_config_from_file():
    return base_api_with_response(
        jaison.get_config_from_file,
        params=[json.loads(request.data)['filename']],
        info_msg="Getting config from file...",
        success_msg="Got config from file!",
        error_message="Failed to get config from file!"
    )

@app.route('/api/get_config_files', methods=['GET'])
def api_get_config_files():
    return base_api_with_response(
        jaison.get_config_files,
        no_toast=True
    )

@app.route('/api/set_config_file', methods=['POST'])
def api_set_config_file():
    return base_api_no_response(
        jaison.set_config_file, 
        params=[json.loads(request.data)['filename']],
        info_msg="Changing config file in use...",
        success_msg="Changed config file in use!",
        error_msg="Failed to change config file in use!"
    )

@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    request_data = json.loads(request.data)
    return base_api_no_response(
        jaison.save_config_file,
        params=[request_data['filename'],request_data['config']],
        info_msg="Saving config to file...",
        success_msg="Saved config to file!",
        error_msg="Failed to save config to file!"
    )

@app.route('/api/cancel_response', methods=['GET'])
def api_cancel_response():
    return base_api_no_response(
        jaison.cancel_response,
        info_msg="Stopping response...",
        success_msg="Stopped response!",
        error_msg="Failed to stop response!"
    )


def start_ui(jaison_app):
    global jaison
    global event_client
    jaison = jaison_app
    event_client = WSBroadcaster(jaison.broadcast_server)
    socketio.run(app, port=PORT)