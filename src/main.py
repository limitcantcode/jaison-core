from utils.logging import setup_logger
setup_logger()

from utils.args import args
from dotenv import load_dotenv
load_dotenv(dotenv_path=args.env)

import asyncio
from utils.server import start_web_server

asyncio.run(start_web_server())