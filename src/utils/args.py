import argparse
import os

args = argparse.ArgumentParser()
args.add_argument('-e', '--env', default=None, type=str, help='Filepath to .env if located elsewhere')
args.add_argument('-c', '--config', default=None, type=str, help='Filename to your yaml config. For example: "example" refers to configs/example.yaml')
args.add_argument('--host', default='127.0.0.1', type=str, help='IP to use as host API and websocket server on. Try 0.0.0.0 for cross machine access to API.')
args.add_argument('--port', default=7272, type=int, help='Post to host API and websocket server on.')
args.add_argument('--log_level', default='INFO', type=str, choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'], help='Level of logs to show')
args.add_argument('--log_dir', default=os.path.join(os.getcwd(), 'logs'), type=str, help='Storing folder for logs')
args.add_argument('--silent', action='store_true', help='Suppress console outputs')
args = args.parse_args()