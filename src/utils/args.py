import argparse
import os

args = argparse.ArgumentParser()
args.add_argument('--config', required=True, type=str, help='Filename to your json config. For example: "example.json" refers to configs/components/example.json')
args.add_argument('--log_level', default='INFO', type=str, choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'], help='Level of logs to show')
args.add_argument('--log_dir', default=os.path.join(os.getcwd(), 'logs'), type=str, help='Storing folder for logs')
args = args.parse_args()