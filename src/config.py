import json

def get_config(config_filepath: str):
    with open(config_filepath, 'r') as f:
        config = json.load(f)

    return config

