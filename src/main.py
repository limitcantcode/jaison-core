from utils.logging import setup_logger
setup_logger()
from utils.args import args
from dotenv import load_dotenv
load_dotenv(dotenv_path=args.env)

from utils.jaison import JAIson

# Initial loading
from utils.config import Config
Config()

jaison_main = JAIson()
