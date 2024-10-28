import json
import argparse

args = argparse.ArgumentParser()
args.add_argument('--config', required=True, type=str, help='Filepath to your json config. See configs/example.json for example.')
args = args.parse_args()

config = None
with open(args.config, 'r') as f:
    config = json.load(f)

