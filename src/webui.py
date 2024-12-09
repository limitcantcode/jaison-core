from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import os

PORT = 5000

app = Flask(__name__)
cors = CORS(app, resources={r"/static/*": {"origins": f"http://127.0.0.1:{PORT}"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'jaisonSecret!'
socketio = SocketIO(app)

@app.route('/')
def page_home():
    return render_template('page_home.html')

@app.route('/assets')
def page_assets():
    return render_template('page_assets.html')

@app.route('/configs')
def page_configs():
    return render_template('page_configs.html')

@app.route('/controls')
def page_controls():
    return render_template('page_controls.html')

@app.route('/datasets')
def page_datasets():
    return render_template('page_datasets.html')

# @socketio.on('open_file_request')
# def open_sys_log(message):
#     print("opening file")
#     file_name = "/home/limit/Projects/J.A.I.son/logs/sys/{}.log".format(message['file_name'])
#     if not os.path.isfile(file_name):
#         emit('open_file_response', {'error': 'No file exists'})
#     else:
#         # Iterate until its read at least 100 lines at end of file
#         BLOCK_SIZE = 4098
#         block_count = -1
#         lines = []
#         with open(file_name, 'rb') as f:
#             try:
#                 while True:
#                     f.seek(block_count*BLOCK_SIZE, os.SEEK_END)
#                     lines = f.readlines()
#                     if len(lines) < 100:
#                         block_count -= 1
#                     else:
#                         break
#             except:
#                 # If too small to read all blocks, just read entire file
#                 f.seek(0,0)
#                 lines = f.readlines()

#         # Keep up to 100 latest lines
#         lines = lines[-100:]
#         lines = list(map(lambda s: s.decode("utf-8"), lines))
#         emit('open_file_response', {'data': lines})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=PORT)