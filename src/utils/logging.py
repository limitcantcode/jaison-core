import logging
import os
import sys
from utils.helpers.time import get_current_time
from utils.args import args

START_TIME = get_current_time(include_ms=False,as_str=False)

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
    
def setup_logger():
    global START_TIME
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, args.log_level))

    file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)-5.5s] [%(filename)s::%(lineno)d %(funcName)s]: %(message)s")
    file_handler = logging.FileHandler(
        os.path.join(args.log_dir, "{}.log".format(get_current_time(include_ms=False,as_str=False).strftime("%Y-%m-%d"))))
    file_handler.setFormatter(file_formatter)
        
    logger.addHandler(file_handler)

    if not args.silent:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)