import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logging import create_sys_logger
logger = create_sys_logger(use_stdout=True)

import asyncio
from src.utils.server import start_web_server

if __name__ == "__main__":
    asyncio.run(start_web_server())