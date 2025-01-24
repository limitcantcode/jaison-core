import logging
import os
import sys
import time
import json
from utils.time import get_current_time
from utils.args import args

SUBFOLDER_SYS = 'sys'
SUBFOLDER_DIALOG = 'dialog'
SUBFOLDER_RESPONSE = 'response'
START_TIME = get_current_time(include_ms=False,as_str=False)

def get_time_filename(time):
    return time.strftime("%Y-%m-%d")

## FOR SYSTEM LOGGING ###########################

SYSTEM_LOGGERS = {}

# Setup formatters and handlers
class CustomFormatter(logging.Formatter):
    # Using console color codes to style text
    reset = "\x1b[0m"
    base_time = "[%(asctime)s]" + reset
    base_level = "[%(levelname)-5.5s]" + reset
    base_func = "[%(filename)s::%(lineno)d %(funcName)s]:" + reset
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

def create_file_handler(id = 'main'):
    file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)-5.5s] [%(filename)s::%(lineno)d %(funcName)s]: %(message)s")
    file_handler = logging.FileHandler(os.path.join(args.log_dir, SUBFOLDER_SYS, f"{get_time_filename(START_TIME)}_sys_{id}.log"))
    file_handler.setFormatter(file_formatter)
    return file_handler
    
def create_sys_logger(id = 'main', use_stdout = False):
    global SYSTEM_LOGGERS
    logger = None
    if id not in SYSTEM_LOGGERS:
        logger = logging.getLogger(f"sys_{id}")
        logger.setLevel(getattr(logging, args.log_level))

        logger.addHandler(create_file_handler(id))
        
        if use_stdout:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(CustomFormatter())
            logger.addHandler(console_handler)
        
        SYSTEM_LOGGERS[id] = logger
    else:
        logger = SYSTEM_LOGGERS[id]

    return logger

## FOR DIALOG LOGGING ################
dialog_formatter = logging.Formatter("[%(asctime)s] %(message)s")
dialog_file_handler = logging.FileHandler(os.path.join(args.log_dir, SUBFOLDER_DIALOG, f"{get_time_filename(START_TIME)}_dialog.log"))
dialog_file_handler.setFormatter(dialog_formatter)

dialog_logger = logging.getLogger('dialog')
dialog_logger.setLevel(logging.INFO)
dialog_logger.addHandler(dialog_file_handler)

def save_dialogue(line: str):
    dialog_logger.info(line)

## FOR RESPONSE OBJECT LOGGING ###################
response_formatter = logging.Formatter("%(message)s")
response_file_handler = logging.FileHandler(os.path.join(args.log_dir, SUBFOLDER_RESPONSE, f"{get_time_filename(START_TIME)}_response.log"))
response_file_handler.setFormatter(response_formatter)

response_logger = logging.getLogger('response')
response_logger.setLevel(logging.INFO)
response_logger.addHandler(response_file_handler)

def save_response(sys_prompt: str, user_prompt: str, response: str):
    response_obj = {
        "time": get_current_time(),
        "prompt": sys_prompt,
        "user_input": user_prompt,
        "response": response
    }
    response_logger.info(json.dumps(response_obj))

