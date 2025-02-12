from dotenv import load_dotenv
from utils.args import args
load_dotenv(dotenv_path=args.env)

from utils.logging import create_sys_logger
logger = create_sys_logger(use_stdout=True)

import asyncio
from utils.server import start_web_server

if __name__=="__main__":
    asyncio.run(start_web_server())