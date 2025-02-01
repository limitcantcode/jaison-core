from flask import Flask, request
from flask_cors import CORS
import json
from utils.jaison import JAIson, NonexistantRunException
from utils.config import Configuration
from utils.logging import create_sys_logger
from .common import create_response

logger = create_sys_logger(use_stdout=True)

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'jaisonSecret!'

jaison = JAIson()
config = Configuration()

# @app.route('/configuration/components')
# def page_home():
#         return {"hello":"world!"}

# @app.route('/configuration/internal')
# def page_home():
#         return {"hello":"world!"}

@app.route('/run', methods=['POST'])
def run_start():
      global jaison
      try:
            new_run_id = jaison.create_run(**json.loads(request.data))
      except Exception as err:
            logger.error("Unknown error", stack_info=True, exc_info=True)
            return create_response(500, err.message, {})
      return create_response(200, f"Run {new_run_id} started", {"run_id": new_run_id})

@app.route('/run', methods=['DELETE'])
def run_cancel():
      global jaison
      request_data = json.loads(request.data)
      if 'run_id' not in request_data:
            return create_response(400, f"Invalid request body", {})
      run_id, reason = request_data['run_id'], request_data.get('reason')
      try:
            jaison.cancel_run(run_id, reason=reason)
            return create_response(200, f"Run {run_id} cancelled", {"run_id": run_id})
      except NonexistantRunException as err:
            return create_response(400, err.message, {"run_id": run_id})
      except Exception as err:
            logger.error("Unknown error", stack_info=True, exc_info=True)
            return create_response(500, err.message, {})
      

def start_rest_api():
      app.run(port=config.web_api_port)