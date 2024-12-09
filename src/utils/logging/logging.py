import logging
import os
import sys
import time
import json
from config import config

curr_time = str(round(time.time() * 1000))

# Setup formatters and handlers
class CustomFormatter(logging.Formatter):
    # Using console color codes to style text
    reset = "\x1b[0m"
    base_time = "[%(asctime)s]" + reset
    base_level = "[%(levelname)-5.5s]" + reset
    base_func = "[%(funcName)s:%(lineno)d]:" + reset
    base_msg = "%(message)s" + reset

    template_line = "\x1b[1m\x1b[1;34m" + base_time + " {}" + base_level + " \x1b[1m\x1b[1;33m" + base_func + " " + base_msg

    FORMATS = {
        logging.DEBUG: template_line.format("\x1b[1m\x1b[1;30m\x1b[47m"),
        logging.INFO: template_line.format("\x1b[1m\x1b[1;30m\x1b[42m"),
        logging.WARNING: template_line.format("\x1b[1m\x1b[1;30m\x1b[43m"),
        logging.ERROR: template_line.format("\x1b[1m\x1b[1;30m\x1b[41m"),
        logging.CRITICAL: template_line.format("\x1b[1m\x1b[31m\x1b[45m")
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

sys_console_handler = logging.StreamHandler(sys.stdout)
sys_console_handler.setFormatter(CustomFormatter())
    
sys_file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)-5.5s] [%(funcName)s:%(lineno)d]: %(message)s")
sys_file_handler = logging.FileHandler(os.path.join(config['sys_log_dir'], f"{curr_time}.log"))
sys_file_handler.setFormatter(sys_file_formatter)

dialog_formatter = logging.Formatter("[%(asctime)s] %(message)s")
dialog_file_handler = logging.FileHandler(os.path.join(config['dialog_log_dir'], f"{curr_time}.log"))
dialog_file_handler.setFormatter(dialog_formatter)

response_formatter = logging.Formatter("%(message)s")
response_file_handler = logging.FileHandler(os.path.join(config['response_log_dir'], f"{curr_time}.log"))
response_file_handler.setFormatter(response_formatter)

# Create loggers
system_logger = logging.getLogger('system_logger')
system_logger.setLevel(getattr(logging, config['log_level']))
system_logger.addHandler(sys_file_handler)
system_logger.addHandler(sys_console_handler)

dialog_logger = logging.getLogger('dialog_logger')
dialog_logger.setLevel(logging.INFO)
dialog_logger.addHandler(dialog_file_handler)

response_logger = logging.getLogger('response_logger')
response_logger.setLevel(logging.INFO)
response_logger.addHandler(response_file_handler)

def save_dialogue(content: str, author: str):
    dialog_logger.info(f"[{author}]: {content}")

def save_response(prompt: str, convo: str, response: str):
    response_obj = {
        "time": round(time.time() * 1000),
        "prompt": prompt,
        "user_input": convo,
        "response": response
    }
    response_logger.info(json.dumps(response_obj))

